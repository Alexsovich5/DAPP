import { Injectable } from '@angular/core';
import { SwUpdate, SwPush } from '@angular/service-worker';
import { BehaviorSubject, Observable, fromEvent } from 'rxjs';
import { environment } from '@environments/environment';

export interface PWAInstallPrompt {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export interface ConnectionStatus {
  isOnline: boolean;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
}

@Injectable({
  providedIn: 'root'
})
export class PWAService {
  private installPromptEvent: PWAInstallPrompt | null = null;
  private isInstallableSubject = new BehaviorSubject<boolean>(false);
  private connectionStatusSubject = new BehaviorSubject<ConnectionStatus>({ isOnline: navigator.onLine });
  private updateAvailableSubject = new BehaviorSubject<boolean>(false);

  public isInstallable$ = this.isInstallableSubject.asObservable();
  public connectionStatus$ = this.connectionStatusSubject.asObservable();
  public updateAvailable$ = this.updateAvailableSubject.asObservable();

  constructor(
    private swUpdate: SwUpdate,
    private swPush: SwPush
  ) {
    this.initializePWA();
    this.monitorConnection();
    this.monitorUpdates();
  }

  private initializePWA(): void {
    // Listen for beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (event: Event) => {
      event.preventDefault();
      this.installPromptEvent = event as PWAInstallPrompt;
      this.isInstallableSubject.next(true);
    });

