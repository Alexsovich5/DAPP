import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { FormsModule } from '@angular/forms';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { OnboardingService } from '../../../core/services/onboarding.service';
import { HapticFeedbackService } from '../../../core/services/haptic-feedback.service';
import { SoulOrbComponent } from '../soul-orb/soul-orb.component';

@Component({
  selector: 'app-onboarding-welcome',
  standalone: true,
  imports: [
    CommonModule, 
    MatButtonModule, 
    MatIconModule, 
    MatCheckboxModule, 
    FormsModule,
    SoulOrbComponent
  ],
  template: `
    <div 
      class="welcome-overlay"
      [@overlayAnimation]="'visible'"
      role="presentation"
      aria-hidden="true">
    </div>

    <div 
      class="welcome-modal"
      [@modalAnimation]="'visible'"
      role="dialog"
      aria-labelledby="welcome-title"
      aria-describedby="welcome-description"
      aria-modal="true">
      
      <!-- Soul Energy Header -->
      <div class="welcome-header">
        <div class="soul-constellation">
          <app-soul-orb
            size="large"
            state="matched"
            [energyLevel]="5"
            [showParticles]="true"
            [showSparkles]="true"
            class="center-orb">
          </app-soul-orb>
          
          <app-soul-orb
            size="small"
            state="connecting"
            [energyLevel]="3"
            class="satellite-orb orb-1">
          </app-soul-orb>
          
          <app-soul-orb
            size="small"
            state="active"
            [energyLevel]="2"
            class="satellite-orb orb-2">
          </app-soul-orb>
          
          <app-soul-orb
            size="small"
            state="connecting"
            [energyLevel]="4"
            class="satellite-orb orb-3">
          </app-soul-orb>
        </div>
        
        <h1 id="welcome-title" class="welcome-title">
          Welcome to Dinner First
        </h1>
        <div class="tagline">Where Soul Meets Soul Before Eyes Meet</div>
      </div>

      <!-- Welcome Content -->
      <div class="welcome-content">
        <div id="welcome-description" class="philosophy-section">
          <h2 class="section-title">✨ Our Philosophy</h2>
          <p class="philosophy-text">
            In a world obsessed with appearances, we believe the most beautiful connections 
            happen when hearts recognize each other first. Here, your emotional depth, 
            values, and dreams take center stage.
          </p>
        </div>

        <!-- How It Works -->
        <div class="how-it-works">
          <h2 class="section-title">💫 How Soul Connections Work</h2>
          
          <div class="steps-container">
            <div class="step" *ngFor="let step of howItWorksSteps; let i = index">
              <div class="step-number">{{ i + 1 }}</div>
              <div class="step-content">
                <h3 class="step-title">{{ step.title }}</h3>
                <p class="step-description">{{ step.description }}</p>
              </div>
              <div class="step-icon" [innerHTML]="step.icon"></div>
            </div>
          </div>
        </div>

        <!-- Benefits -->
        <div class="benefits-section">
          <h2 class="section-title">💖 Why Soul-First Dating Works</h2>
          
          <div class="benefits-grid">
            <div class="benefit" *ngFor="let benefit of benefits">
              <div class="benefit-icon" [innerHTML]="benefit.icon"></div>
              <h3 class="benefit-title">{{ benefit.title }}</h3>
              <p class="benefit-description">{{ benefit.description }}</p>
            </div>
          </div>
        </div>

        <!-- Tutorial Options -->
        <div class="tutorial-options">
          <h2 class="section-title">🎯 Choose Your Journey</h2>
          
          <div class="option-cards">
            <div 
              class="option-card guided"
              [class.selected]="selectedOption === 'guided'"
              (click)="selectOption('guided')"
              (keydown.enter)="selectOption('guided')"
              (keydown.space)="selectOption('guided'); $event.preventDefault()"
              tabindex="0"
              role="button"
              aria-label="Choose guided tutorial">
              <div class="option-header">
                <div class="option-icon">🌟</div>
                <h3 class="option-title">Guided Experience</h3>
              </div>
              <p class="option-description">
                Take a personalized tour to learn how soul connections work. 
                Perfect for discovering all our magical features.
              </p>
              <div class="option-duration">~3 minutes</div>
            </div>

            <div 
              class="option-card quick"
              [class.selected]="selectedOption === 'quick'"
              (click)="selectOption('quick')"
              (keydown.enter)="selectOption('quick')"
              (keydown.space)="selectOption('quick'); $event.preventDefault()"
              tabindex="0"
              role="button"
              aria-label="Choose quick start">
              <div class="option-header">
                <div class="option-icon">🚀</div>
                <h3 class="option-title">Quick Start</h3>
              </div>
              <p class="option-description">
                Jump right in and explore on your own. You can always access 
                tutorials later from your profile.
              </p>
              <div class="option-duration">Instant</div>
            </div>
          </div>
        </div>

        <!-- Preferences -->
        <div class="preferences-section">
          <div class="preference-item">
            <mat-checkbox 
              [(ngModel)]="preferences.showTutorials"
              id="show-tutorials"
              aria-describedby="show-tutorials-desc">
              Show helpful tips and tutorials
            </mat-checkbox>
            <div id="show-tutorials-desc" class="preference-description">
              Get contextual guidance as you explore features
            </div>
          </div>

          <div class="preference-item">
            <mat-checkbox 
              [(ngModel)]="preferences.emotionalAnimations"
              id="emotional-animations"
              aria-describedby="animations-desc">
              Enable emotional animations
            </mat-checkbox>
            <div id="animations-desc" class="preference-description">
              Experience soul orbs, sparkles, and celebration effects
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="welcome-actions">
        <button 
          class="action-btn secondary"
          type="button"
          (click)="onSkip()"
          aria-label="Skip welcome tour and start exploring">
          Skip for Now
        </button>
        
        <button 
          class="action-btn primary"
          type="button"
          [disabled]="!selectedOption"
          (click)="onContinue()"
          [attr.aria-label]="getContinueAriaLabel()">
          {{ getContinueButtonText() }}
        </button>
      </div>

      <!-- Footer -->
      <div class="welcome-footer">
        <p class="footer-text">
          🌙 Welcome to a more meaningful way to connect. Your soul journey begins now.
        </p>
      </div>
    </div>
  `,
  styles: [`
    /* Overlay */
    .welcome-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(135deg, 
        rgba(255, 107, 157, 0.1) 0%, 
        rgba(96, 165, 250, 0.1) 50%,
        rgba(52, 211, 153, 0.1) 100%);
      backdrop-filter: blur(8px);
      z-index: 9998;
    }

    /* Modal */
    .welcome-modal {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      max-width: 800px;
      max-height: 90vh;
      width: calc(100vw - 2rem);
      background: var(--surface-color);
      border-radius: 24px;
      box-shadow: 
        0 32px 64px rgba(0, 0, 0, 0.15),
        0 16px 32px rgba(0, 0, 0, 0.1),
        0 0 0 1px rgba(255, 255, 255, 0.1);
      z-index: 9999;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    /* Header */
    .welcome-header {
      text-align: center;
      padding: 3rem 2rem 2rem;
      background: linear-gradient(135deg, 
        rgba(255, 107, 157, 0.05) 0%, 
        rgba(96, 165, 250, 0.05) 100%);
      position: relative;
      overflow: hidden;
    }

    .soul-constellation {
      position: relative;
      height: 200px;
      margin-bottom: 2rem;
    }

    .center-orb {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 3;
    }

    .satellite-orb {
      position: absolute;
      animation: orbit 8s linear infinite;
    }

    .orb-1 {
      top: 20%;
      left: 20%;
      animation-delay: 0s;
    }

    .orb-2 {
      top: 20%;
      right: 20%;
      animation-delay: 2.7s;
    }

    .orb-3 {
      bottom: 20%;
      left: 50%;
      transform: translateX(-50%);
      animation-delay: 5.3s;
    }

    .welcome-title {
      font-size: 2.5rem;
      font-weight: 700;
      margin: 0 0 0.5rem 0;
      background: linear-gradient(135deg, 
        var(--primary-color) 0%, 
        var(--accent-color) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .tagline {
      font-size: 1.1rem;
      color: var(--text-secondary);
      font-weight: 500;
      font-style: italic;
    }

    /* Content */
    .welcome-content {
      flex: 1;
      overflow-y: auto;
      padding: 0 2rem;
    }

    .section-title {
      font-size: 1.3rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 2rem 0 1rem 0;
      text-align: center;
    }

    /* Philosophy Section */
    .philosophy-section {
      text-align: center;
      margin-bottom: 2rem;
    }

    .philosophy-text {
      font-size: 1.1rem;
      line-height: 1.7;
      color: var(--text-secondary);
      max-width: 600px;
      margin: 0 auto;
    }

    /* How It Works */
    .steps-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .step {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      padding: 1.5rem;
      background: var(--surface-secondary);
      border-radius: 16px;
      border: 1px solid var(--border-color);
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
      }
    }

    .step-number {
      flex-shrink: 0;
      width: 40px;
      height: 40px;
      background: var(--primary-color);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.1rem;
    }

    .step-content {
      flex: 1;
    }

    .step-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 0.5rem 0;
    }

    .step-description {
      color: var(--text-secondary);
      margin: 0;
      line-height: 1.5;
    }

    .step-icon {
      flex-shrink: 0;
      font-size: 2rem;
      opacity: 0.7;
    }

    /* Benefits */
    .benefits-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .benefit {
      text-align: center;
      padding: 1.5rem;
      background: var(--surface-secondary);
      border-radius: 12px;
      border: 1px solid var(--border-color);
    }

    .benefit-icon {
      font-size: 2.5rem;
      margin-bottom: 1rem;
    }

    .benefit-title {
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 0.5rem 0;
    }

    .benefit-description {
      font-size: 0.9rem;
      color: var(--text-secondary);
      margin: 0;
      line-height: 1.4;
    }

    /* Tutorial Options */
    .option-cards {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .option-card {
      padding: 1.5rem;
      border: 2px solid var(--border-color);
      border-radius: 16px;
      cursor: pointer;
      transition: all 0.3s ease;
      background: var(--surface-secondary);
      
      &:hover {
        border-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(255, 107, 157, 0.2);
      }
      
      &:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
      }
      
      &.selected {
        border-color: var(--primary-color);
        background: rgba(255, 107, 157, 0.05);
        box-shadow: 0 8px 24px rgba(255, 107, 157, 0.2);
      }
    }

    .option-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }

    .option-icon {
      font-size: 1.5rem;
    }

    .option-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }

    .option-description {
      color: var(--text-secondary);
      margin: 0 0 1rem 0;
      line-height: 1.5;
      font-size: 0.9rem;
    }

    .option-duration {
      font-size: 0.8rem;
      color: var(--accent-color);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* Preferences */
    .preferences-section {
      margin-bottom: 2rem;
    }

    .preference-item {
      margin-bottom: 1rem;
      
      &:last-child {
        margin-bottom: 0;
      }
    }

    .preference-description {
      margin-left: 2rem;
      font-size: 0.85rem;
      color: var(--text-tertiary);
      margin-top: 0.25rem;
    }

    /* Actions */
    .welcome-actions {
      display: flex;
      gap: 1rem;
      padding: 2rem;
      border-top: 1px solid var(--border-color);
      background: var(--surface-color);
    }

    .action-btn {
      flex: 1;
      padding: 1rem 2rem;
      border: none;
      border-radius: 12px;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.2s ease;
      
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
      }
      
      &.secondary {
        background: var(--surface-secondary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        
        &:hover {
          background: var(--surface-tertiary);
          transform: translateY(-1px);
        }
      }
    }

    /* Footer */
    .welcome-footer {
      text-align: center;
      padding: 1rem 2rem;
      background: rgba(255, 107, 157, 0.03);
      border-top: 1px solid var(--border-color);
    }

    .footer-text {
      color: var(--text-secondary);
      margin: 0;
      font-size: 0.9rem;
      font-style: italic;
    }

    /* Animations */
    @keyframes orbit {
      0% { transform: rotate(0deg) translateX(100px) rotate(0deg); }
      100% { transform: rotate(360deg) translateX(100px) rotate(-360deg); }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .welcome-modal {
        max-width: calc(100vw - 1rem);
        max-height: calc(100vh - 1rem);
        margin: 0.5rem;
      }

      .welcome-header {
        padding: 2rem 1.5rem 1.5rem;
      }

      .welcome-title {
        font-size: 2rem;
      }

      .soul-constellation {
        height: 150px;
        margin-bottom: 1.5rem;
      }

      .option-cards {
        grid-template-columns: 1fr;
      }

      .benefits-grid {
        grid-template-columns: 1fr;
      }

      .step {
        flex-direction: column;
        text-align: center;
        gap: 1rem;
      }

      .welcome-actions {
        flex-direction: column;
        padding: 1.5rem;
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .satellite-orb {
        animation: none !important;
      }
      
      .step:hover,
      .option-card:hover,
      .action-btn:hover {
        transform: none !important;
      }
    }

    /* Dark theme */
    .dark-theme {
      .welcome-modal {
        background: var(--surface-color);
        box-shadow: 
          0 32px 64px rgba(0, 0, 0, 0.3),
          0 16px 32px rgba(0, 0, 0, 0.2);
      }
    }
  `],
  animations: [
    trigger('overlayAnimation', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('500ms ease-out', style({ opacity: 1 }))
      ])
    ]),
    trigger('modalAnimation', [
      transition(':enter', [
        style({ 
          opacity: 0, 
          transform: 'translate(-50%, -50%) scale(0.8)',
          filter: 'blur(8px)'
        }),
        animate('600ms cubic-bezier(0.4, 0, 0.2, 1)', style({ 
          opacity: 1, 
          transform: 'translate(-50%, -50%) scale(1)',
          filter: 'blur(0px)'
        }))
      ])
    ])
  ]
})
export class OnboardingWelcomeComponent implements OnInit {
  selectedOption: 'guided' | 'quick' | null = null;
  
