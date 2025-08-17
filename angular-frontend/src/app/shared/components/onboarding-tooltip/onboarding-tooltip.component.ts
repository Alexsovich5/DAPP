import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { Subscription } from 'rxjs';
import { OnboardingService, OnboardingStep } from '../../../core/services/onboarding.service';
import { HapticFeedbackService } from '../../../core/services/haptic-feedback.service';

@Component({
  selector: 'app-onboarding-tooltip',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    <div 
      class="onboarding-overlay"
      *ngIf="currentStep && currentStep.showOverlay"
      [@overlayAnimation]="'visible'"
      (click)="onOverlayClick()"
      role="presentation"
      aria-hidden="true">
    </div>

    <div 
      class="onboarding-tooltip"
      #tooltip
      *ngIf="currentStep"
      [@tooltipAnimation]="'visible'"
      [ngClass]="[
        'position-' + currentStep.position,
        'theme-' + (currentStep.emotionalTheme || 'discovery'),
        { 'has-overlay': currentStep.showOverlay }
      ]"
      role="dialog"
      [attr.aria-labelledby]="'tooltip-title-' + currentStep.id"
      [attr.aria-describedby]="'tooltip-description-' + currentStep.id"
      aria-modal="true">
      
      <!-- Soul Energy Animation for Emotional Themes -->
      <div class="soul-energy" [ngClass]="'energy-' + (currentStep.emotionalTheme || 'discovery')">
        <svg class="energy-orb" width="40" height="40" viewBox="0 0 40 40" aria-hidden="true">
          <defs>
            <radialGradient [id]="'energy-gradient-' + currentStep.id" cx="50%" cy="50%" r="50%">
              <stop offset="0%" [attr.stop-color]="getEnergyColors().center"/>
              <stop offset="70%" [attr.stop-color]="getEnergyColors().middle"/>
              <stop offset="100%" [attr.stop-color]="getEnergyColors().outer"/>
            </radialGradient>
          </defs>
          <circle 
            cx="20" cy="20" r="15"
            [attr.fill]="'url(#energy-gradient-' + currentStep.id + ')'"
            class="energy-core">
          </circle>
          <circle 
            cx="20" cy="20" r="18"
            fill="none"
            [attr.stroke]="getEnergyColors().accent"
            stroke-width="2"
            stroke-opacity="0.6"
            class="energy-ring">
          </circle>
        </svg>
      </div>

      <!-- Tooltip Content -->
      <div class="tooltip-content">
        <!-- Header -->
        <div class="tooltip-header">
          <h3 
            [id]="'tooltip-title-' + currentStep.id"
            class="tooltip-title">
            {{ currentStep.title }}
          </h3>
          
          <button 
            class="close-btn"
            type="button"
            aria-label="Close tutorial"
            (click)="onSkipTour()"
            (keydown.enter)="onSkipTour()"
            matTooltip="Close tutorial">
            <mat-icon aria-hidden="true">close</mat-icon>
          </button>
        </div>

        <!-- Description -->
        <div 
          [id]="'tooltip-description-' + currentStep.id"
          class="tooltip-description">
          <p>{{ currentStep.description }}</p>
        </div>

        <!-- Progress Indicator -->
        <div class="progress-container" *ngIf="showProgress">
          <div class="progress-bar">
            <div 
              class="progress-fill"
              [style.width.%]="progressPercentage">
            </div>
          </div>
          <span class="progress-text" aria-live="polite">
            Step {{ currentStepIndex + 1 }} of {{ totalSteps }}
          </span>
        </div>

        <!-- Action Buttons -->
        <div class="tooltip-actions" role="group" aria-label="Tutorial navigation">
          <button 
            *ngFor="let action of currentStep.actions; trackBy: trackAction"
            class="action-btn"
            [ngClass]="{ 'primary': action.primary, 'secondary': !action.primary }"
            type="button"
            [attr.aria-label]="getActionAriaLabel(action)"
            (click)="onAction(action)"
            (keydown.enter)="onAction(action)"
            [disabled]="isProcessingAction">
            {{ action.label }}
          </button>
        </div>

        <!-- Keyboard Hint -->
        <div class="keyboard-hint" *ngIf="showKeyboardHints">
          <small>
            <kbd>Esc</kbd> to close • 
            <kbd>Space</kbd> or <kbd>Enter</kbd> for primary action •
            <kbd>→</kbd> next • <kbd>←</kbd> previous
          </small>
        </div>
      </div>

      <!-- Pointer Arrow -->
      <div 
        class="tooltip-arrow"
        *ngIf="currentStep.targetSelector && currentStep.position !== 'center'"
        [ngClass]="'arrow-' + currentStep.position"
        aria-hidden="true">
      </div>
    </div>
  `,
  styles: [`
    /* Overlay */
    .onboarding-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(4px);
      z-index: 9998;
      cursor: pointer;
    }

    /* Main Tooltip */
    .onboarding-tooltip {
      position: fixed;
      max-width: 400px;
      min-width: 300px;
      background: var(--surface-color);
      border-radius: 16px;
      box-shadow: 
        0 24px 48px rgba(0, 0, 0, 0.15),
        0 8px 24px rgba(0, 0, 0, 0.1),
        0 0 0 1px rgba(255, 255, 255, 0.1);
      z-index: 9999;
      border: 2px solid transparent;
      overflow: hidden;
      transform-origin: center;
    }

    /* Positioning */
    .position-center {
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }

    .position-top {
      transform: translateX(-50%);
    }

    .position-bottom {
      transform: translateX(-50%);
    }

    .position-left {
      transform: translateY(-50%);
    }

    .position-right {
      transform: translateY(-50%);
    }

    /* Emotional Themes */
    .theme-discovery {
      border-color: rgba(96, 165, 250, 0.3);
      background: linear-gradient(135deg, 
        var(--surface-color) 0%, 
        rgba(96, 165, 250, 0.05) 100%);
    }

    .theme-connection {
      border-color: rgba(255, 107, 157, 0.3);
      background: linear-gradient(135deg, 
        var(--surface-color) 0%, 
        rgba(255, 107, 157, 0.05) 100%);
    }

    .theme-growth {
      border-color: rgba(52, 211, 153, 0.3);
      background: linear-gradient(135deg, 
        var(--surface-color) 0%, 
        rgba(52, 211, 153, 0.05) 100%);
    }

    .theme-celebration {
      border-color: rgba(255, 215, 0, 0.3);
      background: linear-gradient(135deg, 
        var(--surface-color) 0%, 
        rgba(255, 215, 0, 0.05) 100%);
    }

    /* Soul Energy Animation */
    .soul-energy {
      position: absolute;
      top: -20px;
      right: -20px;
      width: 40px;
      height: 40px;
      z-index: 1;
    }

    .energy-orb {
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
    }

    .energy-core {
      animation: energy-pulse 2s ease-in-out infinite;
      transform-origin: center;
    }

    .energy-ring {
      animation: energy-rotate 4s linear infinite;
      transform-origin: center;
    }

    /* Tooltip Content */
    .tooltip-content {
      padding: 1.5rem;
      position: relative;
      z-index: 2;
    }

    .tooltip-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 1rem;
    }

    .tooltip-title {
      color: var(--text-primary);
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
      flex: 1;
      line-height: 1.4;
    }

    .close-btn {
      background: none;
      border: none;
      color: var(--text-secondary);
      cursor: pointer;
      padding: 0.25rem;
      border-radius: 4px;
      transition: all 0.2s ease;
      margin-left: 1rem;
      flex-shrink: 0;
      
      &:hover, &:focus {
        background: var(--surface-secondary);
        color: var(--text-primary);
      }
    }

    .tooltip-description {
      margin-bottom: 1.5rem;
      
      p {
        color: var(--text-secondary);
        font-size: 1rem;
        line-height: 1.6;
        margin: 0;
      }
    }

    /* Progress Indicator */
    .progress-container {
      margin-bottom: 1.5rem;
    }

    .progress-bar {
      width: 100%;
      height: 4px;
      background: var(--surface-secondary);
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: 0.5rem;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
      border-radius: 2px;
      transition: width 0.3s ease;
      position: relative;
      
      &::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        width: 20px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3));
        animation: progress-shimmer 2s ease-in-out infinite;
      }
    }

    .progress-text {
      font-size: 0.875rem;
      color: var(--text-secondary);
      font-weight: 500;
    }

    /* Action Buttons */
    .tooltip-actions {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }

    .action-btn {
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
      overflow: hidden;
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      &.primary {
        background: var(--primary-color);
        color: white;
        
        &:hover:not(:disabled) {
          background: var(--primary-color-dark);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(255, 107, 157, 0.4);
        }
        
        &:focus {
          outline: 2px solid var(--primary-color);
          outline-offset: 2px;
        }
      }
      
      &.secondary {
        background: var(--surface-secondary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        
        &:hover:not(:disabled) {
          background: var(--surface-tertiary);
          transform: translateY(-1px);
        }
        
        &:focus {
          outline: 2px solid var(--focus-ring-secondary);
          outline-offset: 2px;
        }
      }
    }

    /* Keyboard Hints */
    .keyboard-hint {
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border-color);
      
      small {
        color: var(--text-tertiary);
        font-size: 0.75rem;
      }
      
      kbd {
        background: var(--surface-secondary);
        border: 1px solid var(--border-color);
        border-radius: 3px;
        padding: 0.125rem 0.25rem;
        font-size: 0.7rem;
        font-family: monospace;
      }
    }

    /* Tooltip Arrow */
    .tooltip-arrow {
      position: absolute;
      width: 0;
      height: 0;
      border: 8px solid transparent;
    }

    .arrow-top {
      bottom: -16px;
      left: 50%;
      transform: translateX(-50%);
      border-top-color: var(--surface-color);
    }

    .arrow-bottom {
      top: -16px;
      left: 50%;
      transform: translateX(-50%);
      border-bottom-color: var(--surface-color);
    }

    .arrow-left {
      right: -16px;
      top: 50%;
      transform: translateY(-50%);
      border-left-color: var(--surface-color);
    }

    .arrow-right {
      left: -16px;
      top: 50%;
      transform: translateY(-50%);
      border-right-color: var(--surface-color);
    }

    /* Animations */
    @keyframes energy-pulse {
      0%, 100% { 
        transform: scale(1); 
        opacity: 1; 
      }
      50% { 
        transform: scale(1.1); 
        opacity: 0.8; 
      }
    }

    @keyframes energy-rotate {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    @keyframes progress-shimmer {
      0% { transform: translateX(-100%); }
      50% { transform: translateX(0); }
      100% { transform: translateX(100%); }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .onboarding-tooltip {
        max-width: calc(100vw - 2rem);
        min-width: calc(100vw - 2rem);
        margin: 1rem;
      }

      .position-center {
        position: fixed !important;
        top: 50% !important;
        left: 1rem !important;
        right: 1rem !important;
        transform: translateY(-50%) !important;
      }

      .tooltip-content {
        padding: 1.25rem;
      }

      .tooltip-actions {
        flex-direction: column;
        
        .action-btn {
          width: 100%;
          justify-content: center;
        }
      }
    }

    /* Dark theme adaptation */
    .dark-theme {
      .onboarding-tooltip {
        background: var(--surface-color);
        box-shadow: 
          0 24px 48px rgba(0, 0, 0, 0.3),
          0 8px 24px rgba(0, 0, 0, 0.2),
          0 0 0 1px rgba(255, 255, 255, 0.05);
      }
      
      .progress-bar {
        background: var(--surface-tertiary);
      }
      
      .keyboard-hint kbd {
        background: var(--surface-tertiary);
        border-color: var(--border-color);
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .energy-core,
      .energy-ring,
      .progress-fill::after {
        animation: none !important;
      }
      
      .action-btn:hover {
        transform: none !important;
      }
    }

    /* High contrast mode */
    @media (prefers-contrast: high) {
      .onboarding-tooltip {
        border: 3px solid var(--text-primary);
      }
      
      .action-btn.primary {
        border: 2px solid var(--text-primary);
      }
    }
  `],
  animations: [
    trigger('overlayAnimation', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-out', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ opacity: 0 }))
      ])
    ]),
    trigger('tooltipAnimation', [
      transition(':enter', [
        style({ 
          opacity: 0, 
          transform: 'scale(0.8) translateY(-20px)',
          filter: 'blur(4px)'
        }),
        animate('400ms cubic-bezier(0.4, 0, 0.2, 1)', style({ 
          opacity: 1, 
          transform: 'scale(1) translateY(0)',
          filter: 'blur(0px)'
        }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ 
          opacity: 0, 
          transform: 'scale(0.9) translateY(-10px)',
          filter: 'blur(2px)'
        }))
      ])
    ])
  ]
})
export class OnboardingTooltipComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('tooltip', { static: false }) tooltipElement?: ElementRef;

  currentStep: OnboardingStep | null = null;
  currentStepIndex = 0;
  totalSteps = 0;
  showProgress = true;
  showKeyboardHints = true;
  isProcessingAction = false;

  private subscription = new Subscription();
  private keyboardListener?: (event: KeyboardEvent) => void;

  constructor(
    private onboardingService: OnboardingService,
    private hapticFeedbackService: HapticFeedbackService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    // Subscribe to active step changes
    this.subscription.add(
      this.onboardingService.activeStep$.subscribe(step => {
        this.currentStep = step;
        if (step) {
          this.positionTooltip();
          this.setupKeyboardNavigation();
        } else {
          this.removeKeyboardNavigation();
        }
        this.cdr.detectChanges();
      })
    );

    // Subscribe to state changes for progress tracking
    this.subscription.add(
      this.onboardingService.state$.subscribe(state => {
        this.currentStepIndex = state.currentStep;
        if (state.currentTour) {
          const tour = this.onboardingService.getAvailableTours()
            .find(t => t.id === state.currentTour);
          this.totalSteps = tour?.steps.length || 0;
        }
        this.cdr.detectChanges();
      })
    );
  }

  ngAfterViewInit(): void {
    if (this.currentStep) {
      this.positionTooltip();
    }
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
    this.removeKeyboardNavigation();
  }

  get progressPercentage(): number {
    if (this.totalSteps === 0) return 0;
    return ((this.currentStepIndex + 1) / this.totalSteps) * 100;
  }

  /**
   * Position tooltip relative to target element
   */
  private positionTooltip(): void {
    if (!this.currentStep || !this.tooltipElement || this.currentStep.position === 'center') {
      return;
    }

    setTimeout(() => {
      const tooltip = this.tooltipElement?.nativeElement;
      const target = this.currentStep?.targetSelector ? 
        document.querySelector(this.currentStep.targetSelector) : null;

      if (!tooltip || !target) return;

      const targetRect = target.getBoundingClientRect();
      const tooltipRect = tooltip.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let left = 0;
      let top = 0;

      switch (this.currentStep!.position) {
        case 'top':
          left = targetRect.left + (targetRect.width / 2);
          top = targetRect.top - tooltipRect.height - 20;
          break;
        case 'bottom':
          left = targetRect.left + (targetRect.width / 2);
          top = targetRect.bottom + 20;
          break;
        case 'left':
          left = targetRect.left - tooltipRect.width - 20;
          top = targetRect.top + (targetRect.height / 2);
          break;
        case 'right':
          left = targetRect.right + 20;
          top = targetRect.top + (targetRect.height / 2);
          break;
      }

      // Ensure tooltip stays within viewport
      left = Math.max(20, Math.min(left, viewportWidth - tooltipRect.width - 20));
      top = Math.max(20, Math.min(top, viewportHeight - tooltipRect.height - 20));

      tooltip.style.left = `${left}px`;
      tooltip.style.top = `${top}px`;
    }, 0);
  }

  /**
   * Setup keyboard navigation
   */
  private setupKeyboardNavigation(): void {
    this.removeKeyboardNavigation();

    this.keyboardListener = (event: KeyboardEvent) => {
      if (!this.currentStep) return;

      switch (event.key) {
        case 'Escape':
          event.preventDefault();
          this.onSkipTour();
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          const primaryAction = this.currentStep.actions.find(a => a.primary);
          if (primaryAction) {
            this.onAction(primaryAction);
          }
          break;
        case 'ArrowRight':
          event.preventDefault();
          this.onNext();
          break;
        case 'ArrowLeft':
          event.preventDefault();
          this.onPrevious();
          break;
      }
    };

    document.addEventListener('keydown', this.keyboardListener);
  }

  /**
   * Remove keyboard navigation
   */
  private removeKeyboardNavigation(): void {
    if (this.keyboardListener) {
      document.removeEventListener('keydown', this.keyboardListener);
      this.keyboardListener = undefined;
    }
  }

  /**
   * Handle action button clicks
   */
  onAction(action: any): void {
    if (this.isProcessingAction) return;

    this.isProcessingAction = true;
    this.hapticFeedbackService.triggerSelectionFeedback();

    // Execute custom action if provided
    if (action.action) {
      action.action();
    }

    // Handle built-in action types
    switch (action.type) {
      case 'next':
        this.onNext();
        break;
      case 'skip':
        this.onSkip();
        break;
      case 'complete':
        this.onComplete();
        break;
      case 'custom':
        // Custom actions handled above
        break;
    }

    setTimeout(() => {
      this.isProcessingAction = false;
    }, 300);
  }

  /**
   * Move to next step
   */
  onNext(): void {
    this.onboardingService.nextStep();
  }

  /**
   * Skip current step
   */
  onSkip(): void {
    this.onboardingService.skipStep();
  }

  /**
   * Move to previous step (if supported)
   */
  onPrevious(): void {
    // Note: This would require additional service method
    // For now, just announce that previous is not supported
    console.log('Previous step not implemented yet');
  }

  /**
   * Complete the tour
   */
  onComplete(): void {
    this.hapticFeedbackService.triggerSuccessFeedback();
    this.onboardingService.completeTour();
  }

  /**
   * Skip entire tour
   */
  onSkipTour(): void {
    this.onboardingService.skipTour();
  }

  /**
   * Handle overlay click (close tour)
   */
  onOverlayClick(): void {
    this.onSkipTour();
  }

  /**
   * Get energy colors based on emotional theme
   */
  getEnergyColors(): { center: string; middle: string; outer: string; accent: string } {
    const theme = this.currentStep?.emotionalTheme || 'discovery';
    
    const themes = {
      discovery: {
        center: '#ffffff',
        middle: '#60a5fa',
        outer: '#3b82f6',
        accent: '#60a5fa'
      },
      connection: {
        center: '#ffffff',
        middle: '#ff6b9d',
        outer: '#ec4899',
        accent: '#ff6b9d'
      },
      growth: {
        center: '#ffffff',
        middle: '#34d399',
        outer: '#10b981',
        accent: '#34d399'
      },
      celebration: {
        center: '#ffffff',
        middle: '#ffd700',
        outer: '#f59e0b',
        accent: '#ffd700'
      }
    };

    return themes[theme];
  }

  /**
   * Get ARIA label for action button
   */
  getActionAriaLabel(action: any): string {
    const stepInfo = `Step ${this.currentStepIndex + 1} of ${this.totalSteps}`;
    return `${action.label}. ${stepInfo}`;
  }

  /**
   * Track function for actions
   */
  trackAction(index: number, action: any): string {
    return action.type + action.label;
  }
}