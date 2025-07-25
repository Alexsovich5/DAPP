import { Injectable, ElementRef, NgZone } from '@angular/core';
import { Observable, Subject, fromEvent, merge } from 'rxjs';
import { map, filter, takeUntil, tap, debounceTime } from 'rxjs/operators';
import { MobileFeaturesService } from './mobile-features.service';

export interface GestureEvent {
  type: GestureType;
  element: HTMLElement;
  startPoint: Point;
  currentPoint: Point;
  deltaX: number;
  deltaY: number;
  distance: number;
  velocity: number;
  direction: Direction;
  timestamp: number;
  originalEvent: TouchEvent | MouseEvent;
}

export interface SwipeEvent extends GestureEvent {
  type: 'swipe';
  swipeDirection: 'left' | 'right' | 'up' | 'down';
}

export interface PinchEvent extends GestureEvent {
  type: 'pinch';
  scale: number;
  previousScale: number;
  center: Point;
}

export interface LongPressEvent extends GestureEvent {
  type: 'longpress';
  duration: number;
}

export interface DragEvent extends GestureEvent {
  type: 'drag';
  isDragging: boolean;
}

export interface Point {
  x: number;
  y: number;
}

export interface Direction {
  horizontal: 'left' | 'right' | 'none';
  vertical: 'up' | 'down' | 'none';
}

export type GestureType = 'swipe' | 'pinch' | 'longpress' | 'drag' | 'tap' | 'doubletap';

export interface GestureConfig {
  // Swipe configuration
  swipeThreshold: number;
  swipeVelocityThreshold: number;
  swipeMaxTime: number;
  
  // Pinch configuration
  pinchThreshold: number;
  
  // Long press configuration
  longPressTime: number;
  longPressMoveThreshold: number;
  
  // Drag configuration
  dragThreshold: number;
  
  // Tap configuration
  tapThreshold: number;
  doubleTapTime: number;
  
