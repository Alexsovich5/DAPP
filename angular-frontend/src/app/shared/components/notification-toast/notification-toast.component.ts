import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription, Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { NotificationService } from '../../../core/services/notification.service';
import { WebSocketService } from '../../../core/services/websocket.service';
import { AuthService } from '../../../core/services/auth.service';

export interface RealtimeNotification {
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

export interface NotificationSettings {
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

@Component({
  selector: 'app-notification-toast',
  templateUrl: './notification-toast.component.html',
  styleUrls: ['./notification-toast.component.scss']
})
export class NotificationToastComponent implements OnInit, OnDestroy {
  activeNotifications: RealtimeNotification[] = [];
  notificationQueue: RealtimeNotification[] = [];
  offlineNotificationQueue: RealtimeNotification[] = [];
  notificationHistory: RealtimeNotification[] = [];

  settings: NotificationSettings = {
    enableSounds: true,
    enableDesktopNotifications: true,
    enableInAppNotifications: true,
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00'
    },
    categorySettings: {
      soul_connection: { enabled: true, priority: 'high', sound: true },
      messaging: { enabled: true, priority: 'medium', sound: true },
      system: { enabled: true, priority: 'low', sound: false },
      social: { enabled: true, priority: 'medium', sound: true }
    },
    maxVisibleNotifications: 5,
    autoCloseDelay: 8000
  };

  maxVisibleNotifications = 5;
  maxQueueSize = 50;
  maxStoredNotifications = 100;
  isMobile = false;
  highContrastMode = false;
  showNotificationHistory = false;

  private subscriptions = new Subscription();
  private notificationSubject = new Subject<RealtimeNotification>();
  private autoDismissTimers = new Map<string, ReturnType<typeof setTimeout>>();

  constructor(
    private readonly notificationService: NotificationService,
    private readonly webSocketService: WebSocketService,
    private readonly authService: AuthService,
    private readonly router: Router
  ) {
    this.isMobile = window.innerWidth <= 768;
  }

  ngOnInit(): void {
    this.loadSettings();
    this.subscribeToNotifications();

    if (this.settings.enableDesktopNotifications) {
      this.notificationService.requestDesktopPermission();
    }

    this.subscriptions.add(
      this.notificationSubject.pipe(
        debounceTime(300)
      ).subscribe(() => {
        this.processNotificationQueue();
      })
    );

    setInterval(() => {
      this.cleanupExpiredNotifications();
    }, 60000);
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.autoDismissTimers.forEach(timer => clearTimeout(timer));
    this.autoDismissTimers.clear();
  }

  loadSettings(): void {
    this.subscriptions.add(
      this.notificationService.getNotificationSettings().subscribe({
        next: (settings: any) => {
          this.settings = settings;
          this.maxVisibleNotifications = settings.maxVisibleNotifications;
        },
        error: () => {
          // Use default settings
          this.settings.enableInAppNotifications = true;
        }
      })
    );
  }

  private subscribeToNotifications(): void {
    this.subscriptions.add(
      this.webSocketService.onMessage().subscribe(data => {
        if (data.type && data.title && data.message) {
          const notification = data as RealtimeNotification;
          this.handleIncomingNotification(notification);
        }
      })
    );
  }

  private handleIncomingNotification(notification: RealtimeNotification): void {
    if (this.webSocketService.isConnected()) {
      if (this.shouldShowNotification(notification)) {
        this.showNotification(notification);
      }
    } else {
      this.offlineNotificationQueue.push(notification);
    }
  }

  shouldShowNotification(notification: RealtimeNotification): boolean {
    const categorySettings = this.settings.categorySettings[notification.category];
    if (!categorySettings || !categorySettings.enabled) {
      return false;
    }

    if (this.isInQuietHours() && notification.priority !== 'urgent') {
      return false;
    }

    if (notification.expires_at) {
      const expiresAt = new Date(notification.expires_at);
      if (expiresAt < new Date()) {
        return false;
      }
    }

    return true;
  }

  isInQuietHours(): boolean {
    if (!this.settings.quietHours.enabled) {
      return false;
    }

    const now = new Date();
    const currentHour = now.getHours();
    const startHour = parseInt(this.settings.quietHours.start.split(':')[0]);
    const endHour = parseInt(this.settings.quietHours.end.split(':')[0]);

    if (startHour < endHour) {
      return currentHour >= startHour && currentHour < endHour;
    } else {
      return currentHour >= startHour || currentHour < endHour;
    }
  }

