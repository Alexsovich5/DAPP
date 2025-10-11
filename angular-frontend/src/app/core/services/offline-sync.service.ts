import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, fromEvent, merge } from 'rxjs';
import { map, distinctUntilChanged } from 'rxjs/operators';
import { StorageService } from './storage.service';

export interface OfflineAction {
  id: string;
  type: string;
  data: Record<string, unknown>;
  timestamp: number;
  retryCount: number;
  maxRetries: number;
  priority: 'high' | 'medium' | 'low';
  endpoint: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
}

export interface SyncStatus {
  isOnline: boolean;
  pendingActions: number;
  lastSyncTime: number;
  syncInProgress: boolean;
  failedActions: number;
}

export interface OfflineData {
  messages: Record<string, unknown>[];
  revelations: Record<string, unknown>[];
  profiles: Record<string, unknown>[];
  connections: Record<string, unknown>[];
  lastUpdated: number;
}

@Injectable({
  providedIn: 'root'
})
export class OfflineSyncService {
  private readonly OFFLINE_ACTIONS_KEY = 'dinner_first_offline_actions';
  private readonly OFFLINE_DATA_KEY = 'dinner_first_offline_data';
  private readonly SYNC_STATUS_KEY = 'dinner_first_sync_status';

  private syncStatusSubject = new BehaviorSubject<SyncStatus>({
    isOnline: navigator.onLine,
    pendingActions: 0,
    lastSyncTime: 0,
    syncInProgress: false,
    failedActions: 0
  });

  public syncStatus$ = this.syncStatusSubject.asObservable();
  public isOnline$ = this.syncStatus$.pipe(
    map(status => status.isOnline),
    distinctUntilChanged()
  );

  private syncQueue: OfflineAction[] = [];
  private syncInProgress = false;

  constructor(
    private http: HttpClient,
    private storage: StorageService
  ) {
    this.initializeOfflineSync();
    this.monitorConnectionStatus();
    this.loadPendingActions();
  }

  private initializeOfflineSync(): void {
    // Load sync status from storage
    this.loadSyncStatus();

    // Start automatic sync when online
    this.isOnline$.subscribe(isOnline => {
      if (isOnline && !this.syncInProgress) {
        this.syncPendingActions();
      }
    });
  }

  private monitorConnectionStatus(): void {
    const online$ = fromEvent(window, 'online').pipe(map(() => true));
    const offline$ = fromEvent(window, 'offline').pipe(map(() => false));

    merge(online$, offline$).subscribe(isOnline => {
      this.updateSyncStatus({ isOnline });

      if (isOnline) {
        this.syncPendingActions();
      }
    });
  }

  // Queue offline actions
  async queueAction(action: Omit<OfflineAction, 'id' | 'timestamp' | 'retryCount'>): Promise<string> {
    const offlineAction: OfflineAction = {
      ...action,
      id: this.generateActionId(),
      timestamp: Date.now(),
      retryCount: 0,
      maxRetries: action.maxRetries || 3
    };

    this.syncQueue.push(offlineAction);
    await this.savePendingActions();

    this.updateSyncStatus({
      pendingActions: this.syncQueue.length
    });

    // Try immediate sync if online
    if (navigator.onLine && !this.syncInProgress) {
      this.syncPendingActions();
    }

    return offlineAction.id;
  }

  // Dating app specific offline actions
  async queueSendMessage(connectionId: number, message: string): Promise<string> {
    return this.queueAction({
      type: 'send_message',
      data: { connectionId, message, clientTimestamp: Date.now() },
      priority: 'high',
      endpoint: `/api/v1/messages/${connectionId}`,
      method: 'POST',
      maxRetries: 5
    });
  }

  async queueCreateRevelation(connectionId: number, revelation: Record<string, unknown>): Promise<string> {
    return this.queueAction({
      type: 'create_revelation',
      data: { connectionId, ...revelation, clientTimestamp: Date.now() },
      priority: 'high',
      endpoint: '/api/v1/revelations/create',
      method: 'POST',
      maxRetries: 3
    });
  }

  async queueUpdateProfile(profileData: Record<string, unknown>): Promise<string> {
    return this.queueAction({
      type: 'update_profile',
      data: { ...profileData, clientTimestamp: Date.now() },
      priority: 'medium',
      endpoint: '/api/v1/profiles/me',
      method: 'PUT',
      maxRetries: 3
    });
  }

  async queueInitiateConnection(targetUserId: number): Promise<string> {
    return this.queueAction({
      type: 'initiate_connection',
      data: { targetUserId, clientTimestamp: Date.now() },
      priority: 'high',
      endpoint: '/api/v1/soul-connections/initiate',
      method: 'POST',
      maxRetries: 3
    });
  }

  async queuePhotoUpload(photoData: Record<string, unknown>, connectionId?: number): Promise<string> {
    return this.queueAction({
      type: 'upload_photo',
      data: { photoData, connectionId, clientTimestamp: Date.now() },
      priority: 'medium',
      endpoint: '/api/v1/photos/upload',
      method: 'POST',
      maxRetries: 2
    });
  }