  // General
  preventDefault: boolean;
  stopPropagation: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class GestureService {
  private readonly defaultConfig: GestureConfig = {
    swipeThreshold: 50,
    swipeVelocityThreshold: 0.3,
    swipeMaxTime: 300,
    pinchThreshold: 10,
    longPressTime: 500,
    longPressMoveThreshold: 10,
    dragThreshold: 10,
    tapThreshold: 10,
    doubleTapTime: 300,
    preventDefault: true,
    stopPropagation: false
  };

  private gestureSubject = new Subject<GestureEvent>();
  public gesture$ = this.gestureSubject.asObservable();

  private activeGestures = new Map<HTMLElement, GestureState>();
  private longPressTimers = new Map<HTMLElement, number>();

  constructor(
    private ngZone: NgZone,
    private mobileFeatures: MobileFeaturesService
  ) {}

  /**
   * Enable gestures on an element for dating app interactions
   */
  enableGestures(element: ElementRef<HTMLElement> | HTMLElement, config?: Partial<GestureConfig>): Observable<GestureEvent> {
    const el = element instanceof ElementRef ? element.nativeElement : element;
    const gestureConfig = { ...this.defaultConfig, ...config };

    this.setupGestureListeners(el, gestureConfig);

    return this.gesture$.pipe(
      filter(event => event.element === el)
    );
  }

  /**
   * Enable dating app specific swipe gestures (like/pass on profiles)
   */
  enableProfileSwipeGestures(element: ElementRef<HTMLElement> | HTMLElement): Observable<SwipeEvent> {
    const swipeConfig: Partial<GestureConfig> = {
      swipeThreshold: 80,
      swipeVelocityThreshold: 0.4,
      swipeMaxTime: 500,
      preventDefault: true
    };

    return this.enableGestures(element, swipeConfig).pipe(
      filter((event): event is SwipeEvent => event.type === 'swipe'),
      tap(event => {
        // Haptic feedback for profile swipes
        if (event.swipeDirection === 'right') {
          this.mobileFeatures.vibrateNewMatch(); // Like gesture
        } else if (event.swipeDirection === 'left') {
          this.mobileFeatures.vibrateNewMessage(); // Pass gesture
        }
      })
    );
  }

  /**
   * Enable photo gallery gestures (pinch-to-zoom, swipe between photos)
   */
  enablePhotoGalleryGestures(element: ElementRef<HTMLElement> | HTMLElement): Observable<GestureEvent> {
    const photoConfig: Partial<GestureConfig> = {
      pinchThreshold: 5,
      swipeThreshold: 30,
      preventDefault: true,
      stopPropagation: true
    };

    return this.enableGestures(element, photoConfig).pipe(
      filter(event => ['pinch', 'swipe'].includes(event.type))
    );
  }

  /**
   * Enable long press for context menus and advanced actions
   */
  enableLongPressGestures(element: ElementRef<HTMLElement> | HTMLElement): Observable<LongPressEvent> {
    const longPressConfig: Partial<GestureConfig> = {
      longPressTime: 600,
      longPressMoveThreshold: 15,
      preventDefault: false
    };

    return this.enableGestures(element, longPressConfig).pipe(
      filter((event): event is LongPressEvent => event.type === 'longpress'),
      tap(() => {
        this.mobileFeatures.vibrateNewRevelation(); // Haptic feedback for long press
      })
    );
  }

  /**
   * Enable drag gestures for revelation cards and interactive elements
   */
  enableDragGestures(element: ElementRef<HTMLElement> | HTMLElement): Observable<DragEvent> {
    const dragConfig: Partial<GestureConfig> = {
      dragThreshold: 5,
      preventDefault: false
    };

    return this.enableGestures(element, dragConfig).pipe(
      filter((event): event is DragEvent => event.type === 'drag')
    );
  }

  /**
   * Enable double tap for like/favorite actions
   */
  enableDoubleTapGestures(element: ElementRef<HTMLElement> | HTMLElement): Observable<GestureEvent> {
    const doubleTapConfig: Partial<GestureConfig> = {
      tapThreshold: 5,
      doubleTapTime: 250,
      preventDefault: false
    };

    return this.enableGestures(element, doubleTapConfig).pipe(
      filter(event => event.type === 'doubletap'),
      tap(() => {
        this.mobileFeatures.vibrateNewMatch(); // Haptic feedback for double tap like
      })
    );
  }

  private setupGestureListeners(element: HTMLElement, config: GestureConfig): void {
    this.ngZone.runOutsideAngular(() => {
      // Touch events
      const touchStart$ = fromEvent<TouchEvent>(element, 'touchstart', { passive: !config.preventDefault });
      const touchMove$ = fromEvent<TouchEvent>(element, 'touchmove', { passive: !config.preventDefault });
      const touchEnd$ = fromEvent<TouchEvent>(element, 'touchend', { passive: !config.preventDefault });
      const touchCancel$ = fromEvent<TouchEvent>(element, 'touchcancel', { passive: !config.preventDefault });

      // Mouse events for desktop testing
      const mouseDown$ = fromEvent<MouseEvent>(element, 'mousedown');
      const mouseMove$ = fromEvent<MouseEvent>(element, 'mousemove');
      const mouseUp$ = fromEvent<MouseEvent>(element, 'mouseup');

      // Unified start events
      const start$ = merge(
        touchStart$.pipe(map(e => this.normalizeEvent(e))),
        mouseDown$.pipe(map(e => this.normalizeEvent(e)))
      );

      const move$ = merge(
        touchMove$.pipe(map(e => this.normalizeEvent(e))),
        mouseMove$.pipe(map(e => this.normalizeEvent(e)))
      );

      const end$ = merge(
        touchEnd$.pipe(map(e => this.normalizeEvent(e))),
        touchCancel$.pipe(map(e => this.normalizeEvent(e))),
        mouseUp$.pipe(map(e => this.normalizeEvent(e)))
      );

      // Handle gesture start
      start$.subscribe(event => {
        this.handleGestureStart(element, event, config);
      });

      // Handle gesture move
      move$.subscribe(event => {
        this.handleGestureMove(element, event, config);
      });

      // Handle gesture end
      end$.subscribe(event => {
        this.handleGestureEnd(element, event, config);
      });
    });
  }

  private handleGestureStart(element: HTMLElement, event: NormalizedEvent, config: GestureConfig): void {
    if (config.preventDefault) {
      event.originalEvent.preventDefault();
    }
    if (config.stopPropagation) {
      event.originalEvent.stopPropagation();
    }

    const gestureState: GestureState = {
      startPoint: event.points[0],
      startTime: Date.now(),
      lastPoint: event.points[0],
      lastTime: Date.now(),
      totalDistance: 0,
      isActive: true,
      startTouches: event.points.length,
      lastTapTime: this.activeGestures.get(element)?.lastTapTime || 0
    };

    this.activeGestures.set(element, gestureState);

    // Start long press timer
    if (event.points.length === 1) {
      this.startLongPressTimer(element, event, config);
    }

    // Handle multi-touch for pinch gestures
    if (event.points.length === 2) {
      gestureState.initialDistance = this.getDistance(event.points[0], event.points[1]);
      gestureState.lastScale = 1;
    }
  }

  private handleGestureMove(element: HTMLElement, event: NormalizedEvent, config: GestureConfig): void {
    const gestureState = this.activeGestures.get(element);
    if (!gestureState || !gestureState.isActive) return;

    if (config.preventDefault) {
      event.originalEvent.preventDefault();
    }

    const currentPoint = event.points[0];
    const deltaX = currentPoint.x - gestureState.startPoint.x;
    const deltaY = currentPoint.y - gestureState.startPoint.y;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    gestureState.totalDistance = distance;
    gestureState.lastPoint = currentPoint;
    gestureState.lastTime = Date.now();

    // Cancel long press if moved too much
    const moveDistance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    if (moveDistance > config.longPressMoveThreshold) {
      this.cancelLongPressTimer(element);
    }

    // Handle pinch gesture
    if (event.points.length === 2 && gestureState.initialDistance) {
      this.handlePinchGesture(element, event, gestureState, config);
    }

    // Handle drag gesture
    if (distance > config.dragThreshold && event.points.length === 1) {
      this.handleDragGesture(element, event, gestureState, config);
    }
  }

  private handleGestureEnd(element: HTMLElement, event: NormalizedEvent, config: GestureConfig): void {
    const gestureState = this.activeGestures.get(element);
    if (!gestureState || !gestureState.isActive) return;

    const endTime = Date.now();
    const duration = endTime - gestureState.startTime;
    const deltaX = gestureState.lastPoint.x - gestureState.startPoint.x;
    const deltaY = gestureState.lastPoint.y - gestureState.startPoint.y;
    const distance = gestureState.totalDistance;
    const velocity = distance / duration;

    gestureState.isActive = false;
    this.cancelLongPressTimer(element);

    // Determine gesture type
    if (this.isSwipeGesture(distance, velocity, duration, config)) {
      this.emitSwipeGesture(element, event, gestureState, config, deltaX, deltaY, velocity);
    } else if (this.isTapGesture(distance, duration, config)) {
      this.handleTapGesture(element, event, gestureState, config);
    }

    // Clean up
    if (event.points.length === 0) {
      this.activeGestures.delete(element);
    }
  }

  private handlePinchGesture(element: HTMLElement, event: NormalizedEvent, gestureState: GestureState, config: GestureConfig): void {
    if (event.points.length !== 2 || !gestureState.initialDistance) return;

    const currentDistance = this.getDistance(event.points[0], event.points[1]);
    const scale = currentDistance / gestureState.initialDistance;
    const center = this.getCenter(event.points[0], event.points[1]);

    const pinchEvent: PinchEvent = {
      type: 'pinch',
      element,
      startPoint: gestureState.startPoint,
      currentPoint: center,
      deltaX: center.x - gestureState.startPoint.x,
      deltaY: center.y - gestureState.startPoint.y,
      distance: currentDistance,
      velocity: 0,
      direction: this.getDirection(0, 0),
      timestamp: Date.now(),
      originalEvent: event.originalEvent,
      scale,
      previousScale: gestureState.lastScale || 1,
      center
    };

    gestureState.lastScale = scale;

    this.ngZone.run(() => {
      this.gestureSubject.next(pinchEvent);
    });
  }

  private handleDragGesture(element: HTMLElement, event: NormalizedEvent, gestureState: GestureState, config: GestureConfig): void {
    const currentPoint = event.points[0];
    const deltaX = currentPoint.x - gestureState.startPoint.x;
    const deltaY = currentPoint.y - gestureState.startPoint.y;

    const dragEvent: DragEvent = {
      type: 'drag',
      element,
      startPoint: gestureState.startPoint,
      currentPoint,
      deltaX,
      deltaY,
      distance: Math.sqrt(deltaX * deltaX + deltaY * deltaY),
      velocity: 0,
      direction: this.getDirection(deltaX, deltaY),
      timestamp: Date.now(),
      originalEvent: event.originalEvent,
      isDragging: true
    };

    this.ngZone.run(() => {
      this.gestureSubject.next(dragEvent);
    });
  }

  private handleTapGesture(element: HTMLElement, event: NormalizedEvent, gestureState: GestureState, config: GestureConfig): void {
    const currentTime = Date.now();
    const timeSinceLastTap = currentTime - gestureState.lastTapTime;

    if (timeSinceLastTap < config.doubleTapTime) {
      // Double tap
      const doubleTapEvent: GestureEvent = {
        type: 'doubletap',
        element,
        startPoint: gestureState.startPoint,
        currentPoint: gestureState.lastPoint,
        deltaX: 0,
        deltaY: 0,
        distance: 0,
        velocity: 0,
        direction: this.getDirection(0, 0),
        timestamp: currentTime,
        originalEvent: event.originalEvent
      };

      this.ngZone.run(() => {
        this.gestureSubject.next(doubleTapEvent);
      });
    } else {
      // Single tap
      const tapEvent: GestureEvent = {
        type: 'tap',
        element,
        startPoint: gestureState.startPoint,
        currentPoint: gestureState.lastPoint,
        deltaX: 0,
        deltaY: 0,
        distance: 0,
        velocity: 0,
        direction: this.getDirection(0, 0),
        timestamp: currentTime,
        originalEvent: event.originalEvent
      };

      gestureState.lastTapTime = currentTime;

      this.ngZone.run(() => {
        this.gestureSubject.next(tapEvent);
      });
    }
  }

  private emitSwipeGesture(element: HTMLElement, event: NormalizedEvent, gestureState: GestureState, 
                          config: GestureConfig, deltaX: number, deltaY: number, velocity: number): void {
    const swipeDirection = this.getSwipeDirection(deltaX, deltaY);
    
    const swipeEvent: SwipeEvent = {
      type: 'swipe',
      element,
      startPoint: gestureState.startPoint,
      currentPoint: gestureState.lastPoint,
      deltaX,
      deltaY,
      distance: gestureState.totalDistance,
      velocity,
      direction: this.getDirection(deltaX, deltaY),
      timestamp: Date.now(),
      originalEvent: event.originalEvent,
      swipeDirection
    };

    this.ngZone.run(() => {
      this.gestureSubject.next(swipeEvent);
    });
  }

  private startLongPressTimer(element: HTMLElement, event: NormalizedEvent, config: GestureConfig): void {
    const timer = window.setTimeout(() => {
      const gestureState = this.activeGestures.get(element);
      if (gestureState && gestureState.isActive) {
        const longPressEvent: LongPressEvent = {
          type: 'longpress',
          element,
          startPoint: gestureState.startPoint,
          currentPoint: gestureState.lastPoint,
          deltaX: gestureState.lastPoint.x - gestureState.startPoint.x,
          deltaY: gestureState.lastPoint.y - gestureState.startPoint.y,
          distance: gestureState.totalDistance,
          velocity: 0,
          direction: this.getDirection(0, 0),
          timestamp: Date.now(),
          originalEvent: event.originalEvent,
          duration: config.longPressTime
        };

        this.ngZone.run(() => {
          this.gestureSubject.next(longPressEvent);
        });
      }
    }, config.longPressTime);

    this.longPressTimers.set(element, timer);
  }

  private cancelLongPressTimer(element: HTMLElement): void {
    const timer = this.longPressTimers.get(element);
    if (timer) {
      window.clearTimeout(timer);
      this.longPressTimers.delete(element);
    }
  }

  private isSwipeGesture(distance: number, velocity: number, duration: number, config: GestureConfig): boolean {
    return distance > config.swipeThreshold && 
           velocity > config.swipeVelocityThreshold && 
           duration < config.swipeMaxTime;
  }

  private isTapGesture(distance: number, duration: number, config: GestureConfig): boolean {
    return distance < config.tapThreshold;
  }

  private getSwipeDirection(deltaX: number, deltaY: number): 'left' | 'right' | 'up' | 'down' {
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      return deltaX > 0 ? 'right' : 'left';
    } else {
      return deltaY > 0 ? 'down' : 'up';
    }
  }

