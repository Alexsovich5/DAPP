import { TestBed } from '@angular/core/testing';
import { SwipeGestureService, SwipeEvent, SwipeConfig } from './swipe-gesture.service';

describe('SwipeGestureService', () => {
  let service: SwipeGestureService;
  let mockElement: HTMLElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [SwipeGestureService]
    });
    service = TestBed.inject(SwipeGestureService);

    // Create mock element
    mockElement = document.createElement('div');
    document.body.appendChild(mockElement);
  });

  afterEach(() => {
    // Clean up
    document.body.removeChild(mockElement);
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should have default configuration', () => {
      const zone = service.getSwipeZone('test');
      expect(zone).toBeUndefined();
    });

    it('should provide swipeInProgress observable', (done) => {
      service.swipeInProgress$.subscribe(inProgress => {
        expect(typeof inProgress).toBe('boolean');
        done();
      });
    });

    it('should detect touch device capability', () => {
      const isTouchDevice = service.isTouchDevice();
      expect(typeof isTouchDevice).toBe('boolean');
    });
  });

  describe('Swipe Zone Registration', () => {
    it('should register a swipe zone', () => {
      const onSwipe = jasmine.createSpy('onSwipe');

      service.registerSwipeZone('test-zone', mockElement, onSwipe);

      const zone = service.getSwipeZone('test-zone');
      expect(zone).toBeDefined();
      expect(zone!.id).toBe('test-zone');
      expect(zone!.element).toBe(mockElement);
      expect(zone!.isActive).toBe(true);
    });

    it('should register zone with custom configuration', () => {
      const onSwipe = jasmine.createSpy('onSwipe');
      const config: Partial<SwipeConfig> = {
        threshold: 100,
        velocityThreshold: 0.5
      };

      service.registerSwipeZone('test-zone', mockElement, onSwipe, config);

      const zone = service.getSwipeZone('test-zone');
      expect(zone!.config.threshold).toBe(100);
      expect(zone!.config.velocityThreshold).toBe(0.5);
    });

    it('should register zone with move callback', () => {
      const onSwipe = jasmine.createSpy('onSwipe');
      const onMove = jasmine.createSpy('onMove');

      service.registerSwipeZone('test-zone', mockElement, onSwipe, {}, onMove);

      const zone = service.getSwipeZone('test-zone');
      expect(zone!.onMove).toBeDefined();
    });

    it('should unregister a swipe zone', () => {
      const onSwipe = jasmine.createSpy('onSwipe');

      service.registerSwipeZone('test-zone', mockElement, onSwipe);
      expect(service.getSwipeZone('test-zone')).toBeDefined();

      service.unregisterSwipeZone('test-zone');
      expect(service.getSwipeZone('test-zone')).toBeUndefined();
    });

    it('should handle unregistering non-existent zone', () => {
      expect(() => {
        service.unregisterSwipeZone('non-existent');
      }).not.toThrow();
    });
  });

  describe('Swipe Zone Management', () => {
    beforeEach(() => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe);
    });

    it('should toggle swipe zone active state', () => {
      service.toggleSwipeZone('test-zone', false);

      const zone = service.getSwipeZone('test-zone');
      expect(zone!.isActive).toBe(false);

      service.toggleSwipeZone('test-zone', true);
      expect(zone!.isActive).toBe(true);
    });

    it('should update swipe zone configuration', () => {
      service.updateSwipeZoneConfig('test-zone', { threshold: 200 });

      const zone = service.getSwipeZone('test-zone');
      expect(zone!.config.threshold).toBe(200);
    });

    it('should merge updated configuration with existing', () => {
      const zone = service.getSwipeZone('test-zone');
      const originalVelocity = zone!.config.velocityThreshold;

      service.updateSwipeZoneConfig('test-zone', { threshold: 150 });

      const updatedZone = service.getSwipeZone('test-zone');
      expect(updatedZone!.config.threshold).toBe(150);
      expect(updatedZone!.config.velocityThreshold).toBe(originalVelocity);
    });

    it('should get all active swipe zones', () => {
      const onSwipe = jasmine.createSpy('onSwipe');
      const element2 = document.createElement('div');
      document.body.appendChild(element2);

      service.registerSwipeZone('test-zone-2', element2, onSwipe);
      service.toggleSwipeZone('test-zone', false);

      const activeZones = service.getActiveSwipeZones();
      expect(activeZones.length).toBe(1);
      expect(activeZones[0].id).toBe('test-zone-2');

      document.body.removeChild(element2);
    });
  });

  describe('Touch Event Handling', () => {
    it('should handle touch-like events (tested with mouse events)', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe);

      // Use mouse events which work reliably in test environment
      const mouseDown = new MouseEvent('mousedown', {
        clientX: 100,
        clientY: 100,
        bubbles: true
      });

      mockElement.dispatchEvent(mouseDown);

      service.swipeInProgress$.subscribe(inProgress => {
        if (inProgress) {
          expect(mockElement.classList.contains('swipe-active')).toBe(true);
          done();
        }
      });
    });

    it('should handle move events during swipe', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      const onMove = jasmine.createSpy('onMove');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {}, onMove);

      // Start swipe with mouse event (simulates touch)
      const mouseDown = new MouseEvent('mousedown', {
        clientX: 100,
        clientY: 100,
        bubbles: true
      });
      mockElement.dispatchEvent(mouseDown);

      setTimeout(() => {
        // Move significantly
        const mouseMove = new MouseEvent('mousemove', {
          clientX: 200,
          clientY: 100,
          bubbles: true
        });
        mockElement.dispatchEvent(mouseMove);

        setTimeout(() => {
          expect(onMove).toHaveBeenCalled();
          done();
        }, 50);
      }, 50);
    });

    it('should complete swipe gesture', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      // Complete swipe using mouse events (simulates touch)
      simulateSwipe(mockElement, 100, 100, 250, 100);

      setTimeout(() => {
        expect(onSwipe).toHaveBeenCalled();
        const swipeEvent: SwipeEvent = onSwipe.calls.mostRecent().args[0];
        expect(swipeEvent.direction).toBe('right');
        expect(swipeEvent.distance).toBeGreaterThan(0);
        done();
      }, 150);
    });
  });

  describe('Mouse Event Handling', () => {
    it('should handle mousedown event', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe);

      const mouseDown = new MouseEvent('mousedown', {
        clientX: 100,
        clientY: 100,
        bubbles: true
      });

      mockElement.dispatchEvent(mouseDown);

      service.swipeInProgress$.subscribe(inProgress => {
        if (inProgress) {
          expect(mockElement.classList.contains('swipe-active')).toBe(true);
          done();
        }
      });
    });

    it('should handle mousemove event', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      const onMove = jasmine.createSpy('onMove');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {}, onMove);

      // Start swipe
      const mouseDown = new MouseEvent('mousedown', {
        clientX: 100,
        clientY: 100,
        bubbles: true
      });
      mockElement.dispatchEvent(mouseDown);

      setTimeout(() => {
        // Move
        const mouseMove = new MouseEvent('mousemove', {
          clientX: 200,
          clientY: 100,
          bubbles: true
        });
        mockElement.dispatchEvent(mouseMove);

        setTimeout(() => {
          expect(onMove).toHaveBeenCalled();
          done();
        }, 50);
      }, 50);
    });

    it('should handle mouseup event', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      // Start swipe
      const mouseDown = new MouseEvent('mousedown', {
        clientX: 100,
        clientY: 100,
        bubbles: true
      });
      mockElement.dispatchEvent(mouseDown);

      setTimeout(() => {
        // End swipe
        const mouseUp = new MouseEvent('mouseup', {
          clientX: 250,
          clientY: 100,
          bubbles: true
        });
        mockElement.dispatchEvent(mouseUp);

        setTimeout(() => {
          expect(onSwipe).toHaveBeenCalled();
          done();
        }, 100);
      }, 50);
    });
  });

  describe('Swipe Direction Detection', () => {
    it('should detect left swipe', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      simulateSwipe(mockElement, 200, 100, 50, 100);

      setTimeout(() => {
        expect(onSwipe).toHaveBeenCalled();
        const event: SwipeEvent = onSwipe.calls.mostRecent().args[0];
        expect(event.direction).toBe('left');
        done();
      }, 150);
    });

    it('should detect right swipe', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      simulateSwipe(mockElement, 50, 100, 200, 100);

      setTimeout(() => {
        expect(onSwipe).toHaveBeenCalled();
        const event: SwipeEvent = onSwipe.calls.mostRecent().args[0];
        expect(event.direction).toBe('right');
        done();
      }, 150);
    });

    it('should detect up swipe', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      simulateSwipe(mockElement, 100, 200, 100, 50);

      setTimeout(() => {
        expect(onSwipe).toHaveBeenCalled();
        const event: SwipeEvent = onSwipe.calls.mostRecent().args[0];
        expect(event.direction).toBe('up');
        done();
      }, 150);
    });

    it('should detect down swipe', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      simulateSwipe(mockElement, 100, 50, 100, 200);

      setTimeout(() => {
        expect(onSwipe).toHaveBeenCalled();
        const event: SwipeEvent = onSwipe.calls.mostRecent().args[0];
        expect(event.direction).toBe('down');
        done();
      }, 150);
    });
  });

  describe('Swipe Validation', () => {
    it('should reject swipe below threshold distance', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 100,
        velocityThreshold: 0.1
      });

      // Swipe only 30px (below 100px threshold)
      simulateSwipe(mockElement, 100, 100, 130, 100);

      setTimeout(() => {
        expect(onSwipe).not.toHaveBeenCalled();
        done();
      }, 150);
    });

    it('should reject swipe below velocity threshold', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 10.0 // Very high velocity requirement
      });

      simulateSwipe(mockElement, 100, 100, 200, 100);

      setTimeout(() => {
        expect(onSwipe).not.toHaveBeenCalled();
        done();
      }, 150);
    });

    it('should reject swipe for disabled direction', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1,
        enabledDirections: ['up', 'down'] // Only vertical swipes allowed
      });

      // Try horizontal swipe
      simulateSwipe(mockElement, 100, 100, 250, 100);

      setTimeout(() => {
        expect(onSwipe).not.toHaveBeenCalled();
        done();
      }, 150);
    });

    it('should accept swipe for enabled direction', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1,
        enabledDirections: ['left', 'right']
      });

      simulateSwipe(mockElement, 100, 100, 250, 100);

      setTimeout(() => {
        expect(onSwipe).toHaveBeenCalled();
        done();
      }, 150);
    });
  });

  describe('Swipe Event Properties', () => {
    it('should calculate distance correctly', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      simulateSwipe(mockElement, 100, 100, 200, 100);

      setTimeout(() => {
        const event: SwipeEvent = onSwipe.calls.mostRecent().args[0];
        expect(event.distance).toBeCloseTo(100, 1);
        done();
      }, 150);
    });

    it('should calculate velocity correctly', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      simulateSwipe(mockElement, 100, 100, 200, 100);

      setTimeout(() => {
        const event: SwipeEvent = onSwipe.calls.mostRecent().args[0];
        expect(event.velocity).toBeGreaterThan(0);
        expect(event.duration).toBeGreaterThan(0);
        done();
      }, 150);
    });

    it('should provide deltaX and deltaY', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      simulateSwipe(mockElement, 100, 100, 200, 150);

      setTimeout(() => {
        const event: SwipeEvent = onSwipe.calls.mostRecent().args[0];
        expect(event.deltaX).toBe(100);
        expect(event.deltaY).toBe(50);
        done();
      }, 150);
    });
  });

  describe('Visual Feedback', () => {
    it('should add swipe-active class on start', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe);

      const mouseDown = new MouseEvent('mousedown', {
        clientX: 100,
        clientY: 100,
        bubbles: true
      });
      mockElement.dispatchEvent(mouseDown);

      setTimeout(() => {
        expect(mockElement.classList.contains('swipe-active')).toBe(true);
        done();
      }, 50);
    });

    it('should add swipe-threshold-reached class during move', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      const onMove = jasmine.createSpy('onMove');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 100
      }, onMove);

      const mouseDown = new MouseEvent('mousedown', {
        clientX: 100,
        clientY: 100,
        bubbles: true
      });
      mockElement.dispatchEvent(mouseDown);

      setTimeout(() => {
        // Move past 30% of threshold (30px of 100px)
        const mouseMove = new MouseEvent('mousemove', {
          clientX: 140,
          clientY: 100,
          bubbles: true
        });
        mockElement.dispatchEvent(mouseMove);

        setTimeout(() => {
          expect(mockElement.classList.contains('swipe-threshold-reached')).toBe(true);
          done();
        }, 50);
      }, 50);
    });

    it('should remove classes after swipe end', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      simulateSwipe(mockElement, 100, 100, 250, 100);

      setTimeout(() => {
        expect(mockElement.classList.contains('swipe-active')).toBe(false);
        expect(mockElement.classList.contains('swipe-threshold-reached')).toBe(false);
        done();
      }, 300);
    });
  });

  describe('Swipe Observable', () => {
    it('should create swipe observable', (done) => {
      const observable = service.createSwipeObservable(mockElement, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      observable.subscribe((event: SwipeEvent) => {
        expect(event.direction).toBeDefined();
        expect(event.distance).toBeGreaterThan(0);
        done();
      });

      setTimeout(() => {
        simulateSwipe(mockElement, 100, 100, 250, 100);
      }, 50);
    });

    it('should unregister zone on unsubscribe', (done) => {
      const observable = service.createSwipeObservable(mockElement);
      const subscription = observable.subscribe(() => {});

      setTimeout(() => {
        const zonesCount = service.getActiveSwipeZones().length;
        expect(zonesCount).toBeGreaterThan(0);

        subscription.unsubscribe();

        setTimeout(() => {
          const newZonesCount = service.getActiveSwipeZones().length;
          expect(newZonesCount).toBe(zonesCount - 1);
          done();
        }, 50);
      }, 50);
    });
  });

  describe('Inactive Zone Handling', () => {
    it('should not trigger swipe when zone is inactive', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      service.toggleSwipeZone('test-zone', false);

      simulateSwipe(mockElement, 100, 100, 250, 100);

      setTimeout(() => {
        expect(onSwipe).not.toHaveBeenCalled();
        done();
      }, 150);
    });

    it('should resume triggering after reactivation', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      service.toggleSwipeZone('test-zone', false);
      service.toggleSwipeZone('test-zone', true);

      simulateSwipe(mockElement, 100, 100, 250, 100);

      setTimeout(() => {
        expect(onSwipe).toHaveBeenCalled();
        done();
      }, 150);
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid swipes', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      // First swipe
      simulateSwipe(mockElement, 100, 100, 250, 100);

      setTimeout(() => {
        // Second swipe immediately after
        simulateSwipe(mockElement, 100, 100, 250, 100);

        setTimeout(() => {
          expect(onSwipe).toHaveBeenCalledTimes(2);
          done();
        }, 150);
      }, 150);
    });

    it('should handle swipe without move events', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      // Just start and end, no move
      const mouseDown = new MouseEvent('mousedown', {
        clientX: 100,
        clientY: 100,
        bubbles: true
      });
      mockElement.dispatchEvent(mouseDown);

      setTimeout(() => {
        const mouseUp = new MouseEvent('mouseup', {
          clientX: 250,
          clientY: 100,
          bubbles: true
        });
        mockElement.dispatchEvent(mouseUp);

        setTimeout(() => {
          expect(onSwipe).toHaveBeenCalled();
          done();
        }, 100);
      }, 50);
    });

    it('should handle zero distance swipe', (done) => {
      const onSwipe = jasmine.createSpy('onSwipe');
      service.registerSwipeZone('test-zone', mockElement, onSwipe, {
        threshold: 50,
        velocityThreshold: 0.1
      });

      // Same start and end position
      simulateSwipe(mockElement, 100, 100, 100, 100);

      setTimeout(() => {
        expect(onSwipe).not.toHaveBeenCalled();
        done();
      }, 150);
    });
  });
});

// Helper function to simulate complete swipe gesture
function simulateSwipe(
  element: HTMLElement,
  startX: number,
  startY: number,
  endX: number,
  endY: number
): void {
  const mouseDown = new MouseEvent('mousedown', {
    clientX: startX,
    clientY: startY,
    bubbles: true
  });
  element.dispatchEvent(mouseDown);

  setTimeout(() => {
    const mouseUp = new MouseEvent('mouseup', {
      clientX: endX,
      clientY: endY,
      bubbles: true
    });
    element.dispatchEvent(mouseUp);
  }, 50);
}
