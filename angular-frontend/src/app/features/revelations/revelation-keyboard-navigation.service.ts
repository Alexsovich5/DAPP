import { Injectable, ElementRef } from '@angular/core';
import { fromEvent, Subject } from 'rxjs';
import { takeUntil, filter } from 'rxjs/operators';

export interface NavigableElement {
  id: string;
  element: HTMLElement;
  type: 'step' | 'form' | 'action' | 'timeline-item';
  priority: number;
  isEnabled: boolean;
  ariaLabel?: string;
}

export interface KeyboardNavigationConfig {
  enableArrowKeys: boolean;
  enableTabTrapping: boolean;
  enableShortcuts: boolean;
  announceChanges: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class RevelationKeyboardNavigationService {
  private navigableElements: NavigableElement[] = [];
  private currentIndex = 0;
  private destroy$ = new Subject<void>();
  private container?: HTMLElement;
  private config: KeyboardNavigationConfig = {
    enableArrowKeys: true,
    enableTabTrapping: true,
    enableShortcuts: true,
    announceChanges: true
  };

  // Observable for external components to listen to navigation events
  private navigationEvent$ = new Subject<{
    action: string;
    element: NavigableElement;
    index: number;
  }>();

  get navigationEvents$() {
    return this.navigationEvent$.asObservable();
  }

  /**
   * Initialize keyboard navigation for the revelations component
   */
  initialize(containerRef: ElementRef, config?: Partial<KeyboardNavigationConfig>): void {
    this.container = containerRef.nativeElement;
    this.config = { ...this.config, ...config };

    this.setupKeyboardListeners();
    this.updateNavigableElements();
    this.focusFirstElement();
  }

  /**
   * Clean up event listeners and reset state
   */
  destroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.navigableElements = [];
    this.currentIndex = 0;
  }

  /**
   * Update the list of navigable elements
   */
  updateNavigableElements(): void {
    if (!this.container) return;

    const elements: NavigableElement[] = [];

    // Find all focusable elements in the container
    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'textarea:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '.day-circle',
      '.revelation-item',
      '.prompt-card',
      '.photo-reveal-card'
    ];

    const focusableElements = this.container.querySelectorAll(
      focusableSelectors.join(', ')
    ) as NodeListOf<HTMLElement>;

    focusableElements.forEach((element, index) => {
      if (this.isElementVisible(element)) {
        elements.push({
          id: element.id || `nav-element-${index}`,
          element,
          type: this.getElementType(element),
          priority: this.getElementPriority(element),
          isEnabled: !element.hasAttribute('disabled'),
          ariaLabel: element.getAttribute('aria-label') || element.textContent?.trim()
        });
      }
    });

    // Sort by priority and position
    this.navigableElements = elements.sort((a, b) => {
      if (a.priority !== b.priority) {
        return a.priority - b.priority;
      }
      // Secondary sort by DOM position
      return this.getDOMPosition(a.element) - this.getDOMPosition(b.element);
    });

