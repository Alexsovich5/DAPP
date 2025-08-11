/**
 * Comprehensive Dashboard Component Tests - Maximum Coverage
 * Tests main user dashboard with soul connections, activities, and statistics
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialogModule } from '@angular/material/dialog';
import { of, throwError, BehaviorSubject } from 'rxjs';

import { DashboardComponent } from './dashboard.component';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { RevelationService } from '../../core/services/revelation.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { WebSocketService } from '../../core/services/websocket.service';

interface DashboardStats {
  active_connections: number;
  pending_connections: number;
  completed_revelations: number;
  photo_reveals_completed: number;
  compatibility_avg: number;
  profile_views_this_week: number;
  messages_exchanged: number;
  soul_depth_score: number;
}

interface ActiveConnection {
  id: number;
  partner_name: string;
  compatibility_score: number;
  current_day: number;
  last_activity: string;
  unread_messages: number;
  connection_stage: string;
  revelation_progress: {
    user_completed: number;
    partner_completed: number;
    total_days: number;
  };
  recent_activity: {
    type: string;
    description: string;
    timestamp: string;
  }[];
}

interface RecentActivity {
  id: number;
  type: 'new_connection' | 'revelation_shared' | 'message_received' | 'photo_reveal' | 'profile_view';
  title: string;
  description: string;
  timestamp: string;
  connection_id?: number;
  partner_name?: string;
  is_read: boolean;
  priority: 'high' | 'medium' | 'low';
}

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let soulConnectionService: jasmine.SpyObj<SoulConnectionService>;
  let revelationService: jasmine.SpyObj<RevelationService>;
  let authService: jasmine.SpyObj<AuthService>;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let webSocketService: jasmine.SpyObj<WebSocketService>;

  const mockDashboardStats: DashboardStats = {
    active_connections: 3,
    pending_connections: 2,
    completed_revelations: 15,
    photo_reveals_completed: 1,
    compatibility_avg: 84.5,
    profile_views_this_week: 12,
    messages_exchanged: 47,
    soul_depth_score: 8.7
  };

  const mockActiveConnections: ActiveConnection[] = [
    {
      id: 1,
      partner_name: 'Emma',
      compatibility_score: 88.5,
      current_day: 4,
      last_activity: '2025-01-20T14:30:00Z',
      unread_messages: 2,
      connection_stage: 'revelation_cycle',
      revelation_progress: {
        user_completed: 4,
        partner_completed: 3,
        total_days: 7
      },
      recent_activity: [
        {
          type: 'revelation_shared',
          description: 'Emma shared a hope and dream',
          timestamp: '2025-01-20T14:30:00Z'
        },
        {
          type: 'message_received',
          description: 'New message about day 4 revelation',
          timestamp: '2025-01-20T13:15:00Z'
        }
      ]
    },
    {
      id: 2,
      partner_name: 'Sofia',
      compatibility_score: 79.2,
      current_day: 6,
      last_activity: '2025-01-20T10:45:00Z',
      unread_messages: 0,
      connection_stage: 'photo_reveal_pending',
      revelation_progress: {
        user_completed: 7,
        partner_completed: 7,
        total_days: 7
      },
      recent_activity: [
        {
          type: 'photo_consent',
          description: 'Both ready for photo reveal!',
          timestamp: '2025-01-20T10:45:00Z'
        }
      ]
    }
  ];

  const mockRecentActivities: RecentActivity[] = [
    {
      id: 1,
      type: 'revelation_shared',
      title: 'New Revelation Shared',
      description: 'Emma shared their hopes and dreams with you',
      timestamp: '2025-01-20T14:30:00Z',
      connection_id: 1,
      partner_name: 'Emma',
      is_read: false,
      priority: 'high'
    },
    {
      id: 2,
      type: 'new_connection',
      title: 'New Soul Connection',
      description: 'Alex wants to start a soul connection journey with you',
      timestamp: '2025-01-20T09:15:00Z',
      connection_id: 3,
      partner_name: 'Alex',
      is_read: false,
      priority: 'high'
    },
    {
      id: 3,
      type: 'profile_view',
      title: 'Profile Views',
      description: '3 people viewed your soul profile today',
      timestamp: '2025-01-20T08:00:00Z',
      is_read: true,
      priority: 'medium'
    }
  ];

  beforeEach(async () => {
    const soulConnectionSpy = jasmine.createSpyObj('SoulConnectionService', [
      'getDashboardStats',
      'getActiveConnections',
      'acceptConnection',
      'declineConnection'
    ]);

    const revelationSpy = jasmine.createSpyObj('RevelationService', [
      'getRecentActivities',
      'getRevelationProgress',
      'getTodaysRevelations'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser',
      'getUserProfile'
    ]);

    const notificationSpy = jasmine.createSpyObj('NotificationService', [
      'showSuccess',
      'showError',
      'showInfo',
      'markAsRead'
    ]);

    const webSocketSpy = jasmine.createSpyObj('WebSocketService', [
      'connect',
      'disconnect',
      'onMessage',
      'onConnectionStatusChange'
    ]);

    await TestBed.configureTestingModule({
      declarations: [DashboardComponent],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NoopAnimationsModule,
        MatCardModule,
        MatButtonModule,
        MatProgressBarModule,
        MatIconModule,
        MatBadgeModule,
        MatMenuModule,
        MatTooltipModule,
        MatDialogModule
      ],
      providers: [
        { provide: SoulConnectionService, useValue: soulConnectionSpy },
        { provide: RevelationService, useValue: revelationSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notificationSpy },
        { provide: WebSocketService, useValue: webSocketSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;

    soulConnectionService = TestBed.inject(SoulConnectionService) as jasmine.SpyObj<SoulConnectionService>;
    revelationService = TestBed.inject(RevelationService) as jasmine.SpyObj<RevelationService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;
    webSocketService = TestBed.inject(WebSocketService) as jasmine.SpyObj<WebSocketService>;

    // Default mock returns
    authService.getCurrentUser.and.returnValue(of({
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      emotional_onboarding_completed: true
    }));
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with loading states', () => {
      expect(component.isLoading).toBe(true);
      expect(component.dashboardStats).toBeUndefined();
      expect(component.activeConnections).toEqual([]);
      expect(component.recentActivities).toEqual([]);
    });

    it('should load all dashboard data on init', fakeAsync(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(mockDashboardStats));
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      revelationService.getRecentActivities.and.returnValue(of(mockRecentActivities));

      fixture.detectChanges();
      tick();

      expect(soulConnectionService.getDashboardStats).toHaveBeenCalled();
      expect(soulConnectionService.getActiveConnections).toHaveBeenCalled();
      expect(revelationService.getRecentActivities).toHaveBeenCalled();
      expect(component.isLoading).toBe(false);
    }));

    it('should handle loading errors gracefully', fakeAsync(() => {
      soulConnectionService.getDashboardStats.and.returnValue(
        throwError({ error: { detail: 'Dashboard data unavailable' } })
      );

      fixture.detectChanges();
      tick();

      expect(component.loadingError).toBeTruthy();
      expect(notificationService.showError).toHaveBeenCalledWith(
        'Unable to load dashboard data. Please refresh the page.'
      );
    }));
  });

  describe('Dashboard Statistics Display', () => {
    beforeEach(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(mockDashboardStats));
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      revelationService.getRecentActivities.and.returnValue(of(mockRecentActivities));
    });

    it('should display all key statistics', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const statCards = fixture.debugElement.queryAll(By.css('.stat-card'));
      expect(statCards.length).toBeGreaterThanOrEqual(6);

      const statTexts = statCards.map(card => card.nativeElement.textContent);
      expect(statTexts.some(text => text.includes('3'))).toBe(true); // Active connections
      expect(statTexts.some(text => text.includes('84.5'))).toBe(true); // Compatibility avg
      expect(statTexts.some(text => text.includes('8.7'))).toBe(true); // Soul depth score
    }));

    it('should format statistics with appropriate units', () => {
      component.dashboardStats = mockDashboardStats;

      expect(component.formatCompatibilityAvg()).toBe('84.5%');
      expect(component.formatSoulDepthScore()).toBe('8.7/10');
      expect(component.formatMessagesExchanged()).toBe('47 messages');
    });

    it('should show progress indicators for stats', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const progressBars = fixture.debugElement.queryAll(By.css('.stat-progress'));
      expect(progressBars.length).toBeGreaterThan(0);

      const soulDepthProgress = fixture.debugElement.query(By.css('.soul-depth-progress'));
      expect(soulDepthProgress).toBeTruthy();
    }));

    it('should handle zero or missing statistics', () => {
      const emptyStats: DashboardStats = {
        active_connections: 0,
        pending_connections: 0,
        completed_revelations: 0,
        photo_reveals_completed: 0,
        compatibility_avg: 0,
        profile_views_this_week: 0,
        messages_exchanged: 0,
        soul_depth_score: 0
      };

      soulConnectionService.getDashboardStats.and.returnValue(of(emptyStats));
      fixture.detectChanges();

      expect(component.getEmptyStateMessage()).toContain('Get started');
    });

    it('should show statistical trends and insights', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const insights = fixture.debugElement.queryAll(By.css('.stat-insight'));
      expect(insights.length).toBeGreaterThan(0);

      expect(component.getCompatibilityTrend()).toBeDefined();
      expect(component.getSoulDepthInsight()).toBeDefined();
    }));
  });

  describe('Active Connections Display', () => {
    beforeEach(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(mockDashboardStats));
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      revelationService.getRecentActivities.and.returnValue(of(mockRecentActivities));
    });

    it('should display all active connections', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const connectionCards = fixture.debugElement.queryAll(By.css('.connection-card'));
      expect(connectionCards.length).toBe(mockActiveConnections.length);

      expect(connectionCards[0].nativeElement.textContent).toContain('Emma');
      expect(connectionCards[1].nativeElement.textContent).toContain('Sofia');
    }));

    it('should show compatibility scores with visual indicators', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const compatibilityScores = fixture.debugElement.queryAll(By.css('.compatibility-score'));
      expect(compatibilityScores.length).toBe(mockActiveConnections.length);

      expect(compatibilityScores[0].nativeElement.textContent).toContain('88.5%');
      expect(compatibilityScores[1].nativeElement.textContent).toContain('79.2%');
    }));

    it('should display revelation progress for each connection', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const progressBars = fixture.debugElement.queryAll(By.css('.revelation-progress'));
      expect(progressBars.length).toBe(mockActiveConnections.length);

      const firstProgress = progressBars[0];
      expect(firstProgress.nativeElement.textContent).toContain('4/7');
    }));

    it('should show unread message indicators', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageIndicators = fixture.debugElement.queryAll(By.css('.message-indicator'));
      const emmaCard = fixture.debugElement.query(By.css('[data-connection-id="1"]'));
      
      const emmaBadge = emmaCard.query(By.css('.unread-badge'));
      expect(emmaBadge).toBeTruthy();
      expect(emmaBadge.nativeElement.textContent.trim()).toBe('2');
    }));

    it('should display connection stage information', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const stageIndicators = fixture.debugElement.queryAll(By.css('.stage-indicator'));
      expect(stageIndicators.length).toBe(mockActiveConnections.length);

      expect(stageIndicators[0].nativeElement.textContent).toContain('revelation_cycle');
      expect(stageIndicators[1].nativeElement.textContent).toContain('photo_reveal_pending');
    }));

    it('should show last activity timestamps', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const timestamps = fixture.debugElement.queryAll(By.css('.last-activity'));
      expect(timestamps.length).toBe(mockActiveConnections.length);

      expect(component.formatLastActivity(mockActiveConnections[0].last_activity)).toContain('ago');
    }));

    it('should navigate to connection details on click', fakeAsync(() => {
      const routerSpy = spyOn(component['router'], 'navigate');
      fixture.detectChanges();
      tick();

      const firstConnection = fixture.debugElement.query(By.css('.connection-card'));
      firstConnection.triggerEventHandler('click', {});

      expect(routerSpy).toHaveBeenCalledWith(['/connections', mockActiveConnections[0].id]);
    }));

    it('should handle empty connections state', () => {
      soulConnectionService.getActiveConnections.and.returnValue(of([]));
      fixture.detectChanges();

      const emptyState = fixture.debugElement.query(By.css('.empty-connections'));
      expect(emptyState).toBeTruthy();
      expect(emptyState.nativeElement.textContent).toContain('No active connections');
    });
  });

  describe('Recent Activities Display', () => {
    beforeEach(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(mockDashboardStats));
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      revelationService.getRecentActivities.and.returnValue(of(mockRecentActivities));
    });

    it('should display all recent activities', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const activityItems = fixture.debugElement.queryAll(By.css('.activity-item'));
      expect(activityItems.length).toBe(mockRecentActivities.length);
    }));

    it('should show activity types with appropriate icons', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const activityIcons = fixture.debugElement.queryAll(By.css('.activity-icon'));
      expect(activityIcons.length).toBe(mockRecentActivities.length);

      expect(component.getActivityIcon('revelation_shared')).toBe('favorite');
      expect(component.getActivityIcon('new_connection')).toBe('connect_without_contact');
      expect(component.getActivityIcon('profile_view')).toBe('visibility');
    }));

    it('should mark activities as read/unread', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const unreadItems = fixture.debugElement.queryAll(By.css('.activity-item.unread'));
      expect(unreadItems.length).toBe(2); // Two unread activities in mock data
    }));

    it('should handle activity interactions', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const firstActivity = fixture.debugElement.query(By.css('.activity-item'));
      firstActivity.triggerEventHandler('click', {});

      expect(component.handleActivityClick).toHaveBeenCalledWith(mockRecentActivities[0]);
    }));

    it('should show activity timestamps with relative formatting', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const timestamps = fixture.debugElement.queryAll(By.css('.activity-timestamp'));
      expect(timestamps.length).toBe(mockRecentActivities.length);

      expect(component.formatActivityTimestamp(mockRecentActivities[0].timestamp)).toContain('ago');
    }));

    it('should prioritize high-priority activities', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const highPriorityItems = fixture.debugElement.queryAll(By.css('.activity-item.high-priority'));
      expect(highPriorityItems.length).toBe(2);
    }));

    it('should show "Mark all as read" option', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const markAllButton = fixture.debugElement.query(By.css('.mark-all-read'));
      expect(markAllButton).toBeTruthy();

      markAllButton.triggerEventHandler('click', {});
      expect(component.markAllActivitiesAsRead).toHaveBeenCalled();
    }));
  });

  describe('Real-Time Updates', () => {
    beforeEach(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(mockDashboardStats));
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      revelationService.getRecentActivities.and.returnValue(of(mockRecentActivities));
    });

    it('should connect to WebSocket on init', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(webSocketService.connect).toHaveBeenCalled();
    }));

    it('should handle real-time connection updates', fakeAsync(() => {
      const connectionUpdate = {
        type: 'connection_update',
        connection_id: 1,
        unread_messages: 3
      };

      webSocketService.onMessage.and.returnValue(of(connectionUpdate));
      fixture.detectChanges();
      tick();

      expect(component.handleRealtimeUpdate).toHaveBeenCalledWith(connectionUpdate);
    }));

    it('should update activity feed in real-time', fakeAsync(() => {
      const newActivity: RecentActivity = {
        id: 4,
        type: 'message_received',
        title: 'New Message',
        description: 'You have a new message from Emma',
        timestamp: new Date().toISOString(),
        connection_id: 1,
        partner_name: 'Emma',
        is_read: false,
        priority: 'high'
      };

      const activityUpdate = {
        type: 'new_activity',
        activity: newActivity
      };

      webSocketService.onMessage.and.returnValue(of(activityUpdate));
      fixture.detectChanges();
      tick();

      expect(component.recentActivities).toContain(newActivity);
    }));

    it('should show real-time notifications for important events', fakeAsync(() => {
      const photoRevealNotification = {
        type: 'photo_reveal_ready',
        connection_id: 1,
        partner_name: 'Emma'
      };

      webSocketService.onMessage.and.returnValue(of(photoRevealNotification));
      fixture.detectChanges();
      tick();

      expect(notificationService.showInfo).toHaveBeenCalledWith(
        'Emma is ready for photo reveal! 📸'
      );
    }));

    it('should update statistics in real-time', fakeAsync(() => {
      const statsUpdate = {
        type: 'stats_update',
        stats: {
          ...mockDashboardStats,
          active_connections: 4,
          unread_messages: 5
        }
      };

      webSocketService.onMessage.and.returnValue(of(statsUpdate));
      fixture.detectChanges();
      tick();

      expect(component.dashboardStats.active_connections).toBe(4);
    }));

    it('should handle WebSocket disconnection gracefully', fakeAsync(() => {
      const connectionStatus = new BehaviorSubject(false); // Disconnected
      webSocketService.onConnectionStatusChange.and.returnValue(connectionStatus.asObservable());

      fixture.detectChanges();
      tick();

      expect(component.isOffline).toBe(true);

      const offlineIndicator = fixture.debugElement.query(By.css('.offline-indicator'));
      expect(offlineIndicator).toBeTruthy();
    }));
  });

  describe('User Interactions', () => {
    beforeEach(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(mockDashboardStats));
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      revelationService.getRecentActivities.and.returnValue(of(mockRecentActivities));
    });

    it('should handle connection acceptance', fakeAsync(() => {
      soulConnectionService.acceptConnection.and.returnValue(of({ success: true }));
      fixture.detectChanges();
      tick();

      component.acceptConnection(mockActiveConnections[0]);

      expect(soulConnectionService.acceptConnection).toHaveBeenCalledWith(mockActiveConnections[0].id);
      expect(notificationService.showSuccess).toHaveBeenCalledWith(
        'Connection with Emma accepted! 🎉'
      );
    }));

    it('should handle connection decline', fakeAsync(() => {
      soulConnectionService.declineConnection.and.returnValue(of({ success: true }));
      fixture.detectChanges();
      tick();

      component.declineConnection(mockActiveConnections[0], 'Not feeling the connection');

      expect(soulConnectionService.declineConnection).toHaveBeenCalledWith(
        mockActiveConnections[0].id,
        'Not feeling the connection'
      );
    }));

    it('should refresh dashboard data on user request', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      soulConnectionService.getDashboardStats.calls.reset();
      
      component.refreshDashboard();

      expect(soulConnectionService.getDashboardStats).toHaveBeenCalled();
      expect(component.isRefreshing).toBe(true);
    }));

    it('should navigate to different sections from dashboard', () => {
      const routerSpy = spyOn(component['router'], 'navigate');

      component.navigateToDiscovery();
      expect(routerSpy).toHaveBeenCalledWith(['/discover']);

      component.navigateToMessages();
      expect(routerSpy).toHaveBeenCalledWith(['/messages']);

      component.navigateToProfile();
      expect(routerSpy).toHaveBeenCalledWith(['/profile']);
    }));

    it('should handle quick actions from dashboard', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const quickActionButtons = fixture.debugElement.queryAll(By.css('.quick-action'));
      expect(quickActionButtons.length).toBeGreaterThan(0);

      // Test quick message action
      const messageButton = fixture.debugElement.query(By.css('.quick-message'));
      if (messageButton) {
        messageButton.triggerEventHandler('click', {});
        expect(component.quickMessage).toHaveBeenCalled();
      }
    }));

    it('should show context menus for connections', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const menuTriggers = fixture.debugElement.queryAll(By.css('.connection-menu'));
      expect(menuTriggers.length).toBe(mockActiveConnections.length);

      const firstMenu = menuTriggers[0];
      firstMenu.triggerEventHandler('click', {});

      const menuItems = fixture.debugElement.queryAll(By.css('.menu-item'));
      expect(menuItems.length).toBeGreaterThan(0);
    }));
  });

  describe('Performance and Optimization', () => {
    it('should track connections by ID for ngFor performance', () => {
      expect(component.trackByConnectionId).toBeDefined();
      expect(component.trackByConnectionId(0, mockActiveConnections[0])).toBe(mockActiveConnections[0].id);
    });

    it('should track activities by ID for ngFor performance', () => {
      expect(component.trackByActivityId).toBeDefined();
      expect(component.trackByActivityId(0, mockRecentActivities[0])).toBe(mockRecentActivities[0].id);
    });

    it('should implement virtual scrolling for large activity lists', () => {
      const largeActivityList = Array.from({ length: 100 }, (_, i) => ({
        ...mockRecentActivities[0],
        id: i + 1
      }));

      revelationService.getRecentActivities.and.returnValue(of(largeActivityList));
      fixture.detectChanges();

      const virtualScroll = fixture.debugElement.query(By.css('cdk-virtual-scroll-viewport'));
      expect(virtualScroll).toBeTruthy();
    });

    it('should lazy load connection details', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      // Initially should not load detailed data
      expect(component.detailedConnectionData).toBeUndefined();

      // Only load when connection is expanded
      component.loadConnectionDetails(mockActiveConnections[0]);
      expect(component.detailedConnectionData).toBeDefined();
    }));

    it('should debounce search and filter operations', fakeAsync(() => {
      component.searchConnections('test query');
      component.searchConnections('test query updated');

      tick(300); // Debounce delay

      expect(component.filterConnections).toHaveBeenCalledTimes(1);
    }));
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(mockDashboardStats));
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      revelationService.getRecentActivities.and.returnValue(of(mockRecentActivities));
    });

    it('should have proper ARIA labels for statistics', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const statCards = fixture.debugElement.queryAll(By.css('.stat-card'));
      statCards.forEach(card => {
        expect(card.nativeElement.getAttribute('aria-label')).toBeTruthy();
      });
    }));

    it('should support keyboard navigation', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const firstConnection = fixture.debugElement.query(By.css('.connection-card'));
      
      // Test Enter key navigation
      firstConnection.triggerEventHandler('keydown.enter', {});
      expect(component.navigateToConnection).toHaveBeenCalledWith(mockActiveConnections[0]);

      // Test Space key activation
      firstConnection.triggerEventHandler('keydown.space', {});
      expect(component.selectConnection).toHaveBeenCalledWith(mockActiveConnections[0]);
    }));

    it('should announce updates to screen readers', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const liveRegion = fixture.debugElement.query(By.css('[aria-live="polite"]'));
      expect(liveRegion).toBeTruthy();

      component.announceUpdate('New message from Emma');
      fixture.detectChanges();

      expect(liveRegion.nativeElement.textContent).toContain('New message from Emma');
    }));

    it('should have high contrast mode support', () => {
      component.toggleHighContrast();
      fixture.detectChanges();

      const dashboardElement = fixture.debugElement.query(By.css('.dashboard'));
      expect(dashboardElement.nativeElement.classList).toContain('high-contrast');
    });

    it('should provide skip navigation links', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const skipLinks = fixture.debugElement.queryAll(By.css('.skip-link'));
      expect(skipLinks.length).toBeGreaterThan(0);
      expect(skipLinks[0].nativeElement.getAttribute('href')).toBe('#main-content');
    }));
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle partial data loading failures', fakeAsync(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(mockDashboardStats));
      soulConnectionService.getActiveConnections.and.returnValue(
        throwError({ error: { detail: 'Connections unavailable' } })
      );
      revelationService.getRecentActivities.and.returnValue(of(mockRecentActivities));

      fixture.detectChanges();
      tick();

      // Should still show available data
      expect(component.dashboardStats).toEqual(mockDashboardStats);
      expect(component.recentActivities).toEqual(mockRecentActivities);
      
      // Should show error for failed section
      expect(component.connectionLoadError).toBeTruthy();
    }));

    it('should handle empty or null data gracefully', fakeAsync(() => {
      soulConnectionService.getDashboardStats.and.returnValue(of(null));
      soulConnectionService.getActiveConnections.and.returnValue(of([]));
      revelationService.getRecentActivities.and.returnValue(of([]));

      fixture.detectChanges();
      tick();

      const emptyStates = fixture.debugElement.queryAll(By.css('.empty-state'));
      expect(emptyStates.length).toBeGreaterThan(0);
    }));

    it('should handle network connectivity issues', () => {
      const networkError = new Error('Network unavailable');
      networkError.name = 'NetworkError';

      soulConnectionService.getDashboardStats.and.returnValue(throwError(networkError));
      fixture.detectChanges();

      expect(component.isOffline).toBe(true);
      expect(component.showOfflineMessage()).toBe(true);
    }));

    it('should implement retry logic for failed requests', fakeAsync(() => {
      let callCount = 0;
      soulConnectionService.getDashboardStats.and.callFake(() => {
        callCount++;
        if (callCount <= 2) {
          return throwError({ error: { detail: 'Server error' } });
        }
        return of(mockDashboardStats);
      });

      fixture.detectChanges();
      tick();

      component.retryLoadData();
      tick();

      expect(callCount).toBe(3);
      expect(component.dashboardStats).toEqual(mockDashboardStats);
    }));

    it('should handle rapid user interactions', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      // Rapid clicking should be debounced
      for (let i = 0; i < 10; i++) {
        component.acceptConnection(mockActiveConnections[0]);
      }

      tick(500);

      expect(soulConnectionService.acceptConnection).toHaveBeenCalledTimes(1);
    }));
  });

  describe('Mobile Responsiveness', () => {
    it('should adapt layout for mobile screens', () => {
      spyOnProperty(window, 'innerWidth').and.returnValue(375);
      
      component.ngOnInit();
      fixture.detectChanges();

      expect(component.isMobile).toBe(true);

      const mobileLayout = fixture.debugElement.query(By.css('.mobile-dashboard'));
      expect(mobileLayout).toBeTruthy();
    });

    it('should use swipe gestures for navigation on mobile', () => {
      component.isMobile = true;
      fixture.detectChanges();

      const swipeContainer = fixture.debugElement.query(By.css('.swipe-container'));
      expect(swipeContainer).toBeTruthy();

      // Simulate swipe gesture
      component.onSwipeLeft();
      expect(component.currentTabIndex).toBe(1);
    });

    it('should optimize touch targets for mobile', () => {
      component.isMobile = true;
      fixture.detectChanges();

      const touchTargets = fixture.debugElement.queryAll(By.css('.touch-target'));
      touchTargets.forEach(target => {
        const styles = getComputedStyle(target.nativeElement);
        const minSize = parseInt(styles.minHeight) || parseInt(styles.height);
        expect(minSize).toBeGreaterThanOrEqual(44); // 44px minimum touch target
      });
    });
  });
});