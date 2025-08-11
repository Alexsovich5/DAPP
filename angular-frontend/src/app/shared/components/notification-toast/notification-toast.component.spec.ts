/**
 * Comprehensive Real-Time Notifications Tests - Maximum Coverage
 * Tests notification system, toast displays, and real-time event handling
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';
import { OverlayModule } from '@angular/cdk/overlay';
import { of, Subject, BehaviorSubject } from 'rxjs';

import { NotificationToastComponent } from './notification-toast.component';
import { NotificationService } from '../../../core/services/notification.service';
import { WebSocketService } from '../../../core/services/websocket.service';
import { AuthService } from '../../../core/services/auth.service';

interface RealtimeNotification {
  id: string;
  type: 'revelation_shared' | 'connection_request' | 'photo_reveal_ready' | 'message_received' | 'profile_view' | 'connection_accepted' | 'system_update';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: 'soul_connection' | 'messaging' | 'system' | 'social';
  timestamp: string;
  from_user?: {
    user_id: number;
    user_name: string;
    avatar_url?: string;
  };
  action_data?: {
    connection_id?: number;
    message_id?: number;
    revelation_day?: number;
    action_url?: string;
    requires_response?: boolean;
  };
  expires_at?: string;
  is_read: boolean;
  auto_dismiss?: boolean;
  dismiss_timeout?: number;
}

interface NotificationSettings {
  enableSounds: boolean;
  enableDesktopNotifications: boolean;
  enableInAppNotifications: boolean;
  quietHours: {
    enabled: boolean;
    start: string;
    end: string;
  };
  categorySettings: {
    [key: string]: {
      enabled: boolean;
      priority: 'low' | 'medium' | 'high';
      sound: boolean;
    };
  };
  maxVisibleNotifications: number;
  autoCloseDelay: number;
}

describe('NotificationToastComponent', () => {
  let component: NotificationToastComponent;
  let fixture: ComponentFixture<NotificationToastComponent>;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let webSocketService: jasmine.SpyObj<WebSocketService>;
  let authService: jasmine.SpyObj<AuthService>;
  let snackBar: jasmine.SpyObj<MatSnackBar>;
  let notificationSubject: Subject<RealtimeNotification>;

  const mockNotifications: RealtimeNotification[] = [
    {
      id: 'notif-1',
      type: 'revelation_shared',
      title: 'New Revelation Shared',
      message: 'Emma shared their hopes and dreams with you',
      priority: 'high',
      category: 'soul_connection',
      timestamp: new Date().toISOString(),
      from_user: {
        user_id: 2,
        user_name: 'Emma',
        avatar_url: 'https://example.com/avatar2.jpg'
      },
      action_data: {
        connection_id: 1,
        revelation_day: 4,
        action_url: '/connections/1/revelations'
      },
      is_read: false,
      auto_dismiss: false
    },
    {
      id: 'notif-2',
      type: 'connection_request',
      title: 'New Soul Connection Request',
      message: 'Alex wants to start a soul connection journey with you',
      priority: 'high',
      category: 'soul_connection',
      timestamp: new Date().toISOString(),
      from_user: {
        user_id: 3,
        user_name: 'Alex',
        avatar_url: 'https://example.com/avatar3.jpg'
      },
      action_data: {
        connection_id: 2,
        action_url: '/connections/requests',
        requires_response: true
      },
      is_read: false,
      auto_dismiss: false
    },
    {
      id: 'notif-3',
      type: 'message_received',
      title: 'New Message',
      message: 'Sofia sent you a message',
      priority: 'medium',
      category: 'messaging',
      timestamp: new Date().toISOString(),
      from_user: {
        user_id: 4,
        user_name: 'Sofia'
      },
      action_data: {
        connection_id: 3,
        message_id: 123,
        action_url: '/messages/3'
      },
      is_read: false,
      auto_dismiss: true,
      dismiss_timeout: 5000
    },
    {
      id: 'notif-4',
      type: 'photo_reveal_ready',
      title: 'Photo Reveal Ready! 📸',
      message: 'Both you and Emma are ready for photo reveal',
      priority: 'urgent',
      category: 'soul_connection',
      timestamp: new Date().toISOString(),
      action_data: {
        connection_id: 1,
        action_url: '/connections/1/photo-reveal'
      },
      is_read: false,
      auto_dismiss: false
    }
  ];

  const mockSettings: NotificationSettings = {
    enableSounds: true,
    enableDesktopNotifications: true,
    enableInAppNotifications: true,
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00'
    },
    categorySettings: {
      soul_connection: {
        enabled: true,
        priority: 'high',
        sound: true
      },
      messaging: {
        enabled: true,
        priority: 'medium',
        sound: true
      },
      system: {
        enabled: true,
        priority: 'low',
        sound: false
      }
    },
    maxVisibleNotifications: 5,
    autoCloseDelay: 8000
  };

  beforeEach(async () => {
    notificationSubject = new Subject<RealtimeNotification>();

    const notificationSpy = jasmine.createSpyObj('NotificationService', [
      'getNotificationSettings',
      'updateNotificationSettings',
      'markAsRead',
      'dismissNotification',
      'getUnreadCount',
      'playNotificationSound',
      'requestDesktopPermission',
      'showDesktopNotification'
    ]);

    const webSocketSpy = jasmine.createSpyObj('WebSocketService', [
      'onMessage',
      'connect',
      'isConnected'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser'
    ]);

    const snackBarSpy = jasmine.createSpyObj('MatSnackBar', [
      'openFromComponent',
      'dismiss',
      'dismissWithAction'
    ]);

    await TestBed.configureTestingModule({
      declarations: [NotificationToastComponent],
      imports: [
        BrowserAnimationsModule,
        MatSnackBarModule,
        MatIconModule,
        MatButtonModule,
        MatBadgeModule,
        OverlayModule
      ],
      providers: [
        { provide: NotificationService, useValue: notificationSpy },
        { provide: WebSocketService, useValue: webSocketSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: MatSnackBar, useValue: snackBarSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(NotificationToastComponent);
    component = fixture.componentInstance;

    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;
    webSocketService = TestBed.inject(WebSocketService) as jasmine.SpyObj<WebSocketService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    snackBar = TestBed.inject(MatSnackBar) as jasmine.SpyObj<MatSnackBar>;

    // Default mocks
    authService.getCurrentUser.and.returnValue(of({
      id: 1,
      email: 'test@example.com',
      first_name: 'Test'
    }));

    notificationService.getNotificationSettings.and.returnValue(of(mockSettings));
    webSocketService.onMessage.and.returnValue(notificationSubject.asObservable());
    webSocketService.isConnected.and.returnValue(true);
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with notification settings', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(notificationService.getNotificationSettings).toHaveBeenCalled();
      expect(component.settings).toEqual(mockSettings);
    }));

    it('should subscribe to real-time notifications', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(webSocketService.onMessage).toHaveBeenCalled();
      expect(component.activeNotifications).toEqual([]);
    }));

    it('should request desktop notification permission if enabled', fakeAsync(() => {
      mockSettings.enableDesktopNotifications = true;
      fixture.detectChanges();
      tick();

      expect(notificationService.requestDesktopPermission).toHaveBeenCalled();
    }));

    it('should initialize notification queue', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.notificationQueue).toEqual([]);
      expect(component.maxVisibleNotifications).toBe(mockSettings.maxVisibleNotifications);
    }));
  });

  describe('Receiving Real-Time Notifications', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should receive and display revelation notifications', fakeAsync(() => {
      const revelationNotification = mockNotifications[0];
      notificationSubject.next(revelationNotification);
      tick();

      expect(component.activeNotifications).toContain(revelationNotification);
      expect(snackBar.openFromComponent).toHaveBeenCalled();
    }));

    it('should receive connection request notifications', fakeAsync(() => {
      const connectionRequest = mockNotifications[1];
      notificationSubject.next(connectionRequest);
      tick();

      expect(component.activeNotifications).toContain(connectionRequest);
      expect(component.getNotificationIcon(connectionRequest.type)).toBe('connect_without_contact');
    }));

    it('should receive photo reveal notifications', fakeAsync(() => {
      const photoRevealNotification = mockNotifications[3];
      notificationSubject.next(photoRevealNotification);
      tick();

      expect(component.activeNotifications).toContain(photoRevealNotification);
      expect(component.getNotificationPriority(photoRevealNotification)).toBe('urgent');
    }));

    it('should filter notifications based on settings', fakeAsync(() => {
      // Disable messaging notifications
      mockSettings.categorySettings.messaging.enabled = false;
      component.settings = mockSettings;

      const messagingNotification = mockNotifications[2];
      notificationSubject.next(messagingNotification);
      tick();

      expect(component.activeNotifications).not.toContain(messagingNotification);
    }));

    it('should respect quiet hours', fakeAsync(() => {
      mockSettings.quietHours.enabled = true;
      mockSettings.quietHours.start = '22:00';
      mockSettings.quietHours.end = '08:00';
      
      // Mock current time as midnight (within quiet hours)
      spyOn(Date.prototype, 'getHours').and.returnValue(0);
      component.settings = mockSettings;

      const notification = mockNotifications[0];
      notificationSubject.next(notification);
      tick();

      expect(component.isInQuietHours()).toBe(true);
      expect(component.activeNotifications).not.toContain(notification);
    }));

    it('should handle high priority notifications during quiet hours', fakeAsync(() => {
      mockSettings.quietHours.enabled = true;
      spyOn(Date.prototype, 'getHours').and.returnValue(0);
      component.settings = mockSettings;

      const urgentNotification = mockNotifications[3]; // Photo reveal (urgent)
      notificationSubject.next(urgentNotification);
      tick();

      // Urgent notifications should bypass quiet hours
      expect(component.activeNotifications).toContain(urgentNotification);
    }));

    it('should queue notifications when max visible limit is reached', fakeAsync(() => {
      component.settings.maxVisibleNotifications = 2;

      // Add 3 notifications
      mockNotifications.slice(0, 3).forEach(notification => {
        notificationSubject.next(notification);
        tick(10);
      });

      expect(component.activeNotifications.length).toBe(2);
      expect(component.notificationQueue.length).toBe(1);
    }));
  });

  describe('Notification Display and UI', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should display notification with correct styling based on priority', fakeAsync(() => {
      const urgentNotification = mockNotifications[3];
      component.showNotification(urgentNotification);
      tick();

      const notificationElement = fixture.debugElement.query(By.css('.notification-urgent'));
      expect(notificationElement).toBeTruthy();
      expect(notificationElement.nativeElement.classList).toContain('priority-urgent');
    }));

    it('should show user avatar in notifications', fakeAsync(() => {
      const notificationWithAvatar = mockNotifications[0];
      component.showNotification(notificationWithAvatar);
      tick();
      fixture.detectChanges();

      const avatar = fixture.debugElement.query(By.css('.notification-avatar'));
      expect(avatar).toBeTruthy();
      expect(avatar.nativeElement.src).toBe(notificationWithAvatar.from_user!.avatar_url);
    }));

    it('should display notification title and message', fakeAsync(() => {
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const title = fixture.debugElement.query(By.css('.notification-title'));
      const message = fixture.debugElement.query(By.css('.notification-message'));

      expect(title.nativeElement.textContent).toContain(notification.title);
      expect(message.nativeElement.textContent).toContain(notification.message);
    }));

    it('should show timestamp with relative formatting', fakeAsync(() => {
      const notification = {
        ...mockNotifications[0],
        timestamp: new Date(Date.now() - 120000).toISOString() // 2 minutes ago
      };

      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const timestamp = fixture.debugElement.query(By.css('.notification-timestamp'));
      expect(timestamp.nativeElement.textContent).toContain('2 minutes ago');
    }));

    it('should display appropriate icons for different notification types', fakeAsync(() => {
      const typeIconTests = [
        { type: 'revelation_shared', expectedIcon: 'favorite' },
        { type: 'connection_request', expectedIcon: 'connect_without_contact' },
        { type: 'message_received', expectedIcon: 'message' },
        { type: 'photo_reveal_ready', expectedIcon: 'photo_camera' }
      ];

      typeIconTests.forEach(test => {
        expect(component.getNotificationIcon(test.type as any)).toBe(test.expectedIcon);
      });
    }));

    it('should show action buttons for notifications that require response', fakeAsync(() => {
      const actionableNotification = mockNotifications[1]; // Connection request
      component.showNotification(actionableNotification);
      tick();
      fixture.detectChanges();

      const actionButtons = fixture.debugElement.queryAll(By.css('.notification-action'));
      expect(actionButtons.length).toBeGreaterThan(0);
      
      const viewButton = fixture.debugElement.query(By.css('.action-view'));
      expect(viewButton).toBeTruthy();
    }));

    it('should show dismiss button for all notifications', fakeAsync(() => {
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const dismissButton = fixture.debugElement.query(By.css('.dismiss-button'));
      expect(dismissButton).toBeTruthy();
    }));

    it('should display progress bar for auto-dismiss notifications', fakeAsync(() => {
      const autoDismissNotification = mockNotifications[2];
      component.showNotification(autoDismissNotification);
      tick();
      fixture.detectChanges();

      const progressBar = fixture.debugElement.query(By.css('.auto-dismiss-progress'));
      expect(progressBar).toBeTruthy();
    }));
  });

  describe('Notification Interactions', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should handle notification click to navigate', fakeAsync(() => {
      const notification = mockNotifications[0];
      spyOn(component, 'navigateToAction');
      
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const notificationElement = fixture.debugElement.query(By.css('.notification-container'));
      notificationElement.triggerEventHandler('click', {});

      expect(component.navigateToAction).toHaveBeenCalledWith(notification);
    }));

    it('should dismiss notification on dismiss button click', fakeAsync(() => {
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const dismissButton = fixture.debugElement.query(By.css('.dismiss-button'));
      dismissButton.triggerEventHandler('click', {});

      expect(component.activeNotifications).not.toContain(notification);
      expect(notificationService.dismissNotification).toHaveBeenCalledWith(notification.id);
    }));

    it('should mark notification as read on view', fakeAsync(() => {
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();

      component.markAsRead(notification);

      expect(notificationService.markAsRead).toHaveBeenCalledWith(notification.id);
      expect(notification.is_read).toBe(true);
    }));

    it('should handle swipe gestures for dismissal on mobile', fakeAsync(() => {
      component.isMobile = true;
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const notificationElement = fixture.debugElement.query(By.css('.notification-container'));
      
      // Simulate swipe left gesture
      notificationElement.triggerEventHandler('swipeleft', {});

      expect(component.dismissNotification).toHaveBeenCalledWith(notification);
    }));

    it('should handle notification action button clicks', fakeAsync(() => {
      const actionableNotification = mockNotifications[1];
      spyOn(component, 'handleActionClick');
      
      component.showNotification(actionableNotification);
      tick();
      fixture.detectChanges();

      const actionButton = fixture.debugElement.query(By.css('.action-view'));
      actionButton.triggerEventHandler('click', { stopPropagation: () => {} });

      expect(component.handleActionClick).toHaveBeenCalledWith(actionableNotification, 'view');
    }));

    it('should prevent notification click when action button is clicked', fakeAsync(() => {
      const notification = mockNotifications[1];
      spyOn(component, 'navigateToAction');
      
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const actionButton = fixture.debugElement.query(By.css('.action-view'));
      const clickEvent = { stopPropagation: jasmine.createSpy('stopPropagation') };
      actionButton.triggerEventHandler('click', clickEvent);

      expect(clickEvent.stopPropagation).toHaveBeenCalled();
      expect(component.navigateToAction).not.toHaveBeenCalled();
    }));
  });

  describe('Auto-Dismiss and Timeouts', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should auto-dismiss notifications with timeout', fakeAsync(() => {
      const autoDismissNotification = mockNotifications[2];
      component.showNotification(autoDismissNotification);
      tick();

      // Fast-forward to timeout
      tick(autoDismissNotification.dismiss_timeout!);

      expect(component.activeNotifications).not.toContain(autoDismissNotification);
    }));

    it('should show countdown for auto-dismiss notifications', fakeAsync(() => {
      const autoDismissNotification = mockNotifications[2];
      component.showNotification(autoDismissNotification);
      tick();
      fixture.detectChanges();

      const countdown = fixture.debugElement.query(By.css('.dismiss-countdown'));
      expect(countdown).toBeTruthy();
      expect(countdown.nativeElement.textContent).toContain('5');
    }));

    it('should cancel auto-dismiss on hover', fakeAsync(() => {
      const autoDismissNotification = mockNotifications[2];
      component.showNotification(autoDismissNotification);
      tick();
      fixture.detectChanges();

      const notificationElement = fixture.debugElement.query(By.css('.notification-container'));
      notificationElement.triggerEventHandler('mouseenter', {});

      // Fast-forward past timeout
      tick(autoDismissNotification.dismiss_timeout! + 1000);

      // Should still be visible due to hover
      expect(component.activeNotifications).toContain(autoDismissNotification);
    }));

    it('should resume auto-dismiss after hover ends', fakeAsync(() => {
      const autoDismissNotification = mockNotifications[2];
      component.showNotification(autoDismissNotification);
      tick();
      fixture.detectChanges();

      const notificationElement = fixture.debugElement.query(By.css('.notification-container'));
      
      // Hover to cancel auto-dismiss
      notificationElement.triggerEventHandler('mouseenter', {});
      tick(1000);

      // Stop hovering
      notificationElement.triggerEventHandler('mouseleave', {});
      tick(autoDismissNotification.dismiss_timeout!);

      expect(component.activeNotifications).not.toContain(autoDismissNotification);
    }));

    it('should handle expired notifications', fakeAsync(() => {
      const expiredNotification = {
        ...mockNotifications[0],
        expires_at: new Date(Date.now() - 1000).toISOString() // Expired 1 second ago
      };

      component.showNotification(expiredNotification);
      tick();

      expect(component.activeNotifications).not.toContain(expiredNotification);
    }));
  });

  describe('Sound and Desktop Notifications', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should play sound for notifications when enabled', fakeAsync(() => {
      component.settings.enableSounds = true;
      const notification = mockNotifications[0];
      
      component.showNotification(notification);
      tick();

      expect(notificationService.playNotificationSound).toHaveBeenCalledWith(notification.category);
    }));

    it('should not play sound when disabled', fakeAsync(() => {
      component.settings.enableSounds = false;
      const notification = mockNotifications[0];
      
      component.showNotification(notification);
      tick();

      expect(notificationService.playNotificationSound).not.toHaveBeenCalled();
    }));

    it('should show desktop notification when enabled and page not focused', fakeAsync(() => {
      component.settings.enableDesktopNotifications = true;
      Object.defineProperty(document, 'hidden', { value: true });
      
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();

      expect(notificationService.showDesktopNotification).toHaveBeenCalledWith(
        notification.title,
        notification.message,
        notification.from_user?.avatar_url
      );
    }));

    it('should not show desktop notification when page is focused', fakeAsync(() => {
      component.settings.enableDesktopNotifications = true;
      Object.defineProperty(document, 'hidden', { value: false });
      
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();

      expect(notificationService.showDesktopNotification).not.toHaveBeenCalled();
    }));

    it('should respect category sound settings', fakeAsync(() => {
      component.settings.categorySettings.messaging.sound = false;
      const messagingNotification = mockNotifications[2];
      
      component.showNotification(messagingNotification);
      tick();

      expect(notificationService.playNotificationSound).not.toHaveBeenCalled();
    }));
  });

  describe('Notification Queue Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should process notification queue when space becomes available', fakeAsync(() => {
      component.settings.maxVisibleNotifications = 1;

      // Fill up visible notifications
      component.showNotification(mockNotifications[0]);
      tick();

      // Queue additional notifications
      component.showNotification(mockNotifications[1]);
      component.showNotification(mockNotifications[2]);
      tick();

      expect(component.activeNotifications.length).toBe(1);
      expect(component.notificationQueue.length).toBe(2);

      // Dismiss the visible notification
      component.dismissNotification(mockNotifications[0]);
      tick();

      // Next queued notification should become visible
      expect(component.activeNotifications.length).toBe(1);
      expect(component.notificationQueue.length).toBe(1);
    }));

    it('should prioritize higher priority notifications in queue', fakeAsync(() => {
      component.settings.maxVisibleNotifications = 1;
      
      // Add low priority notification first
      component.showNotification({ ...mockNotifications[2], priority: 'low' });
      tick();

      // Queue high priority notification
      component.showNotification({ ...mockNotifications[3], priority: 'urgent' });
      tick();

      // Dismiss visible notification
      component.dismissNotification(mockNotifications[2]);
      tick();

      // High priority should be shown next
      expect(component.activeNotifications[0].priority).toBe('urgent');
    }));

    it('should limit queue size to prevent memory issues', () => {
      const maxQueueSize = 50;
      component.maxQueueSize = maxQueueSize;

      // Try to queue many notifications
      for (let i = 0; i < 100; i++) {
        component.queueNotification({
          ...mockNotifications[0],
          id: `queue-${i}`
        });
      }

      expect(component.notificationQueue.length).toBeLessThanOrEqual(maxQueueSize);
    });

    it('should clear queue when user navigates away', () => {
      component.notificationQueue = [...mockNotifications];
      
      component.clearNotificationQueue();
      
      expect(component.notificationQueue.length).toBe(0);
    });
  });

  describe('Settings and Preferences', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should update notification settings', fakeAsync(() => {
      const newSettings = {
        ...mockSettings,
        enableSounds: false,
        maxVisibleNotifications: 3
      };

      component.updateSettings(newSettings);
      tick();

      expect(notificationService.updateNotificationSettings).toHaveBeenCalledWith(newSettings);
      expect(component.settings).toEqual(newSettings);
    }));

    it('should apply category-specific settings', fakeAsync(() => {
      component.settings.categorySettings.messaging.enabled = false;
      
      const messagingNotification = mockNotifications[2];
      const result = component.shouldShowNotification(messagingNotification);
      
      expect(result).toBe(false);
    }));

    it('should handle settings loading errors', fakeAsync(() => {
      notificationService.getNotificationSettings.and.returnValue(
        throwError({ error: 'Settings unavailable' })
      );

      component.loadSettings();
      tick();

      // Should use default settings
      expect(component.settings).toBeDefined();
      expect(component.settings.enableInAppNotifications).toBe(true);
    }));

    it('should save settings changes persistently', fakeAsync(() => {
      const updatedSettings = { ...mockSettings, enableSounds: false };
      
      component.updateSettings(updatedSettings);
      tick();

      expect(notificationService.updateNotificationSettings).toHaveBeenCalledWith(updatedSettings);
    }));
  });

  describe('Performance and Memory Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should limit number of stored notifications to prevent memory leaks', () => {
      const maxStoredNotifications = 100;
      component.maxStoredNotifications = maxStoredNotifications;

      // Add many notifications
      for (let i = 0; i < 150; i++) {
        component.addToNotificationHistory({
          ...mockNotifications[0],
          id: `history-${i}`
        });
      }

      expect(component.notificationHistory.length).toBeLessThanOrEqual(maxStoredNotifications);
    });

    it('should cleanup expired notifications periodically', fakeAsync(() => {
      const expiredNotification = {
        ...mockNotifications[0],
        expires_at: new Date(Date.now() - 1000).toISOString()
      };

      component.activeNotifications.push(expiredNotification);
      
      // Trigger cleanup
      component.cleanupExpiredNotifications();
      tick();

      expect(component.activeNotifications).not.toContain(expiredNotification);
    }));

    it('should debounce rapid notification updates', fakeAsync(() => {
      spyOn(component, 'processNotificationQueue').and.callThrough();

      // Rapid notifications
      for (let i = 0; i < 10; i++) {
        notificationSubject.next({
          ...mockNotifications[0],
          id: `rapid-${i}`
        });
      }

      tick(300); // Debounce delay

      expect(component.processNotificationQueue).toHaveBeenCalledTimes(1);
    }));

    it('should implement virtual scrolling for notification history', () => {
      component.showNotificationHistory = true;
      fixture.detectChanges();

      const virtualScrollViewport = fixture.debugElement.query(By.css('cdk-virtual-scroll-viewport'));
      expect(virtualScrollViewport).toBeTruthy();
    });

    it('should unsubscribe from observables on destroy', () => {
      spyOn(component['subscriptions'], 'unsubscribe');
      
      component.ngOnDestroy();
      
      expect(component['subscriptions'].unsubscribe).toHaveBeenCalled();
    });
  });

  describe('Accessibility and Keyboard Support', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should have proper ARIA labels', fakeAsync(() => {
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const notificationElement = fixture.debugElement.query(By.css('.notification-container'));
      expect(notificationElement.nativeElement.getAttribute('role')).toBe('alert');
      expect(notificationElement.nativeElement.getAttribute('aria-label')).toContain(notification.title);
    }));

    it('should support keyboard navigation', fakeAsync(() => {
      const notification = mockNotifications[1];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const actionButton = fixture.debugElement.query(By.css('.action-view'));
      expect(actionButton.nativeElement.getAttribute('tabindex')).toBe('0');

      actionButton.triggerEventHandler('keydown.enter', {});
      expect(component.handleActionClick).toHaveBeenCalled();
    }));

    it('should announce notifications to screen readers', fakeAsync(() => {
      const liveRegion = fixture.debugElement.query(By.css('[aria-live="polite"]'));
      expect(liveRegion).toBeTruthy();

      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      expect(liveRegion.nativeElement.textContent).toContain(notification.message);
    }));

    it('should support high contrast mode', fakeAsync(() => {
      component.highContrastMode = true;
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const notificationElement = fixture.debugElement.query(By.css('.notification-container'));
      expect(notificationElement.nativeElement.classList).toContain('high-contrast');
    }));

    it('should respect reduced motion preferences', fakeAsync(() => {
      spyOnProperty(window, 'matchMedia').and.returnValue({
        matches: true,
        media: '(prefers-reduced-motion: reduce)'
      } as MediaQueryList);

      component.ngOnInit();
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const notificationElement = fixture.debugElement.query(By.css('.notification-container'));
      expect(notificationElement.nativeElement.classList).toContain('reduced-motion');
    }));
  });

  describe('Mobile and Responsive Behavior', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should adapt layout for mobile screens', fakeAsync(() => {
      spyOnProperty(window, 'innerWidth').and.returnValue(375);
      
      component.ngOnInit();
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const notificationElement = fixture.debugElement.query(By.css('.notification-container'));
      expect(notificationElement.nativeElement.classList).toContain('mobile');
    }));

    it('should use bottom positioning on mobile', fakeAsync(() => {
      component.isMobile = true;
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const container = fixture.debugElement.query(By.css('.notifications-container'));
      expect(container.nativeElement.classList).toContain('bottom-positioned');
    }));

    it('should support pull-to-refresh gesture', fakeAsync(() => {
      component.isMobile = true;
      spyOn(component, 'refreshNotifications');
      fixture.detectChanges();

      const container = fixture.debugElement.query(By.css('.notifications-container'));
      container.triggerEventHandler('refresh', {});

      expect(component.refreshNotifications).toHaveBeenCalled();
    }));

    it('should optimize touch targets for mobile', fakeAsync(() => {
      component.isMobile = true;
      const notification = mockNotifications[1];
      component.showNotification(notification);
      tick();
      fixture.detectChanges();

      const actionButtons = fixture.debugElement.queryAll(By.css('.notification-action'));
      actionButtons.forEach(button => {
        const styles = getComputedStyle(button.nativeElement);
        const minHeight = parseInt(styles.minHeight);
        expect(minHeight).toBeGreaterThanOrEqual(44); // 44px minimum touch target
      });
    }));
  });

  describe('Error Handling and Fallbacks', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should handle WebSocket disconnection', fakeAsync(() => {
      webSocketService.isConnected.and.returnValue(false);
      
      const notification = mockNotifications[0];
      notificationSubject.next(notification);
      tick();

      // Should queue notification for when connection is restored
      expect(component.offlineNotificationQueue).toContain(notification);
    }));

    it('should handle malformed notification data', fakeAsync(() => {
      spyOn(console, 'error');
      
      const malformedNotification = {
        id: null,
        type: undefined,
        message: ''
      } as any;

      notificationSubject.next(malformedNotification);
      tick();

      expect(console.error).toHaveBeenCalled();
      expect(component.activeNotifications).not.toContain(malformedNotification);
    }));

    it('should provide fallback for missing user information', fakeAsync(() => {
      const notificationWithoutUser = {
        ...mockNotifications[0],
        from_user: undefined
      };

      component.showNotification(notificationWithoutUser);
      tick();
      fixture.detectChanges();

      const avatar = fixture.debugElement.query(By.css('.notification-avatar, .default-avatar'));
      expect(avatar).toBeTruthy();
    }));

    it('should handle notification service errors', fakeAsync(() => {
      notificationService.markAsRead.and.returnValue(throwError({ error: 'Service unavailable' }));
      
      const notification = mockNotifications[0];
      component.showNotification(notification);
      tick();

      // Should continue working despite service errors
      expect(component.activeNotifications).toContain(notification);
    }));

    it('should implement retry logic for failed operations', fakeAsync(() => {
      let callCount = 0;
      notificationService.markAsRead.and.callFake(() => {
        callCount++;
        if (callCount === 1) {
          return throwError({ error: 'Network error' });
        }
        return of(true);
      });

      const notification = mockNotifications[0];
      component.markAsRead(notification);
      tick(2000); // Wait for retry

      expect(callCount).toBe(2);
    }));
  });
});