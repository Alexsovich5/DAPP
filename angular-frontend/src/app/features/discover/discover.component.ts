import { Component, OnInit, OnDestroy } from '@angular/core';
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
import { HapticFeedbackService } from '@core/services/haptic-feedback.service';
import { ErrorBoundaryComponent } from '@shared/components/error-boundary/error-boundary.component';
import { DiscoverEmptyStateComponent } from './discover-empty-state.component';
import { SoulLoadingComponent } from '@shared/components/soul-loading/soul-loading.component';
import { CompatibilityScoreComponent } from '@shared/components/compatibility-score/compatibility-score.component';
import { SoulOrbComponent } from '@shared/components/soul-orb/soul-orb.component';
import { OnboardingTargetDirective } from '@shared/directives/onboarding-target.directive';
import { SwipeDirective } from '@shared/directives/swipe.directive';
import { ABTestDirective, ABTestConfigPipe } from '@shared/directives/ab-test.directive';
import { SwipeEvent } from '@core/services/swipe-gesture.service';
import { ABTestingService } from '@core/services/ab-testing.service';
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
        </div>

        <!-- Discovery Filters -->
        <div
          class="discovery-filters"
          [class.expanded]="showFilters"
          role="region"
          aria-labelledby="filters-title"
          appOnboardingTarget="discovery-filters"
          onboardingTour="discovery-tour"
          [onboardingAutoTrigger]="true">
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
                (change)="onFiltersChange()"
                (keydown)="handleFilterKeydown($event, 'toggle')">
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
                (input)="onFiltersChange()"
                (keydown)="handleFilterKeydown($event, 'slider')">
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
                (input)="onFiltersChange()"
                (keydown)="handleFilterKeydown($event, 'slider')">
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
        <!-- Soul Loading State -->
        <app-soul-loading
          *ngIf="isLoading"
          size="large"
          variant="immersive"
          title="Discovering Soul Connections"
          subtitle="We're analyzing compatibility based on your emotional profile and values"
          [showProgress]="true"
          [progressSteps]="4"
          [currentProgress]="loadingProgress">
        </app-soul-loading>

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

        <!-- Keyboard Navigation Instructions -->
        <div
          class="keyboard-help"
          *ngIf="!isLoading && !error && discoveries.length > 0"
          role="complementary"
          aria-label="Keyboard navigation instructions">
          <details>
            <summary>Keyboard Navigation Help</summary>
            <div class="help-content">
              <h4>Discovery Cards Navigation:</h4>
              <ul>
                <li><kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd> Navigate between cards</li>
                <li><kbd>Enter</kbd> or <kbd>Space</kbd> Focus card actions</li>
                <li><kbd>C</kbd> Quick connect with current profile</li>
                <li><kbd>P</kbd> Quick pass on current profile</li>
                <li><kbd>Home</kbd> Go to first card</li>
                <li><kbd>End</kbd> Go to last card</li>
                <li><kbd>Esc</kbd> Return to main list</li>
              </ul>
              <h4>Action Buttons:</h4>
              <ul>
                <li><kbd>←</kbd><kbd>→</kbd> Navigate between Pass and Connect buttons</li>
                <li><kbd>Enter</kbd> or <kbd>Space</kbd> Activate button</li>
                <li><kbd>Esc</kbd> Return to card</li>
              </ul>
            </div>
          </details>
        </div>

        <!-- Discovery Cards -->
        <div
          class="discovery-cards"
          *ngIf="!isLoading && !error && discoveries.length > 0"
          role="list"
          [attr.aria-label]="discoveries.length + ' soul connection matches found'"
          tabindex="-1"
          class="stagger">
          <!-- Undo banner -->
          <div class="undo-banner" *ngIf="lastAction" role="status" aria-live="polite">
            <span>{{ lastAction.message }}</span>
            <button type="button" class="undo-btn" (click)="undoLastAction()">Undo</button>
          </div>
          <article
            *ngFor="let discovery of discoveries; trackBy: trackByUserId; let i = index"
            class="soul-card discovery-card"
            role="listitem"
            [attr.aria-labelledby]="'card-title-' + discovery.user_id"
            [attr.aria-describedby]="'card-desc-' + discovery.user_id"
            [@cardAnimation]="getCardAnimation(discovery.user_id)"
            [attr.tabindex]="i === currentCardIndex ? 0 : -1"
            [attr.data-card-index]="i"
            appSwipe
            [swipeConfig]="getSwipeConfig()"
            [swipeEnabled]="true"
            (swipeLeft)="onSwipeLeft(discovery, $event)"
            (swipeRight)="onSwipeRight(discovery, $event)"
            (swipeUp)="onSwipeUp(discovery, $event)"
            (swipeMove)="onSwipeMove($event)"
            (keydown)="handleCardKeydown($event, discovery, i)"
            (focus)="onCardFocus(i)"
            (blur)="onCardBlur(i)"
            (mouseenter)="onCardHover(discovery, true)"
            (mouseleave)="onCardHover(discovery, false)">

            <!-- Soul Connection Display -->
            <div class="soul-connection-header"
                 appOnboardingTarget="soul-connection-display">
              <app-soul-orb
                size="medium"
                [state]="getSoulOrbState(discovery)"
                [energyLevel]="getEnergyLevel(discovery.compatibility.total_compatibility)"
                [compatibilityScore]="discovery.compatibility.total_compatibility"
                [showCompatibility]="true"
                [showParticles]="discovery.compatibility.total_compatibility >= 70"
                [showSparkles]="discovery.compatibility.total_compatibility >= 80"
                appOnboardingTarget="soul-orb">
              </app-soul-orb>

              <app-compatibility-score
                [score]="discovery.compatibility.total_compatibility"
                size="small"
                [animated]="false"
                [showDescription]="false"
                [showIndicators]="false"
                [breakdown]="discovery.compatibility.breakdown"
                appOnboardingTarget="compatibility-score">
              </app-compatibility-score>
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
                [attr.aria-labelledby]="'interests-heading-' + discovery.user_id">
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
                (keydown)="handleActionButtonKeydown($event, 'pass', discovery)"
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
                (keydown)="handleActionButtonKeydown($event, 'connect', discovery)"
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
          </article>
        </div>
      </div>
    <!-- End of template -->
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
    DiscoverEmptyStateComponent,
    SoulLoadingComponent,
    CompatibilityScoreComponent,
    SoulOrbComponent,
    OnboardingTargetDirective,
    SwipeDirective,
    ABTestDirective,
    ABTestConfigPipe
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
export class DiscoverComponent implements OnInit, OnDestroy {
  discoveries: DiscoveryResponse[] = [];
  currentUser: User | null = null;
  isLoading = false;
  isActing = false;
  error: string | null = null;
  needsOnboarding = false;
  showFilters = false;
  cardAnimations: Map<number, string> = new Map();
  loadingProgress = 0;

