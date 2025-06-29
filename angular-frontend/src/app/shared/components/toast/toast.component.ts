import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { Subscription } from 'rxjs';
import { NotificationService, Notification } from '@core/services/notification.service';
import { environment } from '@environments/environment';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule],
  template: `
    <div class="toast-container">
      <div 
        *ngFor="let notification of displayedNotifications" 
        class="toast"
        [ngClass]="'toast-' + notification.type"
      >
        <div class="toast-content">
          <mat-icon class="toast-icon">{{ getIcon(notification.type) }}</mat-icon>
          <div class="toast-message">
            <div class="toast-title">{{ notification.title }}</div>
            <div class="toast-text">{{ notification.message }}</div>
          </div>
          <button 
            mat-icon-button 
            class="toast-close"
            (click)="closeToast(notification.id)"
          >
            <mat-icon>close</mat-icon>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .toast-container {
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      max-width: 400px;
    }

    .toast {
      margin-bottom: 12px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
      overflow: hidden;
      animation: slideIn ${environment.ui.animationDuration}ms ease-out;
    }

    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .toast-content {
      display: flex;
      align-items: flex-start;
      padding: 16px;
      background: white;
    }

    .toast-icon {
      margin-right: 12px;
      margin-top: 2px;
      font-size: 20px;
      width: 20px;
      height: 20px;
    }

    .toast-message {
      flex: 1;
      min-width: 0;
    }

    .toast-title {
      font-weight: 600;
      font-size: 14px;
      margin-bottom: 4px;
      color: #1f2937;
    }

    .toast-text {
      font-size: 13px;
      color: #6b7280;
      line-height: 1.4;
    }

    .toast-close {
      margin-left: 8px;
      margin-top: -4px;
      color: #9ca3af;
      width: 32px;
      height: 32px;
      
      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    }

    .toast-close:hover {
      color: #6b7280;
    }

    /* Toast type styles */
    .toast-error {
      border-left: 4px solid #ef4444;
    }
    .toast-error .toast-icon {
      color: #ef4444;
    }

    .toast-success {
      border-left: 4px solid #10b981;
    }
    .toast-success .toast-icon {
      color: #10b981;
    }

    .toast-warning {
      border-left: 4px solid #f59e0b;
    }
    .toast-warning .toast-icon {
      color: #f59e0b;
    }

    .toast-info {
      border-left: 4px solid #3b82f6;
    }
    .toast-info .toast-icon {
      color: #3b82f6;
    }

    @media (max-width: 480px) {
      .toast-container {
        left: 20px;
        right: 20px;
        top: 20px;
        max-width: none;
      }
      
      .toast-content {
        padding: 12px;
      }
      
      .toast-title {
        font-size: 13px;
      }
      
      .toast-text {
        font-size: 12px;
      }
    }
  `]
})
export class ToastComponent implements OnInit, OnDestroy {
  displayedNotifications: Notification[] = [];
  private subscription?: Subscription;
  private timeouts: Map<string, number> = new Map();

  constructor(private notificationService: NotificationService) {}

  ngOnInit(): void {
    this.subscription = this.notificationService.getNotifications().subscribe(notifications => {
      // Only show error, success, warning, and info notifications as toasts
      const toastNotifications = notifications.filter(n => 
        ['error', 'success', 'warning', 'info'].includes(n.type) && !n.isRead
      );
      
      this.displayedNotifications = toastNotifications;
      
      // Auto-hide notifications that have autoHide enabled
      toastNotifications.forEach(notification => {
        if (notification.autoHide && !this.timeouts.has(notification.id)) {
          const timeoutId = window.setTimeout(() => {
            this.closeToast(notification.id);
            this.timeouts.delete(notification.id);
          }, notification.duration || environment.ui.toastDuration);
          
          this.timeouts.set(notification.id, timeoutId);
        }
      });
    });
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
    
    // Clear all timeouts
    this.timeouts.forEach(timeoutId => {
      clearTimeout(timeoutId);
    });
    this.timeouts.clear();
  }

  closeToast(notificationId: string): void {
    // Clear timeout if exists
    const timeoutId = this.timeouts.get(notificationId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.timeouts.delete(notificationId);
    }
    
    // Mark as read (removes from display)
    this.notificationService.markAsRead(notificationId);
  }

  getIcon(type: string): string {
    switch (type) {
      case 'error':
        return 'error';
      case 'success':
        return 'check_circle';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'notifications';
    }
  }
}