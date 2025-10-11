import { Injectable, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, fromEvent, interval } from 'rxjs';
import { map, filter, debounceTime, distinctUntilChanged, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface UIPersonalization {
  theme_adaptations: Record<string, unknown>;
  layout_optimizations: Record<string, unknown>;
  interaction_enhancements: Record<string, unknown>;
  accessibility_improvements: Record<string, unknown>;
  performance_optimizations: Record<string, unknown>;
  component_adaptations: Record<string, unknown>;
}

export interface InteractionData {
  type: string;
  element_type?: string;
  element_id?: string;
  page_route?: string;
  device_type?: string;
  screen_size?: string;
  viewport_size?: string;
  scroll_position?: number;
  session_id?: string;
  time_since_last?: number;
  duration?: number;
  coordinates?: { x: number; y: number };
  scroll_distance?: number;
  swipe_direction?: string;
  gesture_data?: Record<string, unknown>;
  emotional_state?: string;
  connection_context?: Record<string, unknown>;
  feature_flags?: Record<string, boolean>;
  render_time?: number;
  response_time?: number;
  error?: boolean;
  error_details?: string;
}

export interface UIProfile {
  id: number;
  user_id: number;
  primary_device_type: string;
  preferred_theme: string;
  font_size_preference: string;
  animation_preference: string;
  layout_density: string;
  interaction_speed: string;
  navigation_pattern: string;
  personalization_score: number;
  accessibility_settings: { [key: string]: boolean };
  current_preferences: Record<string, unknown>;
  last_updated: string;
}

@Injectable({
  providedIn: 'root'
})
export class UIPersonalizationService {
  private readonly apiUrl = `${environment.apiUrl}/ui-personalization`;

  // State management
  private personalizations = new BehaviorSubject<UIPersonalization | null>(null);
  private uiProfile = new BehaviorSubject<UIProfile | null>(null);
  private isTracking = new BehaviorSubject<boolean>(false);

  // Session tracking
  private sessionId: string;
  private lastInteractionTime: number = 0;
  private interactionQueue: InteractionData[] = [];
  private currentRoute: string = '';

  // Performance monitoring
  private performanceObserver?: PerformanceObserver;
  private renderTimes: number[] = [];

  // Public observables
  personalizations$ = this.personalizations.asObservable();
  uiProfile$ = this.uiProfile.asObservable();
  isTracking$ = this.isTracking.asObservable();

  constructor(
    private http: HttpClient,
    private ngZone: NgZone
  ) {
    this.sessionId = this.generateSessionId();
    this.initializeTracking();
    this.setupPerformanceMonitoring();
  }

  /**
   * Initialize interaction tracking
   */
  private initializeTracking(): void {
    if (typeof window === 'undefined') return;

    // Track various interaction types
    this.setupInteractionListeners();
    this.setupNavigationTracking();
    this.setupErrorTracking();

    // Process interaction queue periodically
    interval(5000).subscribe(() => {
      this.processInteractionQueue();
    });
  }

  /**
   * Start tracking user interactions
   */
  startTracking(): void {
    this.isTracking.next(true);
  }

  /**
   * Stop tracking user interactions
   */
  stopTracking(): void {
    this.isTracking.next(false);
    this.processInteractionQueue(); // Process remaining interactions
  }

  /**
   * Get UI profile
   */
  getUIProfile(): Observable<UIProfile> {
    return this.http.get<UIProfile>(`${this.apiUrl}/profile`).pipe(
      tap(profile => this.uiProfile.next(profile))
    );
  }

  /**
   * Generate UI personalizations
   */
  generatePersonalizations(context: Record<string, unknown> = {}): Observable<UIPersonalization> {
    const request = {
      current_context: {
        ...context,
        page_route: this.currentRoute,
        timestamp: new Date().toISOString(),
        session_id: this.sessionId,
        screen_size: `${window.innerWidth}x${window.innerHeight}`,
        device_type: this.detectDeviceType(),
        user_agent: navigator.userAgent
      }
    };

    return this.http.post<{ personalizations: UIPersonalization }>(`${this.apiUrl}/generate-adaptations`, request).pipe(
      map(response => response.personalizations),
      tap(personalizations => this.personalizations.next(personalizations))
    );
  }

  /**
   * Apply UI personalizations
   */
  applyPersonalizations(personalizations: UIPersonalization): void {
    this.ngZone.run(() => {
      // Apply theme adaptations
      this.applyThemeAdaptations(personalizations.theme_adaptations);

      // Apply layout optimizations
      this.applyLayoutOptimizations(personalizations.layout_optimizations);

      // Apply interaction enhancements
      this.applyInteractionEnhancements(personalizations.interaction_enhancements);

      // Apply accessibility improvements
      this.applyAccessibilityImprovements(personalizations.accessibility_improvements);

      // Apply performance optimizations
      this.applyPerformanceOptimizations(personalizations.performance_optimizations);

      // Apply component adaptations
      this.applyComponentAdaptations(personalizations.component_adaptations);
    });
  }

  /**
   * Track user interaction
   */
  trackInteraction(interaction: Partial<InteractionData>): void {
    if (!this.isTracking.value) return;

    const fullInteraction: InteractionData = {
      type: interaction.type || 'unknown',
      session_id: this.sessionId,
      page_route: this.currentRoute,
      device_type: this.detectDeviceType(),
      screen_size: `${window.innerWidth}x${window.innerHeight}`,
      viewport_size: `${window.innerWidth}x${window.innerHeight}`,
      time_since_last: this.lastInteractionTime ? Date.now() - this.lastInteractionTime : 0,
      ...interaction
    };

    this.interactionQueue.push(fullInteraction);
    this.lastInteractionTime = Date.now();

    // Process immediately for critical interactions
    if (interaction.error || interaction.type === 'navigation') {
      this.processInteractionQueue();
    }
  }

  /**
   * Update UI preferences
   */
  updatePreferences(preferences: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.http.put<Record<string, unknown>>(`${this.apiUrl}/preferences`, preferences);
  }

  /**
   * Submit personalization feedback
   */
  submitFeedback(feedback: {
    satisfaction_score: number;
    feature?: string;
    comments?: string;
  }): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.apiUrl}/feedback`, feedback);
  }

  /**
   * Get personalization insights
   */
  getInsights(): Observable<Record<string, unknown>[]> {
    return this.http.get<Record<string, unknown>[]>(`${this.apiUrl}/insights`);
  }

  /**
   * Get UI analytics
   */
  getAnalytics(days: number = 30): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.apiUrl}/analytics?days=${days}`);
  }

  /**
   * Trigger real-time adaptation
   */
  triggerRealTimeAdaptation(context: Record<string, unknown> = {}): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.apiUrl}/real-time-adaptation`, {
      ...context,
      current_route: this.currentRoute,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Set current route for tracking
   */
  setCurrentRoute(route: string): void {
    const previousRoute = this.currentRoute;
    this.currentRoute = route;

    if (previousRoute && previousRoute !== route) {
      this.trackInteraction({
        type: 'navigation',
        element_type: 'route_change',
        element_id: route,
        duration: Date.now() - this.lastInteractionTime
      });
    }
  }

  // Private methods

  private setupInteractionListeners(): void {
    if (typeof window === 'undefined') return;

    // Click tracking
    fromEvent(document, 'click').pipe(
      filter(() => this.isTracking.value),
      debounceTime(100)
    ).subscribe((event: Event) => {
      const clickEvent = event as MouseEvent;
      const target = event.target as HTMLElement;

      this.trackInteraction({
        type: 'click',
        element_type: target.tagName.toLowerCase(),
        element_id: target.id || target.className,
        coordinates: { x: clickEvent.clientX, y: clickEvent.clientY },
        duration: 0
      });
    });

    // Scroll tracking
    fromEvent(window, 'scroll').pipe(
      filter(() => this.isTracking.value),
      debounceTime(250),
      distinctUntilChanged()
    ).subscribe(() => {
      this.trackInteraction({
        type: 'scroll',
        scroll_position: window.scrollY,
        scroll_distance: Math.abs(window.scrollY - (this.getLastScrollPosition() || 0))
      });
    });

    // Touch/swipe tracking (mobile)
    this.setupTouchTracking();

    // Keyboard tracking
    fromEvent(document, 'keydown').pipe(
      filter(() => this.isTracking.value),
      debounceTime(100)
    ).subscribe((event: Event) => {
      const keyEvent = event as KeyboardEvent;

      this.trackInteraction({
        type: 'keyboard',
        element_type: 'keypress',
        element_id: keyEvent.key,
        duration: 0
      });
    });

    // Form interaction tracking
    fromEvent(document, 'input').pipe(
      filter(() => this.isTracking.value),
      debounceTime(300)
    ).subscribe((event: Event) => {
      const target = event.target as HTMLInputElement;

      this.trackInteraction({
        type: 'form_interaction',
        element_type: target.type,
        element_id: target.id || target.name,
        duration: 0
      });
    });

    // Hover tracking (desktop)
    if (!this.isMobileDevice()) {
      fromEvent(document, 'mouseover').pipe(
        filter(() => this.isTracking.value),
        debounceTime(500)
      ).subscribe((event: Event) => {
        const target = event.target as HTMLElement;

        this.trackInteraction({
          type: 'hover',
          element_type: target.tagName.toLowerCase(),
          element_id: target.id || target.className,
          duration: 0
        });
      });
    }
  }

  private setupTouchTracking(): void {
    if (typeof window === 'undefined' || !('ontouchstart' in window)) return;

    let touchStartTime: number;
    let touchStartPos: { x: number; y: number };

    fromEvent(document, 'touchstart').pipe(
      filter(() => this.isTracking.value)
    ).subscribe((event: Event) => {
      const touchEvent = event as TouchEvent;
      touchStartTime = Date.now();
      touchStartPos = {
        x: touchEvent.touches[0].clientX,
        y: touchEvent.touches[0].clientY
      };
    });

    fromEvent(document, 'touchend').pipe(
      filter(() => this.isTracking.value)
    ).subscribe((event: Event) => {
      const touchEvent = event as TouchEvent;
      const touchEndTime = Date.now();
      const touchEndPos = {
        x: touchEvent.changedTouches[0].clientX,
        y: touchEvent.changedTouches[0].clientY
      };

      const duration = touchEndTime - touchStartTime;
      const deltaX = touchEndPos.x - touchStartPos.x;
      const deltaY = touchEndPos.y - touchStartPos.y;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

      // Determine if it's a swipe
      if (distance > 50 && duration < 300) {
        const swipeDirection = Math.abs(deltaX) > Math.abs(deltaY)
          ? (deltaX > 0 ? 'right' : 'left')
          : (deltaY > 0 ? 'down' : 'up');

        this.trackInteraction({
          type: 'swipe',
          swipe_direction: swipeDirection,
          coordinates: touchStartPos,
          duration: duration,
          gesture_data: { distance, deltaX, deltaY }
        });
      } else {
        // Regular touch
        this.trackInteraction({
          type: 'click', // Treat as click for touch devices
          coordinates: touchStartPos,
          duration: duration
        });
      }
    });
  }

  private setupNavigationTracking(): void {
    // This would integrate with Angular Router to track route changes
    // For now, we'll track it manually via setCurrentRoute
  }

  private setupErrorTracking(): void {
    if (typeof window === 'undefined') return;

    // JavaScript errors
    window.addEventListener('error', (event) => {
      if (this.isTracking.value) {
        this.trackInteraction({
          type: 'error',
          error: true,
          error_details: event.message,
          element_id: event.filename,
          page_route: this.currentRoute
        });
      }
    });

    // Promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      if (this.isTracking.value) {
        this.trackInteraction({
          type: 'error',
          error: true,
          error_details: event.reason?.toString() || 'Unhandled promise rejection',
          page_route: this.currentRoute
        });
      }
    });
  }

  private setupPerformanceMonitoring(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    this.performanceObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          const navEntry = entry as PerformanceNavigationTiming;
          this.trackInteraction({
            type: 'navigation',
            render_time: navEntry.loadEventEnd - navEntry.loadEventStart,
            response_time: navEntry.responseEnd - navEntry.requestStart,
            page_route: this.currentRoute
          });
        }
      }
    });

    try {
      this.performanceObserver.observe({ entryTypes: ['navigation', 'measure'] });
    } catch (e) {
      console.warn('Performance monitoring not supported');
    }
  }

  private processInteractionQueue(): void {
    if (this.interactionQueue.length === 0) return;

    const interactions = [...this.interactionQueue];
    this.interactionQueue = [];

    // Send interactions in batches to backend
    interactions.forEach(interaction => {
      this.http.post(`${this.apiUrl}/track-interaction`, interaction).subscribe({
        error: (err) => {
          console.warn('Failed to track interaction:', err);
          // Re-queue on failure (with limit to prevent infinite growth)
          if (this.interactionQueue.length < 100) {
            this.interactionQueue.push(interaction);
          }
        }
      });
    });
  }

  private applyThemeAdaptations(adaptations: Record<string, unknown>): void {
    if (!adaptations) return;

    const root = document.documentElement;

    const suggestDarkMode = adaptations['suggest_dark_mode'] as { enabled?: boolean } | undefined;
    if (suggestDarkMode?.enabled) {
      root.setAttribute('data-theme', 'dark');
    }

    const highContrast = adaptations['high_contrast'] as { enabled?: boolean } | undefined;
    if (highContrast?.enabled) {
      root.classList.add('high-contrast');
    }

    const fontScaling = adaptations['font_scaling'] as { scale_factor?: number } | undefined;
    if (fontScaling?.scale_factor) {
      root.style.fontSize = `${fontScaling.scale_factor * 16}px`;
    }
  }

  private applyLayoutOptimizations(optimizations: Record<string, unknown>): void {
    if (!optimizations) return;

    const body = document.body;

    const mobileFirst = optimizations['mobile_first'] as { thumb_friendly_layout?: boolean } | undefined;
    if (mobileFirst?.thumb_friendly_layout) {
      body.classList.add('thumb-friendly');
    }

    const swipeOptimized = optimizations['swipe_optimized'] as { increase_swipe_targets?: boolean } | undefined;
    if (swipeOptimized?.increase_swipe_targets) {
      body.classList.add('swipe-optimized');
    }

    const clickOptimized = optimizations['click_optimized'] as { larger_touch_targets?: boolean } | undefined;
    if (clickOptimized?.larger_touch_targets) {
      body.classList.add('large-touch-targets');
    }
  }

  private applyInteractionEnhancements(enhancements: Record<string, unknown>): void {
    if (!enhancements) return;

    const fastUserOptimizations = enhancements['fast_user_optimizations'] as { enable_keyboard_shortcuts?: boolean } | undefined;
    if (fastUserOptimizations?.enable_keyboard_shortcuts) {
      // Enable keyboard shortcuts
      document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    const engagementBoosters = enhancements['engagement_boosters'] as { add_micro_interactions?: boolean } | undefined;
    if (engagementBoosters?.add_micro_interactions) {
      document.body.classList.add('micro-interactions-enabled');
    }
  }

  private applyAccessibilityImprovements(improvements: Record<string, unknown>): void {
    if (!improvements) return;

    const keyboardNavigation = improvements['keyboard_navigation'] as { visible_focus_indicators?: boolean } | undefined;
    if (keyboardNavigation?.visible_focus_indicators) {
      document.body.classList.add('enhanced-focus');
    }

    const motorAccessibility = improvements['motor_accessibility'] as { larger_touch_targets?: boolean } | undefined;
    if (motorAccessibility?.larger_touch_targets) {
      document.body.classList.add('motor-accessible');
    }
  }

  private applyPerformanceOptimizations(optimizations: Record<string, unknown>): void {
    if (!optimizations) return;

    const loadingOptimizations = optimizations['loading_optimizations'] as { lazy_loading?: boolean } | undefined;
    if (loadingOptimizations?.lazy_loading) {
      // Enable lazy loading for images
      document.body.setAttribute('data-lazy-loading', 'true');
    }

    const mobilePerformance = optimizations['mobile_performance'] as { reduced_animations?: boolean } | undefined;
    if (mobilePerformance?.reduced_animations) {
      document.body.classList.add('reduced-animations');
    }
  }

  private applyComponentAdaptations(adaptations: Record<string, unknown>): void {
    if (!adaptations) return;

    // Apply component-specific adaptations
    Object.keys(adaptations).forEach(component => {
      const componentAdaptations = adaptations[component] as { keyboard_optimized?: boolean; swipe_optimized?: boolean } | undefined;
      const elements = document.querySelectorAll(`[data-component="${component}"]`);

      elements.forEach(element => {
        if (componentAdaptations?.keyboard_optimized) {
          element.classList.add('keyboard-optimized');
        }

        if (componentAdaptations?.swipe_optimized) {
          element.classList.add('swipe-optimized');
        }
      });
    });
  }

  private handleKeyboardShortcuts(event: KeyboardEvent): void {
    // Implement keyboard shortcuts based on user behavior
    if (event.ctrlKey || event.metaKey) {
      switch (event.key) {
        case '/': {
          event.preventDefault();
          // Focus search
          const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement;
          if (searchInput) searchInput.focus();
          break;
        }

        case 'k':
          event.preventDefault();
          // Open command palette or quick actions
          this.trackInteraction({
            type: 'keyboard',
            element_type: 'shortcut',
            element_id: 'quick_action'
          });
          break;
      }
    }
  }

  private detectDeviceType(): string {
    if (typeof window === 'undefined') return 'unknown';

    const width = window.innerWidth;

    if (width <= 768) return 'mobile';
    if (width <= 1024) return 'tablet';
    return 'desktop';
  }

  private isMobileDevice(): boolean {
    return this.detectDeviceType() === 'mobile';
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }

  private getLastScrollPosition(): number | null {
    // Retrieve from session storage or memory
    return 0; // Placeholder
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.stopTracking();

    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
    }
  }
}