  // Keyboard navigation state
  currentCardIndex = 0;
  isCardFocused = false;

  // Card interaction state
  hoveredCards = new Set<number>();
  lastAction: { type: 'pass' | 'connect' | 'super_like'; item: DiscoveryResponse; index: number; message: string; timeoutId: any } | null = null;

  discoveryFilters: DiscoveryRequest = {
    max_results: 10,
    min_compatibility: 50,
    hide_photos: true,
    age_range_min: 21,
    age_range_max: 35
  };

  constructor(
    private readonly router: Router,
    private readonly soulConnectionService: SoulConnectionService,
    private readonly authService: AuthService,
    private readonly errorLoggingService: ErrorLoggingService,
    private readonly hapticFeedbackService: HapticFeedbackService,
    private readonly abTestingService: ABTestingService
  ) {}

  ngOnInit(): void {
    // Initialize A/B testing
    this.initializeABTesting();
    
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
    this.currentCardIndex = 0; // Reset card navigation
    console.log('Loading discoveries with filters:', this.discoveryFilters);
    this.announceAction('Loading soul connections...');
    // Trigger loading haptic feedback
    this.hapticFeedbackService.triggerLoadingFeedback();

    this.loadDiscoveriesWithProgress();
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
    this.announceAction(this.showFilters ? 'Filters expanded' : 'Filters collapsed');

    // Focus first filter control when opening
    if (this.showFilters) {
      setTimeout(() => {
        const firstFilterControl = document.querySelector('.filter-content mat-slide-toggle, .filter-content mat-slider') as HTMLElement;
        firstFilterControl?.focus();
      }, 100);
    }
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


  onPass(userId: number): void {
    if (this.isActing) return;

    const discovery = this.discoveries.find(d => d.user_id === userId);
    const firstName = discovery?.profile_preview.first_name || 'this profile';

    this.isActing = true;
    this.cardAnimations.set(userId, 'pass');
    // Trigger gentle pass haptic feedback
    this.hapticFeedbackService.triggerPassFeedback();
    this.announceAction(`Passing on ${firstName}'s profile...`);

    // Remove from discoveries after animation
    setTimeout(() => {
      const removedIndex = this.discoveries.findIndex(d => d.user_id === userId);
      const removedItem = this.discoveries.find(d => d.user_id === userId)!;
      this.discoveries = this.discoveries.filter(d => d.user_id !== userId);
      this.queueUndo('pass', removedItem, removedIndex, `Passed on ${firstName}.`);
      this.isActing = false;

      // Update navigation index if needed
      if (this.currentCardIndex >= this.discoveries.length) {
        this.currentCardIndex = Math.max(0, this.discoveries.length - 1);
      }

      // Focus next card if available
      if (this.discoveries.length > 0) {
        setTimeout(() => {
          this.navigateToCard(this.currentCardIndex);
          this.announceAction(`Passed on ${firstName}. ${this.discoveries.length} profile${this.discoveries.length === 1 ? '' : 's'} remaining.`);
        }, 100);
      } else {
        this.announceAction(`Passed on ${firstName}. No more profiles to review.`);
      }
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

  trackByUserId(_index: number, discovery: DiscoveryResponse): number {
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

  /**
   * Handle keyboard navigation for discovery cards
   */
  handleCardKeydown(event: KeyboardEvent, discovery: DiscoveryResponse, index: number): void {
    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        event.preventDefault();
        this.navigateToCard(index + 1);
        this.announceCardNavigation(index + 1);
        break;

      case 'ArrowUp':
      case 'ArrowLeft':
        event.preventDefault();
        this.navigateToCard(index - 1);
        this.announceCardNavigation(index - 1);
        break;

      case 'Home':
        event.preventDefault();
        this.navigateToCard(0);
        this.announceCardNavigation(0);
        break;

      case 'End':
        event.preventDefault();
        this.navigateToCard(this.discoveries.length - 1);
        this.announceCardNavigation(this.discoveries.length - 1);
        break;

      case 'Enter':
      case ' ':
        event.preventDefault();
        this.focusCardActions(discovery);
        break;

      case 'p':
      case 'P':
        event.preventDefault();
        this.onPass(discovery.user_id);
        this.announceAction(`Passed on ${discovery.profile_preview.first_name}'s profile`);
        break;

      case 'c':
      case 'C':
        event.preventDefault();
        this.onConnect(discovery);
        this.announceAction(`Connecting with ${discovery.profile_preview.first_name}`);
        break;

      case 'Escape':
        event.preventDefault();
        this.blurCurrentCard();
        break;
    }
  }

  /**
   * Navigate to a specific card index
   */
  private navigateToCard(targetIndex: number): void {
    if (this.discoveries.length === 0) return;

    // Wrap around navigation
    if (targetIndex < 0) {
      targetIndex = this.discoveries.length - 1;
    } else if (targetIndex >= this.discoveries.length) {
      targetIndex = 0;
    }

    this.currentCardIndex = targetIndex;

    // Focus the card element
    setTimeout(() => {
      const cardElement = document.querySelector(`[data-card-index="${targetIndex}"]`) as HTMLElement;
      cardElement?.focus();
    }, 0);
  }

  /**
   * Focus on card action buttons
   */
  private focusCardActions(discovery: DiscoveryResponse): void {
    setTimeout(() => {
      const cardElement = document.querySelector(`[data-card-index="${this.currentCardIndex}"]`);
      const firstActionButton = cardElement?.querySelector('.card-actions button') as HTMLElement;
      firstActionButton?.focus();
      this.announceAction(`Focused on actions for ${discovery.profile_preview.first_name}`);
    }, 0);
  }

  /**
   * Blur current card and return focus to main container
   */
  private blurCurrentCard(): void {
    const mainContainer = document.querySelector('.discovery-cards') as HTMLElement;
    mainContainer?.focus();
    this.announceAction('Returned to discovery list');
  }

  /**
   * Handle card focus events
   */
  onCardFocus(index: number): void {
    this.currentCardIndex = index;
    this.isCardFocused = true;
  }

  /**
   * Handle card blur events
   */
  onCardBlur(_index: number): void {
    this.isCardFocused = false;
  }

  /**
   * Announce card navigation to screen readers
   */
  private announceCardNavigation(newIndex: number): void {
    if (newIndex >= 0 && newIndex < this.discoveries.length) {
      const discovery = this.discoveries[newIndex];
      const announcement = `Card ${newIndex + 1} of ${this.discoveries.length}: ${discovery.profile_preview.first_name}, ${discovery.compatibility.total_compatibility}% compatibility`;
      this.announceAction(announcement);
    }
  }

  /**
   * Announce actions to screen readers using accessibility service
   */
  private announceAction(message: string): void {
    // Create live region for immediate announcements
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'assertive');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    // Remove after announcement
    setTimeout(() => {
      if (announcement.parentNode) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  }

  /**
   * Handle keyboard navigation for action buttons within cards
   */
  handleActionButtonKeydown(event: KeyboardEvent, action: 'pass' | 'connect', discovery: DiscoveryResponse): void {
    const cardElement = (event.target as HTMLElement).closest('.soul-card');
    const actionButtons = Array.from(cardElement?.querySelectorAll('.card-actions button') || []) as HTMLElement[];
    const currentButtonIndex = actionButtons.findIndex(btn => btn === event.target);

    switch (event.key) {
      case 'ArrowLeft':
      case 'ArrowUp': {
        event.preventDefault();
        const prevButton = actionButtons[currentButtonIndex - 1] || actionButtons[actionButtons.length - 1];
        prevButton?.focus();
        break;
      }

      case 'ArrowRight':
      case 'ArrowDown': {
        event.preventDefault();
        const nextButton = actionButtons[currentButtonIndex + 1] || actionButtons[0];
        nextButton?.focus();
        break;
      }

      case 'Enter':
      case ' ':
        event.preventDefault();
        if (action === 'pass') {
          this.onPass(discovery.user_id);
          this.announceAction(`Passed on ${discovery.profile_preview.first_name}'s profile`);
        } else {
          this.onConnect(discovery);
          this.announceAction(`Connecting with ${discovery.profile_preview.first_name}`);
        }
        break;

      case 'Escape': {
        event.preventDefault();
        // Return focus to the card
        const card = cardElement as HTMLElement;
        card?.focus();
        this.announceAction(`Returned to ${discovery.profile_preview.first_name}'s card`);
        break;
      }
    }
  }

  /**
   * Handle keyboard navigation for filter controls
   */
  handleFilterKeydown(event: KeyboardEvent, filterType: 'toggle' | 'slider'): void {
    const filterContainer = document.querySelector('.filter-content');
    const filterControls = Array.from(filterContainer?.querySelectorAll('mat-slide-toggle, mat-slider') || []) as HTMLElement[];
    const currentControlIndex = filterControls.findIndex(control =>
      control.contains(event.target as Node) || control === event.target
    );

    switch (event.key) {
      case 'ArrowDown': {
        event.preventDefault();
        const nextControl = filterControls[currentControlIndex + 1] || filterControls[0];
        nextControl?.focus();
        this.announceAction('Next filter control');
        break;
      }

      case 'ArrowUp': {
        event.preventDefault();
        const prevControl = filterControls[currentControlIndex - 1] || filterControls[filterControls.length - 1];
        prevControl?.focus();
        this.announceAction('Previous filter control');
        break;
      }

      case 'Home':
        event.preventDefault();
        filterControls[0]?.focus();
        this.announceAction('First filter control');
        break;

      case 'End':
        event.preventDefault();
        filterControls[filterControls.length - 1]?.focus();
        this.announceAction('Last filter control');
        break;

      case 'Escape': {
        event.preventDefault();
        const filterToggleButton = document.querySelector('.filter-toggle') as HTMLElement;
        filterToggleButton?.focus();
        this.announceAction('Returned to filter toggle button');
        break;
      }
    }

    // Announce filter value changes
    if (filterType === 'slider' && (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
      setTimeout(() => {
        if (event.target && 'value' in event.target) {
          const slider = event.target as any;
          const ariaLabel = slider.getAttribute('aria-label') || 'Filter';
          this.announceAction(`${ariaLabel}: ${slider.value}`);
        }
      }, 100);
    }
  }

  /**
   * Handle card hover interactions for emotional feedback
   */
  onCardHover(discovery: DiscoveryResponse, isHovering: boolean): void {
    const userId = discovery.user_id;

    if (isHovering) {
      this.hoveredCards.add(userId);

      // Add compatibility-based class for special hover effects
      setTimeout(() => {
        const cardElement = document.querySelector(`[data-card-index="${this.discoveries.findIndex(d => d.user_id === userId)}"]`);
        if (cardElement && discovery.compatibility.total_compatibility >= 80) {
          cardElement.classList.add('high-compatibility');
        }
      }, 0);

      // Announce hover for screen readers if compatibility is high
      if (discovery.compatibility.total_compatibility >= 80) {
        this.announceAction(`High compatibility profile: ${discovery.profile_preview.first_name}, ${discovery.compatibility.total_compatibility}% match`);
        // Trigger haptic feedback for high compatibility
        this.hapticFeedbackService.triggerHighCompatibilityFeedback();
      } else {
        // Gentle hover feedback for medium compatibility
        this.hapticFeedbackService.triggerHoverFeedback();
      }

      // Trigger soul orb hover effects
      this.triggerSoulOrbInteraction(userId, 'hover');

    } else {
      this.hoveredCards.delete(userId);

      // Remove compatibility class
      setTimeout(() => {
        const cardElement = document.querySelector(`[data-card-index="${this.discoveries.findIndex(d => d.user_id === userId)}"]`);
        if (cardElement) {
          cardElement.classList.remove('high-compatibility');
        }
      }, 0);
    }
  }

  /**
   * Trigger soul orb interactions
   */
  private triggerSoulOrbInteraction(userId: number, interaction: 'hover' | 'connect' | 'pass'): void {
    // Find soul orb in the card and trigger appropriate interaction
    const cardIndex = this.discoveries.findIndex(d => d.user_id === userId);
    const cardElement = document.querySelector(`[data-card-index="${cardIndex}"]`);
    const soulOrbContainer = cardElement?.querySelector('.soul-orb-display');

    if (soulOrbContainer) {
      switch (interaction) {
        case 'hover':
          // Trigger hover effects on soul orb
          soulOrbContainer.dispatchEvent(new Event('mouseenter'));
          break;
        case 'connect': {
          // Trigger celebration animation
          const soulOrbComponent = soulOrbContainer.querySelector('app-soul-orb');
          if (soulOrbComponent) {
            // Access component instance if needed for celebration
            this.triggerConnectionCelebration(userId);
          }
          break;
        }
      }
    }
  }

  /**
   * Enhanced connection method with celebration
   */
  onConnect(discovery: DiscoveryResponse): void {
    if (this.isActing) return;

    this.isActing = true;
    this.cardAnimations.set(discovery.user_id, 'connect');

    // Trigger soul orb celebration before API call
    this.triggerSoulOrbInteraction(discovery.user_id, 'connect');

    // Trigger haptic feedback for connection attempt
    this.hapticFeedbackService.triggerCompatibilityFeedback(discovery.compatibility.total_compatibility);

    this.announceAction(`Initiating soul connection with ${discovery.profile_preview.first_name}...`);

    const connectionData: SoulConnectionCreate = {
      user2_id: discovery.user_id
    };

    this.soulConnectionService.initiateSoulConnection(connectionData).subscribe({
      next: (connection: any) => {
        // Enhanced success animation
        setTimeout(() => {
          // Trigger additional celebration effects
          this.triggerConnectionSuccessEffects(discovery);

          this.discoveries = this.discoveries.filter(d => d.user_id !== discovery.user_id);
          this.isActing = false;

          // Update navigation index if needed
          if (this.currentCardIndex >= this.discoveries.length) {
            this.currentCardIndex = Math.max(0, this.discoveries.length - 1);
          }

          this.announceAction(`Successfully connected with ${discovery.profile_preview.first_name}! Navigating to your connection...`);

          // Navigate to connection or show success message
          this.router.navigate(['/connections', connection.id]);
        }, 300);
      },
      error: (err) => {
        this.error = err.message || 'Failed to initiate connection';
        this.cardAnimations.set(discovery.user_id, 'default');
        this.isActing = false;
        this.announceAction(`Failed to connect with ${discovery.profile_preview.first_name}: ${this.error}`);
      }
    });
  }

  /**
   * Trigger connection celebration animation
   */
  private triggerConnectionCelebration(userId: number): void {
    const cardIndex = this.discoveries.findIndex(d => d.user_id === userId);
    const cardElement = document.querySelector(`[data-card-index="${cardIndex}"]`);

    if (cardElement) {
      // Add celebration class
      cardElement.classList.add('connection-celebrating');

      // Create floating hearts effect
      this.createFloatingHearts(cardElement as HTMLElement);

      // Remove celebration class after animation
      setTimeout(() => {
        cardElement.classList.remove('connection-celebrating');
      }, 2000);
    }
  }

  /**
   * Create floating hearts effect for connection
   */
  private createFloatingHearts(cardElement: HTMLElement): void {
    const heartsCount = 8;

    for (let i = 0; i < heartsCount; i++) {
      const heart = document.createElement('div');
      heart.innerHTML = '💖';
      heart.style.position = 'absolute';
      heart.style.fontSize = '1.5rem';
      heart.style.pointerEvents = 'none';
      heart.style.zIndex = '1000';
      heart.style.left = Math.random() * 100 + '%';
      heart.style.top = Math.random() * 100 + '%';
      heart.style.animation = `float-away 2s ease-out forwards`;
      heart.style.animationDelay = (i * 0.2) + 's';

      cardElement.style.position = 'relative';
      cardElement.appendChild(heart);

      // Remove heart after animation
      setTimeout(() => {
        if (heart.parentNode) {
          heart.parentNode.removeChild(heart);
        }
      }, 2200 + (i * 200));
    }
  }

  /**
   * Trigger additional connection success effects
   */
  private triggerConnectionSuccessEffects(discovery: DiscoveryResponse): void {
    // Create success announcement with sound for screen readers
    this.announceAction(`🎉 Soul connection established with ${discovery.profile_preview.first_name}! Compatibility: ${discovery.compatibility.total_compatibility}%`);

    // Create page-wide celebration effect
    const celebrationOverlay = document.createElement('div');
    celebrationOverlay.style.position = 'fixed';
    celebrationOverlay.style.top = '0';
    celebrationOverlay.style.left = '0';
    celebrationOverlay.style.width = '100%';
    celebrationOverlay.style.height = '100%';
    celebrationOverlay.style.pointerEvents = 'none';
    celebrationOverlay.style.zIndex = '9999';
    celebrationOverlay.style.background = 'radial-gradient(circle, rgba(255, 215, 0, 0.1) 0%, transparent 70%)';
    celebrationOverlay.style.animation = 'celebration-flash 1s ease-out';

    document.body.appendChild(celebrationOverlay);

    setTimeout(() => {
      if (celebrationOverlay.parentNode) {
        document.body.removeChild(celebrationOverlay);
      }
    }, 1000);
  }

  /**
   * Get soul orb state based on discovery data
   */
  getSoulOrbState(discovery: DiscoveryResponse): 'active' | 'connecting' | 'matched' | 'dormant' {
    if (discovery.compatibility.total_compatibility >= 90) {
      return 'matched';
    } else if (discovery.compatibility.total_compatibility >= 70) {
      return 'connecting';
    } else {
      return 'active';
    }
  }

  /**
   * Get energy level based on compatibility score
   */
  getEnergyLevel(compatibilityScore: number): number {
    if (compatibilityScore >= 90) return 5;
    if (compatibilityScore >= 80) return 4;
    if (compatibilityScore >= 70) return 3;
    if (compatibilityScore >= 60) return 2;
    if (compatibilityScore >= 50) return 1;
    return 0;
  }

  /**
   * Enhanced loading with progress updates
   */
  private async loadDiscoveriesWithProgress(): Promise<void> {
    this.isLoading = true;
    this.loadingProgress = 0;
    this.error = null;

    try {
      // Step 1: Analyzing your profile
      this.loadingProgress = 0;
      await this.delay(800);

      // Step 2: Finding compatible souls
      this.loadingProgress = 1;
      await this.delay(800);

      // Step 3: Calculating compatibility
      this.loadingProgress = 2;

      const discoveries = await new Promise<DiscoveryResponse[]>((resolve, reject) => {
        this.soulConnectionService.discoverSoulConnections(this.discoveryFilters).subscribe({
          next: (data) => resolve(data || []),
          error: (err) => reject(err instanceof Error ? err : new Error(String(err)))
        });
      });

      // Step 4: Preparing your matches
      this.loadingProgress = 3;
      await this.delay(500);

      this.discoveries = discoveries;

      // Initialize card animations
      this.discoveries.forEach(d => {
        this.cardAnimations.set(d.user_id, 'default');
      });

      // Announce results to screen reader
      if (this.discoveries.length === 0) {
        this.announceAction('No soul connections found. Try adjusting your filters.');
      } else {
        this.announceAction(`Found ${this.discoveries.length} soul connection${this.discoveries.length === 1 ? '' : 's'}. Use arrow keys to navigate between profiles.`);
      }
    } catch (error: any) {
      console.error('Discovery error:', error);
      this.error = error.message || 'Failed to load soul connections';
      this.announceAction(`Error loading connections: ${this.error}`);
      this.errorLoggingService.logError(error, {
        component: 'discover',
        action: 'load_discoveries',
        filters: this.discoveryFilters
      });
    } finally {
      this.isLoading = false;
      this.loadingProgress = 0;
    }
  }

  /**
   * Utility delay function for loading states
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // === SWIPE GESTURE METHODS ===

  /**
   * Get swipe configuration for discovery cards
   */
  getSwipeConfig() {
    return {
      threshold: 80, // Higher threshold for intentional swipes
      velocityThreshold: 0.5, // Faster swipe required
      timeThreshold: 400, // Quick swipe within 400ms
      enabledDirections: ['left', 'right', 'up'] as ('left' | 'right' | 'up' | 'down')[],
      hapticFeedback: true,
      preventDefaultEvents: true
    };
  }

  /**
   * Handle swipe left gesture (Pass/Reject)
   */
  onSwipeLeft(discovery: DiscoveryResponse, event: SwipeEvent): void {
    // Add visual feedback
    const element = event.element;
    element.classList.add('swipe-pass', 'swipe-left-preview');

    // Trigger haptic feedback
    this.hapticFeedbackService.triggerPassFeedback();

    // Announce action for accessibility
    this.announceAction(`Passed on ${this.getPartnerName(discovery)}`);

    // Perform pass action with animation
    setTimeout(() => {
      this.handlePassAction(discovery);
      element.classList.remove('swipe-pass', 'swipe-left-preview');
    }, 200);

    // Log swipe action
    console.log('Swipe pass action:', {
      userId: discovery.user_id,
      compatibilityScore: discovery.compatibility.total_compatibility,
      swipeVelocity: event.velocity,
      swipeDistance: event.distance
    });
  }

  /**
   * Handle swipe move to preview physics-based movement
   */
  onSwipeMove(event: SwipeEvent): void {
    const element = event.element;
    const deltaX = event.deltaX || 0;
    const deltaY = event.deltaY || 0;
    const rotation = Math.max(-20, Math.min(20, deltaX / 10));
    element.style.transition = 'transform 0s';
    element.style.transform = `translate(${deltaX}px, ${deltaY}px) rotate(${rotation}deg)`;
  }

  /**
   * Handle swipe right gesture (Like/Connect)
   */
  onSwipeRight(discovery: DiscoveryResponse, event: SwipeEvent): void {
    // Add visual feedback
    const element = event.element;
    element.classList.add('swipe-like', 'swipe-right-preview');

    // Trigger haptic feedback based on compatibility
    const compatibilityScore = discovery.compatibility.total_compatibility;
    if (compatibilityScore >= 90) {
      this.hapticFeedbackService.triggerSuccessFeedback(); // Strong feedback for high compatibility
    } else {
      this.hapticFeedbackService.triggerSelectionFeedback();
    }

    // Announce action for accessibility
    this.announceAction(`Connected with ${this.getPartnerName(discovery)}`);

    // Perform connect action with animation
    setTimeout(() => {
      this.handleConnectAction(discovery);
      element.classList.remove('swipe-like', 'swipe-right-preview');
    }, 200);

    // Log swipe action
    console.log('Swipe connect action:', {
      userId: discovery.user_id,
      compatibilityScore: discovery.compatibility.total_compatibility,
      swipeVelocity: event.velocity,
      swipeDistance: event.distance
    });
  }

  /**
   * Handle swipe up gesture (Super Like)
   */
  onSwipeUp(discovery: DiscoveryResponse, event: SwipeEvent): void {
    // Only allow super like for high compatibility
    const compatibilityScore = discovery.compatibility.total_compatibility;
    if (compatibilityScore < 80) {
      // Provide feedback that super like isn't available
      this.hapticFeedbackService.triggerErrorFeedback();
      this.announceAction('Super like requires 80% compatibility or higher');
      return;
    }

    // Add visual feedback
    const element = event.element;
    element.classList.add('swipe-superlike');

    // Strong haptic feedback for super like
    this.hapticFeedbackService.triggerSuccessFeedback();

    // Announce action for accessibility
    this.announceAction(`Super liked ${this.getPartnerName(discovery)}! This shows special interest.`);

    // Perform super like action with special animation
    setTimeout(() => {
      this.superLikeDiscovery(discovery);
      element.classList.remove('swipe-superlike');
    }, 300);

    // Log swipe action
    console.log('Swipe superlike action:', {
      userId: discovery.user_id,
      compatibilityScore: discovery.compatibility.total_compatibility,
      swipeVelocity: event.velocity,
      swipeDistance: event.distance
    });
  }

  /**
   * Super like a discovery (enhanced connection request)
   */
  private superLikeDiscovery(discovery: DiscoveryResponse): void {
    this.soulConnectionService.initiateSoulConnection({ user2_id: discovery.user_id }).subscribe({
      next: (_connection: any) => {
        // Remove from discoveries
        this.discoveries = this.discoveries.filter(d => d.user_id !== discovery.user_id);

        // Show success feedback
        this.announceAction(`Super like sent to ${this.getPartnerName(discovery)}! They'll be notified of your special interest.`);

        // Navigate to connections if this was the last discovery
        if (this.discoveries.length === 0) {
          setTimeout(() => {
            this.router.navigate(['/connections']);
          }, 2000);
        }
      },
      error: (error: any) => {
        this.announceAction(`Failed to send super like: ${error?.message || 'Unknown error'}`);
        this.errorLoggingService.logError(error as any, {
          component: 'discover',
          action: 'super_like',
          targetUserId: discovery.user_id
        });
      }
    });
  }

  /**
   * Get partner name for accessibility announcements
   */
  private getPartnerName(discovery: DiscoveryResponse): string {
    return discovery.profile_preview?.first_name || 'soul connection';
  }

  /**
   * Get current discovery card layout configuration
   */
  getDiscoveryCardConfig(): any {
    return this.abTestingService.getVariantConfig('discovery_card_layout') || {
      layout: 'vertical',
      showCompatibilityFirst: false,
      cardAnimation: 'default',
      buttonStyle: 'standard'
    };
  }

  /**
   * Check if user is in specific A/B test variant
   */
  isInVariant(testId: string, variantId: string): boolean {
    return this.abTestingService.isInVariant(testId, variantId);
  }

  /**
   * Track discovery card interaction
   */
  private trackCardInteraction(discovery: DiscoveryResponse, action: string): void {
    this.abTestingService.trackEvent('discovery_card_layout', action, {
      userId: discovery.user_id,
      compatibilityScore: discovery.compatibility.total_compatibility,
      cardPosition: this.discoveries.findIndex(d => d.user_id === discovery.user_id)
    });
  }

  /**
   * Enhanced pass action with A/B testing
   */
  private handlePassAction(discovery: DiscoveryResponse): void {
    // Track A/B test interaction
    this.trackCardInteraction(discovery, 'card_passed');
    
    // Remove from discoveries list
    const removedIndex = this.discoveries.findIndex(d => d.user_id === discovery.user_id);
    this.discoveries = this.discoveries.filter(d => d.user_id !== discovery.user_id);
    this.queueUndo('pass', discovery, removedIndex, `Passed on ${this.getPartnerName(discovery)}.`);

    // Show next discovery if available
    if (this.discoveries.length === 0) {
      this.loadDiscoveries();
    }
  }

  /**
   * Track time spent on discovery page
   */
  private handleConnectAction(discovery: DiscoveryResponse): void {
    this.soulConnectionService.initiateSoulConnection({ user2_id: discovery.user_id }).subscribe({
      next: (_connection: any) => {
        // Remove from discoveries
        const removedIndex = this.discoveries.findIndex(d => d.user_id === discovery.user_id);
        this.discoveries = this.discoveries.filter(d => d.user_id !== discovery.user_id);
        this.queueUndo('connect', discovery, removedIndex, `Connection request sent to ${this.getPartnerName(discovery)}.`);

        // Show success feedback
        this.announceAction(`Connection request sent to ${this.getPartnerName(discovery)}!`);
      },
      error: (error: any) => {
        console.error('Failed to create connection:', error);
        this.announceAction('Failed to send connection request. Please try again.');
      }
    });
  }

  /**
   * Queue undo action for last dismissal/connect
   */
  private queueUndo(type: 'pass' | 'connect' | 'super_like', item: DiscoveryResponse, index: number, message: string): void {
    if (this.lastAction?.timeoutId) {
      clearTimeout(this.lastAction.timeoutId);
    }
    const timeoutId = setTimeout(() => {
      this.lastAction = null;
    }, 5000);
    this.lastAction = { type, item, index, message, timeoutId };
  }

  /**
   * Undo the last action if within the time window
   */
  undoLastAction(): void {
    if (!this.lastAction) return;
    const { item, index, timeoutId } = this.lastAction;
    clearTimeout(timeoutId);
    // Reinsert item at previous index
    this.discoveries = [
      ...this.discoveries.slice(0, index),
      item,
      ...this.discoveries.slice(index)
    ];
    this.cardAnimations.set(item.user_id, 'default');
    this.lastAction = null;
    this.announceAction('Action undone.');
    // Focus restored card
    setTimeout(() => this.navigateToCard(index), 0);
  }
}
