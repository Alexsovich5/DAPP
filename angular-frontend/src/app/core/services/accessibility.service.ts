import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface AriaLiveRegion {
  id: string;
  message: string;
  priority: 'polite' | 'assertive';
  duration?: number;
}

export interface FocusableElement {
  element: HTMLElement;
  originalTabIndex?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AccessibilityService {
  private announcements$ = new BehaviorSubject<AriaLiveRegion[]>([]);
  private focusStack: HTMLElement[] = [];
  private originalFocusElement: HTMLElement | null = null;

  /**
   * Announce a message to screen readers
   * @param message - The message to announce
   * @param priority - Whether to interrupt current announcements ('assertive') or wait ('polite')
   * @param duration - How long to keep the announcement (default: 3000ms)
   */
  announce(message: string, priority: 'polite' | 'assertive' = 'polite', duration: number = 3000): void {
    const announcement: AriaLiveRegion = {
      id: this.generateId(),
      message,
      priority,
      duration
    };

    // Create live region element
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', priority);
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.id = announcement.id;
    liveRegion.textContent = message;

    document.body.appendChild(liveRegion);

    // Remove after duration
    setTimeout(() => {
      const element = document.getElementById(announcement.id);
      if (element) {
        document.body.removeChild(element);
      }
    }, duration);

    // Add to announcements stream
    const current = this.announcements$.value;
    this.announcements$.next([...current, announcement]);

    // Clean up announcements stream
    setTimeout(() => {
      const updated = this.announcements$.value.filter(a => a.id !== announcement.id);
      this.announcements$.next(updated);
    }, duration);
  }

  /**
   * Get current announcements
   */
  getAnnouncements(): Observable<AriaLiveRegion[]> {
    return this.announcements$.asObservable();
  }

  /**
   * Trap focus within a container element
   * @param container - The container to trap focus within
   * @param autoFocus - Whether to automatically focus the first focusable element
   */
  trapFocus(container: HTMLElement, autoFocus: boolean = true): void {
    this.originalFocusElement = document.activeElement as HTMLElement;
    
    const focusableElements = this.getFocusableElements(container);
    
    if (focusableElements.length === 0) {
      return;
    }

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Focus first element if autoFocus is enabled
    if (autoFocus) {
      firstElement.focus();
    }

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        // Shift + Tab: moving backwards
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab: moving forwards
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    
    // Store cleanup function
    const cleanup = () => {
      container.removeEventListener('keydown', handleTabKey);
    };

    // Store cleanup for later use
    (container as any)._focusTrapCleanup = cleanup;
  }

  /**
   * Release focus trap and restore original focus
   * @param container - The container that had focus trapped
   */
  releaseFocusTrap(container: HTMLElement): void {
    const cleanup = (container as any)._focusTrapCleanup;
    if (cleanup) {
      cleanup();
      delete (container as any)._focusTrapCleanup;
    }

    // Restore original focus
    if (this.originalFocusElement) {
      this.originalFocusElement.focus();
      this.originalFocusElement = null;
    }
  }

  /**
   * Get all focusable elements within a container
   */
  private getFocusableElements(container: HTMLElement): HTMLElement[] {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      'iframe',
      'object',
      'embed',
      '[contenteditable]',
      'audio[controls]',
      'video[controls]',
      'summary'
    ].join(', ');

    const elements = Array.from(container.querySelectorAll(focusableSelectors)) as HTMLElement[];
    
    return elements.filter(element => {
      return !this.isHidden(element) && this.isVisible(element);
    });
  }

  /**
   * Check if an element is hidden
   */
  private isHidden(element: HTMLElement): boolean {
    return element.hasAttribute('hidden') || 
           element.getAttribute('aria-hidden') === 'true' ||
           element.style.display === 'none' ||
           element.style.visibility === 'hidden';
  }

