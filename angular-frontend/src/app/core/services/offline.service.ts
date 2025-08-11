import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent, merge } from 'rxjs';
import { map, startWith } from 'rxjs/operators';

// === OFFLINE INTERFACES ===

export interface OfflineAction {
  id: string;
  type: 'connection_request' | 'message_send' | 'profile_update' | 'discovery_interaction';
  data: any;
  timestamp: Date;
  retryCount: number;
  maxRetries: number;
}

export interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  pendingActions: number;
  lastSyncTime?: Date;
  syncError?: string;
}

export interface CacheStrategy {
  name: string;
  urlPattern: RegExp;
  strategy: 'cache-first' | 'network-first' | 'stale-while-revalidate' | 'network-only' | 'cache-only';
  cacheName: string;
  maxAge?: number; // in milliseconds
  maxEntries?: number;
}

// === CACHE STRATEGIES CONFIGURATION ===

export const CACHE_STRATEGIES: CacheStrategy[] = [
  // App Shell - Cache First (static assets)
  {
    name: 'app-shell',
    urlPattern: /\.(js|css|html|png|jpg|jpeg|svg|woff|woff2)$/,
    strategy: 'cache-first',
    cacheName: 'app-shell-v1',
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    maxEntries: 100
  },
  
  // API Data - Network First with fallback
  {
    name: 'api-data',
    urlPattern: /\/api\/v1\/(discoveries|profiles|connections)/,
    strategy: 'network-first',
    cacheName: 'api-data-v1',
    maxAge: 5 * 60 * 1000, // 5 minutes
    maxEntries: 50
  },
  
  // Messages - Stale while revalidate
  {
    name: 'messages',
    urlPattern: /\/api\/v1\/messages/,
    strategy: 'stale-while-revalidate',
    cacheName: 'messages-v1',
    maxAge: 2 * 60 * 1000, // 2 minutes
    maxEntries: 100
  },
  
  // User Profile Images - Cache First (long cache)
  {
    name: 'profile-images',
    urlPattern: /\/api\/v1\/images\/profiles/,
    strategy: 'cache-first',
    cacheName: 'profile-images-v1',
    maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
    maxEntries: 200
  }
];

@Injectable({
  providedIn: 'root'
})
export class OfflineService {
  private isOnlineSubject = new BehaviorSubject<boolean>(navigator.onLine);
  private syncStatusSubject = new BehaviorSubject<SyncStatus>({
    isOnline: navigator.onLine,
    isSyncing: false,
    pendingActions: 0
  });

  private offlineQueue: OfflineAction[] = [];
  private readonly STORAGE_KEY = 'dinner_first_offline_queue';
  private readonly DB_NAME = 'DinnerFirstOfflineDB';
  private readonly DB_VERSION = 1;

  public isOnline$ = this.isOnlineSubject.asObservable();
  public syncStatus$ = this.syncStatusSubject.asObservable();

  constructor() {
    this.initializeOfflineSupport();
    this.loadOfflineQueue();
    this.registerServiceWorker();
  }

