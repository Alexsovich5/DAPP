import { 
  Directive, 
  Input, 
  ElementRef, 
  OnInit, 
  OnDestroy, 
  HostListener,
  Output,
  EventEmitter
} from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil, throttleTime, debounceTime } from 'rxjs/operators';
import { MobileAnalyticsService, EventCategory } from '../services/mobile-analytics.service';
import { GestureService, GestureEvent } from '../services/gesture.service';

@Directive({
  selector: '[appAnalytics]',
  standalone: true
})
export class AnalyticsDirective implements OnInit, OnDestroy {
  @Input() trackingName!: string;
  @Input() trackingCategory: EventCategory = 'user_interaction';
  @Input() trackingData: Record<string, any> = {};
  @Input() trackClicks: boolean = true;
  @Input() trackHovers: boolean = false;
  @Input() trackScrollIntoView: boolean = false;
  @Input() trackTimeSpent: boolean = false;
  @Input() trackGestures: boolean = false;
  @Input() throttleMs: number = 1000;

  @Output() analyticsEvent = new EventEmitter<string>();

  private destroy$ = new Subject<void>();
  private viewStartTime?: number;
  private isInView = false;
  private intersectionObserver?: IntersectionObserver;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private analytics: MobileAnalyticsService,
    private gestureService: GestureService
  ) {}

  ngOnInit(): void {
    this.setupTracking();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }

    // Track time spent if element was in view
    if (this.trackTimeSpent && this.viewStartTime) {
      this.trackTimeSpentEvent();
    }
  }

  private setupTracking(): void {
    if (this.trackScrollIntoView || this.trackTimeSpent) {
      this.setupIntersectionObserver();
    }

    if (this.trackGestures) {
      this.setupGestureTracking();
    }
  }

  private setupIntersectionObserver(): void {
    this.intersectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !this.isInView) {
            this.isInView = true;
            this.viewStartTime = Date.now();
            
            if (this.trackScrollIntoView) {
              this.trackEvent('scroll_into_view');
            }
          } else if (!entry.isIntersecting && this.isInView) {
            this.isInView = false;
            
            if (this.trackTimeSpent && this.viewStartTime) {
              this.trackTimeSpentEvent();
            }
          }
        });
      },
      { threshold: 0.5 }
    );

    this.intersectionObserver.observe(this.elementRef.nativeElement);
  }

  private setupGestureTracking(): void {
    this.gestureService.enableGestures(this.elementRef)
      .pipe(
        takeUntil(this.destroy$),
        throttleTime(this.throttleMs)
      )
      .subscribe((gestureEvent: GestureEvent) => {
        this.analytics.trackGesture(gestureEvent);
        this.trackEvent('gesture', {
          gestureType: gestureEvent.type,
          gestureDirection: (gestureEvent as any).swipeDirection || 'none'
        });
      });
  }

  @HostListener('click', ['$event'])
  onElementClick(event: MouseEvent): void {
    if (this.trackClicks) {
      this.trackEvent('click', {
        clickX: event.clientX,
        clickY: event.clientY,
        button: event.button,
        altKey: event.altKey,
        ctrlKey: event.ctrlKey,
        shiftKey: event.shiftKey
      });
    }
  }

  @HostListener('mouseenter')
  onElementHover(): void {
    if (this.trackHovers) {
      this.trackEvent('hover');
    }
  }

  @HostListener('focus')
  onElementFocus(): void {
    this.trackEvent('focus');
  }

  private trackEvent(action: string, additionalData: Record<string, any> = {}): void {
    const eventName = `${this.trackingName}_${action}`;
    const eventData = {
      ...this.trackingData,
      ...additionalData,
      elementId: this.elementRef.nativeElement.id,
      elementClass: this.elementRef.nativeElement.className,
      elementTag: this.elementRef.nativeElement.tagName.toLowerCase()
    };

    this.analytics.trackEvent(eventName, this.trackingCategory, eventData);
    this.analyticsEvent.emit(eventName);
  }

  private trackTimeSpentEvent(): void {
    if (!this.viewStartTime) return;

    const timeSpent = Date.now() - this.viewStartTime;
    this.trackEvent('time_spent', { timeSpent });
    this.viewStartTime = undefined;
  }
}

