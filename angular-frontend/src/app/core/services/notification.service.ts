import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';

export interface Notification {
  id: string;
  type: 'revelation' | 'message' | 'match' | 'photo_reveal' | 'system' | 'error' | 'success' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  isRead: boolean;
  actionUrl?: string;
  metadata?: Record<string, unknown>;
  autoHide?: boolean;
  duration?: number;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notifications$ = new BehaviorSubject<Notification[]>([]);
  private unreadCount$ = new BehaviorSubject<number>(0);

  constructor() {
    this.initializeMockNotifications();
  }

  getNotifications(): Observable<Notification[]> {
    return this.notifications$.asObservable();
  }

  getUnreadCount(): Observable<number> {
    return this.unreadCount$.asObservable();
  }

  getCurrentUnreadCount(): number {
    return this.unreadCount$.value;
  }

  markAsRead(notificationId: string): void {
    const notifications = this.notifications$.value;
    const notification = notifications.find(n => n.id === notificationId);

    if (notification && !notification.isRead) {
      notification.isRead = true;
      this.notifications$.next([...notifications]);
      this.updateUnreadCount();
    }
  }

  markAllAsRead(): void {
    const notifications = this.notifications$.value.map(n => ({
      ...n,
      isRead: true
    }));

    this.notifications$.next(notifications);
    this.updateUnreadCount();
  }

  addNotification(notification: Omit<Notification, 'id' | 'timestamp' | 'isRead'>): void {
    const newNotification: Notification = {
      ...notification,
      id: this.generateId(),
      timestamp: new Date(),
      isRead: false
    };

    const notifications = [newNotification, ...this.notifications$.value];
    this.notifications$.next(notifications);
    this.updateUnreadCount();
  }

  removeNotification(notificationId: string): void {
    const notifications = this.notifications$.value.filter(n => n.id !== notificationId);
    this.notifications$.next(notifications);
    this.updateUnreadCount();
  }

  clearAll(): void {
    this.notifications$.next([]);
    this.updateUnreadCount();
  }

  // Convenience methods for different notification types
  showError(message: string, title = 'Error', duration = 5000): void {
    this.addNotification({
      type: 'error',
      title,
      message,
      autoHide: true,
      duration
    });
  }

  showSuccess(message: string, title = 'Success', duration = 3000): void {
    this.addNotification({
      type: 'success',
      title,
      message,
      autoHide: true,
      duration
    });
  }

  showWarning(message: string, title = 'Warning', duration = 4000): void {
    this.addNotification({
      type: 'warning',
      title,
      message,
      autoHide: true,
      duration
    });
  }

  showInfo(message: string, title = 'Info', duration = 3000): void {
    this.addNotification({
      type: 'info',
      title,
      message,
      autoHide: true,
      duration
    });
  }

  private updateUnreadCount(): void {
    const unreadCount = this.notifications$.value.filter(n => !n.isRead).length;
    this.unreadCount$.next(unreadCount);
  }

  private generateId(): string {
    return Math.random().toString(36).substr(2, 9);
  }

  private initializeMockNotifications(): void {
    // No mock notifications - use real data from backend
    this.notifications$.next([]);
    this.updateUnreadCount();

    // NOTE: Mock data removed to use real backend notifications
    // In production, notifications will be populated via:
    // - WebSocket real-time updates (messages, revelations, matches)
    // - API polling for notification history
    // - Backend notification service
  }

  // Simulate real-time notifications
  simulateRealTimeNotification(): void {
    const notificationTypes = [
      {
        type: 'message' as const,
        title: 'New Message',
        message: 'You received a heartfelt message',
        actionUrl: '/messages'
      },
      {
        type: 'revelation' as const,
        title: 'New Revelation',
        message: 'Someone shared a meaningful revelation with you',
        actionUrl: '/revelations?connectionId=1'
      },
      {
        type: 'match' as const,
        title: 'New Match',
        message: 'You have a high compatibility match waiting',
        actionUrl: '/matches'
      }
    ];

    const randomNotification = notificationTypes[Math.floor(Math.random() * notificationTypes.length)];
    this.addNotification(randomNotification);
  }

  // Stub methods for notification-toast component compatibility
  // TODO: Implement these methods properly when real-time notification system is built

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getNotificationSettings(): Observable<any> {
    // Return mock settings for now
    return of({
      enableSounds: true,
      enableDesktopNotifications: false,
      enableInAppNotifications: true,
      quietHours: { enabled: false, start: '22:00', end: '08:00' },
      categorySettings: {},
      maxVisibleNotifications: 5,
      autoCloseDelay: 8000
    });
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  updateNotificationSettings(settings: any): Observable<any> {
    // Stub implementation
    return of(settings);
  }

  dismissNotification(notificationId: string): Observable<void> {
    // Call existing removeNotification method
    this.removeNotification(notificationId);
    return of(undefined);
  }

  playNotificationSound(category: string): void {
    // Stub implementation - would play sound based on category
    console.log(`Playing notification sound for category: ${category}`);
  }

  requestDesktopPermission(): void {
    // Stub implementation - would request browser notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  showDesktopNotification(title: string, options: any): void {
    // Stub implementation - would show desktop notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, options);
    }
  }
}