    // Listen for app installed event
    window.addEventListener('appinstalled', () => {
      this.installPromptEvent = null;
      this.isInstallableSubject.next(false);
      this.trackInstallation();
    });
  }

  private monitorConnection(): void {
    // Monitor online/offline status
    fromEvent(window, 'online').subscribe(() => {
      this.updateConnectionStatus();
    });

    fromEvent(window, 'offline').subscribe(() => {
      this.updateConnectionStatus();
    });

    // Monitor connection quality if available
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      connection?.addEventListener('change', () => {
        this.updateConnectionStatus();
      });
    }

    // Initial status
    this.updateConnectionStatus();
  }

  private monitorUpdates(): void {
    if (this.swUpdate.isEnabled) {
      this.swUpdate.versionUpdates.subscribe(event => {
        if (event.type === 'VERSION_READY') {
          this.updateAvailableSubject.next(true);
        }
      });

      // Check for updates every 6 hours
      setInterval(() => {
        this.swUpdate.checkForUpdate();
      }, 6 * 60 * 60 * 1000);
    }
  }

  private updateConnectionStatus(): void {
    const connection = (navigator as any).connection;
    
    const status: ConnectionStatus = {
      isOnline: navigator.onLine,
      effectiveType: connection?.effectiveType,
      downlink: connection?.downlink,
      rtt: connection?.rtt
    };

    this.connectionStatusSubject.next(status);
  }

  async promptInstall(): Promise<boolean> {
    if (!this.installPromptEvent) {
      return false;
    }

    try {
      await this.installPromptEvent.prompt();
      const result = await this.installPromptEvent.userChoice;
      
      if (result.outcome === 'accepted') {
        this.installPromptEvent = null;
        this.isInstallableSubject.next(false);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Failed to prompt install:', error);
      return false;
    }
  }

  async activateUpdate(): Promise<boolean> {
    if (!this.swUpdate.isEnabled) {
      return false;
    }

    try {
      await this.swUpdate.activateUpdate();
      window.location.reload();
      return true;
    } catch (error) {
      console.error('Failed to activate update:', error);
      return false;
    }
  }

  async requestNotificationPermission(): Promise<boolean> {
    if (!this.swPush.isEnabled) {
      console.warn('Push notifications not supported');
      return false;
    }

    try {
      const subscription = await this.swPush.requestSubscription({
        serverPublicKey: environment.vapidPublicKey
      });

      // Send subscription to backend
      await this.sendSubscriptionToServer(subscription);
      return true;
    } catch (error) {
      console.error('Failed to get push subscription:', error);
      return false;
    }
  }

  private async sendSubscriptionToServer(subscription: PushSubscription): Promise<void> {
    try {
      const response = await fetch('/api/v1/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify({
          subscription: subscription.toJSON(),
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save subscription');
      }
    } catch (error) {
      console.error('Failed to send subscription to server:', error);
      throw error;
    }
  }

  listenToNotificationClicks(): Observable<any> {
    return this.swPush.notificationClicks;
  }

  listenToNotificationMessages(): Observable<any> {
    return this.swPush.messages;
  }

  handleNotificationClick(notification: any): void {
    const data = notification.notification.data;
    
    // Handle different notification types
    switch (data?.type) {
      case 'new_message':
        this.navigateToMessages(data.connectionId);
        break;
      case 'new_revelation':
        this.navigateToRevelations(data.connectionId);
        break;
      case 'new_match':
        this.navigateToDiscover();
        break;
      case 'photo_reveal':
        this.navigateToConnection(data.connectionId);
        break;
      default:
        this.navigateToHome();
    }
  }

  private navigateToMessages(connectionId?: string): void {
    const url = connectionId ? `/messages/${connectionId}` : '/messages';
    window.location.href = url;
  }

  private navigateToRevelations(connectionId?: string): void {
    const url = connectionId ? `/revelations/${connectionId}` : '/revelations';
    window.location.href = url;
  }

  private navigateToDiscover(): void {
    window.location.href = '/discover';
  }

  private navigateToConnection(connectionId: string): void {
    window.location.href = `/connections/${connectionId}`;
  }

  private navigateToHome(): void {
    window.location.href = '/';
  }

  private getAuthToken(): string {
    // Get token from storage service or auth service
    return localStorage.getItem('auth_token') || '';
  }

  private trackInstallation(): void {
    // Track PWA installation for analytics
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_installed', {
        event_category: 'PWA',
        event_label: 'dinner1_app'
      });
    }
  }

  isStandalone(): boolean {
    return window.matchMedia('(display-mode: standalone)').matches ||
           (window.navigator as any).standalone ||
           document.referrer.includes('android-app://');
  }

  getConnectionQuality(): 'high' | 'medium' | 'low' | 'unknown' {
    const connection = (navigator as any).connection;
    
    if (!connection) {
      return 'unknown';
    }

    const { effectiveType, downlink } = connection;
    
    if (effectiveType === '4g' && downlink > 5) {
      return 'high';
    } else if (effectiveType === '4g' || (effectiveType === '3g' && downlink > 1)) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  async shareContent(shareData: {
    title?: string;
    text?: string;
    url?: string;
    files?: File[];
  }): Promise<boolean> {
    if ('share' in navigator) {
      try {
        await (navigator as any).share(shareData);
        return true;
      } catch (error) {
        console.error('Failed to share:', error);
        return false;
      }
    }
    
    // Fallback for browsers without Web Share API
    if (shareData.url && 'clipboard' in navigator) {
      try {
        await navigator.clipboard.writeText(shareData.url);
        return true;
      } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        return false;
      }
    }
    
    return false;
  }

  async addToHomeScreen(): Promise<void> {
    // For iOS Safari
    if (this.isIOSSafari()) {
      this.showIOSInstallInstructions();
      return;
    }

    // For other browsers with beforeinstallprompt
    if (this.installPromptEvent) {
      await this.promptInstall();
    }
  }

  private isIOSSafari(): boolean {
    const userAgent = window.navigator.userAgent;
    return /iP(ad|od|hone)/i.test(userAgent) && /WebKit/i.test(userAgent) && !(/(CriOS|FxiOS|OPiOS|mercury)/i.test(userAgent));
  }

  private showIOSInstallInstructions(): void {
    // This would show a modal with iOS installation instructions
    console.log('Show iOS installation instructions');
  }

  // Background sync for offline actions
  async scheduleBackgroundSync(tag: string): Promise<void> {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register(tag);
      } catch (error) {
        console.error('Failed to register background sync:', error);
      }
    }
  }

  // Cache management
  async clearOldCache(): Promise<void> {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      const oldCaches = cacheNames.filter(name => 
        name.includes('dinner1') && !name.includes(this.getCurrentCacheVersion())
      );
      
      await Promise.all(oldCaches.map(cache => caches.delete(cache)));
    }
  }

  private getCurrentCacheVersion(): string {
    // This should match your app version
    return environment.production ? 'v1.0.0' : 'dev';
  }

  // Performance monitoring
  getPerformanceMetrics(): {
    loadTime: number;
    domContentLoaded: number;
    firstContentfulPaint: number;
  } {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const paint = performance.getEntriesByType('paint');
    
    const fcp = paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0;
    
    return {
      loadTime: navigation.loadEventEnd - navigation.loadEventStart,
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
      firstContentfulPaint: fcp
    };
  }
}