import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { OnboardingService, OnboardingState } from '@core/services/onboarding.service';
import { AuthService } from '@core/services/auth.service';
import { OnboardingTooltipComponent } from '@shared/components/onboarding-tooltip/onboarding-tooltip.component';
import { OnboardingWelcomeComponent } from '@shared/components/onboarding-welcome/onboarding-welcome.component';

@Component({
  selector: 'app-onboarding-manager',
  standalone: true,
  imports: [
    CommonModule,
    OnboardingTooltipComponent,
    OnboardingWelcomeComponent
  ],
  template: `
    <!-- Welcome Modal for New Users -->
    <app-onboarding-welcome
      *ngIf="showWelcome">
    </app-onboarding-welcome>

    <!-- Interactive Tutorial Tooltip -->
    <app-onboarding-tooltip
      *ngIf="showTooltip">
    </app-onboarding-tooltip>

    <!-- Onboarding Controls (Debug/Admin) -->
    <div 
      class="onboarding-controls"
      *ngIf="showControls && isDevelopment"
      role="region"
      aria-label="Onboarding development controls">
      
      <div class="controls-header">
        <h4>Onboarding Controls</h4>
        <button 
          class="toggle-btn"
          type="button"
          (click)="toggleControls()"
          aria-label="Toggle onboarding controls">
          {{ controlsExpanded ? '−' : '+' }}
        </button>
      </div>

      <div class="controls-content" *ngIf="controlsExpanded">
        <!-- Tour Management -->
        <div class="control-section">
          <h5>Available Tours</h5>
          <div class="tour-list">
            <div 
              *ngFor="let tour of availableTours"
              class="tour-item"
              [class.completed]="isTourCompleted(tour.id)">
              <div class="tour-info">
                <span class="tour-name">{{ tour.name }}</span>
                <span class="tour-category">{{ tour.category }}</span>
              </div>
              <div class="tour-actions">
                <button 
                  class="start-btn"
                  type="button"
                  [disabled]="currentState?.currentTour === tour.id"
                  (click)="startTour(tour.id)"
                  [attr.aria-label]="'Start ' + tour.name + ' tour'">
                  {{ currentState?.currentTour === tour.id ? 'Active' : 'Start' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- State Information -->
        <div class="control-section">
          <h5>Current State</h5>
          <div class="state-info">
            <div class="state-item">
              <span class="label">Current Tour:</span>
              <span class="value">{{ currentState?.currentTour || 'None' }}</span>
            </div>
            <div class="state-item">
              <span class="label">Current Step:</span>
              <span class="value">{{ currentState?.currentStep || 0 }}</span>
            </div>
            <div class="state-item">
              <span class="label">Completed Tours:</span>
              <span class="value">{{ currentState?.completedTours?.length || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="control-section">
          <h5>Quick Actions</h5>
          <div class="quick-actions">
            <button 
              class="action-btn"
              type="button"
              (click)="showWelcomeModal()"
              aria-label="Show welcome modal">
              Show Welcome
            </button>
            <button 
              class="action-btn"
              type="button"
              (click)="resetOnboarding()"
              aria-label="Reset all onboarding progress">
              Reset All
            </button>
            <button 
              class="action-btn"
              type="button"
              (click)="completeCurrentTour()"
              [disabled]="!currentState?.currentTour"
              aria-label="Complete current tour">
              Complete Tour
            </button>
          </div>
        </div>

        <!-- Preferences -->
        <div class="control-section">
          <h5>Preferences</h5>
          <div class="preferences">
            <label class="preference-item">
              <input 
                type="checkbox"
                [checked]="currentState?.userPreferences?.showTutorials || false"
                (change)="updatePreference('showTutorials', $event)">
              Show Tutorials
            </label>
            <label class="preference-item">
              <input 
                type="checkbox"
                [checked]="currentState?.userPreferences?.skipIntroductions || false"
                (change)="updatePreference('skipIntroductions', $event)">
              Skip Introductions
            </label>
            <label class="preference-item">
              <input 
                type="checkbox"
                [checked]="currentState?.userPreferences?.autoAdvance || false"
                (change)="updatePreference('autoAdvance', $event)">
              Auto Advance
            </label>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    /* Onboarding Controls */
    .onboarding-controls {
      position: fixed;
      bottom: 20px;
      left: 20px;
      max-width: 350px;
      background: var(--surface-color);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      z-index: 8000;
      font-size: 0.875rem;
    }

    .controls-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem;
      border-bottom: 1px solid var(--border-color);
      background: var(--surface-secondary);
      border-radius: 12px 12px 0 0;
    }

    .controls-header h4 {
      margin: 0;
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-primary);
    }

    .toggle-btn {
      background: none;
      border: none;
      color: var(--text-secondary);
      cursor: pointer;
      padding: 0.25rem;
      border-radius: 4px;
      font-weight: bold;
      
      &:hover {
        background: var(--surface-tertiary);
        color: var(--text-primary);
      }
    }

    .controls-content {
      padding: 1rem;
      max-height: 60vh;
      overflow-y: auto;
    }

    .control-section {
      margin-bottom: 1.5rem;
      
      &:last-child {
        margin-bottom: 0;
      }
    }

    .control-section h5 {
      margin: 0 0 0.75rem 0;
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--text-primary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* Tour List */
    .tour-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .tour-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem;
      background: var(--surface-secondary);
      border-radius: 8px;
      border: 1px solid var(--border-color);
      
      &.completed {
        border-color: var(--success-color);
        background: rgba(52, 211, 153, 0.05);
      }
    }

    .tour-info {
      flex: 1;
    }

    .tour-name {
      display: block;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 0.25rem;
    }

    .tour-category {
      display: block;
      font-size: 0.75rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .start-btn {
      padding: 0.5rem 1rem;
      border: none;
      border-radius: 6px;
      background: var(--primary-color);
      color: white;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      
      &:hover:not(:disabled) {
        background: var(--primary-color-dark);
      }
      
      &:disabled {
        background: var(--surface-tertiary);
        color: var(--text-secondary);
        cursor: not-allowed;
      }
    }

    /* State Info */
    .state-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .state-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .state-item .label {
      font-weight: 500;
      color: var(--text-secondary);
    }

    .state-item .value {
      font-weight: 600;
      color: var(--text-primary);
    }

    /* Quick Actions */
    .quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .action-btn {
      padding: 0.5rem 0.75rem;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      background: var(--surface-secondary);
      color: var(--text-primary);
      font-size: 0.75rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      
      &:hover:not(:disabled) {
        background: var(--surface-tertiary);
        border-color: var(--primary-color);
      }
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }

    /* Preferences */
    .preferences {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .preference-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      font-size: 0.85rem;
      color: var(--text-primary);
      
      input[type="checkbox"] {
        margin: 0;
      }
    }

    /* Responsive */
    @media (max-width: 768px) {
      .onboarding-controls {
        bottom: 10px;
        left: 10px;
        right: 10px;
        max-width: none;
      }
      
      .controls-content {
        max-height: 50vh;
      }
      
      .tour-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }
      
      .tour-actions {
        width: 100%;
        display: flex;
        justify-content: flex-end;
      }
    }

    /* Dark theme */
    .dark-theme {
      .onboarding-controls {
        background: var(--surface-color);
        border-color: var(--border-color);
      }
    }
  `]
})
export class OnboardingManagerComponent implements OnInit, OnDestroy {
  showWelcome = false;
  showTooltip = false;
  showControls = false;
  controlsExpanded = false;
  isDevelopment = false;

