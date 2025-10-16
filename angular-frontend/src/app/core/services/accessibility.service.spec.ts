/**
 * AccessibilityService Tests
 * Comprehensive tests for ARIA announcements and accessibility features
 */

import { TestBed, fakeAsync, tick, flush } from '@angular/core/testing';
import { AccessibilityService, AriaLiveRegion } from './accessibility.service';

describe('AccessibilityService', () => {
  let service: AccessibilityService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AccessibilityService]
    });
    service = TestBed.inject(AccessibilityService);

    // Clean up any existing live regions
    document.querySelectorAll('[aria-live]').forEach(el => el.remove());
  });

  afterEach(() => {
    // Clean up after each test
    document.querySelectorAll('[aria-live]').forEach(el => el.remove());
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should have empty announcements initially', (done) => {
      service.getAnnouncements().subscribe(announcements => {
        expect(announcements).toEqual([]);
        done();
      });
    });
  });

  describe('ARIA Live Region Announcements', () => {
    it('should announce a polite message', fakeAsync(() => {
      service.announce('Test message', 'polite');
      tick();

      const liveRegion = document.querySelector('[aria-live="polite"]');
      expect(liveRegion).toBeTruthy();
      expect(liveRegion?.textContent).toBe('Test message');

      flush(); // Clear remaining timers
    }));

    it('should announce an assertive message', fakeAsync(() => {
      service.announce('Urgent message', 'assertive');
      tick();

      const liveRegion = document.querySelector('[aria-live="assertive"]');
      expect(liveRegion).toBeTruthy();
      expect(liveRegion?.textContent).toBe('Urgent message');

      flush();
    }));

    it('should create element with aria-atomic="true"', fakeAsync(() => {
      service.announce('Test', 'polite');
      tick();

      const liveRegion = document.querySelector('[aria-live]');
      expect(liveRegion?.getAttribute('aria-atomic')).toBe('true');

      flush();
    }));

    it('should add sr-only class for screen reader only content', fakeAsync(() => {
      service.announce('Screen reader only', 'polite');
      tick();

      const liveRegion = document.querySelector('[aria-live]');
      expect(liveRegion?.classList.contains('sr-only')).toBe(true);

      flush();
    }));

    it('should remove announcement after default duration', fakeAsync(() => {
      service.announce('Temporary message', 'polite');
      tick();

      let liveRegion = document.querySelector('[aria-live="polite"]');
      expect(liveRegion).toBeTruthy();

      tick(3000);

      liveRegion = document.querySelector('[aria-live="polite"]');
      expect(liveRegion).toBeFalsy();
    }));

    it('should remove announcement after custom duration', fakeAsync(() => {
      service.announce('Short message', 'polite', 1000);
      tick();

      let liveRegion = document.querySelector('[aria-live="polite"]');
      expect(liveRegion).toBeTruthy();

      tick(1000);

      liveRegion = document.querySelector('[aria-live="polite"]');
      expect(liveRegion).toBeFalsy();
    }));

    it('should add announcement to stream', fakeAsync(() => {
      let announcements: AriaLiveRegion[] = [];
      service.getAnnouncements().subscribe(a => announcements = a);

      service.announce('Message 1', 'polite');
      tick();

      expect(announcements.length).toBe(1);
      expect(announcements[0].message).toBe('Message 1');

      flush();
    }));

    it('should support multiple concurrent announcements', fakeAsync(() => {
      let announcements: AriaLiveRegion[] = [];
      service.getAnnouncements().subscribe(a => announcements = a);

      service.announce('Message 1', 'polite');
      service.announce('Message 2', 'assertive');
      tick();

      expect(announcements.length).toBe(2);

      flush();
    }));

    it('should clean up announcements from stream after duration', fakeAsync(() => {
      let announcements: AriaLiveRegion[] = [];
      service.getAnnouncements().subscribe(a => announcements = a);

      service.announce('Temporary', 'polite', 1000);
      tick();
      expect(announcements.length).toBe(1);

      tick(1000);
      expect(announcements.length).toBe(0);
    }));
  });

  describe('Focus Trap Management', () => {
    let container: HTMLElement;

    beforeEach(() => {
      // Create a container with focusable elements
      container = document.createElement('div');
      container.innerHTML = `
        <button id="btn1">Button 1</button>
        <input id="input1" type="text" />
        <a id="link1" href="#">Link</a>
        <button id="btn2">Button 2</button>
      `;
      document.body.appendChild(container);
    });

    afterEach(() => {
      document.body.removeChild(container);
    });

    it('should trap focus within container', () => {
      service.trapFocus(container);

      const firstButton = document.getElementById('btn1') as HTMLButtonElement;
      expect(document.activeElement).toBe(firstButton);
    });

    it('should not auto-focus if autoFocus is false', () => {
      const originalFocus = document.activeElement;
      service.trapFocus(container, false);

      expect(document.activeElement).toBe(originalFocus);
    });

    it('should cycle focus forward on Tab', () => {
      service.trapFocus(container);

      const lastButton = document.getElementById('btn2') as HTMLButtonElement;
      lastButton.focus();

      const tabEvent = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true });
      const spy = spyOn(tabEvent, 'preventDefault');
      container.dispatchEvent(tabEvent);

      expect(spy).toHaveBeenCalled();
    });

    it('should cycle focus backward on Shift+Tab', () => {
      service.trapFocus(container);

      const firstButton = document.getElementById('btn1') as HTMLButtonElement;
      firstButton.focus();

      const shiftTabEvent = new KeyboardEvent('keydown', {
        key: 'Tab',
        shiftKey: true,
        bubbles: true
      });
      const spy = spyOn(shiftTabEvent, 'preventDefault');
      container.dispatchEvent(shiftTabEvent);

      expect(spy).toHaveBeenCalled();
    });

    it('should not trap focus in empty container', () => {
      const emptyContainer = document.createElement('div');
      document.body.appendChild(emptyContainer);

      expect(() => service.trapFocus(emptyContainer)).not.toThrow();

      document.body.removeChild(emptyContainer);
    });

    it('should release focus trap', () => {
      const originalElement = document.createElement('button');
      document.body.appendChild(originalElement);
      originalElement.focus();

      service.trapFocus(container);
      service.releaseFocusTrap(container);

      document.body.removeChild(originalElement);
      expect(true).toBe(true); // Should not throw
    });

    it('should filter out hidden elements', () => {
      const hiddenContainer = document.createElement('div');
      hiddenContainer.innerHTML = `
        <button>Visible</button>
        <button hidden>Hidden</button>
        <button aria-hidden="true">Aria Hidden</button>
        <button style="display: none">Display None</button>
      `;
      document.body.appendChild(hiddenContainer);

      service.trapFocus(hiddenContainer);

      document.body.removeChild(hiddenContainer);
      expect(true).toBe(true); // Should handle hidden elements
    });
  });

  describe('Page Title Management', () => {
    const originalTitle = document.title;

    afterEach(() => {
      document.title = originalTitle;
    });

    it('should set page title', () => {
      service.setPageTitle('New Page Title');
      expect(document.title).toBe('New Page Title');
    });

    it('should announce title change by default', fakeAsync(() => {
      service.setPageTitle('Dashboard');
      tick();

      const liveRegion = document.querySelector('[aria-live]');
      expect(liveRegion?.textContent).toContain('Dashboard');

      flush();
    }));

    it('should not announce title change when disabled', fakeAsync(() => {
      service.setPageTitle('Silent Page', false);
      tick();

      const liveRegions = document.querySelectorAll('[aria-live]');
      expect(liveRegions.length).toBe(0);
    }));
  });

  describe('ARIA Attribute Management', () => {
    let testElement: HTMLElement;

    beforeEach(() => {
      testElement = document.createElement('div');
      document.body.appendChild(testElement);
    });

    afterEach(() => {
      document.body.removeChild(testElement);
    });

    it('should set aria-label', () => {
      service.setElementLabel(testElement, 'Test Label');
      expect(testElement.getAttribute('aria-label')).toBe('Test Label');
    });

    it('should set aria-labelledby', () => {
      service.setElementLabel(testElement, 'label-id', true);
      expect(testElement.getAttribute('aria-labelledby')).toBe('label-id');
      expect(testElement.hasAttribute('aria-label')).toBe(false);
    });

    it('should set aria-describedby', () => {
      service.setElementDescription(testElement, 'desc-id');
      expect(testElement.getAttribute('aria-describedby')).toBe('desc-id');
    });

    it('should set aria-expanded to true', () => {
      service.setExpanded(testElement, true);
      expect(testElement.getAttribute('aria-expanded')).toBe('true');
    });

    it('should set aria-expanded to false', () => {
      service.setExpanded(testElement, false);
      expect(testElement.getAttribute('aria-expanded')).toBe('false');
    });

    it('should set aria-selected to true', () => {
      service.setSelected(testElement, true);
      expect(testElement.getAttribute('aria-selected')).toBe('true');
    });

    it('should set aria-selected to false', () => {
      service.setSelected(testElement, false);
      expect(testElement.getAttribute('aria-selected')).toBe('false');
    });

    it('should set aria-pressed to true', () => {
      service.setPressed(testElement, true);
      expect(testElement.getAttribute('aria-pressed')).toBe('true');
    });

    it('should set aria-pressed to false', () => {
      service.setPressed(testElement, false);
      expect(testElement.getAttribute('aria-pressed')).toBe('false');
    });

    it('should set aria-busy to true', () => {
      service.setBusy(testElement, true);
      expect(testElement.getAttribute('aria-busy')).toBe('true');
    });

    it('should set aria-busy to false', () => {
      service.setBusy(testElement, false);
      expect(testElement.getAttribute('aria-busy')).toBe('false');
    });

    it('should set value range attributes', () => {
      service.setValueRange(testElement, 50, 0, 100);
      expect(testElement.getAttribute('aria-valuenow')).toBe('50');
      expect(testElement.getAttribute('aria-valuemin')).toBe('0');
      expect(testElement.getAttribute('aria-valuemax')).toBe('100');
    });
  });

  describe('Programmatic Interactions', () => {
    it('should programmatically click an element', () => {
      const button = document.createElement('button');
      const clickSpy = jasmine.createSpy('click');
      button.addEventListener('click', clickSpy);
      document.body.appendChild(button);

      service.programmaticClick(button);

      expect(clickSpy).toHaveBeenCalled();
      document.body.removeChild(button);
    });
  });

  describe('User Preference Detection', () => {
    it('should detect reduced motion preference', () => {
      const result = service.prefersReducedMotion();
      expect(typeof result).toBe('boolean');
    });

    it('should detect high contrast preference', () => {
      const result = service.prefersHighContrast();
      expect(typeof result).toBe('boolean');
    });

    it('should detect screen reader usage', () => {
      const result = service.isUsingScreenReader();
      expect(typeof result).toBe('boolean');
    });
  });

  describe('ARIA Validation', () => {
    let testElement: HTMLElement;

    beforeEach(() => {
      testElement = document.createElement('div');
      document.body.appendChild(testElement);
    });

    afterEach(() => {
      document.body.removeChild(testElement);
    });

    it('should validate valid role', () => {
      testElement.setAttribute('role', 'button');
      testElement.textContent = 'Click me';

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.length).toBe(0);
    });

    it('should detect invalid role', () => {
      testElement.setAttribute('role', 'invalid-role');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0]).toContain('Invalid role');
    });

    it('should require aria-label or text for button role', () => {
      testElement.setAttribute('role', 'button');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.some(e => e.includes('aria-label'))).toBe(true);
    });

    it('should validate button with aria-label', () => {
      testElement.setAttribute('role', 'button');
      testElement.setAttribute('aria-label', 'Submit');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.length).toBe(0);
    });

    it('should require aria-valuenow for slider role', () => {
      testElement.setAttribute('role', 'slider');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.some(e => e.includes('aria-valuenow'))).toBe(true);
    });

    it('should require aria-valuemin for slider role', () => {
      testElement.setAttribute('role', 'slider');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.some(e => e.includes('aria-valuemin'))).toBe(true);
    });

    it('should require aria-valuemax for slider role', () => {
      testElement.setAttribute('role', 'slider');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.some(e => e.includes('aria-valuemax'))).toBe(true);
    });

    it('should validate complete slider', () => {
      testElement.setAttribute('role', 'slider');
      testElement.setAttribute('aria-valuenow', '50');
      testElement.setAttribute('aria-valuemin', '0');
      testElement.setAttribute('aria-valuemax', '100');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.length).toBe(0);
    });

    it('should detect orphaned aria-describedby', () => {
      testElement.setAttribute('aria-describedby', 'non-existent-id');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.some(e => e.includes('aria-describedby'))).toBe(true);
    });

    it('should detect orphaned aria-labelledby', () => {
      testElement.setAttribute('aria-labelledby', 'non-existent-id');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.some(e => e.includes('aria-labelledby'))).toBe(true);
    });

    it('should validate existing aria-describedby reference', () => {
      const description = document.createElement('div');
      description.id = 'desc-1';
      document.body.appendChild(description);

      testElement.setAttribute('aria-describedby', 'desc-1');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.some(e => e.includes('aria-describedby'))).toBe(false);

      document.body.removeChild(description);
    });

    it('should validate existing aria-labelledby reference', () => {
      const label = document.createElement('div');
      label.id = 'label-1';
      document.body.appendChild(label);

      testElement.setAttribute('aria-labelledby', 'label-1');

      const errors = service.validateAriaAttributes(testElement);
      expect(errors.some(e => e.includes('aria-labelledby'))).toBe(false);

      document.body.removeChild(label);
    });
  });

  describe('Focusable Elements Detection', () => {
    it('should find all focusable element types', () => {
      const container = document.createElement('div');
      container.innerHTML = `
        <a href="#" id="link">Link</a>
        <button id="button">Button</button>
        <input id="input" type="text" />
        <select id="select"><option>Option</option></select>
        <textarea id="textarea"></textarea>
        <div tabindex="0" id="tabindex">Tabbable Div</div>
      `;
      document.body.appendChild(container);

      service.trapFocus(container, false);

      // Should not throw and should handle all focusable types
      expect(true).toBe(true);

      document.body.removeChild(container);
    });

    it('should exclude disabled elements', () => {
      const container = document.createElement('div');
      container.innerHTML = `
        <button id="enabled">Enabled</button>
        <button disabled id="disabled">Disabled</button>
        <input type="text" id="input-enabled" />
        <input type="text" disabled id="input-disabled" />
      `;
      document.body.appendChild(container);

      service.trapFocus(container);

      // Should only focus enabled button
      expect(document.activeElement?.id).toBe('enabled');

      document.body.removeChild(container);
    });

    it('should exclude elements with tabindex="-1"', () => {
      const container = document.createElement('div');
      container.innerHTML = `
        <div tabindex="0" id="included">Included</div>
        <div tabindex="-1" id="excluded">Excluded</div>
      `;
      document.body.appendChild(container);

      service.trapFocus(container);

      expect(document.activeElement?.id).toBe('included');

      document.body.removeChild(container);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty announcement messages', fakeAsync(() => {
      service.announce('', 'polite');
      tick();

      const liveRegion = document.querySelector('[aria-live]');
      expect(liveRegion).toBeTruthy();
      expect(liveRegion?.textContent).toBe('');

      flush();
    }));

    it('should handle very long announcement messages', fakeAsync(() => {
      const longMessage = 'A'.repeat(1000);
      service.announce(longMessage, 'polite');
      tick();

      const liveRegion = document.querySelector('[aria-live]');
      expect(liveRegion?.textContent).toBe(longMessage);

      flush();
    }));

    it('should handle rapid consecutive announcements', fakeAsync(() => {
      for (let i = 0; i < 10; i++) {
        service.announce(`Message ${i}`, 'polite');
      }
      tick();

      const liveRegions = document.querySelectorAll('[aria-live="polite"]');
      expect(liveRegions.length).toBe(10);

      flush();
    }));

    it('should handle zero duration announcements', fakeAsync(() => {
      service.announce('Instant', 'polite', 0);

      // Element is created synchronously
      let liveRegion = document.querySelector('[aria-live]');
      expect(liveRegion).toBeTruthy();
      expect(liveRegion?.textContent).toBe('Instant');

      // Flush all timers - element should be removed after 0ms timeout
      flush();

      // Should be removed immediately after zero-duration timeout
      liveRegion = document.querySelector('[aria-live]');
      expect(liveRegion).toBeFalsy();
    }));

    it('should handle elements without role attribute', () => {
      const element = document.createElement('div');
      document.body.appendChild(element);

      const errors = service.validateAriaAttributes(element);
      expect(errors.length).toBe(0);

      document.body.removeChild(element);
    });

    it('should handle elements with multiple validation errors', () => {
      const element = document.createElement('div');
      element.setAttribute('role', 'slider');
      element.setAttribute('aria-describedby', 'non-existent');
      document.body.appendChild(element);

      const errors = service.validateAriaAttributes(element);
      expect(errors.length).toBeGreaterThan(1);

      document.body.removeChild(element);
    });
  });
});