    // Ensure current index is valid
    if (this.currentIndex >= this.navigableElements.length) {
      this.currentIndex = Math.max(0, this.navigableElements.length - 1);
    }
  }

  /**
   * Navigate to the next element
   */
  navigateNext(): void {
    const nextIndex = this.findNextNavigableIndex(1);
    if (nextIndex !== -1) {
      this.navigateToIndex(nextIndex);
    }
  }

  /**
   * Navigate to the previous element
   */
  navigatePrevious(): void {
    const prevIndex = this.findNextNavigableIndex(-1);
    if (prevIndex !== -1) {
      this.navigateToIndex(prevIndex);
    }
  }

  /**
   * Navigate to a specific element by ID
   */
  navigateToId(id: string): boolean {
    const index = this.navigableElements.findIndex(el => el.id === id);
    if (index !== -1) {
      this.navigateToIndex(index);
      return true;
    }
    return false;
  }

  /**
   * Navigate to a specific day in the progress
   */
  navigateToDay(day: number): void {
    const dayElement = this.container?.querySelector(`.day-circle:nth-child(${day})`) as HTMLElement;
    if (dayElement) {
      this.focusElement(dayElement);
      this.announceNavigation(`Navigated to Day ${day}`);
    }
  }

  /**
   * Focus the current revelation form
   */
  focusRevelationForm(): void {
    const formElement = this.container?.querySelector('#revelation-content') as HTMLElement;
    if (formElement) {
      this.focusElement(formElement);
      this.announceNavigation('Focused on revelation form');
    }
  }

  /**
   * Navigate to timeline items
   */
  navigateTimelineItems(direction: 'next' | 'previous'): void {
    const timelineItems = this.navigableElements.filter(el => el.type === 'timeline-item');
    if (timelineItems.length === 0) return;

    const currentTimelineIndex = timelineItems.findIndex(
      item => item.element === this.navigableElements[this.currentIndex]?.element
    );

    let targetIndex: number;
    if (direction === 'next') {
      targetIndex = currentTimelineIndex + 1 < timelineItems.length ? currentTimelineIndex + 1 : 0;
    } else {
      targetIndex = currentTimelineIndex - 1 >= 0 ? currentTimelineIndex - 1 : timelineItems.length - 1;
    }

    const targetElement = timelineItems[targetIndex];
    const globalIndex = this.navigableElements.findIndex(el => el.id === targetElement.id);
    if (globalIndex !== -1) {
      this.navigateToIndex(globalIndex);
    }
  }

  /**
   * Get the currently focused element
   */
  getCurrentElement(): NavigableElement | null {
    return this.navigableElements[this.currentIndex] || null;
  }

  /**
   * Check if an element is currently focused
   */
  isElementFocused(element: HTMLElement): boolean {
    return this.navigableElements[this.currentIndex]?.element === element;
  }

  private setupKeyboardListeners(): void {
    if (!this.container) return;

    const keydown$ = fromEvent<KeyboardEvent>(this.container, 'keydown');

    // Handle keydown events
    keydown$.pipe(
      takeUntil(this.destroy$),
      filter(event => this.shouldHandleKeyEvent(event))
    ).subscribe(event => {
      this.handleKeyDown(event);
    });

    // Handle focus events for accessibility
    fromEvent(this.container, 'focusin').pipe(
      takeUntil(this.destroy$)
    ).subscribe((event: Event) => {
      const target = event.target as HTMLElement;
      this.updateCurrentIndexFromFocus(target);
    });
  }

  private handleKeyDown(event: KeyboardEvent): void {
    const { key, ctrlKey, metaKey, shiftKey } = event;

    // Arrow key navigation
    if (this.config.enableArrowKeys) {
      switch (key) {
        case 'ArrowDown':
        case 'ArrowRight':
          event.preventDefault();
          this.navigateNext();
          break;
        case 'ArrowUp':
        case 'ArrowLeft':
          event.preventDefault();
          this.navigatePrevious();
          break;
      }
    }

    // Tab key handling with trapping
    if (key === 'Tab' && this.config.enableTabTrapping) {
      if (shiftKey) {
        this.navigatePrevious();
      } else {
        this.navigateNext();
      }
      event.preventDefault();
    }

    // Shortcut keys
    if (this.config.enableShortcuts) {
      const modifierPressed = ctrlKey || metaKey;

      switch (key) {
        case 'Home':
          event.preventDefault();
          this.navigateToIndex(0);
          break;
        case 'End':
          event.preventDefault();
          this.navigateToIndex(this.navigableElements.length - 1);
          break;
        case 'Enter':
        case ' ':
          if (this.navigableElements[this.currentIndex]?.element.tagName === 'BUTTON') {
            event.preventDefault();
            this.activateCurrentElement();
          }
          break;
        case 'f':
          if (modifierPressed) {
            event.preventDefault();
            this.focusRevelationForm();
          }
          break;
        case 't':
          if (modifierPressed) {
            event.preventDefault();
            this.navigateTimelineItems('next');
          }
          break;
      }

      // Number keys for day navigation
      if (key >= '1' && key <= '7' && modifierPressed) {
        event.preventDefault();
        this.navigateToDay(parseInt(key));
      }
    }

    // Escape key to exit navigation mode
    if (key === 'Escape') {
      this.blur();
    }
  }

  private navigateToIndex(index: number): void {
    if (index < 0 || index >= this.navigableElements.length) return;

    this.currentIndex = index;
    const element = this.navigableElements[index];

    this.focusElement(element.element);
    this.announceNavigation(
      `${element.ariaLabel || 'Element'} (${index + 1} of ${this.navigableElements.length})`
    );

    this.navigationEvent$.next({
      action: 'navigate',
      element,
      index
    });
  }

  private findNextNavigableIndex(direction: 1 | -1): number {
    const totalElements = this.navigableElements.length;
    if (totalElements === 0) return -1;

    for (let i = 1; i < totalElements; i++) {
      const nextIndex = (this.currentIndex + (direction * i) + totalElements) % totalElements;
      const element = this.navigableElements[nextIndex];

      if (element.isEnabled && this.isElementVisible(element.element)) {
        return nextIndex;
      }
    }

    return -1;
  }

  private focusElement(element: HTMLElement): void {
    element.focus();
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Add visual focus indicator
    element.classList.add('keyboard-focused');
    setTimeout(() => {
      element.classList.remove('keyboard-focused');
    }, 200);
  }

  private focusFirstElement(): void {
    if (this.navigableElements.length > 0) {
      this.navigateToIndex(0);
    }
  }

  private activateCurrentElement(): void {
    const element = this.navigableElements[this.currentIndex]?.element;
    if (element) {
      element.click();
      this.announceNavigation('Activated');
    }
  }

  private blur(): void {
    const activeElement = document.activeElement as HTMLElement;
    if (activeElement) {
      activeElement.blur();
    }
  }

  private updateCurrentIndexFromFocus(target: HTMLElement): void {
    const index = this.navigableElements.findIndex(el => el.element === target);
    if (index !== -1) {
      this.currentIndex = index;
    }
  }

  private getElementType(element: HTMLElement): NavigableElement['type'] {
    if (element.classList.contains('day-circle')) return 'step';
    if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') return 'form';
    if (element.classList.contains('revelation-item')) return 'timeline-item';
    return 'action';
  }

  private getElementPriority(element: HTMLElement): number {
    // Higher priority = lower number (sorted first)
    if (element.classList.contains('day-circle')) return 1;
    if (element.id === 'revelation-content') return 2;
    if (element.classList.contains('share-btn')) return 3;
    if (element.classList.contains('revelation-item')) return 4;
    if (element.classList.contains('action-btn')) return 5;
    return 10;
  }

  private getDOMPosition(element: HTMLElement): number {
    const rect = element.getBoundingClientRect();
    return rect.top * 1000 + rect.left;
  }

  private isElementVisible(element: HTMLElement): boolean {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);

    return rect.width > 0 &&
           rect.height > 0 &&
           style.visibility !== 'hidden' &&
           style.display !== 'none' &&
           element.offsetParent !== null;
  }

  private shouldHandleKeyEvent(event: KeyboardEvent): boolean {
    const target = event.target as HTMLElement;

    // Don't handle if in an input/textarea unless it's specific navigation keys
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
      return ['Escape', 'Tab', 'F1'].includes(event.key) ||
             (event.ctrlKey || event.metaKey);
    }

    return true;
  }

  private announceNavigation(message: string): void {
    if (!this.config.announceChanges) return;

    // Create screen reader announcement
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    setTimeout(() => {
      if (announcement.parentNode) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  }
}
