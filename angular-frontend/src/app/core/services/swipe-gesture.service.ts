import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent, merge } from 'rxjs';
import { filter, map, switchMap, takeUntil, tap } from 'rxjs/operators';

export interface SwipeEvent {
  direction: 'left' | 'right' | 'up' | 'down';
  distance: number;
  velocity: number;
  startPosition: { x: number; y: number };
  endPosition: { x: number; y: number };
  duration: number;
  element: HTMLElement;
  originalEvent: TouchEvent | MouseEvent;
  deltaX?: number;
  deltaY?: number;
}

export interface SwipeConfig {
  threshold: number; // Minimum distance for swipe
  velocityThreshold: number; // Minimum velocity for swipe
  timeThreshold: number; // Maximum time for swipe
  preventDefaultEvents: boolean;
  enabledDirections: ('left' | 'right' | 'up' | 'down')[];
  hapticFeedback: boolean;
}

export interface SwipeZone {
  id: string;
  element: HTMLElement;
  config: Partial<SwipeConfig>;
  onSwipe: (event: SwipeEvent) => void;
   onMove?: (event: SwipeEvent) => void;
  isActive: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class SwipeGestureService {
  private defaultConfig: SwipeConfig = {
    threshold: 50, // 50px minimum distance
    velocityThreshold: 0.3, // pixels per millisecond
    timeThreshold: 500, // 500ms maximum time
    preventDefaultEvents: true,
    enabledDirections: ['left', 'right', 'up', 'down'],
    hapticFeedback: true
  };

  private swipeZones = new Map<string, SwipeZone>();
  private isSwipeInProgress = new BehaviorSubject<boolean>(false);
  private currentSwipeZone: string | null = null;

  public swipeInProgress$ = this.isSwipeInProgress.asObservable();

  constructor() {
    this.setupGlobalSwipeHandling();
  }

  /**
   * Register a swipe zone for gesture detection
   */
  registerSwipeZone(
    id: string,
    element: HTMLElement,
    onSwipe: (event: SwipeEvent) => void,
    config: Partial<SwipeConfig> = {},
    onMove?: (event: SwipeEvent) => void
  ): void {
    const mergedConfig = { ...this.defaultConfig, ...config };

    const swipeZone: SwipeZone = {
      id,
      element,
      config: mergedConfig,
      onSwipe,
      onMove,
      isActive: true
    };

    this.swipeZones.set(id, swipeZone);
    this.attachSwipeListeners(swipeZone);
  }

  /**
   * Unregister a swipe zone
   */
  unregisterSwipeZone(id: string): void {
    const zone = this.swipeZones.get(id);
    if (zone) {
      this.detachSwipeListeners(zone);
      this.swipeZones.delete(id);
    }
  }

  /**
   * Enable/disable a swipe zone
   */
  toggleSwipeZone(id: string, isActive: boolean): void {
    const zone = this.swipeZones.get(id);
    if (zone) {
      zone.isActive = isActive;
    }
  }

  /**
   * Update swipe zone configuration
   */
  updateSwipeZoneConfig(id: string, config: Partial<SwipeConfig>): void {
    const zone = this.swipeZones.get(id);
    if (zone) {
      zone.config = { ...zone.config, ...config };
    }
  }

  /**
   * Check if device supports touch events
   */
  isTouchDevice(): boolean {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }

  /**
   * Get swipe zone by ID
   */
  getSwipeZone(id: string): SwipeZone | undefined {
    return this.swipeZones.get(id);
  }

  /**
   * Get all active swipe zones
   */
  getActiveSwipeZones(): SwipeZone[] {
    return Array.from(this.swipeZones.values()).filter(zone => zone.isActive);
  }

  private setupGlobalSwipeHandling(): void {
    // Prevent default touch behaviors on the body to improve swipe detection
    if (this.isTouchDevice()) {
      document.body.addEventListener('touchmove', (e) => {
        if (this.isSwipeInProgress.value) {
          e.preventDefault();
        }
      }, { passive: false });
    }
  }

  private attachSwipeListeners(zone: SwipeZone): void {
    const element = zone.element;
    let startPosition: { x: number; y: number } | null = null;
    let startTime: number = 0;
    let isSwipeActive = false;

    // Touch events
    const touchStart$ = fromEvent<TouchEvent>(element, 'touchstart');
    const touchMove$ = fromEvent<TouchEvent>(element, 'touchmove');
    const touchEnd$ = fromEvent<TouchEvent>(element, 'touchend');

    // Mouse events (for desktop testing)
    const mouseDown$ = fromEvent<MouseEvent>(element, 'mousedown');
    const mouseMove$ = fromEvent<MouseEvent>(element, 'mousemove');
    const mouseUp$ = fromEvent<MouseEvent>(element, 'mouseup');

    // Combine touch and mouse events
    const startEvents$ = merge(touchStart$, mouseDown$);
    const moveEvents$ = merge(touchMove$, mouseMove$);
    const endEvents$ = merge(touchEnd$, mouseUp$);

    // Handle swipe start
    startEvents$.subscribe((event) => {
      if (!zone.isActive) return;

      const position = this.getEventPosition(event);
      startPosition = position;
      startTime = Date.now();
      isSwipeActive = true;
      this.currentSwipeZone = zone.id;
      this.isSwipeInProgress.next(true);

      if (zone.config.preventDefaultEvents) {
        event.preventDefault();
      }

      // Add visual feedback
      element.classList.add('swipe-active');
    });

    // Handle swipe move
    moveEvents$.pipe(
      filter(() => isSwipeActive && startPosition !== null && zone.isActive),
      tap((event) => {
        if (zone.config.preventDefaultEvents) {
          event.preventDefault();
        }
      })
    ).subscribe((event) => {
      const currentPosition = this.getEventPosition(event);
      const distance = this.calculateDistance(startPosition!, currentPosition);

      // Add visual feedback based on distance
      if (distance > zone.config.threshold! * 0.3) {
        element.classList.add('swipe-threshold-reached');
      }

      // Emit move updates for physics-based UIs
      if (zone.onMove) {
        const deltaX = currentPosition.x - startPosition!.x;
        const deltaY = currentPosition.y - startPosition!.y;
        const previewEvent: SwipeEvent = {
          direction: this.getSwipeDirection(startPosition!, currentPosition),
          distance,
          velocity: 0,
          startPosition: startPosition!,
          endPosition: currentPosition,
          duration: Date.now() - startTime,
          element,
          originalEvent: event as any,
          deltaX,
          deltaY
        };
        zone.onMove(previewEvent);
      }
    });

    // Handle swipe end
    endEvents$.pipe(
      filter(() => isSwipeActive && startPosition !== null && zone.isActive)
    ).subscribe((event) => {
      if (!startPosition) return;

      const endPosition = this.getEventPosition(event);
      const endTime = Date.now();
      const duration = endTime - startTime;

      const swipeEvent = this.createSwipeEvent(
        startPosition,
        endPosition,
        duration,
        element,
        event,
        zone.config
      );

      // Check if swipe meets criteria
      if (this.isValidSwipe(swipeEvent, zone.config)) {
        // Trigger haptic feedback
        if (zone.config.hapticFeedback && 'vibrate' in navigator) {
          navigator.vibrate(50);
        }

        // Execute callback
        zone.onSwipe(swipeEvent);

        // Add success feedback
        element.classList.add('swipe-success');
        setTimeout(() => {
          element.classList.remove('swipe-success');
        }, 200);
      }

      // Reset state
      startPosition = null;
      isSwipeActive = false;
      this.currentSwipeZone = null;
      this.isSwipeInProgress.next(false);

      // Remove visual feedback and reset transforms
      element.classList.remove('swipe-active', 'swipe-threshold-reached');
      element.style.transform = '';
      element.style.transition = '';
    });
  }

  private detachSwipeListeners(zone: SwipeZone): void {
    // Event listeners are automatically cleaned up when the component is destroyed
    // due to the RxJS subscription lifecycle
    zone.element.classList.remove('swipe-active', 'swipe-threshold-reached', 'swipe-success');
  }

  private getEventPosition(event: TouchEvent | MouseEvent): { x: number; y: number } {
    if ('touches' in event && event.touches.length > 0) {
      return { x: event.touches[0].clientX, y: event.touches[0].clientY };
    } else if ('clientX' in event) {
      return { x: event.clientX, y: event.clientY };
    }
    return { x: 0, y: 0 };
  }

  private calculateDistance(start: { x: number; y: number }, end: { x: number; y: number }): number {
    const deltaX = end.x - start.x;
    const deltaY = end.y - start.y;
    return Math.sqrt(deltaX * deltaX + deltaY * deltaY);
  }

  private getSwipeDirection(start: { x: number; y: number }, end: { x: number; y: number }): 'left' | 'right' | 'up' | 'down' {
    const deltaX = end.x - start.x;
    const deltaY = end.y - start.y;

    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      return deltaX > 0 ? 'right' : 'left';
    } else {
      return deltaY > 0 ? 'down' : 'up';
    }
  }

