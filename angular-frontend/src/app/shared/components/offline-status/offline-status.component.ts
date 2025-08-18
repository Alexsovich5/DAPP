import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatBadgeModule } from '@angular/material/badge';
import { OfflineService, SyncStatus } from '../../../core/services/offline.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-offline-status',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatSnackBarModule,
    MatProgressBarModule,
    MatBadgeModule
  ],
  template: `
    <div class="offline-status-container" [class.expanded]="showDetails">
      <!-- Connection Status Indicator -->
      <div class="connection-indicator" 
           [class.online]="syncStatus.isOnline"
           [class.offline]="!syncStatus.isOnline"
           [class.syncing]="syncStatus.isSyncing"
           (click)="toggleDetails()">
        
        <!-- Online Status -->
        <div *ngIf="syncStatus.isOnline && !syncStatus.isSyncing" class="status-content">
          <mat-icon class="status-icon online-icon">wifi</mat-icon>
          <span class="status-text">Online</span>
        </div>
        
        <!-- Offline Status -->
        <div *ngIf="!syncStatus.isOnline && !syncStatus.isSyncing" class="status-content">
          <mat-icon class="status-icon offline-icon">wifi_off</mat-icon>
          <span class="status-text">Offline</span>
          <mat-icon class="pending-badge" 
                   *ngIf="syncStatus.pendingActions > 0"
                   [matBadge]="syncStatus.pendingActions.toString()"
                   matBadgeColor="warn"
                   matBadgeSize="small">
            schedule
          </mat-icon>
        </div>
        
        <!-- Syncing Status -->
        <div *ngIf="syncStatus.isSyncing" class="status-content">
          <mat-icon class="status-icon syncing-icon spinning">sync</mat-icon>
          <span class="status-text">Syncing...</span>
        </div>
        
        <!-- Expand/Collapse Indicator -->
        <mat-icon class="expand-icon" [class.expanded]="showDetails">
          {{ showDetails ? 'expand_less' : 'expand_more' }}
        </mat-icon>
      </div>
      
      <!-- Detailed Status (expandable) -->
      <div class="status-details" *ngIf="showDetails">
        <div class="details-content">
          
          <!-- Connection Info -->
          <div class="detail-section">
            <h4>Connection Status</h4>
            <div class="detail-item">
              <mat-icon>{{ syncStatus.isOnline ? 'check_circle' : 'error' }}</mat-icon>
              <span>{{ syncStatus.isOnline ? 'Connected to internet' : 'No internet connection' }}</span>
            </div>
            <div class="detail-item" *ngIf="syncStatus.lastSyncTime">
              <mat-icon>schedule</mat-icon>
              <span>Last sync: {{ formatSyncTime(syncStatus.lastSyncTime) }}</span>
            </div>
          </div>
          
          <!-- Pending Actions -->
          <div class="detail-section" *ngIf="syncStatus.pendingActions > 0">
            <h4>Pending Actions</h4>
            <div class="detail-item">
              <mat-icon>pending_actions</mat-icon>
              <span>{{ syncStatus.pendingActions }} actions waiting to sync</span>
            </div>
            <div class="pending-actions-list">
              <div class="pending-item" *ngFor="let action of getPendingActionsSummary()">
                <mat-icon>{{ getActionIcon(action.type) }}</mat-icon>
                <span>{{ getActionDescription(action.type) }}</span>
                <span class="action-count">{{ action.count }}</span>
              </div>
            </div>
          </div>
          
          <!-- Sync Error -->
          <div class="detail-section" *ngIf="syncStatus.syncError">
            <h4>Sync Issues</h4>
            <div class="detail-item error">
              <mat-icon>error</mat-icon>
              <span>{{ syncStatus.syncError }}</span>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="detail-actions">
            <button mat-stroked-button 
                    (click)="forceSyncNow()"
                    [disabled]="!syncStatus.isOnline || syncStatus.isSyncing">
              <mat-icon>sync</mat-icon>
              Sync Now
            </button>
            
            <button mat-stroked-button 
                    (click)="clearPendingActions()"
                    [disabled]="syncStatus.pendingActions === 0"
                    color="warn">
              <mat-icon>clear_all</mat-icon>
              Clear Queue
            </button>
            
            <button mat-stroked-button (click)="showCacheInfo()">
              <mat-icon>storage</mat-icon>
              Cache Info
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .offline-status-container {
      position: fixed;
      top: 1rem;
      right: 1rem;
      z-index: 1000;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
      overflow: hidden;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      min-width: 120px;
    }

    .offline-status-container.expanded {
      min-width: 320px;
      max-width: 400px;
    }

    .connection-indicator {
      padding: 0.75rem 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      transition: all 0.2s ease;
      user-select: none;
    }

    .connection-indicator:hover {
      background: rgba(0, 0, 0, 0.05);
    }

    .connection-indicator.online {
      border-left: 4px solid #4caf50;
    }

    .connection-indicator.offline {
      border-left: 4px solid #f44336;
    }

    .connection-indicator.syncing {
      border-left: 4px solid #2196f3;
    }

    .status-content {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex: 1;
    }

    .status-icon {
      font-size: 1.2rem;
      width: 1.2rem;
      height: 1.2rem;
    }

    .online-icon {
      color: #4caf50;
    }

    .offline-icon {
      color: #f44336;
    }

    .syncing-icon {
      color: #2196f3;
    }

    .spinning {
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    .status-text {
      font-size: 0.9rem;
      font-weight: 500;
      color: #333;
    }

    .pending-badge {
      margin-left: auto;
    }

    .expand-icon {
      font-size: 1rem;
      width: 1rem;
      height: 1rem;
      color: #666;
      transition: transform 0.2s ease;
    }

    .expand-icon.expanded {
      transform: rotate(180deg);
    }

    .status-details {
      border-top: 1px solid #e0e0e0;
      background: rgba(248, 249, 250, 0.8);
      animation: slideDown 0.3s ease-out;
    }

    @keyframes slideDown {
      from {
        max-height: 0;
        opacity: 0;
      }
      to {
        max-height: 500px;
        opacity: 1;
      }
    }

    .details-content {
      padding: 1rem;
    }

    .detail-section {
      margin-bottom: 1.5rem;
    }

    .detail-section:last-child {
      margin-bottom: 0;
    }

    .detail-section h4 {
      font-size: 0.85rem;
      font-weight: 600;
      color: #333;
      margin: 0 0 0.75rem 0;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .detail-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.5rem;
      font-size: 0.85rem;
      color: #555;
    }

    .detail-item.error {
      color: #f44336;
    }

    .detail-item mat-icon {
      font-size: 1rem;
      width: 1rem;
      height: 1rem;
      color: #666;
    }

    .detail-item.error mat-icon {
      color: #f44336;
    }

    .pending-actions-list {
      margin-top: 0.5rem;
      padding-left: 1.5rem;
    }

    .pending-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.25rem;
      font-size: 0.8rem;
      color: #666;
    }

    .pending-item mat-icon {
      font-size: 0.9rem;
      width: 0.9rem;
      height: 0.9rem;
      color: #888;
    }

    .action-count {
      margin-left: auto;
      background: #e3f2fd;
      color: #1976d2;
      padding: 0.1rem 0.4rem;
      border-radius: 10px;
      font-size: 0.7rem;
      font-weight: 600;
      min-width: 1.2rem;
      text-align: center;
    }

    .detail-actions {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid #e0e0e0;
    }

    .detail-actions button {
      font-size: 0.8rem;
      height: 32px;
      text-transform: none;
    }

    .detail-actions button mat-icon {
      font-size: 1rem;
      width: 1rem;
      height: 1rem;
      margin-right: 0.5rem;
    }

    /* Mobile optimizations */
    @media (max-width: 768px) {
      .offline-status-container {
        top: 0.5rem;
        right: 0.5rem;
        left: 0.5rem;
        min-width: auto;
      }

      .offline-status-container.expanded {
        min-width: auto;
        max-width: none;
      }

      .details-content {
        padding: 0.75rem;
      }

      .detail-actions {
        flex-direction: row;
        flex-wrap: wrap;
      }

      .detail-actions button {
        flex: 1;
        min-width: 100px;
      }
    }

    /* Dark theme support */
    .dark-theme .offline-status-container {
      background: rgba(33, 33, 33, 0.95);
      color: #e0e0e0;
    }

    .dark-theme .status-text {
      color: #e0e0e0;
    }

    .dark-theme .status-details {
      background: rgba(48, 48, 48, 0.8);
      border-top-color: #444;
    }

    .dark-theme .detail-section h4 {
      color: #e0e0e0;
    }

    .dark-theme .detail-item {
      color: #bbb;
    }

    .dark-theme .detail-actions {
      border-top-color: #444;
    }

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
      .offline-status-container,
      .connection-indicator,
      .expand-icon,
      .spinning {
        transition: none !important;
        animation: none !important;
      }

      .status-details {
        animation: none !important;
      }
    }
  `]
})
export class OfflineStatusComponent implements OnInit, OnDestroy {
  syncStatus: SyncStatus = {
    isOnline: navigator.onLine,
    isSyncing: false,
    pendingActions: 0
  };