  preferences = {
    showTutorials: true,
    emotionalAnimations: true
  };

  howItWorksSteps = [
    {
      title: 'Share Your Soul',
      description: 'Complete your emotional profile with values, dreams, and what makes you unique.',
      icon: '💖'
    },
    {
      title: 'Algorithm Magic',
      description: 'Our compatibility algorithm finds people who align with your deeper self.',
      icon: '✨'
    },
    {
      title: 'Connect First',
      description: 'Start meaningful conversations based on emotional compatibility.',
      icon: '💬'
    },
    {
      title: 'Reveal Photos',
      description: 'After connecting emotionally, choose when to share photos together.',
      icon: '🌅'
    }
  ];

  benefits = [
    {
      title: 'Deeper Connections',
      description: 'Build relationships based on true compatibility, not just attraction.',
      icon: '🔗'
    },
    {
      title: 'Authentic Self',
      description: 'Be valued for who you truly are, not just your appearance.',
      icon: '🌟'
    },
    {
      title: 'Meaningful Conversations',
      description: 'Start with topics that matter and create genuine understanding.',
      icon: '💭'
    },
    {
      title: 'Quality Matches',
      description: 'Spend time with people who truly align with your values and goals.',
      icon: '🎯'
    }
  ];

  constructor(
    private onboardingService: OnboardingService,
    private hapticFeedbackService: HapticFeedbackService
  ) {}