  currentState: OnboardingState | null = null;
  availableTours: any[] = [];

  private subscription = new Subscription();

  constructor(
    private onboardingService: OnboardingService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Check if we're in development mode
    this.isDevelopment = !environment.production;
    
    // Subscribe to onboarding state changes
    this.subscription.add(
      this.onboardingService.state$.subscribe(state => {
        this.currentState = state;
        this.updateVisibility(state);
      })
    );

    // Subscribe to active step changes
    this.subscription.add(
      this.onboardingService.activeStep$.subscribe(step => {
        this.showTooltip = !!step;
      })
    );

    // Get available tours
    this.availableTours = this.onboardingService.getAvailableTours();

    // Check if user is new and should see welcome
    this.checkForNewUser();

    // Set up keyboard shortcuts for development
    if (this.isDevelopment) {
      this.setupDevelopmentShortcuts();
    }
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
    this.removeDevelopmentShortcuts();
  }

  /**
   * Check if user should see welcome modal
   */
  private checkForNewUser(): void {
    const isNewUser = this.onboardingService.isNewUser();
    const state = this.currentState;
    
    // Show welcome if:
    // - User is new
    // - Tutorials are enabled
    // - No tour is currently active
    if (isNewUser && 
        state?.userPreferences.showTutorials && 
        !state.currentTour) {
      this.showWelcome = true;
    }
  }