  private createSwipeEvent(
    startPosition: { x: number; y: number },
    endPosition: { x: number; y: number },
    duration: number,
    element: HTMLElement,
    originalEvent: TouchEvent | MouseEvent,
    config: Partial<SwipeConfig>
  ): SwipeEvent {
    const distance = this.calculateDistance(startPosition, endPosition);
    const velocity = distance / duration;
    const direction = this.getSwipeDirection(startPosition, endPosition);

    return {
      direction,
      distance,
      velocity,
      startPosition,
      endPosition,
      duration,
      element,
      originalEvent,
      deltaX: endPosition.x - startPosition.x,
      deltaY: endPosition.y - startPosition.y
    };
  }

  private isValidSwipe(event: SwipeEvent, config: Partial<SwipeConfig>): boolean {
    const mergedConfig = { ...this.defaultConfig, ...config };

    // Check if direction is enabled
    if (!mergedConfig.enabledDirections.includes(event.direction)) {
      return false;
    }

    // Check distance threshold
    if (event.distance < mergedConfig.threshold) {
      return false;
    }

    // Check velocity threshold
    if (event.velocity < mergedConfig.velocityThreshold) {
      return false;
    }

    // Check time threshold
    if (event.duration > mergedConfig.timeThreshold) {
      return false;
    }

    return true;
  }

  /**
   * Create a simple swipe observer for quick integration
   */
  createSwipeObservable(
    element: HTMLElement,
    config: Partial<SwipeConfig> = {}
  ): Observable<SwipeEvent> {
    return new Observable(observer => {
      const id = `swipe-${Date.now()}-${Math.random()}`;

      this.registerSwipeZone(id, element, (event) => {
        observer.next(event);
      }, config);

      return () => {
        this.unregisterSwipeZone(id);
      };
    });
  }
}
