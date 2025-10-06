import { Injectable, OnDestroy } from '@angular/core';
import { Observable, BehaviorSubject, Subject, of, timer } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import {
  retryWhen,
  delay,
  tap,
  filter,
  takeUntil
} from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface WebSocketMessage {
  type: string;
  channel?: string;
  data: Record<string, unknown>;
  timestamp?: number;
  userId?: string;
  connectionId?: string;
}

export interface WebSocketConnection {
  id: string;
  url: string;
  subject: WebSocketSubject<WebSocketMessage>;
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  reconnectAttempts: number;
  lastHeartbeat: number;
  channels: Set<string>;
  subscribers: number;
}

export interface WebSocketPoolConfig {
  maxConnections: number;
  maxReconnectAttempts: number;
  reconnectInterval: number;
  heartbeatInterval: number;
  connectionTimeout: number;
  messageQueueSize: number;
}

export interface ChannelSubscription {
  channel: string;
  connectionId: string;
  observer: Subject<WebSocketMessage>;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketPoolService implements OnDestroy {
  private connections = new Map<string, WebSocketConnection>();
  private channelSubscriptions = new Map<string, ChannelSubscription[]>();
  private messageQueue = new Map<string, WebSocketMessage[]>();
  private destroy$ = new Subject<void>();

  private connectionStatus$ = new BehaviorSubject<Map<string, string>>(new Map());
  private globalConnectionCount$ = new BehaviorSubject<number>(0);

  private config: WebSocketPoolConfig = {
    maxConnections: 5,
    maxReconnectAttempts: 5,
    reconnectInterval: 3000,
    heartbeatInterval: 30000,
    connectionTimeout: 10000,
    messageQueueSize: 100
  };

  constructor() {
    this.startHeartbeatMonitoring();
    this.startConnectionCleanup();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.closeAllConnections();
  }

  /**
   * Get or create a WebSocket connection
   */
  getConnection(url: string, channels: string[] = []): Observable<WebSocketConnection> {
    const connectionId = this.generateConnectionId(url);

    if (this.connections.has(connectionId)) {
      const connection = this.connections.get(connectionId)!;
      this.addChannelsToConnection(connection, channels);
      return of(connection);
    }

    if (this.connections.size >= this.config.maxConnections) {
      return this.reuseExistingConnection(url, channels);
    }

    return this.createConnection(url, channels);
  }

  /**
   * Subscribe to specific channels across connections
   */
  subscribeToChannel(channel: string, connectionUrl?: string): Observable<WebSocketMessage> {
    const subject = new Subject<WebSocketMessage>();

    // Use existing connection or create new one
    const connectionObs = connectionUrl ?
      this.getConnection(connectionUrl, [channel]) :
      this.getBestConnectionForChannel(channel);

    connectionObs.subscribe(connection => {
      this.addChannelSubscription(channel, connection.id, subject);

      // Send channel subscription message
      this.sendMessage(connection.id, {
        type: 'subscribe',
        channel: channel,
        timestamp: Date.now()
      });
    });

    return subject.asObservable().pipe(
      takeUntil(this.destroy$)
    );
  }

  /**
   * Send message through specific connection
   */
  sendMessage(connectionId: string, message: WebSocketMessage): boolean {
    const connection = this.connections.get(connectionId);

    if (!connection) {
      console.warn(`WebSocket connection ${connectionId} not found`);
      return false;
    }

    if (connection.status !== 'connected') {
      this.queueMessage(connectionId, message);
      return false;
    }

    try {
      message.timestamp = message.timestamp || Date.now();
      connection.subject.next(message);
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      this.handleConnectionError(connectionId, error);
      return false;
    }
  }

  /**
   * Broadcast message to all connections with specific channel
   */
  broadcastToChannel(channel: string, message: WebSocketMessage): number {
    let sentCount = 0;

    for (const [connectionId, connection] of this.connections) {
      if (connection.channels.has(channel)) {
        if (this.sendMessage(connectionId, { ...message, channel })) {
          sentCount++;
        }
      }
    }

    return sentCount;
  }

  /**
   * Get connection status observable
   */
  getConnectionStatus(): Observable<Map<string, string>> {
    return this.connectionStatus$.asObservable();
  }

  /**
   * Get global connection count
   */
  getConnectionCount(): Observable<number> {
    return this.globalConnectionCount$.asObservable();
  }

  /**
   * Close specific connection
   */
  closeConnection(connectionId: string): void {
    const connection = this.connections.get(connectionId);

    if (connection) {
      connection.subject.complete();
      this.connections.delete(connectionId);
      this.cleanupChannelSubscriptions(connectionId);
      this.updateConnectionStatus();
    }
  }

  /**
   * Close all connections
   */
  closeAllConnections(): void {
    for (const [connectionId] of this.connections) {
      this.closeConnection(connectionId);
    }
  }

  /**
   * Get connection pool statistics
   */
  getPoolStatistics() {
    const stats = {
      totalConnections: this.connections.size,
      connectedCount: 0,
      connectingCount: 0,
      errorCount: 0,
      totalChannels: 0,
      totalSubscribers: 0,
      queuedMessages: 0
    };

    for (const connection of this.connections.values()) {
      switch (connection.status) {
        case 'connected': stats.connectedCount++; break;
        case 'connecting': stats.connectingCount++; break;
        case 'error': stats.errorCount++; break;
      }

      stats.totalChannels += connection.channels.size;
      stats.totalSubscribers += connection.subscribers;
    }

    for (const queue of this.messageQueue.values()) {
      stats.queuedMessages += queue.length;
    }

    return stats;
  }

  private createConnection(url: string, channels: string[]): Observable<WebSocketConnection> {
    const connectionId = this.generateConnectionId(url);

    const wsSubject = webSocket<WebSocketMessage>({
      url: url,
      openObserver: {
        next: () => this.handleConnectionOpen(connectionId)
      },
      closeObserver: {
        next: () => this.handleConnectionClose(connectionId)
      }
    });

    const connection: WebSocketConnection = {
      id: connectionId,
      url: url,
      subject: wsSubject,
      status: 'connecting',
      reconnectAttempts: 0,
      lastHeartbeat: Date.now(),
      channels: new Set(channels),
      subscribers: 0
    };

    this.connections.set(connectionId, connection);
    this.setupConnectionHandlers(connection);
    this.updateConnectionStatus();

    return of(connection);
  }

  private setupConnectionHandlers(connection: WebSocketConnection): void {
    connection.subject.pipe(
      retryWhen(errors =>
        errors.pipe(
          tap(() => this.handleConnectionError(connection.id, 'Connection lost')),
          delay(this.config.reconnectInterval),
          filter(() => connection.reconnectAttempts < this.config.maxReconnectAttempts),
          tap(() => connection.reconnectAttempts++)
        )
      ),
      takeUntil(this.destroy$)
    ).subscribe({
      next: (message) => this.handleIncomingMessage(connection.id, message),
      error: (error) => this.handleConnectionError(connection.id, error),
      complete: () => this.handleConnectionClose(connection.id)
    });
  }

  private handleConnectionOpen(connectionId: string): void {
    const connection = this.connections.get(connectionId);

    if (connection) {
      connection.status = 'connected';
      connection.reconnectAttempts = 0;
      connection.lastHeartbeat = Date.now();

      // Send queued messages
      this.sendQueuedMessages(connectionId);

      // Subscribe to channels
      for (const channel of connection.channels) {
        this.sendMessage(connectionId, {
          type: 'subscribe',
          channel: channel,
          timestamp: Date.now()
        });
      }

      this.updateConnectionStatus();
    }
  }

  private handleConnectionClose(connectionId: string): void {
    const connection = this.connections.get(connectionId);

    if (connection) {
      connection.status = 'disconnected';
      this.updateConnectionStatus();

      // Attempt reconnection if under limit
      if (connection.reconnectAttempts < this.config.maxReconnectAttempts) {
        setTimeout(() => {
          this.attemptReconnection(connectionId);
        }, this.config.reconnectInterval);
      }
    }
  }

  private handleConnectionError(connectionId: string, error: unknown): void {
    const connection = this.connections.get(connectionId);

    if (connection) {
      connection.status = 'error';
      this.updateConnectionStatus();

      console.error(`WebSocket connection ${connectionId} error:`, error);
    }
  }

  private handleIncomingMessage(connectionId: string, message: WebSocketMessage): void {
    const connection = this.connections.get(connectionId);

    if (!connection) return;

    // Update heartbeat
    connection.lastHeartbeat = Date.now();

    // Handle system messages
    if (message.type === 'heartbeat') {
      this.sendMessage(connectionId, { type: 'heartbeat_ack', data: null });
      return;
    }

    // Route message to channel subscribers
    if (message.channel) {
      this.routeMessageToChannelSubscribers(message.channel, message);
    }

    // Route to all subscribers of this connection
    this.routeMessageToConnectionSubscribers(connectionId, message);
  }

  private routeMessageToChannelSubscribers(channel: string, message: WebSocketMessage): void {
    const subscriptions = this.channelSubscriptions.get(channel) || [];

    for (const subscription of subscriptions) {
      subscription.observer.next(message);
    }
  }

  private routeMessageToConnectionSubscribers(_connectionId: string, _message: WebSocketMessage): void {
    // This could be extended to support connection-level subscribers
    // For now, we rely on channel-based routing
  }

  private addChannelSubscription(channel: string, connectionId: string, observer: Subject<WebSocketMessage>): void {
    if (!this.channelSubscriptions.has(channel)) {
      this.channelSubscriptions.set(channel, []);
    }

    this.channelSubscriptions.get(channel)!.push({
      channel,
      connectionId,
      observer
    });

    // Increment subscriber count
    const connection = this.connections.get(connectionId);
    if (connection) {
      connection.subscribers++;
    }
  }

  private addChannelsToConnection(connection: WebSocketConnection, channels: string[]): void {
    for (const channel of channels) {
      if (!connection.channels.has(channel)) {
        connection.channels.add(channel);

        // Subscribe if connection is active
        if (connection.status === 'connected') {
          this.sendMessage(connection.id, {
            type: 'subscribe',
            channel: channel,
            timestamp: Date.now()
          });
        }
      }
    }
  }

  private reuseExistingConnection(url: string, channels: string[]): Observable<WebSocketConnection> {
    // Find connection with least load on same domain
    const domain = new URL(url).host;
    let bestConnection: WebSocketConnection | null = null;
    let lowestLoad = Infinity;

    for (const connection of this.connections.values()) {
      const connectionDomain = new URL(connection.url).host;

      if (connectionDomain === domain && connection.status === 'connected') {
        const load = connection.channels.size + connection.subscribers;

        if (load < lowestLoad) {
          lowestLoad = load;
          bestConnection = connection;
        }
      }
    }

    if (bestConnection) {
      this.addChannelsToConnection(bestConnection, channels);
      return of(bestConnection);
    }

    // Force create new connection by closing oldest one
    this.closeOldestConnection();
    return this.createConnection(url, channels);
  }

  private getBestConnectionForChannel(channel: string): Observable<WebSocketConnection> {
    // Check if channel already exists in a connection
    for (const connection of this.connections.values()) {
      if (connection.channels.has(channel) && connection.status === 'connected') {
        return of(connection);
      }
    }

    // Create new connection for this channel
    const wsUrl = this.buildWebSocketUrl();
    return this.getConnection(wsUrl, [channel]);
  }

  private buildWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = environment.production ?
      window.location.host :
      'localhost:5000';

    return `${protocol}//${host}/ws`;
  }

