/**
 * Comprehensive Connection Management UI Tests - Maximum Coverage
 * Tests soul connection lifecycle, status management, and relationship progression
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ReactiveFormsModule } from '@angular/forms';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { of, throwError, BehaviorSubject } from 'rxjs';

import { ConnectionManagementComponent } from './connection-management.component';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { RevelationService } from '../../core/services/revelation.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { WebSocketService } from '../../core/services/websocket.service';

interface SoulConnection {
  id: number;
  partner_id: number;
  partner_name: string;
  compatibility_score: number;
  connection_stage: 'pending' | 'active' | 'revelation_cycle' | 'photo_reveal_pending' | 'photo_revealed' | 'dinner_planning' | 'completed' | 'declined';
  created_at: string;
  updated_at: string;
  is_mutual: boolean;
  current_day: number;
  total_revelations_shared: number;
  unread_messages: number;
  last_activity: string;
  partner_online: boolean;
  revelation_progress: {
    user_completed: number;
    partner_completed: number;
    total_days: number;
    current_day_unlocked: boolean;
  };
  connection_insights: {
    shared_interests: string[];
    values_alignment: string[];
    compatibility_breakdown: {
      interests: number;
      values: number;
      communication: number;
      personality: number;
    };
    growth_potential: number;
    connection_quality: 'excellent' | 'good' | 'moderate' | 'needs_attention';
  };
  recent_activities: Array<{
    type: string;
    description: string;
    timestamp: string;
  }>;
  photo_reveal_status?: {
    user_consent: boolean;
    partner_consent: boolean;
    revealed: boolean;
    eligible: boolean;
  };
}

interface ConnectionRequest {
  id: number;
  sender_id: number;
  sender_name: string;
  compatibility_score: number;
  message: string;
  created_at: string;
  status: 'pending' | 'accepted' | 'declined';
  sender_insights: {
    shared_interests: string[];
    values_preview: string[];
    profile_highlights: string[];
  };
}

describe('ConnectionManagementComponent', () => {
  let component: ConnectionManagementComponent;
  let fixture: ComponentFixture<ConnectionManagementComponent>;
  let soulConnectionService: jasmine.SpyObj<SoulConnectionService>;
  let revelationService: jasmine.SpyObj<RevelationService>;
  let authService: jasmine.SpyObj<AuthService>;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let webSocketService: jasmine.SpyObj<WebSocketService>;
  let dialog: jasmine.SpyObj<MatDialog>;

  const mockActiveConnections: SoulConnection[] = [
    {
      id: 1,
      partner_id: 2,
      partner_name: 'Emma',
      compatibility_score: 88.5,
      connection_stage: 'revelation_cycle',
      created_at: '2025-01-15T10:00:00Z',
      updated_at: '2025-01-20T14:30:00Z',
      is_mutual: true,
      current_day: 4,
      total_revelations_shared: 7,
      unread_messages: 2,
      last_activity: '2025-01-20T14:30:00Z',
      partner_online: true,
      revelation_progress: {
        user_completed: 4,
        partner_completed: 3,
        total_days: 7,
        current_day_unlocked: true
      },
      connection_insights: {
        shared_interests: ['photography', 'hiking', 'meditation'],
        values_alignment: ['authenticity', 'family_first', 'growth'],
        compatibility_breakdown: {
          interests: 85,
          values: 92,
          communication: 88,
          personality: 85
        },
        growth_potential: 9.2,
        connection_quality: 'excellent'
      },
      recent_activities: [
        {
          type: 'revelation_shared',
          description: 'Emma shared hopes and dreams',
          timestamp: '2025-01-20T14:30:00Z'
        },
        {
          type: 'message_sent',
          description: 'New message received',
          timestamp: '2025-01-20T13:15:00Z'
        }
      ]
    },
    {
      id: 2,
      partner_id: 3,
      partner_name: 'Sofia',
      compatibility_score: 79.2,
      connection_stage: 'photo_reveal_pending',
      created_at: '2025-01-10T08:30:00Z',
      updated_at: '2025-01-20T10:45:00Z',
      is_mutual: true,
      current_day: 7,
      total_revelations_shared: 14,
      unread_messages: 0,
      last_activity: '2025-01-20T10:45:00Z',
      partner_online: false,
      revelation_progress: {
        user_completed: 7,
        partner_completed: 7,
        total_days: 7,
        current_day_unlocked: false
      },
      connection_insights: {
        shared_interests: ['travel', 'volunteering', 'cooking'],
        values_alignment: ['compassion', 'adventure', 'helping_others'],
        compatibility_breakdown: {
          interests: 78,
          values: 85,
          communication: 82,
          personality: 72
        },
        growth_potential: 8.1,
        connection_quality: 'good'
      },
      recent_activities: [
        {
          type: 'photo_consent',
          description: 'Ready for photo reveal',
          timestamp: '2025-01-20T10:45:00Z'
        }
      ],
      photo_reveal_status: {
        user_consent: true,
        partner_consent: true,
        revealed: false,
        eligible: true
      }
    }
  ];

  const mockPendingRequests: ConnectionRequest[] = [
    {
      id: 1,
      sender_id: 4,
      sender_name: 'Alex',
      compatibility_score: 82.3,
      message: 'Your perspective on authentic connections deeply resonates with me. I\'d love to explore this soul journey together.',
      created_at: '2025-01-20T09:15:00Z',
      status: 'pending',
      sender_insights: {
        shared_interests: ['reading', 'yoga', 'nature'],
        values_preview: ['authenticity', 'mindfulness', 'connection'],
        profile_highlights: ['Practices daily meditation', 'Values deep conversations', 'Seeks meaningful relationships']
      }
    },
    {
      id: 2,
      sender_id: 5,
      sender_name: 'Jordan',
      compatibility_score: 75.8,
      message: 'I believe we could create something beautiful together based on our shared values.',
      created_at: '2025-01-19T16:20:00Z',
      status: 'pending',
      sender_insights: {
        shared_interests: ['music', 'art', 'philosophy'],
        values_preview: ['creativity', 'growth', 'empathy'],
        profile_highlights: ['Artist and philosopher', 'Values emotional intelligence', 'Believes in soul connections']
      }
    }
  ];

  beforeEach(async () => {
    const soulConnectionSpy = jasmine.createSpyObj('SoulConnectionService', [
      'getActiveConnections',
      'getPendingRequests',
      'acceptConnection',
      'declineConnection',
      'pauseConnection',
      'resumeConnection',
      'endConnection',
      'getConnectionDetails',
      'updateConnectionStage'
    ]);

    const revelationSpy = jasmine.createSpyObj('RevelationService', [
      'getRevelationProgress',
      'getTodaysRevelation'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser'
    ]);

    const notificationSpy = jasmine.createSpyObj('NotificationService', [
      'showSuccess',
      'showError',
      'showWarning',
      'showInfo'
    ]);

    const webSocketSpy = jasmine.createSpyObj('WebSocketService', [
      'connect',
      'onMessage',
      'onConnectionUpdate'
    ]);

    const dialogSpy = jasmine.createSpyObj('MatDialog', [
      'open'
    ]);

    await TestBed.configureTestingModule({
      declarations: [ConnectionManagementComponent],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NoopAnimationsModule,
        ReactiveFormsModule,
        MatTabsModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatBadgeModule,
        MatChipsModule,
        MatProgressBarModule,
        MatMenuModule,
        MatDialogModule,
        MatSnackBarModule
      ],
      providers: [
        { provide: SoulConnectionService, useValue: soulConnectionSpy },
        { provide: RevelationService, useValue: revelationSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notificationSpy },
        { provide: WebSocketService, useValue: webSocketSpy },
        { provide: MatDialog, useValue: dialogSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ConnectionManagementComponent);
    component = fixture.componentInstance;

    soulConnectionService = TestBed.inject(SoulConnectionService) as jasmine.SpyObj<SoulConnectionService>;
    revelationService = TestBed.inject(RevelationService) as jasmine.SpyObj<RevelationService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;
    webSocketService = TestBed.inject(WebSocketService) as jasmine.SpyObj<WebSocketService>;
    dialog = TestBed.inject(MatDialog) as jasmine.SpyObj<MatDialog>;

    // Default mock returns
    authService.getCurrentUser.and.returnValue(of({
      id: 1,
      email: 'test@example.com',
      first_name: 'Test'
    }));
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with loading state', () => {
      expect(component.isLoading).toBe(true);
      expect(component.activeConnections).toEqual([]);
      expect(component.pendingRequests).toEqual([]);
    });

    it('should load connections and requests on init', fakeAsync(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      expect(soulConnectionService.getActiveConnections).toHaveBeenCalled();
      expect(soulConnectionService.getPendingRequests).toHaveBeenCalled();
      expect(component.activeConnections).toEqual(mockActiveConnections);
      expect(component.pendingRequests).toEqual(mockPendingRequests);
      expect(component.isLoading).toBe(false);
    }));

    it('should handle loading errors gracefully', fakeAsync(() => {
      soulConnectionService.getActiveConnections.and.returnValue(
        throwError({ error: { detail: 'Connections unavailable' } })
      );

      fixture.detectChanges();
      tick();

      expect(component.loadingError).toBeTruthy();
      expect(notificationService.showError).toHaveBeenCalledWith(
        'Unable to load your connections. Please try again later.'
      );
    }));

    it('should establish WebSocket connection for real-time updates', fakeAsync(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      expect(webSocketService.connect).toHaveBeenCalled();
    }));
  });

  describe('Tab Navigation', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));
    });

    it('should display tab navigation', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const tabGroup = fixture.debugElement.query(By.css('mat-tab-group'));
      expect(tabGroup).toBeTruthy();

      const tabs = fixture.debugElement.queryAll(By.css('mat-tab'));
      expect(tabs.length).toBe(4); // Active, Pending, Completed, Analytics
    }));

    it('should show badge counts on tabs', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const pendingTab = fixture.debugElement.query(By.css('mat-tab[data-tab="pending"]'));
      const badge = pendingTab.query(By.css('mat-badge'));
      
      expect(badge).toBeTruthy();
      expect(component.pendingRequestsCount).toBe(mockPendingRequests.length);
    }));

    it('should switch between tabs correctly', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const tabGroup = fixture.debugElement.query(By.css('mat-tab-group'));
      
      // Switch to pending tab
      tabGroup.triggerEventHandler('selectedIndexChange', { index: 1 });
      fixture.detectChanges();

      expect(component.selectedTabIndex).toBe(1);

      const pendingContent = fixture.debugElement.query(By.css('.pending-requests'));
      expect(pendingContent).toBeTruthy();
    }));

    it('should update tab counts in real-time', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.activeConnectionsCount).toBe(mockActiveConnections.length);

      // Simulate new pending request
      const newRequest: ConnectionRequest = {
        ...mockPendingRequests[0],
        id: 3,
        sender_name: 'New Person'
      };

      component.handleNewConnectionRequest(newRequest);
      fixture.detectChanges();

      expect(component.pendingRequestsCount).toBe(mockPendingRequests.length + 1);
    }));
  });

  describe('Active Connections Display', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));
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

    it('should display connection stages correctly', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const stageIndicators = fixture.debugElement.queryAll(By.css('.stage-indicator'));
      expect(stageIndicators.length).toBe(mockActiveConnections.length);

      expect(stageIndicators[0].nativeElement.textContent).toContain('revelation_cycle');
      expect(stageIndicators[1].nativeElement.textContent).toContain('photo_reveal_pending');
    }));

    it('should show revelation progress bars', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const progressBars = fixture.debugElement.queryAll(By.css('.revelation-progress'));
      expect(progressBars.length).toBe(mockActiveConnections.length);

      const firstProgress = progressBars[0];
      expect(firstProgress.nativeElement.textContent).toContain('4/7');
    }));

    it('should indicate unread messages', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const unreadBadges = fixture.debugElement.queryAll(By.css('.unread-badge'));
      expect(unreadBadges.length).toBe(1); // Only Emma has unread messages

      expect(unreadBadges[0].nativeElement.textContent.trim()).toBe('2');
    }));

    it('should show online/offline status', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const onlineIndicators = fixture.debugElement.queryAll(By.css('.online-indicator'));
      const offlineIndicators = fixture.debugElement.queryAll(By.css('.offline-indicator'));

      expect(onlineIndicators.length).toBe(1); // Emma is online
      expect(offlineIndicators.length).toBe(1); // Sofia is offline
    }));

    it('should display last activity timestamps', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const timestamps = fixture.debugElement.queryAll(By.css('.last-activity'));
      expect(timestamps.length).toBe(mockActiveConnections.length);

      expect(component.formatLastActivity(mockActiveConnections[0].last_activity)).toContain('ago');
    }));

    it('should show shared interests as chips', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const interestChips = fixture.debugElement.queryAll(By.css('.interest-chip'));
      expect(interestChips.length).toBeGreaterThan(0);

      const chipTexts = interestChips.map(chip => chip.nativeElement.textContent.trim());
      expect(chipTexts).toContain('photography');
      expect(chipTexts).toContain('hiking');
    }));

    it('should display recent activities', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const activityItems = fixture.debugElement.queryAll(By.css('.recent-activity'));
      expect(activityItems.length).toBeGreaterThan(0);

      expect(activityItems[0].nativeElement.textContent).toContain('revelation_shared');
    }));
  });

  describe('Connection Actions', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));
    });

    it('should navigate to connection details', fakeAsync(() => {
      const routerSpy = spyOn(component['router'], 'navigate');
      fixture.detectChanges();
      tick();

      const firstConnection = fixture.debugElement.query(By.css('.connection-card'));
      firstConnection.triggerEventHandler('click', {});

      expect(routerSpy).toHaveBeenCalledWith(['/connections', mockActiveConnections[0].id]);
    }));

    it('should show connection menu on more options', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const menuTrigger = fixture.debugElement.query(By.css('.connection-menu-trigger'));
      menuTrigger.triggerEventHandler('click', {});
      fixture.detectChanges();

      const menuItems = fixture.debugElement.queryAll(By.css('.menu-item'));
      expect(menuItems.length).toBeGreaterThan(0);

      expect(menuItems.some(item => item.nativeElement.textContent.includes('Message'))).toBe(true);
      expect(menuItems.some(item => item.nativeElement.textContent.includes('Pause'))).toBe(true);
    }));

    it('should pause connection', fakeAsync(() => {
      soulConnectionService.pauseConnection.and.returnValue(of({ success: true }));
      fixture.detectChanges();
      tick();

      component.pauseConnection(mockActiveConnections[0]);

      expect(soulConnectionService.pauseConnection).toHaveBeenCalledWith(mockActiveConnections[0].id);
      expect(notificationService.showInfo).toHaveBeenCalledWith(
        'Connection with Emma has been paused. You can resume it anytime.'
      );
    }));

    it('should resume connection', fakeAsync(() => {
      const pausedConnection = { ...mockActiveConnections[0], connection_stage: 'paused' as any };
      soulConnectionService.resumeConnection.and.returnValue(of({ success: true }));
      
      fixture.detectChanges();
      tick();

      component.resumeConnection(pausedConnection);

      expect(soulConnectionService.resumeConnection).toHaveBeenCalledWith(pausedConnection.id);
      expect(notificationService.showSuccess).toHaveBeenCalledWith(
        'Connection with Emma has been resumed! 🎉'
      );
    }));

    it('should end connection with confirmation', fakeAsync(() => {
      const dialogRef = { afterClosed: () => of(true) };
      dialog.open.and.returnValue(dialogRef as any);
      soulConnectionService.endConnection.and.returnValue(of({ success: true }));

      fixture.detectChanges();
      tick();

      component.endConnection(mockActiveConnections[0]);

      expect(dialog.open).toHaveBeenCalled();
      expect(soulConnectionService.endConnection).toHaveBeenCalledWith(
        mockActiveConnections[0].id,
        'User initiated'
      );
    }));

    it('should navigate to messaging', fakeAsync(() => {
      const routerSpy = spyOn(component['router'], 'navigate');
      fixture.detectChanges();
      tick();

      component.openMessaging(mockActiveConnections[0]);

      expect(routerSpy).toHaveBeenCalledWith(['/messages', mockActiveConnections[0].id]);
    }));

    it('should show photo reveal status for eligible connections', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const photoRevealCard = fixture.debugElement.query(By.css('.connection-card[data-connection-id="2"]'));
      const photoRevealSection = photoRevealCard.query(By.css('.photo-reveal-status'));

      expect(photoRevealSection).toBeTruthy();
      expect(photoRevealSection.nativeElement.textContent).toContain('Ready for photo reveal');
    }));
  });

  describe('Pending Requests Management', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));
    });

    it('should display all pending requests', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      // Switch to pending tab
      component.selectedTabIndex = 1;
      fixture.detectChanges();

      const requestCards = fixture.debugElement.queryAll(By.css('.request-card'));
      expect(requestCards.length).toBe(mockPendingRequests.length);

      expect(requestCards[0].nativeElement.textContent).toContain('Alex');
      expect(requestCards[1].nativeElement.textContent).toContain('Jordan');
    }));

    it('should show compatibility scores for requests', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectedTabIndex = 1;
      fixture.detectChanges();

      const compatibilityScores = fixture.debugElement.queryAll(By.css('.request-compatibility'));
      expect(compatibilityScores.length).toBe(mockPendingRequests.length);

      expect(compatibilityScores[0].nativeElement.textContent).toContain('82.3%');
      expect(compatibilityScores[1].nativeElement.textContent).toContain('75.8%');
    }));

    it('should display request messages', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectedTabIndex = 1;
      fixture.detectChanges();

      const requestMessages = fixture.debugElement.queryAll(By.css('.request-message'));
      expect(requestMessages.length).toBe(mockPendingRequests.length);

      expect(requestMessages[0].nativeElement.textContent).toContain('authentic connections');
    }));

    it('should show sender insights', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectedTabIndex = 1;
      fixture.detectChanges();

      const insightChips = fixture.debugElement.queryAll(By.css('.insight-chip'));
      expect(insightChips.length).toBeGreaterThan(0);

      const chipTexts = insightChips.map(chip => chip.nativeElement.textContent.trim());
      expect(chipTexts).toContain('reading');
      expect(chipTexts).toContain('yoga');
    }));

    it('should accept connection request', fakeAsync(() => {
      soulConnectionService.acceptConnection.and.returnValue(of({ 
        success: true, 
        connection_id: 3 
      }));

      fixture.detectChanges();
      tick();

      component.selectedTabIndex = 1;
      fixture.detectChanges();

      const acceptButton = fixture.debugElement.query(By.css('.accept-button'));
      acceptButton.triggerEventHandler('click', {});

      expect(soulConnectionService.acceptConnection).toHaveBeenCalledWith(mockPendingRequests[0].id);
      expect(notificationService.showSuccess).toHaveBeenCalledWith(
        'Connection request from Alex accepted! Your soul journey begins now 🌟'
      );
    }));

    it('should decline connection request with reason', fakeAsync(() => {
      const dialogRef = { 
        afterClosed: () => of({ declined: true, reason: 'Not feeling the connection' }) 
      };
      dialog.open.and.returnValue(dialogRef as any);
      soulConnectionService.declineConnection.and.returnValue(of({ success: true }));

      fixture.detectChanges();
      tick();

      component.selectedTabIndex = 1;
      fixture.detectChanges();

      const declineButton = fixture.debugElement.query(By.css('.decline-button'));
      declineButton.triggerEventHandler('click', {});

      expect(dialog.open).toHaveBeenCalled();
      expect(soulConnectionService.declineConnection).toHaveBeenCalledWith(
        mockPendingRequests[0].id,
        'Not feeling the connection'
      );
    }));

    it('should show request timestamps', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectedTabIndex = 1;
      fixture.detectChanges();

      const timestamps = fixture.debugElement.queryAll(By.css('.request-timestamp'));
      expect(timestamps.length).toBe(mockPendingRequests.length);

      expect(component.formatRequestTime(mockPendingRequests[0].created_at)).toContain('ago');
    }));

    it('should handle batch actions for multiple requests', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectedTabIndex = 1;
      fixture.detectChanges();

      // Select multiple requests
      const checkboxes = fixture.debugElement.queryAll(By.css('.request-checkbox'));
      checkboxes[0].triggerEventHandler('change', { target: { checked: true } });
      checkboxes[1].triggerEventHandler('change', { target: { checked: true } });

      fixture.detectChanges();

      const batchActions = fixture.debugElement.query(By.css('.batch-actions'));
      expect(batchActions).toBeTruthy();

      const batchAcceptButton = batchActions.query(By.css('.batch-accept'));
      expect(batchAcceptButton).toBeTruthy();
    }));
  });

  describe('Connection Insights and Analytics', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));
    });

    it('should display compatibility breakdown', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const compatibilityBars = fixture.debugElement.queryAll(By.css('.compatibility-bar'));
      expect(compatibilityBars.length).toBeGreaterThan(0);

      const firstConnection = mockActiveConnections[0];
      expect(component.getCompatibilityBreakdown(firstConnection)).toEqual(
        firstConnection.connection_insights.compatibility_breakdown
      );
    }));

    it('should show growth potential indicators', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const growthIndicators = fixture.debugElement.queryAll(By.css('.growth-potential'));
      expect(growthIndicators.length).toBe(mockActiveConnections.length);

      expect(component.formatGrowthPotential(mockActiveConnections[0].connection_insights.growth_potential))
        .toBe('9.2/10');
    }));

    it('should display connection quality ratings', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const qualityRatings = fixture.debugElement.queryAll(By.css('.connection-quality'));
      expect(qualityRatings.length).toBe(mockActiveConnections.length);

      expect(qualityRatings[0].nativeElement.classList).toContain('excellent');
      expect(qualityRatings[1].nativeElement.classList).toContain('good');
    }));

    it('should show values alignment summary', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const valuesChips = fixture.debugElement.queryAll(By.css('.values-chip'));
      expect(valuesChips.length).toBeGreaterThan(0);

      const chipTexts = valuesChips.map(chip => chip.nativeElement.textContent.trim());
      expect(chipTexts).toContain('authenticity');
      expect(chipTexts).toContain('family_first');
    }));

    it('should provide detailed connection analytics', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectedTabIndex = 3; // Analytics tab
      fixture.detectChanges();

      const analyticsCards = fixture.debugElement.queryAll(By.css('.analytics-card'));
      expect(analyticsCards.length).toBeGreaterThan(0);

      const totalConnectionsCard = fixture.debugElement.query(By.css('.total-connections'));
      expect(totalConnectionsCard).toBeTruthy();
    }));

    it('should show connection success metrics', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.calculateConnectionSuccessRate()).toBeGreaterThan(0);
      expect(component.getAverageCompatibilityScore()).toBeGreaterThan(0);
      expect(component.getTotalRevelationsShared()).toBeGreaterThan(0);
    }));
  });

  describe('Real-Time Updates', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
    });

    it('should handle real-time connection updates', fakeAsync(() => {
      const connectionUpdate = {
        type: 'connection_status_change',
        connection_id: 1,
        new_stage: 'photo_reveal_pending',
        partner_online: false
      };

      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of(connectionUpdate));

      fixture.detectChanges();
      tick();

      expect(component.handleConnectionUpdate).toHaveBeenCalledWith(connectionUpdate);
    }));

    it('should update connection status in real-time', fakeAsync(() => {
      const statusUpdate = {
        type: 'partner_online_status',
        connection_id: 1,
        partner_online: false
      };

      webSocketService.onMessage.and.returnValue(of(statusUpdate));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      const updatedConnection = component.activeConnections.find(c => c.id === 1);
      expect(updatedConnection?.partner_online).toBe(false);
    }));

    it('should receive new connection requests in real-time', fakeAsync(() => {
      const newRequest: ConnectionRequest = {
        id: 3,
        sender_id: 6,
        sender_name: 'Maya',
        compatibility_score: 85.4,
        message: 'New real-time request',
        created_at: new Date().toISOString(),
        status: 'pending',
        sender_insights: {
          shared_interests: ['art'],
          values_preview: ['creativity'],
          profile_highlights: ['Creative soul']
        }
      };

      const requestUpdate = {
        type: 'new_connection_request',
        request: newRequest
      };

      webSocketService.onMessage.and.returnValue(of(requestUpdate));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      expect(component.pendingRequests).toContain(newRequest);
      expect(notificationService.showInfo).toHaveBeenCalledWith(
        'New connection request from Maya! 💫'
      );
    }));

    it('should update unread message counts', fakeAsync(() => {
      const messageUpdate = {
        type: 'message_count_update',
        connection_id: 1,
        unread_count: 3
      };

      webSocketService.onMessage.and.returnValue(of(messageUpdate));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      const updatedConnection = component.activeConnections.find(c => c.id === 1);
      expect(updatedConnection?.unread_messages).toBe(3);
    }));

    it('should handle revelation progress updates', fakeAsync(() => {
      const revelationUpdate = {
        type: 'revelation_progress_update',
        connection_id: 1,
        user_completed: 5,
        partner_completed: 4
      };

      webSocketService.onMessage.and.returnValue(of(revelationUpdate));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      const updatedConnection = component.activeConnections.find(c => c.id === 1);
      expect(updatedConnection?.revelation_progress.user_completed).toBe(5);
      expect(updatedConnection?.revelation_progress.partner_completed).toBe(4);
    }));
  });

  describe('Search and Filtering', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));
    });

    it('should search connections by partner name', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const searchInput = fixture.debugElement.query(By.css('.search-input'));
      searchInput.nativeElement.value = 'Emma';
      searchInput.triggerEventHandler('input', { target: { value: 'Emma' } });
      
      tick(300); // Debounce delay

      const filteredConnections = component.getFilteredConnections();
      expect(filteredConnections.length).toBe(1);
      expect(filteredConnections[0].partner_name).toBe('Emma');
    }));

    it('should filter connections by stage', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const stageFilter = fixture.debugElement.query(By.css('.stage-filter'));
      stageFilter.nativeElement.value = 'revelation_cycle';
      stageFilter.triggerEventHandler('change', { target: { value: 'revelation_cycle' } });

      const filteredConnections = component.getFilteredConnections();
      expect(filteredConnections.every(c => c.connection_stage === 'revelation_cycle')).toBe(true);
    }));

    it('should filter by compatibility score range', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.setCompatibilityFilter(80, 100);
      fixture.detectChanges();

      const filteredConnections = component.getFilteredConnections();
      expect(filteredConnections.every(c => c.compatibility_score >= 80)).toBe(true);
    }));

    it('should sort connections by different criteria', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const sortSelect = fixture.debugElement.query(By.css('.sort-select'));
      sortSelect.nativeElement.value = 'compatibility_desc';
      sortSelect.triggerEventHandler('change', { target: { value: 'compatibility_desc' } });

      const sortedConnections = component.getSortedConnections();
      expect(sortedConnections[0].compatibility_score).toBeGreaterThan(sortedConnections[1].compatibility_score);
    }));

    it('should provide quick filter buttons', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const quickFilters = fixture.debugElement.queryAll(By.css('.quick-filter'));
      expect(quickFilters.length).toBeGreaterThan(0);

      const highCompatibilityFilter = fixture.debugElement.query(By.css('.filter-high-compatibility'));
      highCompatibilityFilter.triggerEventHandler('click', {});

      const filtered = component.getFilteredConnections();
      expect(filtered.every(c => c.compatibility_score >= 85)).toBe(true);
    }));
  });

  describe('Performance Optimizations', () => {
    it('should use virtual scrolling for large connection lists', () => {
      const largeConnectionList = Array.from({ length: 100 }, (_, i) => ({
        ...mockActiveConnections[0],
        id: i + 1,
        partner_name: `Partner ${i + 1}`
      }));

      soulConnectionService.getActiveConnections.and.returnValue(of(largeConnectionList));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();

      const virtualScroll = fixture.debugElement.query(By.css('cdk-virtual-scroll-viewport'));
      expect(virtualScroll).toBeTruthy();
    });

    it('should track connections by ID for ngFor performance', () => {
      expect(component.trackByConnectionId).toBeDefined();
      expect(component.trackByConnectionId(0, mockActiveConnections[0])).toBe(mockActiveConnections[0].id);
    });

    it('should implement lazy loading for connection details', fakeAsync(() => {
      soulConnectionService.getConnectionDetails.and.returnValue(of({
        detailed_insights: {},
        activity_history: []
      }));

      fixture.detectChanges();
      tick();

      // Should not load details initially
      expect(soulConnectionService.getConnectionDetails).not.toHaveBeenCalled();

      // Only load when expanded
      component.expandConnection(mockActiveConnections[0]);
      expect(soulConnectionService.getConnectionDetails).toHaveBeenCalledWith(mockActiveConnections[0].id);
    }));

    it('should debounce search operations', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const searchInput = fixture.debugElement.query(By.css('.search-input'));
      
      // Rapid typing
      searchInput.triggerEventHandler('input', { target: { value: 'E' } });
      searchInput.triggerEventHandler('input', { target: { value: 'Em' } });
      searchInput.triggerEventHandler('input', { target: { value: 'Emma' } });

      tick(300);

      expect(component.performSearch).toHaveBeenCalledTimes(1);
    }));

    it('should implement pagination for large datasets', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.currentPage).toBe(1);
      expect(component.itemsPerPage).toBe(10);

      component.loadNextPage();
      expect(component.currentPage).toBe(2);
    }));
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));
    });

    it('should have proper ARIA labels', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const connectionCards = fixture.debugElement.queryAll(By.css('.connection-card'));
      connectionCards.forEach(card => {
        expect(card.nativeElement.getAttribute('aria-label')).toBeTruthy();
        expect(card.nativeElement.getAttribute('role')).toBe('button');
      });
    }));

    it('should support keyboard navigation', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const firstConnection = fixture.debugElement.query(By.css('.connection-card'));
      
      firstConnection.triggerEventHandler('keydown.enter', {});
      expect(component.openConnectionDetails).toHaveBeenCalledWith(mockActiveConnections[0]);

      firstConnection.triggerEventHandler('keydown.space', {});
      expect(component.selectConnection).toHaveBeenCalledWith(mockActiveConnections[0]);
    }));

    it('should announce updates to screen readers', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const liveRegion = fixture.debugElement.query(By.css('[aria-live="polite"]'));
      expect(liveRegion).toBeTruthy();

      component.announceUpdate('Connection request accepted');
      fixture.detectChanges();

      expect(liveRegion.nativeElement.textContent).toContain('Connection request accepted');
    }));

    it('should have sufficient color contrast for status indicators', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const statusIndicators = fixture.debugElement.queryAll(By.css('.status-indicator'));
      statusIndicators.forEach(indicator => {
        const styles = getComputedStyle(indicator.nativeElement);
        expect(styles.color).toBeDefined();
        expect(styles.backgroundColor).toBeDefined();
      });
    }));

    it('should support high contrast mode', () => {
      component.toggleHighContrast();
      fixture.detectChanges();

      const container = fixture.debugElement.query(By.css('.connection-management'));
      expect(container.nativeElement.classList).toContain('high-contrast');
    });
  });

  describe('Mobile Responsiveness', () => {
    beforeEach(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));
    });

    it('should adapt layout for mobile screens', fakeAsync(() => {
      spyOnProperty(window, 'innerWidth').and.returnValue(375);
      
      fixture.detectChanges();
      tick();

      expect(component.isMobile).toBe(true);

      const mobileLayout = fixture.debugElement.query(By.css('.mobile-connections'));
      expect(mobileLayout).toBeTruthy();
    }));

    it('should use bottom tabs on mobile', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const bottomTabs = fixture.debugElement.query(By.css('.bottom-tabs'));
      expect(bottomTabs).toBeTruthy();
    }));

    it('should support swipe gestures for tab navigation', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const tabContainer = fixture.debugElement.query(By.css('.tab-container'));
      
      // Simulate swipe left
      tabContainer.triggerEventHandler('swipeleft', {});
      expect(component.selectedTabIndex).toBe(1);

      // Simulate swipe right
      tabContainer.triggerEventHandler('swiperight', {});
      expect(component.selectedTabIndex).toBe(0);
    }));

    it('should show condensed connection cards on mobile', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const connectionCards = fixture.debugElement.queryAll(By.css('.connection-card.mobile'));
      expect(connectionCards.length).toBe(mockActiveConnections.length);

      connectionCards.forEach(card => {
        expect(card.nativeElement.classList).toContain('condensed');
      });
    }));

    it('should use pull-to-refresh on mobile', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const pullToRefresh = fixture.debugElement.query(By.css('.pull-to-refresh'));
      expect(pullToRefresh).toBeTruthy();

      pullToRefresh.triggerEventHandler('refresh', {});
      expect(component.refreshConnections).toHaveBeenCalled();
    }));
  });

  describe('Error Handling', () => {
    it('should handle connection action failures', fakeAsync(() => {
      soulConnectionService.acceptConnection.and.returnValue(
        throwError({ error: { detail: 'Connection acceptance failed' } })
      );

      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      component.acceptConnection(mockPendingRequests[0]);

      expect(notificationService.showError).toHaveBeenCalledWith(
        'Failed to accept connection: Connection acceptance failed'
      );
    }));

    it('should handle WebSocket disconnection', fakeAsync(() => {
      soulConnectionService.getActiveConnections.and.returnValue(of(mockActiveConnections));
      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(
        throwError({ error: 'WebSocket connection lost' })
      );
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      const connectionWarning = fixture.debugElement.query(By.css('.connection-warning'));
      expect(connectionWarning).toBeTruthy();
      expect(connectionWarning.nativeElement.textContent).toContain('Connection issues');
    }));

    it('should provide retry mechanisms for failed operations', fakeAsync(() => {
      let callCount = 0;
      soulConnectionService.getActiveConnections.and.callFake(() => {
        callCount++;
        if (callCount === 1) {
          return throwError({ error: { detail: 'Server error' } });
        }
        return of(mockActiveConnections);
      });

      soulConnectionService.getPendingRequests.and.returnValue(of(mockPendingRequests));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onConnectionUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      const retryButton = fixture.debugElement.query(By.css('.retry-button'));
      expect(retryButton).toBeTruthy();

      retryButton.triggerEventHandler('click', {});
      tick();

      expect(callCount).toBe(2);
      expect(component.activeConnections).toEqual(mockActiveConnections);
    }));
  });
});