  private getDirection(deltaX: number, deltaY: number): Direction {
    const threshold = 10;
    
    return {
      horizontal: Math.abs(deltaX) > threshold ? (deltaX > 0 ? 'right' : 'left') : 'none',
      vertical: Math.abs(deltaY) > threshold ? (deltaY > 0 ? 'down' : 'up') : 'none'
    };
  }

  private getDistance(point1: Point, point2: Point): number {
    const deltaX = point2.x - point1.x;
    const deltaY = point2.y - point1.y;
    return Math.sqrt(deltaX * deltaX + deltaY * deltaY);
  }

  private getCenter(point1: Point, point2: Point): Point {
    return {
      x: (point1.x + point2.x) / 2,
      y: (point1.y + point2.y) / 2
    };
  }

  private normalizeEvent(event: TouchEvent | MouseEvent): NormalizedEvent {
    if (event instanceof TouchEvent) {
      return {
        originalEvent: event,
        points: Array.from(event.touches).map(touch => ({
          x: touch.clientX,
          y: touch.clientY
        }))
      };
    } else {
      return {
        originalEvent: event,
        points: [{
          x: event.clientX,
          y: event.clientY
        }]
      };
    }
  }

  /**
   * Clean up gestures for an element
   */
  disableGestures(element: ElementRef<HTMLElement> | HTMLElement): void {
    const el = element instanceof ElementRef ? element.nativeElement : element;
    this.activeGestures.delete(el);
    this.cancelLongPressTimer(el);
  }

  /**
   * Get gesture statistics for analytics
   */
  getGestureStats(): { activeGestures: number; totalGestures: number } {
    return {
      activeGestures: this.activeGestures.size,
      totalGestures: this.activeGestures.size // This would be tracked over time in a real implementation
    };
  }
}

interface NormalizedEvent {
  originalEvent: TouchEvent | MouseEvent;
  points: Point[];
}

interface GestureState {
  startPoint: Point;
  startTime: number;
  lastPoint: Point;
  lastTime: number;
  totalDistance: number;
  isActive: boolean;
  startTouches: number;
  lastTapTime: number;
  initialDistance?: number;
  lastScale?: number;
}