  showNotification(notification: RealtimeNotification): void {
    if (!notification.id || !notification.type || !notification.message) {
      console.error('Malformed notification:', notification);
      return;
    }

    if (this.activeNotifications.length >= this.maxVisibleNotifications) {
      this.queueNotification(notification);
      return;
    }

    this.activeNotifications.push(notification);
    this.addToNotificationHistory(notification);

    if (this.settings.enableSounds) {
      const categorySettings = this.settings.categorySettings[notification.category];
      if (categorySettings?.sound) {
        this.notificationService.playNotificationSound(notification.category);
      }
    }

    if (this.settings.enableDesktopNotifications && document.hidden) {
      this.notificationService.showDesktopNotification(
        notification.title,
        notification.message,
        notification.from_user?.avatar_url
      );
    }

    if (notification.auto_dismiss && notification.dismiss_timeout) {
      this.startAutoDismissTimer(notification);
    }
  }

  queueNotification(notification: RealtimeNotification): void {
    if (this.notificationQueue.length >= this.maxQueueSize) {
      this.notificationQueue.shift();
    }

    const insertIndex = this.notificationQueue.findIndex(
      n => this.getPriorityValue(n.priority) < this.getPriorityValue(notification.priority)
    );

    if (insertIndex === -1) {
      this.notificationQueue.push(notification);
    } else {
      this.notificationQueue.splice(insertIndex, 0, notification);
    }
  }

  private getPriorityValue(priority: string): number {
    const priorities: { [key: string]: number } = {
      low: 1,
      medium: 2,
      high: 3,
      urgent: 4
    };
    return priorities[priority] || 0;
  }

  processNotificationQueue(): void {
    while (
      this.activeNotifications.length < this.maxVisibleNotifications &&
      this.notificationQueue.length > 0
    ) {
      const notification = this.notificationQueue.shift();
      if (notification) {
        this.showNotification(notification);
      }
    }
  }

  dismissNotification(notification: RealtimeNotification): void {
    const index = this.activeNotifications.indexOf(notification);
    if (index > -1) {
      this.activeNotifications.splice(index, 1);
    }

    const timer = this.autoDismissTimers.get(notification.id);
    if (timer) {
      clearTimeout(timer);
      this.autoDismissTimers.delete(notification.id);
    }

    this.notificationService.dismissNotification(notification.id).subscribe();
    this.processNotificationQueue();
  }

  markAsRead(notification: RealtimeNotification): void {
    notification.is_read = true;
    this.notificationService.markAsRead(notification.id).subscribe();
  }

  navigateToAction(notification: RealtimeNotification): void {
    if (notification.action_data?.action_url) {
      this.router.navigate([notification.action_data.action_url]);
      this.markAsRead(notification);
      this.dismissNotification(notification);
    }
  }

  handleActionClick(notification: RealtimeNotification, action: string): void {
    if (action === 'view') {
      this.navigateToAction(notification);
    }
  }

  getNotificationIcon(type: string): string {
    const icons: { [key: string]: string } = {
      revelation_shared: 'favorite',
      connection_request: 'connect_without_contact',
      message_received: 'message',
      photo_reveal_ready: 'photo_camera',
      profile_view: 'visibility',
      connection_accepted: 'check_circle',
      system_update: 'info'
    };
    return icons[type] || 'notifications';
  }

  getNotificationPriority(notification: RealtimeNotification): string {
    return notification.priority;
  }

  private startAutoDismissTimer(notification: RealtimeNotification): void {
    if (!notification.dismiss_timeout) {
      return;
    }

    const timer = setTimeout(() => {
      this.dismissNotification(notification);
    }, notification.dismiss_timeout);

    this.autoDismissTimers.set(notification.id, timer);
  }

  cancelAutoDismiss(notification: RealtimeNotification): void {
    const timer = this.autoDismissTimers.get(notification.id);
    if (timer) {
      clearTimeout(timer);
      this.autoDismissTimers.delete(notification.id);
    }
  }

  resumeAutoDismiss(notification: RealtimeNotification): void {
    if (notification.auto_dismiss && notification.dismiss_timeout) {
      this.startAutoDismissTimer(notification);
    }
  }

  addToNotificationHistory(notification: RealtimeNotification): void {
    this.notificationHistory.unshift(notification);
    if (this.notificationHistory.length > this.maxStoredNotifications) {
      this.notificationHistory = this.notificationHistory.slice(0, this.maxStoredNotifications);
    }
  }

  cleanupExpiredNotifications(): void {
    const now = new Date();
    this.activeNotifications = this.activeNotifications.filter(n => {
      if (n.expires_at) {
        return new Date(n.expires_at) > now;
      }
      return true;
    });
  }

  clearNotificationQueue(): void {
    this.notificationQueue = [];
  }

  updateSettings(newSettings: NotificationSettings): void {
    this.settings = newSettings;
    this.notificationService.updateNotificationSettings(newSettings).subscribe();
  }

  refreshNotifications(): void {
    // Refresh notification list
  }

  copyMessageText(notification: RealtimeNotification): void {
    navigator.clipboard.writeText(notification.message);
  }

  getRelativeTime(timestamp: string): string {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`;
    } else if (diffMins < 1440) {
      const hours = Math.floor(diffMins / 60);
      return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
    } else {
      return time.toLocaleDateString();
    }
  }
}
