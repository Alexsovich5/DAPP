import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatBottomSheetModule } from '@angular/material/bottom-sheet';
import { MatDialogModule } from '@angular/material/dialog';
import { MobileFeaturesService } from '@core/services/mobile-features.service';
import { PWAService } from '@core/services/pwa.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

export interface MobileUIConfig {
  showBottomNav: boolean;
  enableSwipeGestures: boolean;
  showFAB: boolean;
  compactMode: boolean;
  hideTopBar: boolean;
}

@Component({
  selector: 'app-mobile-ui',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatBottomSheetModule,
    MatDialogModule
  ],
  template: `
    <!-- Mobile-optimized header -->
    <header class="mobile-header" [class.hidden]="config.hideTopBar" *ngIf="showHeader">
      <div class="header-content">
        <button mat-icon-button (click)="onBackClick()" *ngIf="showBackButton">
          <mat-icon>arrow_back</mat-icon>
        </button>
        
        <div class="header-title">
          <h1>{{ title }}</h1>
          <span class="subtitle" *ngIf="subtitle">{{ subtitle }}</span>
        </div>
        
        <div class="header-actions">
          <button mat-icon-button (click)="onMenuClick()" *ngIf="showMenu">
            <mat-icon>more_vert</mat-icon>
          </button>
          
          <!-- Connection indicator -->
          <div class="connection-indicator" [class.offline]="!isOnline">
            <mat-icon>{{ isOnline ? 'wifi' : 'wifi_off' }}</mat-icon>
          </div>
        </div>
      </div>
      
      <!-- Progress indicator for dating app stages -->
      <div class="progress-bar" *ngIf="showProgress">
        <div class="progress-fill" [style.width.%]="progressValue"></div>
      </div>
    </header>

    <!-- Main content with mobile optimizations -->
    <main class="mobile-content" 
          [class.compact]="config.compactMode"
          [class.with-bottom-nav]="config.showBottomNav"
          [class.with-header]="showHeader && !config.hideTopBar">
      
      <!-- Pull-to-refresh indicator -->
      <div class="pull-refresh" [class.active]="isPullingToRefresh" *ngIf="enablePullToRefresh">
        <div class="refresh-spinner">
          <mat-icon>refresh</mat-icon>
          <span>{{ pullToRefreshText }}</span>
        </div>
      </div>
      
      <!-- Content container with safe area support -->
      <div class="content-container safe-area" 
           (touchstart)="onTouchStart($event)"
           (touchmove)="onTouchMove($event)"
           (touchend)="onTouchEnd($event)">
        <ng-content></ng-content>
      </div>
      
      <!-- Empty state for mobile -->
      <div class="mobile-empty-state" *ngIf="showEmptyState">
        <div class="empty-content">
          <mat-icon class="empty-icon">{{ emptyStateIcon }}</mat-icon>
          <h3>{{ emptyStateTitle }}</h3>
          <p>{{ emptyStateMessage }}</p>
          <button mat-raised-button color="primary" *ngIf="emptyStateAction" 
                  (click)="onEmptyStateAction()">
            {{ emptyStateActionText }}
          </button>
        </div>
      </div>
    </main>

    <!-- Mobile Bottom Navigation -->
    <nav class="mobile-bottom-nav" *ngIf="config.showBottomNav">
      <div class="nav-items">
        <button class="nav-item" 
                [class.active]="activeTab === 'discover'"
                (click)="onTabClick('discover')">
          <mat-icon>favorite</mat-icon>
          <span>Discover</span>
          <div class="badge" *ngIf="discoverBadge">{{ discoverBadge }}</div>
        </button>
        
        <button class="nav-item" 
                [class.active]="activeTab === 'messages'"
                (click)="onTabClick('messages')">
          <mat-icon>chat</mat-icon>
          <span>Messages</span>
          <div class="badge" *ngIf="messagesBadge">{{ messagesBadge }}</div>
        </button>
        
        <button class="nav-item center-item" 
                [class.active]="activeTab === 'revelations'"
                (click)="onTabClick('revelations')">
          <div class="center-icon">
            <mat-icon>auto_awesome</mat-icon>
          </div>
          <span>Revelations</span>
          <div class="badge" *ngIf="revelationsBadge">{{ revelationsBadge }}</div>
        </button>
        
        <button class="nav-item" 
                [class.active]="activeTab === 'connections'"
                (click)="onTabClick('connections')">
          <mat-icon>people</mat-icon>
          <span>Connections</span>
          <div class="badge" *ngIf="connectionsBadge">{{ connectionsBadge }}</div>
        </button>
        
        <button class="nav-item" 
                [class.active]="activeTab === 'profile'"
                (click)="onTabClick('profile')">
          <mat-icon>person</mat-icon>
          <span>Profile</span>
        </button>
      </div>
    </nav>

    <!-- Floating Action Button -->
    <button class="mobile-fab" 
            mat-fab 
            color="primary" 
            *ngIf="config.showFAB && fabAction"
            (click)="onFABClick()"
            [attr.aria-label]="fabLabel">
      <mat-icon>{{ fabIcon }}</mat-icon>
    </button>

    <!-- Mobile-specific overlays -->
    <div class="mobile-overlay" [class.active]="showOverlay" (click)="closeOverlay()"></div>

    <!-- Swipe indicators -->
    <div class="swipe-indicators" *ngIf="config.enableSwipeGestures && showSwipeHints">
      <div class="swipe-hint left" [class.active]="canSwipeLeft">
        <mat-icon>chevron_left</mat-icon>
      </div>
      <div class="swipe-hint right" [class.active]="canSwipeRight">
        <mat-icon>chevron_right</mat-icon>
      </div>
    </div>

    <!-- PWA Install prompt -->
    <div class="pwa-install-prompt" *ngIf="showInstallPrompt" [@slideUp]>
      <div class="install-content">
        <div class="install-icon">
          <mat-icon>get_app</mat-icon>
        </div>
        <div class="install-text">
          <h4>Install Dinner1 App</h4>
          <p>Get the full experience with our app</p>
        </div>
        <div class="install-actions">
          <button mat-button (click)="dismissInstallPrompt()">Not now</button>
          <button mat-raised-button color="primary" (click)="installPWA()">Install</button>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./mobile-ui.component.scss']
})
export class MobileUIComponent implements OnInit, OnDestroy {
  @Input() config: MobileUIConfig = {
    showBottomNav: true,
    enableSwipeGestures: true,
    showFAB: false,
    compactMode: false,
    hideTopBar: false
  };

  @Input() title: string = 'Dinner1';
  @Input() subtitle?: string;
  @Input() showHeader: boolean = true;
  @Input() showBackButton: boolean = false;
  @Input() showMenu: boolean = true;
  @Input() showProgress: boolean = false;
  @Input() progressValue: number = 0;
  
  @Input() activeTab: string = 'discover';
  @Input() discoverBadge?: number;
  @Input() messagesBadge?: number;
  @Input() revelationsBadge?: number;
  @Input() connectionsBadge?: number;
  
  @Input() fabIcon: string = 'add';
  @Input() fabLabel: string = 'Add';
  @Input() fabAction?: () => void;
  
  @Input() showEmptyState: boolean = false;
  @Input() emptyStateIcon: string = 'favorite_border';
  @Input() emptyStateTitle: string = 'No connections yet';
  @Input() emptyStateMessage: string = 'Start discovering soul connections';
  @Input() emptyStateAction?: () => void;
  @Input() emptyStateActionText: string = 'Discover Now';
  
  @Input() enablePullToRefresh: boolean = true;
  @Input() showSwipeHints: boolean = false;
  @Input() canSwipeLeft: boolean = false;
  @Input() canSwipeRight: boolean = false;

  @Output() backClick = new EventEmitter<void>();
  @Output() menuClick = new EventEmitter<void>();
  @Output() tabClick = new EventEmitter<string>();
  @Output() fabClick = new EventEmitter<void>();
  @Output() pullToRefresh = new EventEmitter<void>();
  @Output() swipeLeft = new EventEmitter<void>();
  @Output() swipeRight = new EventEmitter<void>();
  @Output() emptyStateActionClick = new EventEmitter<void>();

  isOnline: boolean = true;
  showOverlay: boolean = false;
  showInstallPrompt: boolean = false;
  isPullingToRefresh: boolean = false;
  pullToRefreshText: string = 'Pull to refresh';

  private destroy$ = new Subject<void>();
  private touchStartX: number = 0;
  private touchStartY: number = 0;
  private touchStartTime: number = 0;
  private isPulling: boolean = false;
  private pullThreshold: number = 80;

  constructor(
    private mobileFeatures: MobileFeaturesService,
    private pwaService: PWAService
  ) {}

  ngOnInit(): void {
    this.initializeMobileFeatures();
    this.setupPWAPrompt();
    this.checkDeviceCapabilities();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeMobileFeatures(): void {
    // Monitor connection status
    this.pwaService.connectionStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        this.isOnline = status.isOnline;
      });

    // Setup mobile-specific features
    const deviceInfo = this.mobileFeatures.getDeviceInfo();
    
    if (deviceInfo.isMobile) {
      this.config.compactMode = true;
      
      // Adjust UI based on screen size
      if (deviceInfo.screenSize.width < 360) {
        this.config.compactMode = true;
      }
    }
  }

  private setupPWAPrompt(): void {
    this.pwaService.isInstallable$
      .pipe(takeUntil(this.destroy$))
      .subscribe(isInstallable => {
        this.showInstallPrompt = isInstallable && !this.pwaService.isStandalone();
      });
  }

  private checkDeviceCapabilities(): void {
    // Check for touch support
    if (!this.mobileFeatures.isTouchDevice()) {
      this.config.enableSwipeGestures = false;
    }
    
    // Check for haptic feedback support
    if (navigator.vibrate) {
      // Enable haptic feedback for interactions
    }
  }

  // Touch event handlers for gestures
  onTouchStart(event: TouchEvent): void {
    if (!this.config.enableSwipeGestures) return;
    
    const touch = event.touches[0];
    this.touchStartX = touch.clientX;
    this.touchStartY = touch.clientY;
    this.touchStartTime = Date.now();
    
    // Check for pull-to-refresh
    if (this.enablePullToRefresh && window.scrollY === 0) {
      this.isPulling = true;
    }
  }

  onTouchMove(event: TouchEvent): void {
    if (!this.config.enableSwipeGestures) return;
    
    const touch = event.touches[0];
    const deltaY = touch.clientY - this.touchStartY;
    
    // Handle pull-to-refresh
    if (this.isPulling && this.enablePullToRefresh) {
      if (deltaY > this.pullThreshold) {
        this.isPullingToRefresh = true;
        this.pullToRefreshText = 'Release to refresh';
        this.mobileFeatures.vibrateNewMessage(); // Light haptic feedback
      } else {
        this.isPullingToRefresh = false;
        this.pullToRefreshText = 'Pull to refresh';
      }
    }
  }

  onTouchEnd(event: TouchEvent): void {
    if (!this.config.enableSwipeGestures) return;
    
    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - this.touchStartX;
    const deltaY = touch.clientY - this.touchStartY;
    const deltaTime = Date.now() - this.touchStartTime;
    
    // Reset pull-to-refresh
    if (this.isPulling) {
      this.isPulling = false;
      
      if (this.isPullingToRefresh) {
        this.isPullingToRefresh = false;
        this.pullToRefreshText = 'Refreshing...';
        this.pullToRefresh.emit();
        this.mobileFeatures.vibrateNewMatch(); // Success haptic
        
        setTimeout(() => {
          this.pullToRefreshText = 'Pull to refresh';
        }, 2000);
      }
    }
    
    // Handle swipe gestures
    const minSwipeDistance = 100;
    const maxSwipeTime = 300;
    
    if (deltaTime < maxSwipeTime && Math.abs(deltaX) > minSwipeDistance && Math.abs(deltaY) < 100) {
      if (deltaX > 0 && this.canSwipeRight) {
        this.swipeRight.emit();
        this.mobileFeatures.vibrateNewMessage();
      } else if (deltaX < 0 && this.canSwipeLeft) {
        this.swipeLeft.emit();
        this.mobileFeatures.vibrateNewMessage();
      }
    }
  }

  // Event handlers
  onBackClick(): void {
    this.mobileFeatures.vibrateNewMessage();
    this.backClick.emit();
  }

  onMenuClick(): void {
    this.mobileFeatures.vibrateNewMessage();
    this.menuClick.emit();
  }

  onTabClick(tab: string): void {
    this.mobileFeatures.vibrateNewMessage();
    this.activeTab = tab;
    this.tabClick.emit(tab);
  }

  onFABClick(): void {
    this.mobileFeatures.vibrateNewMessage();
    this.fabClick.emit();
    if (this.fabAction) {
      this.fabAction();
    }
  }

  onEmptyStateAction(): void {
    this.mobileFeatures.vibrateNewMessage();
    this.emptyStateActionClick.emit();
    if (this.emptyStateAction) {
      this.emptyStateAction();
    }
  }

  // PWA functions
  async installPWA(): Promise<void> {
    const success = await this.pwaService.promptInstall();
    if (success) {
      this.showInstallPrompt = false;
      this.mobileFeatures.vibrateNewMatch(); // Success haptic
    }
  }

  dismissInstallPrompt(): void {
    this.showInstallPrompt = false;
    this.mobileFeatures.vibrateNewMessage();
  }

  // Utility functions
  closeOverlay(): void {
    this.showOverlay = false;
  }

  // Dating app specific methods
  updateConnectionBadges(badges: {
    discover?: number;
    messages?: number;
    revelations?: number;
    connections?: number;
  }): void {
    this.discoverBadge = badges.discover;
    this.messagesBadge = badges.messages;
    this.revelationsBadge = badges.revelations;
    this.connectionsBadge = badges.connections;
  }

  showRevelationProgress(day: number, totalDays: number = 7): void {
    this.showProgress = true;
    this.progressValue = (day / totalDays) * 100;
    this.subtitle = `Day ${day} of ${totalDays}`;
  }

  hideProgress(): void {
    this.showProgress = false;
    this.subtitle = undefined;
  }

  // Mobile-specific UI states
  enterFullscreen(): void {
    this.config.hideTopBar = true;
    this.config.showBottomNav = false;
  }

  exitFullscreen(): void {
    this.config.hideTopBar = false;
    this.config.showBottomNav = true;
  }

  enableCompactMode(): void {
    this.config.compactMode = true;
  }

  disableCompactMode(): void {
    this.config.compactMode = false;
  }

  // Accessibility helpers
  announceToScreenReader(message: string): void {
    // This would integrate with Angular CDK a11y module
    console.log('Screen reader announcement:', message);
  }

  // Performance optimization
  trackByFn(index: number, item: any): any {
    return item.id || index;
  }
}