  /**
   * Check if an element is visible
   */
  private isVisible(element: HTMLElement): boolean {
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  /**
   * Set the page title for screen readers
   * @param title - The page title
   * @param announceChange - Whether to announce the title change
   */
  setPageTitle(title: string, announceChange: boolean = true): void {
    document.title = title;
    
    if (announceChange) {
      this.announce(`Navigated to ${title}`, 'polite');
    }
  }

  /**
   * Update aria-label or aria-labelledby on an element
   * @param element - The element to update
   * @param label - The label text or ID of labelling element
   * @param useAriaLabelledBy - Whether to use aria-labelledby instead of aria-label
   */
  setElementLabel(element: HTMLElement, label: string, useAriaLabelledBy: boolean = false): void {
    if (useAriaLabelledBy) {
      element.setAttribute('aria-labelledby', label);
      element.removeAttribute('aria-label');
    } else {
      element.setAttribute('aria-label', label);
      element.removeAttribute('aria-labelledby');
    }
  }

  /**
   * Update aria-describedby on an element
   * @param element - The element to update
   * @param descriptionId - ID of the element that describes this element
   */
  setElementDescription(element: HTMLElement, descriptionId: string): void {
    element.setAttribute('aria-describedby', descriptionId);
  }

  /**
   * Mark an element as expanded or collapsed
   * @param element - The element to update
   * @param expanded - Whether the element is expanded
   */
  setExpanded(element: HTMLElement, expanded: boolean): void {
    element.setAttribute('aria-expanded', expanded.toString());
  }

  /**
   * Mark an element as selected or unselected
   * @param element - The element to update
   * @param selected - Whether the element is selected
   */
  setSelected(element: HTMLElement, selected: boolean): void {
    element.setAttribute('aria-selected', selected.toString());
  }

  /**
   * Mark an element as pressed or unpressed (for toggle buttons)
   * @param element - The element to update
   * @param pressed - Whether the element is pressed
   */
  setPressed(element: HTMLElement, pressed: boolean): void {
    element.setAttribute('aria-pressed', pressed.toString());
  }

  /**
   * Set the current value and range for sliders/progress bars
   * @param element - The element to update
   * @param value - Current value
   * @param min - Minimum value
   * @param max - Maximum value
   */
  setValueRange(element: HTMLElement, value: number, min: number, max: number): void {
    element.setAttribute('aria-valuenow', value.toString());
    element.setAttribute('aria-valuemin', min.toString());
    element.setAttribute('aria-valuemax', max.toString());
  }

  /**
   * Set aria-busy state for loading elements
   * @param element - The element to update
   * @param busy - Whether the element is busy/loading
   */
  setBusy(element: HTMLElement, busy: boolean): void {
    element.setAttribute('aria-busy', busy.toString());
  }

  /**
   * Programmatically click an element (useful for keyboard events)
   * @param element - The element to click
   */
  programmaticClick(element: HTMLElement): void {
    const event = new MouseEvent('click', {
      view: window,
      bubbles: true,
      cancelable: true
    });
    element.dispatchEvent(event);
  }

  /**
   * Check if the user prefers reduced motion
   */
  prefersReducedMotion(): boolean {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /**
   * Check if the user prefers high contrast
   */
  prefersHighContrast(): boolean {
    return window.matchMedia('(prefers-contrast: high)').matches;
  }

  /**
   * Check if the user is using a screen reader
   */
  isUsingScreenReader(): boolean {
    // This is a best-effort detection - not foolproof
    return !!(
      window.navigator.userAgent.match(/NVDA|JAWS|VoiceOver|ORCA|TalkBack/i) ||
      window.speechSynthesis?.getVoices().length > 0
    );
  }

  /**
   * Generate a unique ID for elements
   */
  private generateId(): string {
    return 'aria-' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Validate ARIA attributes on an element
   * @param element - The element to validate
   * @returns Array of validation errors
   */
  validateAriaAttributes(element: HTMLElement): string[] {
    const errors: string[] = [];
    const tagName = element.tagName.toLowerCase();
    const role = element.getAttribute('role');

    // Check for invalid role values
    const validRoles = [
      'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
      'cell', 'checkbox', 'columnheader', 'combobox', 'complementary',
      'contentinfo', 'definition', 'dialog', 'directory', 'document',
      'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
      'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main',
      'marquee', 'math', 'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
      'menuitemradio', 'navigation', 'none', 'note', 'option', 'presentation',
      'progressbar', 'radio', 'radiogroup', 'region', 'row', 'rowgroup',
      'rowheader', 'scrollbar', 'search', 'searchbox', 'separator',
      'slider', 'spinbutton', 'status', 'switch', 'tab', 'table',
      'tablist', 'tabpanel', 'term', 'textbox', 'timer', 'toolbar',
      'tooltip', 'tree', 'treegrid', 'treeitem'
    ];

    if (role && !validRoles.includes(role)) {
      errors.push(`Invalid role: "${role}"`);
    }

    // Check for required ARIA attributes based on role
    if (role === 'button' && !element.hasAttribute('aria-label') && !element.textContent?.trim()) {
      errors.push('Button role requires aria-label or visible text');
    }

    if (role === 'slider') {
      if (!element.hasAttribute('aria-valuenow')) {
        errors.push('Slider role requires aria-valuenow');
      }
      if (!element.hasAttribute('aria-valuemin')) {
        errors.push('Slider role requires aria-valuemin');
      }
      if (!element.hasAttribute('aria-valuemax')) {
        errors.push('Slider role requires aria-valuemax');
      }
    }

    // Check for orphaned aria-describedby/aria-labelledby
    const describedBy = element.getAttribute('aria-describedby');
    if (describedBy && !document.getElementById(describedBy)) {
      errors.push(`aria-describedby references non-existent element: "${describedBy}"`);
    }

    const labelledBy = element.getAttribute('aria-labelledby');
    if (labelledBy && !document.getElementById(labelledBy)) {
      errors.push(`aria-labelledby references non-existent element: "${labelledBy}"`);
    }

    return errors;
  }
}