  showDetails = false;
  private destroy$ = new Subject<void>();

  constructor(private offlineService: OfflineService) {}

  ngOnInit(): void {
    // Subscribe to sync status updates
    this.offlineService.syncStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        this.syncStatus = status;
      });

    // Auto-show details when there are pending actions or errors
    this.offlineService.syncStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        if ((status.pendingActions > 0 || status.syncError) && !this.showDetails) {
          this.showDetails = true;
          
          // Auto-hide after 5 seconds if no issues
          setTimeout(() => {
            if (status.pendingActions === 0 && !status.syncError) {
              this.showDetails = false;
            }
          }, 5000);
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  toggleDetails(): void {
    this.showDetails = !this.showDetails;
  }

  formatSyncTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    
    if (minutes < 1) {
      return 'Just now';
    } else if (minutes < 60) {
      return `${minutes}m ago`;
    } else {
      const hours = Math.floor(minutes / 60);
      return `${hours}h ago`;
    }
  }

  getPendingActionsSummary(): Array<{type: string, count: number}> {
    // This would get actual pending actions from the service
    // For now, return mock data based on queue status
    const queueStatus = this.offlineService.getQueueStatus();
    
    if (queueStatus.pending === 0) {
      return [];
    }

    // Mock distribution of action types
    return [
      { type: 'connection_request', count: Math.ceil(queueStatus.pending * 0.4) },
      { type: 'message_send', count: Math.ceil(queueStatus.pending * 0.4) },
      { type: 'profile_update', count: Math.ceil(queueStatus.pending * 0.2) }
    ].filter(action => action.count > 0);
  }

  getActionIcon(type: string): string {
    const iconMap: Record<string, string> = {
      'connection_request': 'favorite',
      'message_send': 'message',
      'profile_update': 'person',
      'discovery_interaction': 'explore'
    };
    return iconMap[type] || 'pending';
  }

  getActionDescription(type: string): string {
    const descriptionMap: Record<string, string> = {
      'connection_request': 'Connection requests',
      'message_send': 'Messages to send',
      'profile_update': 'Profile updates',
      'discovery_interaction': 'Discovery actions'
    };
    return descriptionMap[type] || 'Pending actions';
  }

  forceSyncNow(): void {
    if (this.syncStatus.isOnline && !this.syncStatus.isSyncing) {
      // The offline service will handle the actual sync
      // This just provides user feedback
      console.log('Forcing sync now...');
      
      // Show temporary feedback
      this.showSyncFeedback('Synchronizing your actions...');
    }
  }

  clearPendingActions(): void {
    if (confirm('Are you sure you want to clear all pending actions? This cannot be undone.')) {
      this.offlineService.clearQueue();
      this.showSyncFeedback('Pending actions cleared');
    }
  }

  showCacheInfo(): void {
    // Show cache information in a modal or navigate to settings
    console.log('Show cache info');
    this.showSyncFeedback('Cache info coming soon...');
  }

  private showSyncFeedback(message: string): void {
    // Create a temporary status message
    const statusElement = document.createElement('div');
    statusElement.textContent = message;
    statusElement.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 1rem 2rem;
      border-radius: 8px;
      z-index: 10000;
      font-size: 0.9rem;
    `;
    
    document.body.appendChild(statusElement);
    
    setTimeout(() => {
      document.body.removeChild(statusElement);
    }, 2000);
  }
}