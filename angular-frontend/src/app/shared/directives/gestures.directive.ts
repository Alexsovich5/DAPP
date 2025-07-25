import { 
  Directive, 
  ElementRef, 
  Output, 
  EventEmitter, 
  Input, 
  OnInit, 
  OnDestroy,
  HostListener
} from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { 
  GestureService, 
  GestureEvent, 
  SwipeEvent, 
  PinchEvent, 
  LongPressEvent, 
  DragEvent,
  GestureConfig 
} from '../services/gesture.service';
import { MobileFeaturesService } from '../services/mobile-features.service';

@Directive({
  selector: '[appGestures]',
  standalone: true
})
export class GesturesDirective implements OnInit, OnDestroy {
  @Input() gestureConfig?: Partial<GestureConfig>;
  @Input() enableProfileSwipe: boolean = false;
  @Input() enablePhotoGallery: boolean = false;
  @Input() enableLongPress: boolean = false;
  @Input() enableDrag: boolean = false;
  @Input() enableDoubleTap: boolean = false;

  // General gesture events
  @Output() gesture = new EventEmitter<GestureEvent>();
  
  // Specific gesture events
  @Output() swipe = new EventEmitter<SwipeEvent>();
  @Output() swipeLeft = new EventEmitter<SwipeEvent>();
  @Output() swipeRight = new EventEmitter<SwipeEvent>();
  @Output() swipeUp = new EventEmitter<SwipeEvent>();
  @Output() swipeDown = new EventEmitter<SwipeEvent>();
  
  @Output() pinch = new EventEmitter<PinchEvent>();
  @Output() pinchIn = new EventEmitter<PinchEvent>();
  @Output() pinchOut = new EventEmitter<PinchEvent>();
  
  @Output() longPress = new EventEmitter<LongPressEvent>();
  @Output() drag = new EventEmitter<DragEvent>();
  @Output() dragStart = new EventEmitter<DragEvent>();
  @Output() dragEnd = new EventEmitter<DragEvent>();
  
  @Output() tap = new EventEmitter<GestureEvent>();
  @Output() doubleTap = new EventEmitter<GestureEvent>();

  // Dating app specific events
  @Output() profileLike = new EventEmitter<SwipeEvent>();
  @Output() profilePass = new EventEmitter<SwipeEvent>();
  @Output() photoZoom = new EventEmitter<PinchEvent>();
  @Output() contextMenu = new EventEmitter<LongPressEvent>();