// Specialized directive for dating app profile cards
@Directive({
  selector: '[appProfileAnalytics]',
  standalone: true
})
export class ProfileAnalyticsDirective implements OnInit, OnDestroy {
  @Input() profileId!: string;
  @Input() profileData: any;

  private destroy$ = new Subject<void>();
  private viewStartTime?: number;
  private swipeStartTime?: number;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private analytics: MobileAnalyticsService,
    private gestureService: GestureService
  ) {}

  ngOnInit(): void {
    this.setupProfileTracking();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();

    if (this.viewStartTime) {
      this.trackProfileViewDuration();
    }
  }

  private setupProfileTracking(): void {
    // Track profile view
    this.trackProfileView();

    // Setup gesture tracking for swipes
    this.gestureService.enableProfileSwipeGestures(this.elementRef)
      .pipe(takeUntil(this.destroy$))
      .subscribe((swipeEvent) => {
        const swipeDuration = this.swipeStartTime ? Date.now() - this.swipeStartTime : 0;
        
        switch (swipeEvent.swipeDirection) {
          case 'right':
            this.analytics.trackProfileInteraction('like', this.profileId, {
              swipeVelocity: swipeEvent.velocity,
              swipeDuration,
              profileAge: this.profileData?.age,
              profileDistance: this.profileData?.distance
            });
            break;
          case 'left':
            this.analytics.trackProfileInteraction('pass', this.profileId, {
              swipeVelocity: swipeEvent.velocity,
              swipeDuration,
              profileAge: this.profileData?.age,
              profileDistance: this.profileData?.distance
            });
            break;
          case 'up':
            this.analytics.trackProfileInteraction('superlike', this.profileId, {
              swipeVelocity: swipeEvent.velocity,
              swipeDuration,
              profileAge: this.profileData?.age,
              profileDistance: this.profileData?.distance
            });
            break;
        }
      });

    // Track touch start for swipe timing
    this.elementRef.nativeElement.addEventListener('touchstart', () => {
      this.swipeStartTime = Date.now();
    }, { passive: true });
  }

  private trackProfileView(): void {
    this.viewStartTime = Date.now();
    
    this.analytics.trackProfileInteraction('view', this.profileId, {
      profileAge: this.profileData?.age,
      profileDistance: this.profileData?.distance,
      profileInterests: this.profileData?.interests?.length || 0,
      profilePhotoCount: this.profileData?.photos?.length || 0
    });
  }

  private trackProfileViewDuration(): void {
    if (!this.viewStartTime) return;

    const viewDuration = Date.now() - this.viewStartTime;
    
    this.analytics.trackEvent('profile_view_duration', 'engagement', {
      profileId: this.profileId,
      viewDuration,
      engagementLevel: this.getEngagementLevel(viewDuration)
    });
  }

  private getEngagementLevel(duration: number): string {
    if (duration < 2000) return 'low';
    if (duration < 10000) return 'medium';
    return 'high';
  }
}

// Directive for tracking message interactions
@Directive({
  selector: '[appMessageAnalytics]',
  standalone: true
})
export class MessageAnalyticsDirective implements OnInit, OnDestroy {
  @Input() connectionId!: string;
  @Input() messageId?: string;
  @Input() messageType: 'text' | 'revelation' | 'photo' = 'text';