  private queueMessage(connectionId: string, message: WebSocketMessage): void {
    if (!this.messageQueue.has(connectionId)) {
      this.messageQueue.set(connectionId, []);
    }

    const queue = this.messageQueue.get(connectionId)!;

    // Limit queue size
    if (queue.length >= this.config.messageQueueSize) {
      queue.shift(); // Remove oldest message
    }

    queue.push(message);
  }

  private sendQueuedMessages(connectionId: string): void {
    const queue = this.messageQueue.get(connectionId);

    if (queue && queue.length > 0) {
      for (const message of queue) {
        this.sendMessage(connectionId, message);
      }

      this.messageQueue.set(connectionId, []);
    }
  }

  private attemptReconnection(connectionId: string): void {
    const connection = this.connections.get(connectionId);

    if (connection && connection.reconnectAttempts < this.config.maxReconnectAttempts) {
      connection.status = 'connecting';
      this.updateConnectionStatus();

      // Recreate the WebSocket subject
      connection.subject = webSocket<WebSocketMessage>({
        url: connection.url,
        openObserver: {
          next: () => this.handleConnectionOpen(connectionId)
        },
        closeObserver: {
          next: () => this.handleConnectionClose(connectionId)
        }
      });

      this.setupConnectionHandlers(connection);
    }
  }

