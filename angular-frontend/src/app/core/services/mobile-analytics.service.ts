import { Injectable, NgZone } from '@angular/core';
import { BehaviorSubject, Observable, timer, fromEvent, merge } from 'rxjs';
import { throttleTime, debounceTime, map, filter } from 'rxjs/operators';
import { MobileFeaturesService } from './mobile-features.service';
import { MobilePerformanceService } from './mobile-performance.service';
import { GestureEvent } from './gesture.service';

export interface AnalyticsEvent {
  eventName: string;
  category: EventCategory;
  parameters: Record<string, any>;
  timestamp: number;
  sessionId: string;
  userId?: string;
  deviceInfo: DeviceInfo;
  performanceMetrics?: PerformanceSnapshot;
}

export interface DeviceInfo {
  userAgent: string;
  screenSize: { width: number; height: number };
  devicePixelRatio: number;
  isTouch: boolean;
  isMobile: boolean;
  isTablet: boolean;
  isAndroid: boolean;
  isIOS: boolean;
  browserName: string;
  connectionType: string;
  batteryLevel?: number;
  isLowEndDevice: boolean;
}

export interface PerformanceSnapshot {
  memoryUsage: number;
  frameRate: number;
  loadTime: number;
  networkSpeed: string;
  renderTime: number;
}

export interface UserEngagementMetrics {
  sessionDuration: number;
  pageViews: number;
  interactions: number;
  gestureCount: number;
  profilesViewed: number;
  messagesReactions: number;
  revelationsCreated: number;
  connectionsMade: number;
  appInstalled: boolean;
  pushNotificationsEnabled: boolean;
}

export interface DatingAppMetrics {
  profileSwipes: {
    likes: number;
    passes: number;
    superLikes: number;
  };
  messageEngagement: {
    sent: number;
    received: number;
    reactions: number;
    averageResponseTime: number;
  };
  revelationEngagement: {
    created: number;
    viewed: number;
    responded: number;
    averageViewTime: number;
  };
  connectionEngagement: {
    initiated: number;
    accepted: number;
    photoReveals: number;
    completedCycles: number;
  };
}

export type EventCategory = 
  | 'user_interaction' 
  | 'navigation' 
  | 'performance' 
  | 'gesture' 
  | 'dating_action' 
  | 'engagement' 
  | 'error'
  | 'conversion';

@Injectable({
  providedIn: 'root'
})
export class MobileAnalyticsService {
  private readonly SESSION_STORAGE_KEY = 'dinner1_analytics_session';
  private readonly BATCH_SIZE = 50;
  private readonly BATCH_TIMEOUT = 30000; // 30 seconds
  private readonly MAX_RETRY_ATTEMPTS = 3;

  private sessionId: string;
  private userId?: string;
  private eventQueue: AnalyticsEvent[] = [];
  private pendingEvents: AnalyticsEvent[] = [];
  
  private sessionStartTime = Date.now();
  private lastActivityTime = Date.now();
  private pageViewCount = 0;
  private interactionCount = 0;
  private gestureCount = 0;

  private engagementMetrics: UserEngagementMetrics = {
    sessionDuration: 0,
    pageViews: 0,
    interactions: 0,
    gestureCount: 0,
    profilesViewed: 0,
    messagesReactions: 0,
    revelationsCreated: 0,
    connectionsMade: 0,
    appInstalled: false,
    pushNotificationsEnabled: false
  };

  private datingMetrics: DatingAppMetrics = {
    profileSwipes: { likes: 0, passes: 0, superLikes: 0 },
    messageEngagement: { sent: 0, received: 0, reactions: 0, averageResponseTime: 0 },
    revelationEngagement: { created: 0, viewed: 0, responded: 0, averageViewTime: 0 },
    connectionEngagement: { initiated: 0, accepted: 0, photoReveals: 0, completedCycles: 0 }
  };

  private metricsSubject = new BehaviorSubject<UserEngagementMetrics>(this.engagementMetrics);
  public metrics$ = this.metricsSubject.asObservable();

  private batchTimer: number | undefined;
  private deviceInfo: DeviceInfo;

