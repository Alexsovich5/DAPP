import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSliderModule } from '@angular/material/slider';
import { FormsModule } from '@angular/forms';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { Router } from '@angular/router';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { AuthService } from '../../core/services/auth.service';
import { DiscoveryResponse, DiscoveryRequest, SoulConnectionCreate } from '../../core/interfaces/soul-connection.interfaces';
import { User } from '../../core/interfaces/auth.interfaces';

@Component({
  selector: 'app-discover',
  template: `
    <div class="discover-container">
      <!-- Soul Discovery Header -->
      <div class="discovery-header">
        <h1>Soul Discovery</h1>
        <p class="tagline">Discover connections based on emotional compatibility, not just photos</p>
        
        <!-- Discovery Filters -->
        <div class="discovery-filters" [class.expanded]="showFilters">
          <button class="filter-toggle" (click)="toggleFilters()">
            <mat-icon>tune</mat-icon>
            Filters
          </button>
          
          <div class="filter-content" *ngIf="showFilters">
            <div class="filter-group">
              <label>Hide Photos Initially</label>
              <mat-slide-toggle 
                [(ngModel)]="discoveryFilters.hide_photos"
                (change)="onFiltersChange()">
              </mat-slide-toggle>
            </div>
            
            <div class="filter-group">
              <label>Minimum Compatibility: {{ discoveryFilters.min_compatibility }}%</label>
              <mat-slider 
                min="30" 
                max="95" 
                step="5"
                [(ngModel)]="discoveryFilters.min_compatibility"
                (input)="onFiltersChange()">
              </mat-slider>
            </div>
            
            <div class="filter-group">
              <label>Max Results</label>
              <mat-slider 
                min="5" 
                max="20" 
                step="1"
                [(ngModel)]="discoveryFilters.max_results"
                (input)="onFiltersChange()">
              </mat-slider>
              <small>{{ discoveryFilters.max_results }} profiles</small>
            </div>
          </div>
        </div>
      </div>

      <!-- Onboarding Check -->
      <div class="onboarding-required" *ngIf="needsOnboarding">
        <div class="onboarding-card">
          <mat-icon class="onboarding-icon">psychology</mat-icon>
          <h2>Complete Your Soul Profile</h2>
          <p>Before discovering connections, please complete your emotional onboarding to enable our compatibility algorithms.</p>
          <button mat-raised-button color="primary" (click)="goToOnboarding()">
            Complete Soul Profile
          </button>
        </div>
      </div>

      <!-- Discovery Content -->
      <div class="discovery-content" *ngIf="!needsOnboarding">
        <!-- Loading State -->
        <div class="loading-container" *ngIf="isLoading">
          <mat-progress-bar mode="indeterminate"></mat-progress-bar>
          <p>Finding your soul connections...</p>
        </div>

        <!-- Error State -->
        <div class="error-container" *ngIf="error">
          <mat-icon class="error-icon">error</mat-icon>
          <h3>Something went wrong</h3>
          <p>{{ error }}</p>
          <button mat-button (click)="loadDiscoveries()">Try Again</button>
        </div>

        <!-- No Matches State -->
        <div class="no-matches-container" *ngIf="!isLoading && !error && discoveries.length === 0">
          <mat-icon class="no-matches-icon">search_off</mat-icon>
          <h3>No soul connections found</h3>
          <p>Try adjusting your filters or check back later for new members.</p>
          <button mat-button (click)="resetFilters()">Reset Filters</button>
        </div>

        <!-- Discovery Cards -->
        <div class="discovery-cards" *ngIf="!isLoading && !error && discoveries.length > 0">
          <div 
            *ngFor="let discovery of discoveries; trackBy: trackByUserId"
            class="soul-card"
            [@cardAnimation]="getCardAnimation(discovery.user_id)">
            
            <!-- Compatibility Score -->
            <div class="compatibility-header">
              <div class="compatibility-score" [style.color]="getCompatibilityColor(discovery.compatibility.total_compatibility)">
                <span class="score">{{ discovery.compatibility.total_compatibility }}%</span>
                <span class="quality">{{ discovery.compatibility.match_quality }}</span>
              </div>
              <div class="soul-icon">✨</div>
            </div>

            <!-- Profile Preview -->
            <div class="profile-preview">
              <div class="profile-header">
                <h3>{{ discovery.profile_preview.first_name }}</h3>
                <span class="age">{{ discovery.profile_preview.age }}</span>
                <span class="location" *ngIf="discovery.profile_preview.location">
                  <mat-icon>location_on</mat-icon>
                  {{ discovery.profile_preview.location }}
                </span>
              </div>

              <!-- Photo Placeholder (if hidden) -->
              <div class="photo-placeholder" *ngIf="discovery.is_photo_hidden">
                <mat-icon>psychology</mat-icon>
                <p>Photo revealed after connection</p>
              </div>

              <!-- Bio Preview -->
              <div class="bio-preview" *ngIf="discovery.profile_preview.bio">
                <p>{{ discovery.profile_preview.bio }}</p>
              </div>

              <!-- Interests Preview -->
              <div class="interests-preview" *ngIf="discovery.profile_preview.interests?.length">
                <h4>Shared Interests</h4>
                <div class="interest-chips">
                  <mat-chip 
                    *ngFor="let interest of discovery.profile_preview.interests.slice(0, 3)"
                    class="interest-chip">
                    {{ interest }}
                  </mat-chip>
                  <span *ngIf="discovery.profile_preview.interests.length > 3" class="more-interests">
                    +{{ discovery.profile_preview.interests.length - 3 }} more
                  </span>
                </div>
              </div>

              <!-- Emotional Depth Score -->
              <div class="emotional-depth" *ngIf="discovery.profile_preview.emotional_depth_score">
                <span class="depth-label">Emotional Depth:</span>
                <div class="depth-bar">
                  <div 
                    class="depth-fill" 
                    [style.width.%]="discovery.profile_preview.emotional_depth_score">
                  </div>
                </div>
                <span class="depth-score">{{ discovery.profile_preview.emotional_depth_score }}/100</span>
              </div>
            </div>

            <!-- Compatibility Breakdown -->
            <div class="compatibility-breakdown">
              <h4>Compatibility Breakdown</h4>
              <div class="breakdown-items">
                <div class="breakdown-item" *ngFor="let item of getCompatibilityBreakdown(discovery.compatibility.breakdown)">
                  <span class="item-label">{{ item.label }}</span>
                  <div class="item-bar">
                    <div class="item-fill" [style.width.%]="item.score" [style.background-color]="item.color"></div>
                  </div>
                  <span class="item-score">{{ item.score }}%</span>
                </div>
              </div>
            </div>

            <!-- Compatibility Explanation -->
            <div class="compatibility-explanation">
              <p>{{ discovery.compatibility.explanation }}</p>
            </div>

            <!-- Action Buttons -->
            <div class="card-actions">
              <button 
                mat-fab 
                class="pass-btn"
                (click)="onPass(discovery.user_id)"
                [disabled]="isActing"
                matTooltip="Pass">
                <mat-icon>close</mat-icon>
              </button>
              
              <button 
                mat-fab 
                class="connect-btn"
                (click)="onConnect(discovery)"
                [disabled]="isActing"
                matTooltip="Start Soul Connection">
                <mat-icon>favorite</mat-icon>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./discover.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatDividerModule,
    MatChipsModule,
    MatTooltipModule,
    MatSlideToggleModule,
    MatSliderModule
  ],
  animations: [
    trigger('cardAnimation', [
      state('default', style({
        transform: 'scale(1)',
        opacity: 1
      })),
      state('connect', style({
        transform: 'scale(0.8)',
        opacity: 0
      })),
      state('pass', style({
        transform: 'translateX(-100%)',
        opacity: 0
      })),
      transition('default => connect', animate('300ms ease-out')),
      transition('default => pass', animate('300ms ease-out'))
    ])
  ]
})
export class DiscoverComponent implements OnInit {
  discoveries: DiscoveryResponse[] = [];
  currentUser: User | null = null;
  isLoading = false;
  isActing = false;
  error: string | null = null;
  needsOnboarding = false;
  showFilters = false;
  cardAnimations: Map<number, string> = new Map();

  discoveryFilters: DiscoveryRequest = {
    max_results: 10,
    min_compatibility: 50,
    hide_photos: true,
    age_range_min: 21,
    age_range_max: 35
  };

  constructor(
    private router: Router,
    private soulConnectionService: SoulConnectionService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Check authentication and onboarding status
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      
      if (!user) {
        this.router.navigate(['/login']);
        return;
      }

      // Check if user needs emotional onboarding
      this.needsOnboarding = this.soulConnectionService.needsEmotionalOnboarding(user);
      
      if (!this.needsOnboarding) {
        this.loadDiscoveries();
      }
    });
  }

  loadDiscoveries(): void {
    this.isLoading = true;
    this.error = null;
    
    this.soulConnectionService.discoverSoulConnections(this.discoveryFilters).subscribe({
      next: (discoveries) => {
        this.discoveries = discoveries;
        // Initialize card animations
        discoveries.forEach(d => {
          this.cardAnimations.set(d.user_id, 'default');
        });
      },
      error: (err) => {
        this.error = err.message || 'Failed to load soul connections';
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }

  onFiltersChange(): void {
    // Debounce filter changes
    setTimeout(() => {
      if (!this.needsOnboarding) {
        this.loadDiscoveries();
      }
    }, 500);
  }

  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  resetFilters(): void {
    this.discoveryFilters = {
      max_results: 10,
      min_compatibility: 50,
      hide_photos: true
    };
    this.loadDiscoveries();
  }

  goToOnboarding(): void {
    this.router.navigate(['/onboarding']);
  }

  onConnect(discovery: DiscoveryResponse): void {
    if (this.isActing) return;

    this.isActing = true;
    this.cardAnimations.set(discovery.user_id, 'connect');

    const connectionData: SoulConnectionCreate = {
      user2_id: discovery.user_id
    };

    this.soulConnectionService.initiateSoulConnection(connectionData).subscribe({
      next: (connection) => {
        // Remove from discoveries and show success
        setTimeout(() => {
          this.discoveries = this.discoveries.filter(d => d.user_id !== discovery.user_id);
          this.isActing = false;
          
          // Navigate to connection or show success message
          this.router.navigate(['/connections', connection.id]);
        }, 300);
      },
      error: (err) => {
        this.error = err.message || 'Failed to initiate connection';
        this.cardAnimations.set(discovery.user_id, 'default');
        this.isActing = false;
      }
    });
  }

  onPass(userId: number): void {
    if (this.isActing) return;

    this.isActing = true;
    this.cardAnimations.set(userId, 'pass');

    // Remove from discoveries after animation
    setTimeout(() => {
      this.discoveries = this.discoveries.filter(d => d.user_id !== userId);
      this.isActing = false;
    }, 300);
  }

  getCardAnimation(userId: number): string {
    return this.cardAnimations.get(userId) || 'default';
  }

  getCompatibilityColor(score: number): string {
    return this.soulConnectionService.getMatchQualityColor(score);
  }

  getCompatibilityBreakdown(breakdown: any): Array<{label: string, score: number, color: string}> {
    const items = [
      { key: 'interests', label: 'Interests', color: '#8b5cf6' },
      { key: 'values', label: 'Values', color: '#ec4899' },
      { key: 'demographics', label: 'Demographics', color: '#06b6d4' },
      { key: 'communication', label: 'Communication', color: '#10b981' },
      { key: 'personality', label: 'Personality', color: '#f59e0b' }
    ];

    return items.map(item => ({
      label: item.label,
      score: breakdown[item.key] || 0,
      color: item.color
    }));
  }

  trackByUserId(index: number, discovery: DiscoveryResponse): number {
    return discovery.user_id;
  }
}