  private destroy$ = new Subject<void>();
  private isDragging = false;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private gestureService: GestureService,
    private mobileFeatures: MobileFeaturesService
  ) {}

  ngOnInit(): void {
    this.setupGestures();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.gestureService.disableGestures(this.elementRef);
  }

  private setupGestures(): void {
    // Enable profile swipe gestures
    if (this.enableProfileSwipe) {
      this.gestureService.enableProfileSwipeGestures(this.elementRef)
        .pipe(takeUntil(this.destroy$))
        .subscribe(event => {
          this.swipe.emit(event);
          
          // Emit direction-specific events
          switch (event.swipeDirection) {
            case 'right':
              this.swipeRight.emit(event);
              this.profileLike.emit(event);
              this.addGestureVisualFeedback('like');
              break;
            case 'left':
              this.swipeLeft.emit(event);
              this.profilePass.emit(event);
              this.addGestureVisualFeedback('pass');
              break;
            case 'up':
              this.swipeUp.emit(event);
              break;
            case 'down':
              this.swipeDown.emit(event);
              break;
          }
        });
    }

    // Enable photo gallery gestures
    if (this.enablePhotoGallery) {
      this.gestureService.enablePhotoGalleryGestures(this.elementRef)
        .pipe(takeUntil(this.destroy$))
        .subscribe(event => {
          if (event.type === 'pinch') {
            const pinchEvent = event as PinchEvent;
            this.pinch.emit(pinchEvent);
            this.photoZoom.emit(pinchEvent);
            
            if (pinchEvent.scale > pinchEvent.previousScale) {
              this.pinchOut.emit(pinchEvent);
            } else {
              this.pinchIn.emit(pinchEvent);
            }
          } else if (event.type === 'swipe') {
            const swipeEvent = event as SwipeEvent;
            this.swipe.emit(swipeEvent);
            
            switch (swipeEvent.swipeDirection) {
              case 'left':
                this.swipeLeft.emit(swipeEvent);
                break;
              case 'right':
                this.swipeRight.emit(swipeEvent);
                break;
            }
          }
        });
    }

    // Enable long press gestures
    if (this.enableLongPress) {
      this.gestureService.enableLongPressGestures(this.elementRef)
        .pipe(takeUntil(this.destroy$))
        .subscribe(event => {
          this.longPress.emit(event);
          this.contextMenu.emit(event);
          this.addGestureVisualFeedback('longpress');
        });
    }

    // Enable drag gestures
    if (this.enableDrag) {
      this.gestureService.enableDragGestures(this.elementRef)
        .pipe(takeUntil(this.destroy$))
        .subscribe(event => {
          this.drag.emit(event);
          
          if (event.isDragging && !this.isDragging) {
            this.isDragging = true;
            this.dragStart.emit(event);
            this.elementRef.nativeElement.classList.add('dragging');
          } else if (!event.isDragging && this.isDragging) {
            this.isDragging = false;
            this.dragEnd.emit(event);
            this.elementRef.nativeElement.classList.remove('dragging');
          }
        });
    }

    // Enable double tap gestures
    if (this.enableDoubleTap) {
      this.gestureService.enableDoubleTapGestures(this.elementRef)
        .pipe(takeUntil(this.destroy$))
        .subscribe(event => {
          if (event.type === 'tap') {
            this.tap.emit(event);
          } else if (event.type === 'doubletap') {
            this.doubleTap.emit(event);
            this.addGestureVisualFeedback('like'); // Double tap to like
          }
        });
    }

    // Enable general gestures if no specific gestures are enabled
    if (!this.enableProfileSwipe && !this.enablePhotoGallery && !this.enableLongPress && 
        !this.enableDrag && !this.enableDoubleTap) {
      this.gestureService.enableGestures(this.elementRef, this.gestureConfig)
        .pipe(takeUntil(this.destroy$))
        .subscribe(event => {
          this.gesture.emit(event);
          
          // Emit specific events based on gesture type
          switch (event.type) {
            case 'swipe':
              const swipeEvent = event as SwipeEvent;
              this.swipe.emit(swipeEvent);
              
              switch (swipeEvent.swipeDirection) {
                case 'left':
                  this.swipeLeft.emit(swipeEvent);
                  break;
                case 'right':
                  this.swipeRight.emit(swipeEvent);
                  break;
                case 'up':
                  this.swipeUp.emit(swipeEvent);
                  break;
                case 'down':
                  this.swipeDown.emit(swipeEvent);
                  break;
              }
              break;
              
            case 'pinch':
              const pinchEvent = event as PinchEvent;
              this.pinch.emit(pinchEvent);
              break;
              
            case 'longpress':
              this.longPress.emit(event as LongPressEvent);
              break;
              
            case 'drag':
              this.drag.emit(event as DragEvent);
              break;
              
            case 'tap':
              this.tap.emit(event);
              break;
              
            case 'doubletap':
              this.doubleTap.emit(event);
              break;
          }
        });
    }
  }

  private addGestureVisualFeedback(type: 'like' | 'pass' | 'longpress'): void {
    const element = this.elementRef.nativeElement;
    
    // Remove any existing feedback classes
    element.classList.remove('gesture-like', 'gesture-pass', 'gesture-longpress');
    
    // Add appropriate feedback class
    element.classList.add(`gesture-${type}`);
    
    // Remove class after animation
    setTimeout(() => {
      element.classList.remove(`gesture-${type}`);
    }, 300);
  }

  // Host listeners for additional touch feedback
  @HostListener('touchstart', ['$event'])
  onTouchStart(event: TouchEvent): void {
    if (this.mobileFeatures.isTouchDevice()) {
      this.elementRef.nativeElement.classList.add('touch-active');
    }
  }

  @HostListener('touchend', ['$event'])
  @HostListener('touchcancel', ['$event'])
  onTouchEnd(event: TouchEvent): void {
    if (this.mobileFeatures.isTouchDevice()) {
      this.elementRef.nativeElement.classList.remove('touch-active');
    }
  }
}

