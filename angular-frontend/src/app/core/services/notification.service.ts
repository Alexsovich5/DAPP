import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface Notification {
  id: string;
  type: 'revelation' | 'message' | 'match' | 'photo_reveal' | 'system';
  title: string;
  message: string;
  timestamp: Date;
  isRead: boolean;
  actionUrl?: string;
  metadata?: any;
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

  private updateUnreadCount(): void {
    const unreadCount = this.notifications$.value.filter(n => !n.isRead).length;
    this.unreadCount$.next(unreadCount);
  }

  private generateId(): string {
    return Math.random().toString(36).substr(2, 9);
  }

  private initializeMockNotifications(): void {
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'revelation',
        title: 'New Revelation Shared! ✨',
        message: 'Alex shared a beautiful revelation about their core values',
        timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
        isRead: false,
        actionUrl: '/revelations?connectionId=1'
      },
      {
        id: '2',
        type: 'message',
        title: 'New Message 💬',
        message: 'You have a new message from your soul connection',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        isRead: false,
        actionUrl: '/messages'
      },
      {
        id: '3',
        type: 'photo_reveal',
        title: 'Photo Reveal Day! 🎉',
        message: 'It\'s day 7! Both of you are ready for photo reveal',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
        isRead: false,
        actionUrl: '/revelations?connectionId=1'
      },
      {
        id: '4',
        type: 'match',
        title: 'New Soul Connection! 💫',
        message: 'You have a 89% compatibility match with someone special',
        timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
        isRead: true,
        actionUrl: '/matches'
      },
      {
        id: '5',
        type: 'revelation',
        title: 'Revelation Reminder ⏰',
        message: 'Don\'t forget to share today\'s revelation about your dreams',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
        isRead: true,
        actionUrl: '/revelations?connectionId=1'
      },
      {
        id: '6',
        type: 'system',
        title: 'Welcome to Soul Before Skin! 🌟',
        message: 'Complete your emotional onboarding to start connecting',
        timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
        isRead: true,
        actionUrl: '/onboarding'
      }
    ];

    this.notifications$.next(mockNotifications);
    this.updateUnreadCount();
  }

  // Simulate real-time notifications
  simulateRealTimeNotification(): void {
    const notificationTypes = [
      {
        type: 'message' as const,
        title: 'New Message 💬',
        message: 'You received a heartfelt message',
        actionUrl: '/messages'
      },
      {
        type: 'revelation' as const,
        title: 'New Revelation! ✨',
        message: 'Someone shared a meaningful revelation with you',
        actionUrl: '/revelations?connectionId=1'
      },
      {
        type: 'match' as const,
        title: 'New Match! 💫',
        message: 'You have a high compatibility match waiting',
        actionUrl: '/matches'
      }
    ];

    const randomNotification = notificationTypes[Math.floor(Math.random() * notificationTypes.length)];
    this.addNotification(randomNotification);
  }
}