  // Sync pending actions
  async syncPendingActions(): Promise<void> {
    if (this.syncInProgress || !navigator.onLine || this.syncQueue.length === 0) {
      return;
    }

    this.syncInProgress = true;
    this.updateSyncStatus({ syncInProgress: true });

    try {
      // Sort actions by priority and timestamp
      const sortedActions = this.syncQueue.sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];

        if (priorityDiff !== 0) {
          return priorityDiff;
        }

        return a.timestamp - b.timestamp;
      });

      const successfulActions: string[] = [];
      const failedActions: OfflineAction[] = [];

      // Process actions in batches to avoid overwhelming the server
      const batchSize = 5;
      for (let i = 0; i < sortedActions.length; i += batchSize) {
        const batch = sortedActions.slice(i, i + batchSize);

        await Promise.allSettled(
          batch.map(async (action) => {
            try {
              await this.executeAction(action);
              successfulActions.push(action.id);
            } catch (error) {
              action.retryCount++;

              if (action.retryCount < action.maxRetries) {
                failedActions.push(action);
              } else {
                console.error(`Action ${action.id} failed permanently:`, error);
              }
            }
          })
        );

        // Small delay between batches
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Update queue - remove successful actions, keep failed ones for retry
      this.syncQueue = failedActions;
      await this.savePendingActions();

      this.updateSyncStatus({
        pendingActions: this.syncQueue.length,
        lastSyncTime: Date.now(),
        failedActions: failedActions.filter(a => a.retryCount >= a.maxRetries).length
      });

    } catch (error) {
      console.error('Sync process failed:', error);
    } finally {
      this.syncInProgress = false;
      this.updateSyncStatus({ syncInProgress: false });
    }
  }

  private async executeAction(action: OfflineAction): Promise<unknown> {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getAuthToken()}`,
      'X-Offline-Action': 'true',
      'X-Client-Timestamp': action.timestamp.toString()
    };

    switch (action.method) {
      case 'POST':
        return this.http.post(action.endpoint, action.data, { headers }).toPromise();
      case 'PUT':
        return this.http.put(action.endpoint, action.data, { headers }).toPromise();
      case 'DELETE':
        return this.http.delete(action.endpoint, { headers }).toPromise();
      case 'GET':
        return this.http.get(action.endpoint, { headers }).toPromise();
      default:
        throw new Error(`Unsupported method: ${action.method}`);
    }
  }

  // Offline data caching
  async cacheDataForOfflineUse(data: Partial<OfflineData>): Promise<void> {
    const existingData = await this.getOfflineData();
    const updatedData: OfflineData = {
      ...existingData,
      ...data,
      lastUpdated: Date.now()
    };

    this.storage.setJson(this.OFFLINE_DATA_KEY, updatedData);
  }

  async getOfflineData(): Promise<OfflineData> {
    const data = this.storage.getJson<OfflineData>(this.OFFLINE_DATA_KEY);
    return data || {
      messages: [],
      revelations: [],
      profiles: [],
      connections: [],
      lastUpdated: 0
    };
  }

  async getCachedMessages(connectionId?: number): Promise<Record<string, unknown>[]> {
    const data = await this.getOfflineData();
    if (connectionId) {
      return data.messages.filter(msg => msg['connectionId'] === connectionId);
    }
    return data.messages;
  }

  async getCachedRevelations(connectionId?: number): Promise<Record<string, unknown>[]> {
    const data = await this.getOfflineData();
    if (connectionId) {
      return data.revelations.filter(rev => rev['connectionId'] === connectionId);
    }
    return data.revelations;
  }

  async getCachedProfiles(): Promise<Record<string, unknown>[]> {
    const data = await this.getOfflineData();
    return data.profiles;
  }

  async getCachedConnections(): Promise<Record<string, unknown>[]> {
    const data = await this.getOfflineData();
    return data.connections;
  }

  // Background sync
  async scheduleBackgroundSync(tag: string): Promise<void> {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      try {
        const registration = await navigator.serviceWorker.ready;
        // Use type assertion for sync API (not in standard TypeScript types)
        await (registration as ServiceWorkerRegistration & { sync: { register: (tag: string) => Promise<void> } }).sync.register(tag);
      } catch (error) {
        console.error('Failed to register background sync:', error);
      }
    }
  }

  // Optimistic updates
  async addOptimisticMessage(connectionId: number, message: string): Promise<Record<string, unknown>> {
    const optimisticMessage: Record<string, unknown> = {
      id: `temp_${Date.now()}`,
      connectionId,
      message,
      timestamp: Date.now(),
      senderId: 'current_user', // Replace with actual user ID
      status: 'sending',
      isOptimistic: true
    };

    const data = await this.getOfflineData();
    data.messages.push(optimisticMessage);
    await this.cacheDataForOfflineUse({ messages: data.messages });

    return optimisticMessage;
  }

  async addOptimisticRevelation(connectionId: number, revelation: Record<string, unknown>): Promise<Record<string, unknown>> {
    const optimisticRevelation: Record<string, unknown> = {
      id: `temp_${Date.now()}`,
      connectionId,
      ...revelation,
      timestamp: Date.now(),
      status: 'sending',
      isOptimistic: true
    };

    const data = await this.getOfflineData();
    data.revelations.push(optimisticRevelation);
    await this.cacheDataForOfflineUse({ revelations: data.revelations });

    return optimisticRevelation;
  }

  async removeOptimisticUpdate(id: string, type: 'message' | 'revelation'): Promise<void> {
    const data = await this.getOfflineData();

    if (type === 'message') {
      data.messages = data.messages.filter(msg => msg['id'] !== id);
    } else if (type === 'revelation') {
      data.revelations = data.revelations.filter(rev => rev['id'] !== id);
    }

    await this.cacheDataForOfflineUse(data);
  }

  // Cache management
  async clearExpiredCache(maxAge: number = 7 * 24 * 60 * 60 * 1000): Promise<void> {
    const data = await this.getOfflineData();
    const cutoffTime = Date.now() - maxAge;

    if (data.lastUpdated < cutoffTime) {
      await this.storage.removeItem(this.OFFLINE_DATA_KEY);
    }
  }

  async getCacheSize(): Promise<number> {
    try {
      const data = await this.getOfflineData();
      const actions = this.storage.getJson<OfflineAction[]>(this.OFFLINE_ACTIONS_KEY) || [];

      const dataSize = JSON.stringify(data).length;
      const actionsSize = JSON.stringify(actions).length;

      return dataSize + actionsSize;
    } catch (error) {
      return 0;
    }
  }

  async clearAllOfflineData(): Promise<void> {
    await Promise.all([
      this.storage.removeItem(this.OFFLINE_DATA_KEY),
      this.storage.removeItem(this.OFFLINE_ACTIONS_KEY),
      this.storage.removeItem(this.SYNC_STATUS_KEY)
    ]);

    this.syncQueue = [];
    this.updateSyncStatus({
      pendingActions: 0,
      lastSyncTime: 0,
      failedActions: 0
    });
  }

  // Conflict resolution
  async resolveConflict(localData: Record<string, unknown>, serverData: Record<string, unknown>, type: string): Promise<Record<string, unknown>> {
    // Dating app specific conflict resolution
    switch (type) {
      case 'message':
        // Server data wins for messages (they have definitive timestamp)
        return serverData;

      case 'profile': {
        // Merge profile data, preferring most recent updates
        const localTimestamp = localData['clientTimestamp'] as number | undefined;
        const serverTimestamp = serverData['updatedAt'] as number | undefined;

        return {
          ...localData,
          ...serverData,
          // Keep local changes that are newer
          ...((localTimestamp && serverTimestamp && localTimestamp > serverTimestamp) ? {
            bio: localData['bio'],
            interests: localData['interests']
          } : {})
        };
      }

      case 'revelation':
        // Server data wins for revelations
        return serverData;

      default:
        // Default: server data wins
        return serverData;
    }
  }

  // Private helper methods
  private generateActionId(): string {
    return `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async savePendingActions(): Promise<void> {
    this.storage.setJson(this.OFFLINE_ACTIONS_KEY, this.syncQueue);
  }

  private async loadPendingActions(): Promise<void> {
    const actions = this.storage.getJson<OfflineAction[]>(this.OFFLINE_ACTIONS_KEY) || [];
    this.syncQueue = actions;

    this.updateSyncStatus({
      pendingActions: this.syncQueue.length
    });
  }

  private updateSyncStatus(updates: Partial<SyncStatus>): void {
    const currentStatus = this.syncStatusSubject.value;
    const newStatus = { ...currentStatus, ...updates };

    this.syncStatusSubject.next(newStatus);
    this.saveSyncStatus(newStatus);
  }

  private async saveSyncStatus(status: SyncStatus): Promise<void> {
    this.storage.setJson(this.SYNC_STATUS_KEY, status);
  }

  private async loadSyncStatus(): Promise<void> {
    const status = this.storage.getJson<SyncStatus>(this.SYNC_STATUS_KEY);
    if (status) {
      this.syncStatusSubject.next({
        ...status,
        isOnline: navigator.onLine,
        syncInProgress: false
      });
    }
  }

  private getAuthToken(): string {
    // Get token from storage or auth service
    return localStorage.getItem('auth_token') || '';
  }

  // Public getters
  get pendingActionsCount(): number {
    return this.syncQueue.length;
  }

  get isOnline(): boolean {
    return this.syncStatusSubject.value.isOnline;
  }

  get lastSyncTime(): number {
    return this.syncStatusSubject.value.lastSyncTime;
  }
}