// Additional directive for specific dating app gesture patterns
@Directive({
  selector: '[appProfileCard]',
  standalone: true
})
export class ProfileCardGestureDirective implements OnInit, OnDestroy {
  @Output() like = new EventEmitter<void>();
  @Output() pass = new EventEmitter<void>();
  @Output() superLike = new EventEmitter<void>();
  @Output() showDetails = new EventEmitter<void>();

  private destroy$ = new Subject<void>();

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private gestureService: GestureService,
    private mobileFeatures: MobileFeaturesService
  ) {}

  ngOnInit(): void {
    // Enable profile-specific gestures
    this.gestureService.enableProfileSwipeGestures(this.elementRef)
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        switch (event.swipeDirection) {
          case 'right':
            this.like.emit();
            this.animateCard('like', event.velocity);
            break;
          case 'left':
            this.pass.emit();
            this.animateCard('pass', event.velocity);
            break;
          case 'up':
            this.superLike.emit();
            this.animateCard('superlike', event.velocity);
            break;
        }
      });

    // Long press for details
    this.gestureService.enableLongPressGestures(this.elementRef)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.showDetails.emit();
      });

    // Double tap for like
    this.gestureService.enableDoubleTapGestures(this.elementRef)
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        if (event.type === 'doubletap') {
          this.like.emit();
          this.animateCard('like', 1);
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.gestureService.disableGestures(this.elementRef);
  }

  private animateCard(action: 'like' | 'pass' | 'superlike', velocity: number): void {
    const element = this.elementRef.nativeElement;
    const intensity = Math.min(velocity * 100, 100);
    
    // Add animation class
    element.classList.add(`card-${action}`);
    element.style.setProperty('--gesture-intensity', `${intensity}%`);
    
    // Haptic feedback
    switch (action) {
      case 'like':
        this.mobileFeatures.vibrateNewMatch();
        break;
      case 'pass':
        this.mobileFeatures.vibrateNewMessage();
        break;
      case 'superlike':
        this.mobileFeatures.vibrateNewRevelation();
        break;
    }
    
    // Remove animation class after animation completes
    setTimeout(() => {
      element.classList.remove(`card-${action}`);
      element.style.removeProperty('--gesture-intensity');
    }, 500);
  }
}

// Directive for revelation card gestures
@Directive({
  selector: '[appRevelationCard]',
  standalone: true
})
export class RevelationCardGestureDirective implements OnInit, OnDestroy {
  @Output() reveal = new EventEmitter<void>();
  @Output() respond = new EventEmitter<void>();
  @Output() share = new EventEmitter<void>();

  private destroy$ = new Subject<void>();

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private gestureService: GestureService,
    private mobileFeatures: MobileFeaturesService
  ) {}

  ngOnInit(): void {
    // Swipe up to reveal
    this.gestureService.enableGestures(this.elementRef, { 
      swipeThreshold: 60,
      swipeVelocityThreshold: 0.2 
    })
    .pipe(takeUntil(this.destroy$))
    .subscribe(event => {
      if (event.type === 'swipe') {
        const swipeEvent = event as SwipeEvent;
        switch (swipeEvent.swipeDirection) {
          case 'up':
            this.reveal.emit();
            this.mobileFeatures.vibrateNewRevelation();
            break;
          case 'right':
            this.respond.emit();
            this.mobileFeatures.vibrateNewMessage();
            break;
          case 'left':
            this.share.emit();
            this.mobileFeatures.vibrateNewMessage();
            break;
        }
      }
    });

    // Long press for options
    this.gestureService.enableLongPressGestures(this.elementRef)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.respond.emit();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.gestureService.disableGestures(this.elementRef);
  }
}