  /**
   * Initialize offline support and network monitoring
   */
  private initializeOfflineSupport(): void {
    // Monitor online/offline status
    const online$ = fromEvent(window, 'online').pipe(map(() => true));
    const offline$ = fromEvent(window, 'offline').pipe(map(() => false));
    
    merge(online$, offline$).pipe(
      startWith(navigator.onLine)
    ).subscribe(isOnline => {
      this.isOnlineSubject.next(isOnline);
      this.updateSyncStatus({ isOnline });
      
      if (isOnline) {
        this.processPendingActions();
      }
    });

    // Listen for service worker messages
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', event => {
        this.handleServiceWorkerMessage(event.data);
      });
    }
  }

  /**
   * Register service worker for offline support
   */
  private async registerServiceWorker(): Promise<void> {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service workers not supported');
      return;
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });

      console.log('Service Worker registered successfully:', registration.scope);

      // Listen for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New version available
              this.notifyAppUpdate();
            }
          });
        }
      });

    } catch (error) {
      console.error('Service Worker registration failed:', error);
    }
  }

  /**
   * Queue an action for later processing when online
   */
  queueAction(type: OfflineAction['type'], data: any, maxRetries = 3): string {
    const actionId = this.generateActionId();
    const action: OfflineAction = {
      id: actionId,
      type,
      data,
      timestamp: new Date(),
      retryCount: 0,
      maxRetries
    };

    this.offlineQueue.push(action);
    this.saveOfflineQueue();
    this.updateSyncStatus({ pendingActions: this.offlineQueue.length });

    console.log('Action queued for offline processing:', action);
    return actionId;
  }

  /**
   * Process all pending actions when online
   */
  private async processPendingActions(): Promise<void> {
    if (this.offlineQueue.length === 0) {
      return;
    }

    this.updateSyncStatus({ isSyncing: true });

    const actionsToProcess = [...this.offlineQueue];
    const results = await Promise.allSettled(
      actionsToProcess.map(action => this.processAction(action))
    );

    // Remove successful actions from queue
    results.forEach((result, index) => {
      const action = actionsToProcess[index];
      if (result.status === 'fulfilled') {
        this.removeActionFromQueue(action.id);
      } else {
        // Increment retry count
        const queueIndex = this.offlineQueue.findIndex(a => a.id === action.id);
        if (queueIndex !== -1) {
          this.offlineQueue[queueIndex].retryCount++;
          
          // Remove if max retries exceeded
          if (this.offlineQueue[queueIndex].retryCount >= action.maxRetries) {
            console.error('Action failed after max retries:', action);
            this.removeActionFromQueue(action.id);
          }
        }
      }
    });

    this.saveOfflineQueue();
    this.updateSyncStatus({ 
      isSyncing: false, 
      pendingActions: this.offlineQueue.length,
      lastSyncTime: new Date()
    });
  }

  /**
   * Process a single offline action
   */
  private async processAction(action: OfflineAction): Promise<void> {
    try {
      switch (action.type) {
        case 'connection_request':
          await this.processConnectionRequest(action.data);
          break;
        case 'message_send':
          await this.processMessageSend(action.data);
          break;
        case 'profile_update':
          await this.processProfileUpdate(action.data);
          break;
        case 'discovery_interaction':
          await this.processDiscoveryInteraction(action.data);
          break;
        default:
          throw new Error(`Unknown action type: ${action.type}`);
      }
    } catch (error) {
      console.error('Failed to process action:', action, error);
      throw error;
    }
  }

  /**
   * Cache data for offline access
   */
  async cacheData(key: string, data: any, expiryMinutes = 60): Promise<void> {
    try {
      const cacheData = {
        data,
        timestamp: Date.now(),
        expiry: Date.now() + (expiryMinutes * 60 * 1000)
      };

      if ('indexedDB' in window) {
        await this.storeInIndexedDB(key, cacheData);
      } else {
        // Fallback to localStorage
        localStorage.setItem(`offline_cache_${key}`, JSON.stringify(cacheData));
      }
    } catch (error) {
      console.error('Failed to cache data:', error);
    }
  }

  /**
   * Retrieve cached data
   */
  async getCachedData(key: string): Promise<any | null> {
    try {
      let cacheData;

      if ('indexedDB' in window) {
        cacheData = await this.getFromIndexedDB(key);
      } else {
        const stored = localStorage.getItem(`offline_cache_${key}`);
        cacheData = stored ? JSON.parse(stored) : null;
      }

      if (!cacheData) {
        return null;
      }

      // Check if data has expired
      if (Date.now() > cacheData.expiry) {
        await this.removeCachedData(key);
        return null;
      }

      return cacheData.data;
    } catch (error) {
      console.error('Failed to retrieve cached data:', error);
      return null;
    }
  }

  /**
   * Remove cached data
   */
  async removeCachedData(key: string): Promise<void> {
    try {
      if ('indexedDB' in window) {
        await this.removeFromIndexedDB(key);
      } else {
        localStorage.removeItem(`offline_cache_${key}`);
      }
    } catch (error) {
      console.error('Failed to remove cached data:', error);
    }
  }

  /**
   * Get offline queue status
   */
  getQueueStatus(): { pending: number; failed: number } {
    const failed = this.offlineQueue.filter(a => a.retryCount >= a.maxRetries).length;
    return {
      pending: this.offlineQueue.length - failed,
      failed
    };
  }

  /**
   * Clear offline queue (for testing/debugging)
   */
  clearQueue(): void {
    this.offlineQueue = [];
    this.saveOfflineQueue();
    this.updateSyncStatus({ pendingActions: 0 });
  }

  // === PRIVATE METHODS ===

  private generateActionId(): string {
    return `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private loadOfflineQueue(): void {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        this.offlineQueue = JSON.parse(stored).map((action: any) => ({
          ...action,
          timestamp: new Date(action.timestamp)
        }));
        this.updateSyncStatus({ pendingActions: this.offlineQueue.length });
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error);
    }
  }

  private saveOfflineQueue(): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.offlineQueue));
    } catch (error) {
      console.error('Failed to save offline queue:', error);
    }
  }

  private removeActionFromQueue(actionId: string): void {
    this.offlineQueue = this.offlineQueue.filter(action => action.id !== actionId);
  }

  private updateSyncStatus(updates: Partial<SyncStatus>): void {
    const currentStatus = this.syncStatusSubject.value;
    this.syncStatusSubject.next({ ...currentStatus, ...updates });
  }

  private handleServiceWorkerMessage(message: any): void {
    switch (message.type) {
      case 'CACHE_UPDATED':
        console.log('Cache updated by service worker');
        break;
      case 'OFFLINE_FALLBACK':
        console.log('Serving offline fallback');
        break;
      default:
        console.log('Service worker message:', message);
    }
  }

  private notifyAppUpdate(): void {
    // Notify user about app update
    console.log('New app version available. Please refresh.');
    // TODO: Show user notification with refresh option
  }

  // === ACTION PROCESSORS ===

  private async processConnectionRequest(data: any): Promise<void> {
    const response = await fetch('/api/v1/connections', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`Connection request failed: ${response.statusText}`);
    }
  }

  private async processMessageSend(data: any): Promise<void> {
    const response = await fetch(`/api/v1/messages/${data.connectionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({ message: data.message })
    });

    if (!response.ok) {
      throw new Error(`Message send failed: ${response.statusText}`);
    }
  }

  private async processProfileUpdate(data: any): Promise<void> {
    const response = await fetch('/api/v1/profiles/me', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`Profile update failed: ${response.statusText}`);
    }
  }

  private async processDiscoveryInteraction(data: any): Promise<void> {
    const response = await fetch('/api/v1/discoveries/interact', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`Discovery interaction failed: ${response.statusText}`);
    }
  }

  private getAuthToken(): string | null {
    // TODO: Get auth token from AuthService
    return localStorage.getItem('auth_token');
  }

  // === INDEXEDDB METHODS ===

  private async storeInIndexedDB(key: string, data: any): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['cache'], 'readwrite');
        const store = transaction.objectStore('cache');
        
        const putRequest = store.put({ key, ...data });
        putRequest.onsuccess = () => resolve();
        putRequest.onerror = () => reject(putRequest.error);
      };

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' });
        }
      };
    });
  }

  private async getFromIndexedDB(key: string): Promise<any | null> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['cache'], 'readonly');
        const store = transaction.objectStore('cache');
        
        const getRequest = store.get(key);
        getRequest.onsuccess = () => {
          resolve(getRequest.result || null);
        };
        getRequest.onerror = () => reject(getRequest.error);
      };
    });
  }

  private async removeFromIndexedDB(key: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['cache'], 'readwrite');
        const store = transaction.objectStore('cache');
        
        const deleteRequest = store.delete(key);
        deleteRequest.onsuccess = () => resolve();
        deleteRequest.onerror = () => reject(deleteRequest.error);
      };
    });
  }
}