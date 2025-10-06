import { Injectable, OnDestroy } from '@angular/core';
import { Observable, Subject, BehaviorSubject, fromEvent } from 'rxjs';
import { filter, tap, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { WebSocketPoolService, WebSocketMessage } from './websocket-pool.service';
import { ScreenReaderService } from './screen-reader.service';

export interface SoulConnectionUpdate {
  connectionId: string;
  type: 'compatibility_change' | 'energy_sync' | 'revelation_shared' | 'state_change' | 'match_found';
  data: Record<string, unknown>;
  timestamp: number;
  userId?: string;
  soulData?: Record<string, unknown>;
}

export interface EnergySync {
  leftSoulEnergy: number;
  rightSoulEnergy: number;
  connectionStrength: number;
  pulseRate: number;
  syncQuality: 'poor' | 'good' | 'excellent' | 'perfect';
}

export interface CompatibilityUpdate {
  connectionId: string;
  newScore: number;
  previousScore: number;
  breakdown: {
    values: number;
    interests: number;
    communication: number;
    lifestyle?: number;
    goals?: number;
  };
  factors: string[];
}

export interface RevelationNotification {
  connectionId: string;
  senderId: string;
  senderName: string;
  day: number;
  type: 'shared' | 'received' | 'mutual_complete';
  preview?: string;
}

export interface PresenceUpdate {
  userId: string;
  status: 'online' | 'offline' | 'away' | 'typing';
  lastSeen?: number;
  currentActivity?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SoulConnectionRealtimeService implements OnDestroy {
  private destroy$ = new Subject<void>();

  // Real-time observables
  private compatibilityUpdates$ = new Subject<CompatibilityUpdate>();
  private energySyncs$ = new Subject<EnergySync>();
  private revelationNotifications$ = new Subject<RevelationNotification>();
  private presenceUpdates$ = new Subject<PresenceUpdate>();
  private connectionStateChanges$ = new Subject<SoulConnectionUpdate>();

  // Current state tracking
  private activeConnections$ = new BehaviorSubject<string[]>([]);
  private userPresence$ = new BehaviorSubject<Map<string, PresenceUpdate>>(new Map());
  private connectionStates$ = new BehaviorSubject<Map<string, unknown>>(new Map());

  // Connection monitoring
  private isConnected$ = new BehaviorSubject<boolean>(false);
  private connectionHealth$ = new BehaviorSubject<'excellent' | 'good' | 'poor' | 'disconnected'>('disconnected');

  constructor(
    private wsPool: WebSocketPoolService,
    private screenReader: ScreenReaderService
  ) {
    this.initializeRealtimeConnections();
    this.setupPresenceMonitoring();
    this.setupConnectionHealthMonitoring();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Subscribe to compatibility score updates for a connection
   */
  subscribeToCompatibilityUpdates(connectionId: string): Observable<CompatibilityUpdate> {
    this.subscribeToConnectionChannel(connectionId);

    return this.compatibilityUpdates$.pipe(
      filter(update => update.connectionId === connectionId),
      distinctUntilChanged((a, b) => a.newScore === b.newScore),
      tap(update => this.announceCompatibilityChange(update)),
      takeUntil(this.destroy$)
    );
  }

  /**
   * Subscribe to real-time energy synchronization
   */
  subscribeToEnergySync(connectionId: string): Observable<EnergySync> {
    this.subscribeToConnectionChannel(connectionId);

    return this.energySyncs$.pipe(
      filter(sync => sync.connectionStrength > 0),
      distinctUntilChanged((a, b) =>
        a.leftSoulEnergy === b.leftSoulEnergy &&
        a.rightSoulEnergy === b.rightSoulEnergy
      ),
      takeUntil(this.destroy$)
    );
  }

  /**
   * Subscribe to revelation notifications
   */
  subscribeToRevelationNotifications(connectionId: string): Observable<RevelationNotification> {
    this.subscribeToConnectionChannel(connectionId);

    return this.revelationNotifications$.pipe(
      filter(notification => notification.connectionId === connectionId),
      tap(notification => this.announceRevelationUpdate(notification)),
      takeUntil(this.destroy$)
    );
  }

  /**
   * Subscribe to user presence updates
   */
  subscribeToPresenceUpdates(userIds: string[]): Observable<PresenceUpdate> {
    // Subscribe to presence channel
    this.wsPool.subscribeToChannel('user_presence').subscribe();

    return this.presenceUpdates$.pipe(
      filter(update => userIds.includes(update.userId)),
      tap(update => this.updateUserPresence(update)),
      takeUntil(this.destroy$)
    );
  }

  /**
   * Subscribe to connection state changes
   */
  subscribeToConnectionStateChanges(connectionId: string): Observable<SoulConnectionUpdate> {
    this.subscribeToConnectionChannel(connectionId);

    return this.connectionStateChanges$.pipe(
      filter(update => update.connectionId === connectionId),
      tap(update => this.announceConnectionStateChange(update)),
      takeUntil(this.destroy$)
    );
  }

  /**
   * Send energy pulse update
   */
  sendEnergyPulse(connectionId: string, energyLevel: number, soulType: 'left' | 'right'): void {
    const message: WebSocketMessage = {
      type: 'energy_pulse',
      channel: `connection_${connectionId}`,
      data: {
        connectionId,
        soulType,
        energyLevel,
        timestamp: Date.now()
      }
    };

    this.wsPool.broadcastToChannel(`connection_${connectionId}`, message);
  }

  /**
   * Send typing indicator
   */
  sendTypingIndicator(connectionId: string, isTyping: boolean): void {
    const message: WebSocketMessage = {
      type: 'typing_indicator',
      channel: `connection_${connectionId}`,
      data: {
        connectionId,
        isTyping,
        timestamp: Date.now()
      }
    };

    this.wsPool.broadcastToChannel(`connection_${connectionId}`, message);
  }

  /**
   * Send revelation progress update
   */
  sendRevelationProgress(connectionId: string, day: number, completed: boolean): void {
    const message: WebSocketMessage = {
      type: 'revelation_progress',
      channel: `connection_${connectionId}`,
      data: {
        connectionId,
        day,
        completed,
        timestamp: Date.now()
      }
    };

    this.wsPool.broadcastToChannel(`connection_${connectionId}`, message);
  }

  /**
   * Get current connection health
   */
  getConnectionHealth(): Observable<string> {
    return this.connectionHealth$.asObservable();
  }

  /**
   * Get real-time connection status
   */
  getConnectionStatus(): Observable<boolean> {
    return this.isConnected$.asObservable();
  }

  /**
   * Get active connections
   */
  getActiveConnections(): Observable<string[]> {
    return this.activeConnections$.asObservable();
  }

  /**
   * Get user presence map
   */
  getUserPresence(): Observable<Map<string, PresenceUpdate>> {
    return this.userPresence$.asObservable();
  }

  /**
   * Force reconnection to real-time services
   */
  reconnectRealtime(): void {
    this.wsPool.closeAllConnections();
    setTimeout(() => {
      this.initializeRealtimeConnections();
    }, 1000);
  }

  /**
   * Get real-time statistics
   */
  getRealtimeStatistics() {
    const wsStats = this.wsPool.getPoolStatistics();

    return {
      ...wsStats,
      activeConnections: this.activeConnections$.value.length,
      onlineUsers: Array.from(this.userPresence$.value.values())
        .filter(p => p.status === 'online').length,
      connectionHealth: this.connectionHealth$.value,
      isConnected: this.isConnected$.value
    };
  }

  private initializeRealtimeConnections(): void {
    // Subscribe to global soul connection events
    this.wsPool.subscribeToChannel('soul_connections').pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (message) => this.handleGlobalSoulMessage(message),
      error: (error) => console.error('Soul connections channel error:', error)
    });

    // Subscribe to compatibility updates
    this.wsPool.subscribeToChannel('compatibility_updates').pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (message) => this.handleCompatibilityMessage(message),
      error: (error) => console.error('Compatibility updates channel error:', error)
    });

    // Subscribe to revelation updates
    this.wsPool.subscribeToChannel('revelation_updates').pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (message) => this.handleRevelationMessage(message),
      error: (error) => console.error('Revelation updates channel error:', error)
    });

    // Monitor connection status
    this.wsPool.getConnectionStatus().pipe(
      takeUntil(this.destroy$)
    ).subscribe(statusMap => {
      const hasConnected = Array.from(statusMap.values()).some(status => status === 'connected');
      this.isConnected$.next(hasConnected);
    });
  }

  private subscribeToConnectionChannel(connectionId: string): void {
    const channel = `connection_${connectionId}`;

    this.wsPool.subscribeToChannel(channel).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (message) => this.handleConnectionMessage(message),
      error: (error) => console.error(`Connection ${connectionId} channel error:`, error)
    });

    // Add to active connections
    const current = this.activeConnections$.value;
    if (!current.includes(connectionId)) {
      this.activeConnections$.next([...current, connectionId]);
    }
  }

  private handleGlobalSoulMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'new_match':
        this.screenReader.announce(
          `New soul match found! Check your connections to see your latest match.`,
          'assertive',
          'new-match'
        );
        break;

      case 'compatibility_update':
        this.compatibilityUpdates$.next(message.data as CompatibilityUpdate);
        break;

      case 'energy_sync':
        this.energySyncs$.next(message.data as EnergySync);
        break;

      case 'connection_state_change':
        this.connectionStateChanges$.next(message.data as SoulConnectionUpdate);
        break;
    }
  }

  private handleCompatibilityMessage(message: WebSocketMessage): void {
    if (message.type === 'compatibility_change') {
      this.compatibilityUpdates$.next(message.data as CompatibilityUpdate);
    }
  }

  private handleRevelationMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'revelation_shared':
      case 'revelation_received':
      case 'revelation_mutual_complete':
        this.revelationNotifications$.next(message.data as RevelationNotification);
        break;
    }
  }

  private handleConnectionMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'energy_pulse':
        this.energySyncs$.next(message.data as EnergySync);
        break;

      case 'typing_indicator':
        this.presenceUpdates$.next({
          userId: message.data['userId'] as string,
          status: message.data['isTyping'] ? 'typing' : 'online',
          lastSeen: Date.now()
        });
        break;

      case 'revelation_progress':
        this.revelationNotifications$.next(message.data as RevelationNotification);
        break;
    }
  }

  private setupPresenceMonitoring(): void {
    // Update user presence every 30 seconds
    setInterval(() => {
      this.wsPool.broadcastToChannel('user_presence', {
        type: 'presence_update',
        data: {
          status: 'online',
          timestamp: Date.now(),
          activity: this.getCurrentActivity()
        }
      });
    }, 30000);

    // Monitor page visibility for presence updates
    if (typeof document !== 'undefined') {
      fromEvent(document, 'visibilitychange').pipe(
        takeUntil(this.destroy$)
      ).subscribe(() => {
        const status = document.hidden ? 'away' : 'online';
        this.updatePresenceStatus(status);
      });
    }
  }

  private setupConnectionHealthMonitoring(): void {
    // Monitor WebSocket pool health
    this.wsPool.getConnectionCount().pipe(
      debounceTime(1000),
      takeUntil(this.destroy$)
    ).subscribe(count => {
      if (count === 0) {
        this.connectionHealth$.next('disconnected');
      } else {
        const stats = this.wsPool.getPoolStatistics();
        const healthRatio = stats.connectedCount / stats.totalConnections;

        if (healthRatio >= 0.9) {
          this.connectionHealth$.next('excellent');
        } else if (healthRatio >= 0.7) {
          this.connectionHealth$.next('good');
        } else {
          this.connectionHealth$.next('poor');
        }
      }
    });
  }

  private updateUserPresence(update: PresenceUpdate): void {
    const current = this.userPresence$.value;
    current.set(update.userId, update);
    this.userPresence$.next(new Map(current));
  }

  private updatePresenceStatus(status: 'online' | 'away' | 'offline'): void {
    this.wsPool.broadcastToChannel('user_presence', {
      type: 'presence_update',
      data: {
        status,
        timestamp: Date.now(),
        activity: status === 'online' ? this.getCurrentActivity() : undefined
      }
    });
  }

  private getCurrentActivity(): string {
    if (typeof window === 'undefined') return 'unknown';

    const path = window.location.pathname;

    if (path.includes('/discover')) return 'discovering souls';
    if (path.includes('/revelations')) return 'sharing revelations';
    if (path.includes('/connections')) return 'viewing connections';
    if (path.includes('/messages')) return 'messaging';
    if (path.includes('/profile')) return 'updating profile';

    return 'exploring';
  }

  private announceCompatibilityChange(update: CompatibilityUpdate): void {
    const scoreDiff = update.newScore - update.previousScore;
    const direction = scoreDiff > 0 ? 'increased' : 'decreased';

    this.screenReader.announce(
      `Compatibility ${direction} to ${update.newScore}% (${scoreDiff > 0 ? '+' : ''}${scoreDiff}%)`,
      'polite',
      'compatibility-update'
    );
  }

  private announceRevelationUpdate(notification: RevelationNotification): void {
    let message = '';

    switch (notification.type) {
      case 'shared':
        message = `Your day ${notification.day} revelation has been shared`;
        break;
      case 'received':
        message = `${notification.senderName} shared their day ${notification.day} revelation`;
        break;
      case 'mutual_complete':
        message = `Both revelations for day ${notification.day} are now complete`;
        break;
    }

    this.screenReader.announce(message, 'assertive', 'revelation-update');
  }

  private announceConnectionStateChange(update: SoulConnectionUpdate): void {
    const stateMessages = {
      'compatibility_change': 'Soul compatibility has been updated',
      'energy_sync': 'Soul energies are synchronizing',
      'revelation_shared': 'New revelation has been shared',
      'state_change': 'Connection state has changed',
      'match_found': 'New soul match has been discovered'
    };

    const message = stateMessages[update.type] || 'Connection update received';
    this.screenReader.announce(message, 'polite', 'connection-state-change');
  }
}
