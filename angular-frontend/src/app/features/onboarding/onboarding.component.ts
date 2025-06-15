import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, RouterOutlet, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil, filter } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { RevelationService } from '../../core/services/revelation.service';
import { User } from '../../core/interfaces/auth.interfaces';

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  template: `
    <div class="onboarding-container">
      <div class="onboarding-header">
        <h1>Soul Before Skin Journey</h1>
        <p class="tagline">"If someone enters your life, they should make it better."</p>

        <div class="progress-bar">
          <div class="progress-fill" [style.width.%]="progressPercentage"></div>
        </div>
        <p class="progress-text">Step {{ currentStep }} of {{ totalSteps }}</p>
      </div>

      <div class="onboarding-content">
        <router-outlet></router-outlet>
      </div>

      <div class="onboarding-navigation" *ngIf="showNavigation">
        <button
          type="button"
          class="btn btn-outline"
          (click)="goBack()"
          [disabled]="currentStep === 1">
          Previous
        </button>

        <button
          type="button"
          class="btn btn-primary"
          (click)="goNext()"
          [disabled]="!canProceed">
          {{ currentStep === totalSteps ? 'Complete' : 'Next' }}
        </button>
      </div>
    </div>
  `,
  styles: [`
    .onboarding-container {
      max-width: 600px;
      margin: 0 auto;
      padding: 2rem;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .onboarding-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .onboarding-header h1 {
      color: #1f2937;
      font-size: 2rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .tagline {
      color: #6b7280;
      font-style: italic;
      margin-bottom: 2rem;
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background-color: #e5e7eb;
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 0.5rem;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      transition: width 0.3s ease;
    }

    .progress-text {
      color: #6b7280;
      font-size: 0.875rem;
    }

    .onboarding-content {
      flex: 1;
      margin-bottom: 2rem;
    }

    .onboarding-navigation {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
    }

    .btn {
      padding: 0.75rem 1.5rem;
      border-radius: 0.5rem;
      font-weight: 500;
      transition: all 0.2s;
      border: none;
      cursor: pointer;
    }

    .btn-outline {
      background: white;
      border: 1px solid #d1d5db;
      color: #374151;
    }

    .btn-outline:hover:not(:disabled) {
      background: #f9fafb;
    }

    .btn-primary {
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `]
})
export class OnboardingComponent implements OnInit, OnDestroy {
  currentStep = 1;
  totalSteps = 4;
  progressPercentage = 25;
  canProceed = false;
  showNavigation = true;
  currentUser: User | null = null;
  private destroy$ = new Subject<void>();

  private steps = [
    'emotional-questions',
    'personality-assessment',
    'interest-selection',
    'complete'
  ];

  constructor(
    private router: Router,
    private authService: AuthService,
    private revelationService: RevelationService
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(user => {
      this.currentUser = user;

      // Check if user has already completed onboarding
      if (user?.emotional_onboarding_completed) {
        this.router.navigate(['/discover']);
        return;
      }
    });

    // Subscribe to router events to track progress
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd),
      takeUntil(this.destroy$)
    ).subscribe(() => {
      this.updateProgress();
      this.checkStepCompletion();
    });

    // Initial progress update
    this.updateProgress();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private updateProgress(): void {
    const currentPath = this.router.url.split('/').pop();
    const stepIndex = this.steps.indexOf(currentPath || '');

    if (stepIndex !== -1) {
      this.currentStep = stepIndex + 1;
      this.progressPercentage = (this.currentStep / this.totalSteps) * 100;
    }

    // Hide navigation on complete step
    this.showNavigation = currentPath !== 'complete';
  }

  goNext(): void {
    if (this.currentStep < this.totalSteps) {
      const nextStep = this.steps[this.currentStep];
      this.router.navigate(['/onboarding', nextStep]);
    }
  }

  goBack(): void {
    if (this.currentStep > 1) {
      const prevStep = this.steps[this.currentStep - 2];
      this.router.navigate(['/onboarding', prevStep]);
    }
  }

  onStepCompleted(): void {
    this.canProceed = true;
  }

  private checkStepCompletion(): void {
    const currentPath = this.router.url.split('/').pop();
    
    // Check if current step has saved data
    switch (currentPath) {
      case 'emotional-questions':
        this.canProceed = !!localStorage.getItem('onboarding_emotional');
        break;
      case 'personality-assessment':
        this.canProceed = !!localStorage.getItem('onboarding_personality');
        break;
      case 'interest-selection':
        this.canProceed = !!localStorage.getItem('onboarding_interests');
        break;
      case 'complete':
        this.canProceed = false; // No navigation from complete step
        break;
      default:
        this.canProceed = false;
    }
  }
}