  private closeOldestConnection(): void {
    let oldestConnection: WebSocketConnection | null = null;
    let oldestTime = Infinity;

    for (const connection of this.connections.values()) {
      if (connection.lastHeartbeat < oldestTime) {
        oldestTime = connection.lastHeartbeat;
        oldestConnection = connection;
      }
    }

    if (oldestConnection) {
      this.closeConnection(oldestConnection.id);
    }
  }

  private cleanupChannelSubscriptions(connectionId: string): void {
    for (const [channel, subscriptions] of this.channelSubscriptions) {
      const filtered = subscriptions.filter(sub => sub.connectionId !== connectionId);

      if (filtered.length === 0) {
        this.channelSubscriptions.delete(channel);
      } else {
        this.channelSubscriptions.set(channel, filtered);
      }
    }
  }

  private startHeartbeatMonitoring(): void {
    timer(0, this.config.heartbeatInterval).pipe(
      takeUntil(this.destroy$)
    ).subscribe(() => {
      this.checkConnectionHeartbeats();
    });
  }

  private checkConnectionHeartbeats(): void {
    const now = Date.now();
    const timeout = this.config.heartbeatInterval * 2; // Allow 2x interval

    for (const [connectionId, connection] of this.connections) {
      if (connection.status === 'connected' &&
          (now - connection.lastHeartbeat) > timeout) {

        console.warn(`Connection ${connectionId} heartbeat timeout`);
        this.handleConnectionError(connectionId, 'Heartbeat timeout');
      }
    }
  }

  private startConnectionCleanup(): void {
    timer(60000, 60000).pipe( // Every minute
      takeUntil(this.destroy$)
    ).subscribe(() => {
      this.cleanupStaleConnections();
    });
  }

  private cleanupStaleConnections(): void {
    const now = Date.now();
    const staleTimeout = 5 * 60 * 1000; // 5 minutes

    for (const [connectionId, connection] of this.connections) {
      if (connection.status === 'error' &&
          (now - connection.lastHeartbeat) > staleTimeout) {

        console.log(`Cleaning up stale connection ${connectionId}`);
        this.closeConnection(connectionId);
      }
    }
  }

  private updateConnectionStatus(): void {
    const statusMap = new Map<string, string>();

    for (const [id, connection] of this.connections) {
      statusMap.set(id, connection.status);
    }

    this.connectionStatus$.next(statusMap);
    this.globalConnectionCount$.next(this.connections.size);
  }

  private generateConnectionId(url: string): string {
    const urlHash = btoa(url).replace(/[^a-zA-Z0-9]/g, '').substring(0, 8);
    const timestamp = Date.now().toString(36);
    return `ws_${urlHash}_${timestamp}`;
  }
}