  /**
   * Update component visibility based on state
   */
  private updateVisibility(state: OnboardingState): void {
    // Hide welcome when tour starts
    if (state.currentTour && this.showWelcome) {
      this.showWelcome = false;
    }

    // Show controls in development
    if (this.isDevelopment) {
      this.showControls = true;
    }
  }

  /**
   * Start a specific tour
   */
  startTour(tourId: string): void {
    this.onboardingService.startTour(tourId);
  }

  /**
   * Show welcome modal manually
   */
  showWelcomeModal(): void {
    this.showWelcome = true;
  }

  /**
   * Reset all onboarding progress
   */
  resetOnboarding(): void {
    this.onboardingService.resetOnboarding();
    this.showWelcome = this.onboardingService.isNewUser();
  }

  /**
   * Complete current tour
   */
  completeCurrentTour(): void {
    this.onboardingService.completeTour();
  }

  /**
   * Toggle controls visibility
   */
  toggleControls(): void {
    this.controlsExpanded = !this.controlsExpanded;
  }

  /**
   * Update user preference
   */
  updatePreference(key: string, event: Event): void {
    const target = event.target as HTMLInputElement;
    const preferences = { [key]: target.checked };
    this.onboardingService.updatePreferences(preferences);
  }

  /**
   * Check if tour is completed
   */
  isTourCompleted(tourId: string): boolean {
    return this.onboardingService.isTourCompleted(tourId);
  }

  /**
   * Setup development keyboard shortcuts
   */
  private setupDevelopmentShortcuts(): void {
    document.addEventListener('keydown', this.handleDevelopmentShortcuts);
  }

  /**
   * Remove development keyboard shortcuts
   */
  private removeDevelopmentShortcuts(): void {
    document.removeEventListener('keydown', this.handleDevelopmentShortcuts);
  }

  /**
   * Handle development keyboard shortcuts
   */
  private handleDevelopmentShortcuts = (event: KeyboardEvent): void => {
    // Only in development mode
    if (!this.isDevelopment) return;

    // Ctrl/Cmd + Shift + O: Toggle onboarding controls
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'O') {
      event.preventDefault();
      this.showControls = !this.showControls;
      this.controlsExpanded = this.showControls;
    }

    // Ctrl/Cmd + Shift + W: Show welcome modal
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'W') {
      event.preventDefault();
      this.showWelcomeModal();
    }

    // Ctrl/Cmd + Shift + R: Reset onboarding
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'R') {
      event.preventDefault();
      this.resetOnboarding();
    }

    // Ctrl/Cmd + Shift + 1-9: Start specific tours
    const numberKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && numberKeys.includes(event.key)) {
      event.preventDefault();
      const tourIndex = parseInt(event.key) - 1;
      if (tourIndex < this.availableTours.length) {
        this.startTour(this.availableTours[tourIndex].id);
      }
    }
  };

  /**
   * Trigger tour based on page/feature
   */
  triggerTourForFeature(feature: string): void {
    // Map features to tour triggers
    const featureTourMap: { [key: string]: string } = {
      'discovery': 'discovery-tour',
      'conversations': 'conversation-tour',
      'profile': 'profile-tour'
    };

    const tourId = featureTourMap[feature];
    if (tourId) {
      this.onboardingService.checkTourTrigger(feature);
    }
  }
}