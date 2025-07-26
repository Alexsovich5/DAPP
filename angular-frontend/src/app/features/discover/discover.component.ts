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
import { SoulConnectionService } from '@core/services/soul-connection.service';
import { AuthService } from '@core/services/auth.service';
import { ErrorLoggingService } from '@core/services/error-logging.service';
import { ErrorBoundaryComponent } from '@shared/components/error-boundary/error-boundary.component';
import { DiscoverEmptyStateComponent } from './discover-empty-state.component';
import { DiscoveryResponse, DiscoveryRequest, SoulConnectionCreate } from '../../core/interfaces/soul-connection.interfaces';
import { User } from '../../core/interfaces/auth.interfaces';

@Component({
  selector: 'app-discover',
  template: `
    <app-error-boundary 
      [retryCallback]="retryDiscovery" 
      errorTitle="Discovery Error"
      errorMessage="Unable to load soul connections. Please try again.">
      <div class="discover-container">
        <!-- Soul Discovery Header -->
        <div class="discovery-header" role="banner">
          <h1 id="discovery-title">Soul Discovery</h1>
          <p class="tagline" aria-describedby="discovery-title">Discover connections based on emotional compatibility, not just photos</p>
        
        <!-- Discovery Filters -->
        <div 
          class="discovery-filters" 
          [class.expanded]="showFilters"
          role="region"
          aria-labelledby="filters-title">
          <button 
            class="filter-toggle" 
            type="button"
            [attr.aria-expanded]="showFilters"
            aria-controls="filter-content"
            aria-label="Toggle discovery filters"
            (click)="toggleFilters()"
            (keydown.enter)="toggleFilters()"
            (keydown.space)="toggleFilters(); $event.preventDefault()">
            <mat-icon aria-hidden="true">tune</mat-icon>
            <span id="filters-title">Filters</span>
          </button>
          
          <div 
            class="filter-content" 
            *ngIf="showFilters"
            id="filter-content"
            role="group"
            aria-label="Discovery filter options">
            <div class="filter-group" role="group" aria-labelledby="hide-photos-label">
              <label id="hide-photos-label" for="hide-photos-toggle">Hide Photos Initially</label>
              <mat-slide-toggle 
                id="hide-photos-toggle"
                name="hide_photos"
                [(ngModel)]="discoveryFilters.hide_photos"
                [attr.aria-describedby]="'hide-photos-desc'"
                (change)="onFiltersChange()">
              </mat-slide-toggle>
              <div id="hide-photos-desc" class="sr-only">
                When enabled, profile photos will be hidden until you connect with someone
              </div>
            </div>
            
            <div class="filter-group" role="group" aria-labelledby="min-compatibility-label">
              <label id="min-compatibility-label" for="min-compatibility-slider">
                Minimum Compatibility: {{ discoveryFilters.min_compatibility }}%
              </label>
              <mat-slider 
                id="min-compatibility-slider"
                name="min_compatibility"
                min="30" 
                max="95" 
                step="5"
                [(ngModel)]="discoveryFilters.min_compatibility"
                [attr.aria-valuetext]="discoveryFilters.min_compatibility + ' percent minimum compatibility'"
                aria-label="Minimum compatibility percentage"
                (input)="onFiltersChange()">
              </mat-slider>
            </div>
            
            <div class="filter-group" role="group" aria-labelledby="max-results-label">
              <label id="max-results-label" for="max-results-slider">Max Results</label>
              <mat-slider 
                id="max-results-slider"
                name="max_results"
                min="5" 
                max="20" 
                step="1"
                [(ngModel)]="discoveryFilters.max_results"
                [attr.aria-valuetext]="discoveryFilters.max_results + ' profiles maximum'"
                aria-label="Maximum number of profiles to show"
                (input)="onFiltersChange()">
              </mat-slider>
              <small aria-live="polite">{{ discoveryFilters.max_results }} profiles</small>
            </div>
          </div>
        </div>
      </div>

      <!-- Onboarding Check -->
      <div 
        class="onboarding-required" 
        *ngIf="needsOnboarding"
        role="main"
        aria-labelledby="onboarding-title">
        <div class="onboarding-card">
          <mat-icon class="onboarding-icon" aria-hidden="true">psychology</mat-icon>
          <h2 id="onboarding-title">Complete Your Soul Profile</h2>
          <p>Before discovering connections, please complete your emotional onboarding to enable our compatibility algorithms.</p>
          <button 
            mat-raised-button 
            color="primary"
            type="button"
            aria-label="Complete soul profile to start discovering connections"
            (click)="goToOnboarding()"
            (keydown.enter)="goToOnboarding()">
            Complete Soul Profile
          </button>
        </div>
      </div>

      <!-- Discovery Content -->
      <div 
        class="discovery-content" 
        *ngIf="!needsOnboarding"
        role="main"
        aria-label="Soul connection discovery results">
        <!-- Loading State -->
        <div 
          class="loading-container" 
          *ngIf="isLoading"
          role="status"
          aria-live="polite"
          aria-label="Loading soul connections">
          <mat-progress-bar mode="indeterminate" aria-label="Loading progress"></mat-progress-bar>
          <p>Finding your soul connections...</p>
        </div>

        <!-- Error State -->
        <div 
          class="error-container" 
          *ngIf="error"
          role="alert"
          aria-live="assertive">
          <mat-icon class="error-icon" aria-hidden="true">error</mat-icon>
          <h3>Something went wrong</h3>
          <p>{{ error }}</p>
          <button 
            mat-button 
            type="button"
            aria-label="Retry loading soul connections"
            (click)="loadDiscoveries()"
            (keydown.enter)="loadDiscoveries()">
            Try Again
          </button>
        </div>

        <!-- No Matches State -->
        <div 
          class="no-matches-container" 
          *ngIf="!isLoading && !error && discoveries.length === 0"
          role="region"
          aria-label="No matches found">
          <app-discover-empty-state
            (refreshMatches)="loadDiscoveries()"
            (updateProfile)="goToProfile()">
          </app-discover-empty-state>
        </div>

        <!-- Discovery Cards -->
        <div 
          class="discovery-cards" 
          *ngIf="!isLoading && !error && discoveries.length > 0"
          role="list"
          [attr.aria-label]="discoveries.length + ' soul connection matches found'">
          <article 
            *ngFor="let discovery of discoveries; trackBy: trackByUserId; let i = index"
            class="soul-card"
            role="listitem"
            [attr.aria-labelledby]="'card-title-' + discovery.user_id"
            [attr.aria-describedby]="'card-desc-' + discovery.user_id"
            [@cardAnimation]="getCardAnimation(discovery.user_id)"
            tabindex="0">
            
            <!-- Compatibility Score -->
            <div 
              class="compatibility-header"
              role="group"
              [attr.aria-label]="getCompatibilityHeaderAriaLabel(discovery)">
              <div 
                class="compatibility-score" 
                [style.color]="getCompatibilityColor(discovery.compatibility.total_compatibility)"
                role="meter"
                [attr.aria-valuenow]="discovery.compatibility.total_compatibility"
                aria-valuemin="0"
                aria-valuemax="100"
                [attr.aria-label]="discovery.compatibility.total_compatibility + '% compatibility score'">
                <span class="score" aria-hidden="true">{{ discovery.compatibility.total_compatibility }}%</span>
                <span class="quality" aria-hidden="true">{{ discovery.compatibility.match_quality }}</span>
              </div>
              <div class="soul-icon" aria-hidden="true">✨</div>
            </div>

            <!-- Profile Preview -->
            <div 
              class="profile-preview"
              role="group"
              [attr.aria-labelledby]="'card-title-' + discovery.user_id">
              <div class="profile-header">
                <h3 [id]="'card-title-' + discovery.user_id">{{ discovery.profile_preview.first_name }}</h3>
                <span 
                  class="age"
                  [attr.aria-label]="discovery.profile_preview.age + ' years old'">
                  {{ discovery.profile_preview.age }}
                </span>
                <span 
                  class="location" 
                  *ngIf="discovery.profile_preview.location"
                  [attr.aria-label]="'Located in ' + discovery.profile_preview.location">
                  <mat-icon aria-hidden="true">location_on</mat-icon>
                  {{ discovery.profile_preview.location }}
                </span>
              </div>

              <!-- Photo Placeholder (if hidden) -->
              <div 
                class="photo-placeholder" 
                *ngIf="discovery.is_photo_hidden"
                role="img"
                aria-label="Photo will be revealed after connecting">
                <mat-icon aria-hidden="true">psychology</mat-icon>
                <p>Photo revealed after connection</p>
              </div>

              <!-- Bio Preview -->
              <div 
                class="bio-preview" 
                *ngIf="discovery.profile_preview.bio"
                role="region"
                aria-label="Profile bio">
                <p>{{ discovery.profile_preview.bio }}</p>
              </div>

              <!-- Interests Preview -->
              <div 
                class="interests-preview" 
                *ngIf="discovery.profile_preview.interests?.length"
                role="region"
                aria-labelledby="interests-heading-{{ discovery.user_id }}">
                <h4 id="interests-heading-{{ discovery.user_id }}">Shared Interests</h4>
                <div 
                  class="interest-chips"
                  role="list"
                  [attr.aria-label]="discovery.profile_preview.interests.length + ' shared interests'">
                  <mat-chip 
                    *ngFor="let interest of discovery.profile_preview.interests.slice(0, 3)"
                    class="interest-chip"
                    role="listitem"
                    [attr.aria-label]="'Shared interest: ' + interest">
                    {{ interest }}
                  </mat-chip>
                  <span 
                    *ngIf="discovery.profile_preview.interests.length > 3" 
                    class="more-interests"
                    [attr.aria-label]="'Plus ' + (discovery.profile_preview.interests.length - 3) + ' more shared interests'">
                    +{{ discovery.profile_preview.interests.length - 3 }} more
                  </span>
                </div>
              </div>

              <!-- Emotional Depth Score -->
              <div 
                class="emotional-depth" 
                *ngIf="discovery.profile_preview.emotional_depth_score"
                role="group"
                [attr.aria-labelledby]="'depth-label-' + discovery.user_id">
                <span 
                  class="depth-label"
                  [id]="'depth-label-' + discovery.user_id">Emotional Depth:</span>
                <div 
                  class="depth-bar"
                  role="progressbar"
                  [attr.aria-valuenow]="discovery.profile_preview.emotional_depth_score"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  [attr.aria-label]="'Emotional depth score: ' + discovery.profile_preview.emotional_depth_score + ' out of 100'">
                  <div 
                    class="depth-fill" 
                    [style.width.%]="discovery.profile_preview.emotional_depth_score"
                    aria-hidden="true">
                  </div>
                </div>
                <span 
                  class="depth-score"
                  aria-hidden="true">{{ discovery.profile_preview.emotional_depth_score }}/100</span>
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
            <div 
              class="card-actions"
              role="group"
              [attr.aria-label]="'Actions for ' + discovery.profile_preview.first_name + ' profile'">
              <button 
                mat-fab 
                class="pass-btn"
                type="button"
                [attr.aria-label]="'Pass on ' + discovery.profile_preview.first_name + ' profile'"
                [attr.aria-describedby]="'card-desc-' + discovery.user_id"
                (click)="onPass(discovery.user_id)"
                (keydown.enter)="onPass(discovery.user_id)"
                [disabled]="isActing"
                matTooltip="Pass on this connection">
                <mat-icon aria-hidden="true">close</mat-icon>
                <span class="sr-only">Pass</span>
              </button>
              
              <button 
                mat-fab 
                class="connect-btn"
                type="button"
                [attr.aria-label]="'Start soul connection with ' + discovery.profile_preview.first_name + ', ' + discovery.compatibility.total_compatibility + '% compatibility'"
                [attr.aria-describedby]="'card-desc-' + discovery.user_id"
                (click)="onConnect(discovery)"
                (keydown.enter)="onConnect(discovery)"
                [disabled]="isActing"
                matTooltip="Start soul connection">
                <mat-icon aria-hidden="true">favorite</mat-icon>
                <span class="sr-only">Connect</span>
              </button>
            </div>
            
            <!-- Hidden description for screen readers -->
            <div 
              [id]="'card-desc-' + discovery.user_id" 
              class="sr-only">
              {{ getCardDescriptionForScreenReader(discovery) }}
            </div>
          </div>
        </div>
      </div>
    </div>
    </app-error-boundary>
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
    MatSliderModule,
    ErrorBoundaryComponent,
    DiscoverEmptyStateComponent
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
    private authService: AuthService,
    private errorLoggingService: ErrorLoggingService
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
    
    console.log('Loading discoveries with filters:', this.discoveryFilters);
    
    this.soulConnectionService.discoverSoulConnections(this.discoveryFilters).subscribe({
      next: (discoveries) => {
        console.log('Discoveries received:', discoveries);
        this.discoveries = discoveries;
        // Initialize card animations
        discoveries.forEach(d => {
          this.cardAnimations.set(d.user_id, 'default');
        });
      },
      error: (err) => {
        console.error('Discovery error:', err);
        this.error = err.message || 'Failed to load soul connections';
        this.errorLoggingService.logError(err, {
          component: 'discover',
          action: 'load_discoveries',
          filters: this.discoveryFilters
        });
      },
      complete: () => {
        this.isLoading = false;
        console.log('Discovery loading completed. Total discoveries:', this.discoveries.length);
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

  goToProfile(): void {
    this.router.navigate(['/profile']);
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

  /**
   * Retry callback for error boundary
   */
  retryDiscovery = (): void => {
    this.loadDiscoveries();
  }

  /**
   * Get aria label for compatibility header
   */
  getCompatibilityHeaderAriaLabel(discovery: DiscoveryResponse): string {
    return `${discovery.compatibility.total_compatibility}% compatibility score, ${discovery.compatibility.match_quality} match quality`;
  }

  /**
   * Get comprehensive card description for screen readers
   */
  getCardDescriptionForScreenReader(discovery: DiscoveryResponse): string {
    const age = discovery.profile_preview.age;
    const location = discovery.profile_preview.location ? `, located in ${discovery.profile_preview.location}` : '';
    const bio = discovery.profile_preview.bio ? `. ${discovery.profile_preview.bio}` : '';
    const interests = discovery.profile_preview.interests?.length 
      ? `. Shared interests include: ${discovery.profile_preview.interests.slice(0, 3).join(', ')}` 
      : '';
    const moreInterests = discovery.profile_preview.interests && discovery.profile_preview.interests.length > 3
      ? ` and ${discovery.profile_preview.interests.length - 3} more`
      : '';
    const emotionalDepth = discovery.profile_preview.emotional_depth_score
      ? `. Emotional depth score: ${discovery.profile_preview.emotional_depth_score} out of 100`
      : '';
    const explanation = discovery.compatibility.explanation ? `. ${discovery.compatibility.explanation}` : '';

    return `${age} years old${location}${bio}${interests}${moreInterests}${emotionalDepth}${explanation}`;
  }
}