  ngOnInit(): void {
    // Default to guided experience for new users
    this.selectedOption = 'guided';
    
    // Trigger welcome haptic feedback
    this.hapticFeedbackService.triggerWelcomeFeedback();
  }

  /**
   * Select tutorial option
   */
  selectOption(option: 'guided' | 'quick'): void {
    this.selectedOption = option;
    this.hapticFeedbackService.triggerSelectionFeedback();
  }

  /**
   * Continue with selected option
   */
  onContinue(): void {
    if (!this.selectedOption) return;

    // Update preferences
    this.onboardingService.updatePreferences({
      showTutorials: this.preferences.showTutorials,
      skipIntroductions: false
    });

    this.hapticFeedbackService.triggerSuccessFeedback();

    if (this.selectedOption === 'guided') {
      // Start the main tutorial tour
      setTimeout(() => {
        this.onboardingService.startTour('soul-first-experience');
      }, 500);
    } else {
      // Quick start - just close welcome
      this.onboardingService.completeTour();
    }
  }

  /**
   * Skip welcome completely
   */
  onSkip(): void {
    this.onboardingService.updatePreferences({
      showTutorials: false,
      skipIntroductions: true
    });
    
    this.onboardingService.completeTour();
  }

  /**
   * Get continue button text
   */
  getContinueButtonText(): string {
    if (!this.selectedOption) return 'Choose an Option';
    
    return this.selectedOption === 'guided' 
      ? 'Start Guided Tour' 
      : 'Begin Journey';
  }

  /**
   * Get continue button ARIA label
   */
  getContinueAriaLabel(): string {
    if (!this.selectedOption) return 'Please select a tutorial option first';
    
    return this.selectedOption === 'guided'
      ? 'Start guided tutorial tour to learn about soul connections'
      : 'Skip tutorial and begin exploring on your own';
  }
}