  private destroy$ = new Subject<void>();
  private readStartTime?: number;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private analytics: MobileAnalyticsService
  ) {}

  ngOnInit(): void {
    this.setupMessageTracking();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();

    if (this.readStartTime) {
      this.trackMessageReadDuration();
    }
  }

  private setupMessageTracking(): void {
    // Track message view
    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !this.readStartTime) {
            this.readStartTime = Date.now();
            this.trackMessageView();
          } else if (!entry.isIntersecting && this.readStartTime) {
            this.trackMessageReadDuration();
          }
        });
      },
      { threshold: 0.8 }
    );

    intersectionObserver.observe(this.elementRef.nativeElement);

    this.destroy$.subscribe(() => {
      intersectionObserver.disconnect();
    });
  }

  private trackMessageView(): void {
    this.analytics.trackMessageInteraction('view', {
      connectionId: this.connectionId,
      messageId: this.messageId,
      messageType: this.messageType
    });
  }

  private trackMessageReadDuration(): void {
    if (!this.readStartTime) return;

    const readDuration = Date.now() - this.readStartTime;
    
    this.analytics.trackEvent('message_read_duration', 'engagement', {
      connectionId: this.connectionId,
      messageId: this.messageId,
      messageType: this.messageType,
      readDuration,
      readThoroughness: this.getReadThoroughness(readDuration)
    });

    this.readStartTime = undefined;
  }

  private getReadThoroughness(duration: number): string {
    if (duration < 1000) return 'skimmed';
    if (duration < 5000) return 'normal';
    return 'thorough';
  }

  @HostListener('click')
  onMessageClick(): void {
    this.analytics.trackEvent('message_click', 'user_interaction', {
      connectionId: this.connectionId,
      messageId: this.messageId,
      messageType: this.messageType
    });
  }
}

// Directive for tracking revelation interactions
@Directive({
  selector: '[appRevelationAnalytics]',
  standalone: true
})
export class RevelationAnalyticsDirective implements OnInit, OnDestroy {
  @Input() revelationId!: string;
  @Input() revelationDay!: number;
  @Input() connectionId!: string;

  private destroy$ = new Subject<void>();
  private interactionStartTime?: number;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private analytics: MobileAnalyticsService,
    private gestureService: GestureService
  ) {}

  ngOnInit(): void {
    this.setupRevelationTracking();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private setupRevelationTracking(): void {
    this.interactionStartTime = Date.now();

    // Track revelation view
    this.analytics.trackRevelationInteraction('view', {
      revelationId: this.revelationId,
      revelationDay: this.revelationDay,
      connectionId: this.connectionId
    });

    // Track gestures on revelation
    this.gestureService.enableGestures(this.elementRef)
      .pipe(
        takeUntil(this.destroy$),
        debounceTime(300)
      )
      .subscribe((gestureEvent) => {
        this.analytics.trackEvent('revelation_gesture', 'gesture', {
          revelationId: this.revelationId,
          gestureType: gestureEvent.type,
          revelationDay: this.revelationDay
        });
      });
  }

  @HostListener('click')
  onRevelationClick(): void {
    const interactionTime = this.interactionStartTime ? 
      Date.now() - this.interactionStartTime : 0;

    this.analytics.trackRevelationInteraction('respond', {
      revelationId: this.revelationId,
      revelationDay: this.revelationDay,
      connectionId: this.connectionId,
      interactionTime
    });
  }
}

// Directive for tracking navigation analytics
@Directive({
  selector: '[appNavAnalytics]',
  standalone: true
})
export class NavigationAnalyticsDirective implements OnInit {
  @Input() pageName!: string;
  @Input() pageCategory: string = 'main';

  constructor(private analytics: MobileAnalyticsService) {}

  ngOnInit(): void {
    this.analytics.trackNavigation(this.pageName, {
      pageCategory: this.pageCategory,
      userAgent: navigator.userAgent,
      referrer: document.referrer
    });
  }

  @HostListener('click')
  onNavigationClick(): void {
    this.analytics.trackEvent('navigation_click', 'navigation', {
      pageName: this.pageName,
      pageCategory: this.pageCategory
    });
  }
}