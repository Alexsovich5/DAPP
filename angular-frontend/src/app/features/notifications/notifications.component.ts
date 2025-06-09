import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { NotificationService, Notification } from '../../core/services/notification.service';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="notifications-container">
      <header class="notifications-header">
        <h1>Notifications</h1>
        <div class="header-actions">
          <button 
            class="action-btn" 
            (click)="markAllAsRead()"
            [disabled]="unreadCount === 0"
          >
            Mark All Read
          </button>
          <button 
            class="action-btn secondary" 
            (click)="clearAll()"
            [disabled]="notifications.length === 0"
          >
            Clear All
          </button>
        </div>
      </header>

      <div class="notification-stats" *ngIf="notifications.length > 0">
        <div class="stat-item">
          <span class="stat-number">{{notifications.length}}</span>
          <span class="stat-label">Total</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{unreadCount}}</span>
          <span class="stat-label">Unread</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{todayNotifications}}</span>
          <span class="stat-label">Today</span>
        </div>
      </div>

      <div class="notifications-list" *ngIf="notifications.length > 0; else noNotifications">
        <div 
          *ngFor="let notification of notifications; trackBy: trackByNotificationId" 
          class="notification-item"
          [class.unread]="!notification.isRead"
          [class]="'type-' + notification.type"
          (click)="handleNotificationClick(notification)"
        >
          <div class="notification-icon">
            <span>{{getNotificationIcon(notification.type)}}</span>
          </div>

          <div class="notification-content">
            <div class="notification-header">
              <h3 class="notification-title">{{notification.title}}</h3>
              <span class="notification-time">{{formatTime(notification.timestamp)}}</span>
            </div>
            
            <p class="notification-message">{{notification.message}}</p>
            
            <div class="notification-meta">
              <span class="notification-type">{{formatNotificationType(notification.type)}}</span>
              <span class="read-status" *ngIf="!notification.isRead">New</span>
            </div>
          </div>

          <div class="notification-actions">
            <button 
              class="action-btn-small"
              (click)="markAsRead(notification, $event)"
              *ngIf="!notification.isRead"
              title="Mark as read"
            >
              ✓
            </button>
            <button 
              class="action-btn-small secondary"
              (click)="removeNotification(notification, $event)"
              title="Remove"
            >
              ✕
            </button>
          </div>
        </div>
      </div>

      <ng-template #noNotifications>
        <div class="empty-state">
          <div class="empty-icon">🔔</div>
          <h2>No Notifications</h2>
          <p>You're all caught up! Check back later for updates on your soul connections.</p>
          <button class="cta-button" (click)="simulateNotification()">
            <span>🧪</span> Simulate Notification
          </button>
        </div>
      </ng-template>

      <!-- Notification Types Legend -->
      <div class="notification-legend" *ngIf="notifications.length > 0">
        <h3>Notification Types</h3>
        <div class="legend-items">
          <div class="legend-item">
            <span class="legend-icon">✨</span>
            <span>Revelations - Someone shared a revelation</span>
          </div>
          <div class="legend-item">
            <span class="legend-icon">💬</span>
            <span>Messages - New messages received</span>
          </div>
          <div class="legend-item">
            <span class="legend-icon">💫</span>
            <span>Matches - New soul connections found</span>
          </div>
          <div class="legend-item">
            <span class="legend-icon">🎉</span>
            <span>Photo Reveals - Mutual photo reveal ready</span>
          </div>
          <div class="legend-item">
            <span class="legend-icon">🔔</span>
            <span>System - App updates and reminders</span>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .notifications-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 1rem;
      min-height: 100vh;
    }

    .notifications-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }

    .notifications-header h1 {
      font-size: 2rem;
      font-weight: 600;
      color: #2d3748;
      margin: 0;
    }

    .header-actions {
      display: flex;
      gap: 0.5rem;
    }

    .action-btn {
      padding: 0.5rem 1rem;
      border: 1px solid #667eea;
      background: #667eea;
      color: white;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 0.9rem;
      font-weight: 500;
    }

    .action-btn:hover:not(:disabled) {
      background: #5a67d8;
      border-color: #5a67d8;
    }

    .action-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .action-btn.secondary {
      background: white;
      color: #718096;
      border-color: #e2e8f0;
    }

    .action-btn.secondary:hover:not(:disabled) {
      background: #f7fafc;
      border-color: #cbd5e0;
    }

    .notification-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .stat-item {
      background: white;
      padding: 1rem;
      border-radius: 8px;
      text-align: center;
      border: 1px solid #e2e8f0;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .stat-number {
      display: block;
      font-size: 1.5rem;
      font-weight: bold;
      color: #667eea;
      margin-bottom: 0.25rem;
    }

    .stat-label {
      font-size: 0.8rem;
      color: #718096;
    }

    .notifications-list {
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
      margin-bottom: 2rem;
    }

    .notification-item {
      display: flex;
      align-items: flex-start;
      padding: 1rem;
      border-bottom: 1px solid #f7fafc;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
    }

    .notification-item:hover {
      background: #f7fafc;
    }

    .notification-item:last-child {
      border-bottom: none;
    }

    .notification-item.unread {
      background: linear-gradient(90deg, rgba(102, 126, 234, 0.02) 0%, rgba(102, 126, 234, 0.01) 100%);
      border-left: 4px solid #667eea;
    }

    .notification-item.type-revelation {
      border-left-color: #ffd700;
    }

    .notification-item.type-message {
      border-left-color: #48bb78;
    }

    .notification-item.type-match {
      border-left-color: #ed64a6;
    }

    .notification-item.type-photo_reveal {
      border-left-color: #f56565;
    }

    .notification-item.type-system {
      border-left-color: #4299e1;
    }

    .notification-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #f7fafc;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 1rem;
      font-size: 1.2rem;
      flex-shrink: 0;
    }

    .type-revelation .notification-icon {
      background: #fff5cd;
    }

    .type-message .notification-icon {
      background: #c6f6d5;
    }

    .type-match .notification-icon {
      background: #fed7e2;
    }

    .type-photo_reveal .notification-icon {
      background: #fed7d7;
    }

    .type-system .notification-icon {
      background: #bee3f8;
    }

    .notification-content {
      flex: 1;
      min-width: 0;
    }

    .notification-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.5rem;
    }

    .notification-title {
      font-size: 1rem;
      font-weight: 600;
      color: #2d3748;
      margin: 0;
      line-height: 1.3;
    }

    .notification-time {
      font-size: 0.8rem;
      color: #a0aec0;
      white-space: nowrap;
      margin-left: 1rem;
    }

    .notification-message {
      color: #4a5568;
      margin: 0 0 0.75rem 0;
      line-height: 1.4;
      font-size: 0.95rem;
    }

    .notification-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .notification-type {
      font-size: 0.8rem;
      color: #718096;
      font-weight: 500;
    }

    .read-status {
      background: #667eea;
      color: white;
      padding: 0.2rem 0.5rem;
      border-radius: 10px;
      font-size: 0.7rem;
      font-weight: 600;
    }

    .notification-actions {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      margin-left: 0.5rem;
    }

    .action-btn-small {
      width: 24px;
      height: 24px;
      border: none;
      border-radius: 50%;
      background: #f7fafc;
      color: #718096;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
    }

    .action-btn-small:hover {
      background: #edf2f7;
      transform: scale(1.1);
    }

    .action-btn-small.secondary:hover {
      background: #fed7d7;
      color: #c53030;
    }

    .empty-state {
      text-align: center;
      padding: 4rem 2rem;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }

    .empty-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
    }

    .empty-state h2 {
      font-size: 1.5rem;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 0.5rem;
    }

    .empty-state p {
      color: #718096;
      margin-bottom: 2rem;
      line-height: 1.6;
    }

    .cta-button {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }

    .cta-button:hover {
      transform: translateY(-1px);
    }

    .notification-legend {
      background: white;
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }

    .notification-legend h3 {
      color: #2d3748;
      margin: 0 0 1rem 0;
      font-size: 1.1rem;
    }

    .legend-items {
      display: grid;
      gap: 0.75rem;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 0.9rem;
      color: #4a5568;
    }

    .legend-icon {
      width: 24px;
      text-align: center;
    }

    @media (max-width: 768px) {
      .notifications-container {
        padding: 0.5rem;
      }
      
      .notifications-header {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
      }
      
      .header-actions {
        justify-content: center;
      }
      
      .notification-stats {
        grid-template-columns: 1fr;
      }
      
      .notification-item {
        padding: 0.75rem;
      }
      
      .notification-header {
        flex-direction: column;
        gap: 0.25rem;
      }
      
      .notification-time {
        margin-left: 0;
      }
      
      .notification-actions {
        flex-direction: row;
        gap: 0.25rem;
      }
    }
  `]
})
export class NotificationsComponent implements OnInit {
  notifications: Notification[] = [];
  unreadCount = 0;

  constructor(
    private notificationService: NotificationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.notificationService.getNotifications().subscribe(notifications => {
      this.notifications = notifications;
    });

    this.notificationService.getUnreadCount().subscribe(count => {
      this.unreadCount = count;
    });
  }

  get todayNotifications(): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return this.notifications.filter(n => {
      const notificationDate = new Date(n.timestamp);
      notificationDate.setHours(0, 0, 0, 0);
      return notificationDate.getTime() === today.getTime();
    }).length;
  }

  trackByNotificationId(index: number, notification: Notification): string {
    return notification.id;
  }

  getNotificationIcon(type: string): string {
    const icons = {
      revelation: '✨',
      message: '💬',
      match: '💫',
      photo_reveal: '🎉',
      system: '🔔'
    };
    return icons[type as keyof typeof icons] || '🔔';
  }

  formatNotificationType(type: string): string {
    const typeNames = {
      revelation: 'Revelation',
      message: 'Message',
      match: 'Match',
      photo_reveal: 'Photo Reveal',
      system: 'System'
    };
    return typeNames[type as keyof typeof typeNames] || 'Notification';
  }

  formatTime(timestamp: Date): string {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 1) {
      return 'Just now';
    } else if (minutes < 60) {
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return `${days}d ago`;
    } else {
      return timestamp.toLocaleDateString();
    }
  }

  handleNotificationClick(notification: Notification) {
    // Mark as read
    if (!notification.isRead) {
      this.notificationService.markAsRead(notification.id);
    }

    // Navigate to action URL if provided
    if (notification.actionUrl) {
      this.router.navigate([notification.actionUrl]);
    }
  }

  markAsRead(notification: Notification, event: Event) {
    event.stopPropagation();
    this.notificationService.markAsRead(notification.id);
  }

  removeNotification(notification: Notification, event: Event) {
    event.stopPropagation();
    this.notificationService.removeNotification(notification.id);
  }

  markAllAsRead() {
    this.notificationService.markAllAsRead();
  }

  clearAll() {
    this.notificationService.clearAll();
  }

  simulateNotification() {
    this.notificationService.simulateRealTimeNotification();
  }
}