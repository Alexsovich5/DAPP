import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable, Subject, combineLatest } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';
import { WebSocketPoolService } from '../../../core/services/websocket-pool.service';
import { SoulConnectionRealtimeService } from '../../../core/services/soul-connection-realtime.service';

export interface ConnectionStatusInfo {
  isConnected: boolean;
  health: string;
  connectionCount: number;
  activeConnections: number;
  onlineUsers: number;
}

@Component({
  selector: 'app-websocket-status',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="websocket-status"
      [ngClass]="statusInfo?.health"
      [attr.aria-label]="getStatusAriaLabel()"
      [attr.title]="getStatusTooltip()"
    >
      <div class="status-indicator" [ngClass]="statusInfo?.health">
        <div class="status-dot" [class.pulsing]="statusInfo?.isConnected"></div>
      </div>

      <div class="status-text" *ngIf="showText">
        <span class="connection-status">{{getStatusText()}}</span>
        <div class="status-details" *ngIf="showDetails && statusInfo">
          <small>
            {{statusInfo.connectionCount}} connections,
            {{statusInfo.onlineUsers}} users online
          </small>
        </div>
      </div>

      <!-- Compact metrics for minimal display -->
      <div class="status-metrics" *ngIf="showMetrics && statusInfo">
        <span class="metric-item">
          <span class="metric-value">{{statusInfo.connectionCount}}</span>
          <span class="metric-label">WS</span>
        </span>
        <span class="metric-item">
          <span class="metric-value">{{statusInfo.onlineUsers}}</span>
          <span class="metric-label">👥</span>
        </span>
      </div>
    </div>
  `,
  styles: [`
    .websocket-status {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.25rem 0.5rem;
      border-radius: 0.375rem;
      background: var(--surface-color, #f9fafb);
      border: 1px solid var(--border-color, #e5e7eb);
      transition: all 0.3s ease;
    }

    .status-indicator {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      transition: all 0.3s ease;
      background: var(--status-color, #6b7280);
    }

    .status-dot.pulsing {
      animation: pulse 2s ease-in-out infinite;
    }

    .status-text {
      display: flex;
      flex-direction: column;
      gap: 0.125rem;
    }

    .connection-status {
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--text-primary, #111827);
    }

    .status-details {
      font-size: 0.625rem;
      color: var(--text-secondary, #6b7280);
    }

    .status-metrics {
      display: flex;
      gap: 0.5rem;
      margin-left: auto;
    }

    .metric-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.125rem;
    }

    .metric-value {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-primary, #111827);
    }

    .metric-label {
      font-size: 0.625rem;
      color: var(--text-secondary, #6b7280);
    }

    /* Health-based styling */
    .websocket-status.excellent {
      --status-color: #10b981;
      background: var(--success-bg, #ecfdf5);
      border-color: var(--success-border, #d1fae5);
    }

    .websocket-status.good {
      --status-color: #f59e0b;
      background: var(--warning-bg, #fffbeb);
      border-color: var(--warning-border, #fed7aa);
    }

    .websocket-status.poor {
      --status-color: #ef4444;
      background: var(--error-bg, #fef2f2);
      border-color: var(--error-border, #fecaca);
    }

    .websocket-status.disconnected {
      --status-color: #6b7280;
      background: var(--gray-bg, #f9fafb);
      border-color: var(--gray-border, #e5e7eb);
    }

    /* Responsive design */
    @media (max-width: 640px) {
      .websocket-status {
        padding: 0.25rem;
        gap: 0.375rem;
      }

      .status-text {
        display: none;
      }

      .status-metrics {
        margin-left: 0.25rem;
      }
    }

    /* Dark theme */
    .dark-theme .websocket-status {
      background: var(--surface-dark, #1f2937);
      border-color: var(--border-dark, #374151);
    }

    .dark-theme .connection-status {
      color: var(--text-primary-dark, #f9fafb);
    }

    .dark-theme .status-details,
    .dark-theme .metric-label {
      color: var(--text-secondary-dark, #9ca3af);
    }

    .dark-theme .metric-value {
      color: var(--text-primary-dark, #f9fafb);
    }

    /* Animation keyframes */
    @keyframes pulse {
      0%, 100% {
        opacity: 1;
        transform: scale(1);
      }
      50% {
        opacity: 0.7;
        transform: scale(1.2);
      }
    }

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
      .status-dot,
      .websocket-status {
        animation: none !important;
        transition: none !important;
      }
    }
  `]
})
export class WebSocketStatusComponent implements OnInit, OnDestroy {
  @Input() showText: boolean = true;
  @Input() showDetails: boolean = false;
  @Input() showMetrics: boolean = false;
  @Input() compact: boolean = false;

  statusInfo$: Observable<ConnectionStatusInfo>;
  statusInfo: ConnectionStatusInfo | null = null;

  private destroy$ = new Subject<void>();

  constructor(
    private wsPool: WebSocketPoolService,
    private soulRealtime: SoulConnectionRealtimeService
  ) {
    this.statusInfo$ = combineLatest([
      this.soulRealtime.getConnectionStatus(),
      this.soulRealtime.getConnectionHealth(),
      this.wsPool.getConnectionCount(),
      this.soulRealtime.getActiveConnections(),
      this.soulRealtime.getUserPresence()
    ]).pipe(
      map(([isConnected, health, connectionCount, activeConnections, userPresence]) => ({
        isConnected,
        health,
        connectionCount,
        activeConnections: activeConnections.length,
        onlineUsers: Array.from(userPresence.values())
          .filter(p => p.status === 'online').length
      }))
    );
  }

  ngOnInit(): void {
    // Adjust display based on compact mode
    if (this.compact) {
      this.showText = false;
      this.showDetails = false;
      this.showMetrics = true;
    }

    // Subscribe to status updates
    this.statusInfo$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(statusInfo => {
      this.statusInfo = statusInfo;
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  getStatusText(): string {
    if (!this.statusInfo) return 'Connecting...';

    if (!this.statusInfo.isConnected) {
      return 'Disconnected';
    }

    switch (this.statusInfo.health) {
      case 'excellent': return 'Excellent';
      case 'good': return 'Good';
      case 'poor': return 'Poor';
      default: return 'Connected';
    }
  }

  getStatusAriaLabel(): string {
    if (!this.statusInfo) {
      return 'WebSocket connection status: connecting';
    }

    const connectionText = this.statusInfo.isConnected ? 'connected' : 'disconnected';
    const healthText = this.statusInfo.health;

    return `WebSocket connection status: ${connectionText}, health: ${healthText}, ${this.statusInfo.connectionCount} connections, ${this.statusInfo.onlineUsers} users online`;
  }

  getStatusTooltip(): string {
    if (!this.statusInfo) {
      return 'Real-time connection status';
    }

    const lines = [
      `Status: ${this.statusInfo.isConnected ? 'Connected' : 'Disconnected'}`,
      `Health: ${this.statusInfo.health}`,
      `Connections: ${this.statusInfo.connectionCount}`,
      `Active Soul Connections: ${this.statusInfo.activeConnections}`,
      `Online Users: ${this.statusInfo.onlineUsers}`
    ];

    return lines.join('\n');
  }
}