  constructor(
    private ngZone: NgZone,
    private mobileFeatures: MobileFeaturesService,
    private performanceService: MobilePerformanceService
  ) {
    this.sessionId = this.generateSessionId();
    this.deviceInfo = this.getDeviceInfo();
    this.initializeTracking();
    this.setupEventListeners();
    this.startBatchTimer();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private initializeTracking(): void {
    // Track session start
    this.trackEvent('session_start', 'user_interaction', {
      deviceInfo: this.deviceInfo,
      timestamp: this.sessionStartTime
    });

    // Setup periodic session updates
    timer(0, 60000).subscribe(() => {
      this.updateSessionMetrics();
    });

    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.trackEvent('page_hidden', 'navigation', {
          sessionDuration: Date.now() - this.sessionStartTime
        });
        this.flushEvents();
      } else {
        this.trackEvent('page_visible', 'navigation', {
          sessionDuration: Date.now() - this.sessionStartTime
        });
      }
    });

    // Track beforeunload for session end
    window.addEventListener('beforeunload', () => {
      this.trackSessionEnd();
      this.flushEvents();
    });
  }

  private setupEventListeners(): void {
    this.ngZone.runOutsideAngular(() => {
      // Track user interactions
      const interactionEvents = ['click', 'touchstart', 'keydown'];
      interactionEvents.forEach(eventType => {
        document.addEventListener(eventType, (event) => {
          this.trackUserInteraction(event);
        }, { passive: true });
      });

      // Track scroll behavior
      let scrollTimeout: number;
      const trackScrollEnd = () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = window.setTimeout(() => {
          this.trackEvent('scroll_end', 'user_interaction', {
            scrollPosition: window.scrollY,
            maxScroll: document.documentElement.scrollHeight - window.innerHeight
          });
        }, 150);
      };

      window.addEventListener('scroll', trackScrollEnd, { passive: true });

      // Track orientation changes
      window.addEventListener('orientationchange', () => {
        setTimeout(() => {
          this.trackEvent('orientation_change', 'user_interaction', {
            orientation: window.orientation,
            screenSize: {
              width: window.innerWidth,
              height: window.innerHeight
            }
          });
        }, 100);
      });

      // Track network changes
      if ('connection' in navigator) {
        const connection = (navigator as any).connection;
        if (connection) {
          connection.addEventListener('change', () => {
            this.trackEvent('network_change', 'performance', {
              connectionType: connection.effectiveType,
              downlink: connection.downlink,
              rtt: connection.rtt
            });
          });
        }
      }
    });
  }

  /**
   * Track a custom event
   */
  trackEvent(eventName: string, category: EventCategory, parameters: Record<string, any> = {}): void {
    const event: AnalyticsEvent = {
      eventName,
      category,
      parameters: {
        ...parameters,
        url: window.location.href,
        referrer: document.referrer
      },
      timestamp: Date.now(),
      sessionId: this.sessionId,
      userId: this.userId,
      deviceInfo: this.deviceInfo,
      performanceMetrics: this.getCurrentPerformanceSnapshot()
    };

    this.eventQueue.push(event);
    this.lastActivityTime = Date.now();

    // Auto-flush if queue is getting large
    if (this.eventQueue.length >= this.BATCH_SIZE) {
      this.flushEvents();
    }
  }

  /**
   * Track dating app specific events
   */
  trackDatingAction(action: string, details: Record<string, any> = {}): void {
    this.trackEvent(`dating_${action}`, 'dating_action', details);
    this.updateDatingMetrics(action, details);
  }

  /**
   * Track gesture events
   */
  trackGesture(gestureEvent: GestureEvent): void {
    this.gestureCount++;
    this.engagementMetrics.gestureCount++;

    this.trackEvent('gesture', 'gesture', {
      gestureType: gestureEvent.type,
      deltaX: gestureEvent.deltaX,
      deltaY: gestureEvent.deltaY,
      velocity: gestureEvent.velocity,
      distance: gestureEvent.distance,
      duration: Date.now() - gestureEvent.timestamp
    });

    this.updateMetrics();
  }

  /**
   * Track profile interactions
   */
  trackProfileInteraction(action: 'view' | 'like' | 'pass' | 'superlike', profileId: string, additionalData: any = {}): void {
    if (action === 'view') {
      this.engagementMetrics.profilesViewed++;
    }

    // Update dating metrics
    if (action === 'like') {
      this.datingMetrics.profileSwipes.likes++;
    } else if (action === 'pass') {
      this.datingMetrics.profileSwipes.passes++;
    } else if (action === 'superlike') {
      this.datingMetrics.profileSwipes.superLikes++;
    }

    this.trackDatingAction(`profile_${action}`, {
      profileId,
      ...additionalData
    });

    this.updateMetrics();
  }

  /**
   * Track message interactions
   */
  trackMessageInteraction(action: 'send' | 'receive' | 'react' | 'view', messageData: any = {}): void {
    if (action === 'react') {
      this.engagementMetrics.messagesReactions++;
      this.datingMetrics.messageEngagement.reactions++;
    } else if (action === 'send') {
      this.datingMetrics.messageEngagement.sent++;
    } else if (action === 'receive') {
      this.datingMetrics.messageEngagement.received++;
    }

    this.trackDatingAction(`message_${action}`, messageData);
    this.updateMetrics();
  }

  /**
   * Track revelation interactions
   */
  trackRevelationInteraction(action: 'create' | 'view' | 'respond', revelationData: any = {}): void {
    if (action === 'create') {
      this.engagementMetrics.revelationsCreated++;
      this.datingMetrics.revelationEngagement.created++;
    } else if (action === 'view') {
      this.datingMetrics.revelationEngagement.viewed++;
    } else if (action === 'respond') {
      this.datingMetrics.revelationEngagement.responded++;
    }

    this.trackDatingAction(`revelation_${action}`, revelationData);
    this.updateMetrics();
  }

  /**
   * Track connection events
   */
  trackConnectionEvent(action: 'initiate' | 'accept' | 'photo_reveal' | 'complete_cycle', connectionData: any = {}): void {
    if (action === 'initiate') {
      this.datingMetrics.connectionEngagement.initiated++;
    } else if (action === 'accept') {
      this.engagementMetrics.connectionsMade++;
      this.datingMetrics.connectionEngagement.accepted++;
    } else if (action === 'photo_reveal') {
      this.datingMetrics.connectionEngagement.photoReveals++;
    } else if (action === 'complete_cycle') {
      this.datingMetrics.connectionEngagement.completedCycles++;
    }

    this.trackDatingAction(`connection_${action}`, connectionData);
    this.updateMetrics();
  }

  /**
   * Track navigation events
   */
  trackNavigation(page: string, additionalData: any = {}): void {
    this.pageViewCount++;
    this.engagementMetrics.pageViews++;

    this.trackEvent('page_view', 'navigation', {
      page,
      pageViewCount: this.pageViewCount,
      ...additionalData
    });

    this.updateMetrics();
  }

  /**
   * Track performance issues
   */
  trackPerformanceIssue(issue: string, details: any = {}): void {
    this.trackEvent('performance_issue', 'performance', {
      issue,
      ...details,
      performanceSnapshot: this.getCurrentPerformanceSnapshot()
    });
  }

  /**
   * Track errors
   */
  trackError(error: Error | string, context: any = {}): void {
    const errorDetails = typeof error === 'string' ? { message: error } : {
      message: error.message,
      stack: error.stack,
      name: error.name
    };

    this.trackEvent('error', 'error', {
      ...errorDetails,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  }

  /**
   * Track conversion events
   */
  trackConversion(conversionType: string, value?: number, additionalData: any = {}): void {
    this.trackEvent('conversion', 'conversion', {
      conversionType,
      value,
      ...additionalData
    });
  }

  /**
   * Track PWA installation
   */
  trackPWAInstallation(source: 'banner' | 'menu' | 'automatic'): void {
    this.engagementMetrics.appInstalled = true;
    
    this.trackEvent('pwa_install', 'conversion', {
      source,
      timeToInstall: Date.now() - this.sessionStartTime
    });

    this.updateMetrics();
  }

  /**
   * Track push notification permissions
   */
  trackPushNotificationPermission(granted: boolean, source: string): void {
    this.engagementMetrics.pushNotificationsEnabled = granted;
    
    this.trackEvent('push_permission', 'conversion', {
      granted,
      source,
      timeToPrompt: Date.now() - this.sessionStartTime
    });

    this.updateMetrics();
  }

  /**
   * Set user ID for tracking
   */
  setUserId(userId: string): void {
    this.userId = userId;
    this.trackEvent('user_identified', 'user_interaction', {
      userId,
      sessionDuration: Date.now() - this.sessionStartTime
    });
  }

  /**
   * Get current session metrics
   */
  getSessionMetrics(): UserEngagementMetrics {
    this.updateSessionMetrics();
    return { ...this.engagementMetrics };
  }

  /**
   * Get dating app specific metrics
   */
  getDatingMetrics(): DatingAppMetrics {
    return { ...this.datingMetrics };
  }

  private trackUserInteraction(event: Event): void {
    this.interactionCount++;
    this.engagementMetrics.interactions++;
    this.lastActivityTime = Date.now();

    // Track specific interaction types
    const element = event.target as HTMLElement;
    const elementType = element.tagName.toLowerCase();
    const elementClass = element.className;
    const elementId = element.id;

    this.trackEvent('user_interaction', 'user_interaction', {
      interactionType: event.type,
      elementType,
      elementClass,
      elementId,
      timestamp: event.timeStamp
    });
  }

  private updateDatingMetrics(action: string, details: any): void {
    // Update specific dating metrics based on action
    // This is already handled in specific tracking methods
  }

  private updateSessionMetrics(): void {
    this.engagementMetrics.sessionDuration = Date.now() - this.sessionStartTime;
    this.updateMetrics();
  }

  private updateMetrics(): void {
    this.metricsSubject.next({ ...this.engagementMetrics });
  }

  private trackSessionEnd(): void {
    const sessionDuration = Date.now() - this.sessionStartTime;
    
    this.trackEvent('session_end', 'user_interaction', {
      sessionDuration,
      pageViews: this.pageViewCount,
      interactions: this.interactionCount,
      gestureCount: this.gestureCount,
      datingMetrics: this.datingMetrics
    });
  }

  private getDeviceInfo(): DeviceInfo {
    const deviceInfo = this.mobileFeatures.getDeviceInfo();
    
    return {
      userAgent: navigator.userAgent,
      screenSize: deviceInfo.screenSize,
      devicePixelRatio: window.devicePixelRatio,
      isTouch: deviceInfo.isTouchDevice,
      isMobile: deviceInfo.isMobile,
      isTablet: deviceInfo.isTablet,
      isAndroid: deviceInfo.isAndroid,
      isIOS: deviceInfo.isIOS,
      browserName: this.getBrowserName(),
      connectionType: this.getConnectionType(),
      batteryLevel: deviceInfo.batteryLevel,
      isLowEndDevice: deviceInfo.isLowEndDevice
    };
  }

  private getBrowserName(): string {
    const userAgent = navigator.userAgent;
    
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    if (userAgent.includes('Opera')) return 'Opera';
    
    return 'Unknown';
  }

  private getConnectionType(): string {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      return connection?.effectiveType || 'unknown';
    }
    return 'unknown';
  }

  private getCurrentPerformanceSnapshot(): PerformanceSnapshot | undefined {
    try {
      const metrics = this.performanceService.performance$.value;
      return {
        memoryUsage: metrics.memoryUsage,
        frameRate: metrics.frameRate,
        loadTime: metrics.loadTime,
        networkSpeed: metrics.networkSpeed,
        renderTime: metrics.renderTime
      };
    } catch (error) {
      return undefined;
    }
  }

  private startBatchTimer(): void {
    this.batchTimer = window.setInterval(() => {
      if (this.eventQueue.length > 0) {
        this.flushEvents();
      }
    }, this.BATCH_TIMEOUT);
  }

  /**
   * Flush queued events to server
   */
  private async flushEvents(): Promise<void> {
    if (this.eventQueue.length === 0) return;

    const events = [...this.eventQueue];
    this.eventQueue = [];

    try {
      await this.sendEventsToServer(events);
    } catch (error) {
      console.error('Failed to send analytics events:', error);
      
      // Add events back to pending queue for retry
      this.pendingEvents.push(...events);
      
      // Retry pending events
      this.retryPendingEvents();
    }
  }

  private async sendEventsToServer(events: AnalyticsEvent[]): Promise<void> {
    // In a real implementation, this would send to your analytics endpoint
    // For now, we'll just log to console in development
    if (!window.location.hostname.includes('localhost')) {
      const response = await fetch('/api/v1/analytics/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify({ events })
      });

      if (!response.ok) {
        throw new Error(`Analytics request failed: ${response.status}`);
      }
    } else {
      console.log('Analytics Events:', events);
    }
  }

  private async retryPendingEvents(): Promise<void> {
    if (this.pendingEvents.length === 0) return;

    const events = [...this.pendingEvents];
    this.pendingEvents = [];

    try {
      await this.sendEventsToServer(events);
    } catch (error) {
      console.error('Retry failed for analytics events:', error);
      
      // Give up after max retries
      if (events.length < this.MAX_RETRY_ATTEMPTS * this.BATCH_SIZE) {
        // Store in localStorage as fallback
        this.storeEventsLocally(events);
      }
    }
  }

  private storeEventsLocally(events: AnalyticsEvent[]): void {
    try {
      const existingEvents = JSON.parse(localStorage.getItem('failed_analytics_events') || '[]');
      const allEvents = [...existingEvents, ...events];
      
      // Limit stored events to prevent localStorage bloat
      const maxStoredEvents = 1000;
      const eventsToStore = allEvents.slice(-maxStoredEvents);
      
      localStorage.setItem('failed_analytics_events', JSON.stringify(eventsToStore));
    } catch (error) {
      console.error('Failed to store analytics events locally:', error);
    }
  }

  private getAuthToken(): string {
    return localStorage.getItem('auth_token') || '';
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.trackSessionEnd();
    this.flushEvents();
    
    if (this.batchTimer) {
      clearInterval(this.batchTimer);
    }
  }
}