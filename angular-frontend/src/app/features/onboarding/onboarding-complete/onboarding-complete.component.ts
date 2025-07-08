import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { RevelationService } from '../../../core/services/revelation.service';
import { StorageService } from '../../../core/services/storage.service';
import { EmotionalOnboarding } from '../../../core/interfaces/revelation.interfaces';

@Component({
  selector: 'app-onboarding-complete',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="onboarding-complete">
      <div class="completion-content" *ngIf="!isSubmitting">
        <div class="success-icon">✨</div>
        
        <h1>Welcome to Soul Before Skin</h1>
        <p class="welcome-message">
          Your emotional profile is complete! You're now ready to discover meaningful connections 
          based on compatibility, values, and shared interests.
        </p>

        <div class="profile-summary">
          <h3>Your Soul Profile Includes:</h3>
          <ul class="profile-features">
            <li>
              <span class="feature-icon">💭</span>
              Deep emotional insights and relationship values
            </li>
            <li>
              <span class="feature-icon">🤝</span>
              Personality traits and communication style
            </li>
            <li>
              <span class="feature-icon">❤️</span>
              {{ totalInterests }} carefully selected interests
            </li>
            <li>
              <span class="feature-icon">🎯</span>
              Compatibility scoring with local algorithms
            </li>
          </ul>
        </div>

        <div class="next-steps">
          <h3>What happens next?</h3>
          <div class="steps-grid">
            <div class="step-card">
              <div class="step-number">1</div>
              <h4>Discover Connections</h4>
              <p>Find compatible souls based on your emotional profile</p>
            </div>
            <div class="step-card">
              <div class="step-number">2</div>
              <h4>Progressive Revelation</h4>
              <p>Share daily revelations over 7 days to build deep connection</p>
            </div>
            <div class="step-card">
              <div class="step-number">3</div>
              <h4>Photo Reveal</h4>
              <p>Choose to share photos after getting to know each other's soul</p>
            </div>
          </div>
        </div>

        <div class="completion-actions">
          <button 
            class="btn btn-primary btn-large"
            (click)="completeOnboarding()"
            [disabled]="isSubmitting">
            Start Discovering Connections
          </button>
        </div>
      </div>

      <div class="submitting-content" *ngIf="isSubmitting">
        <div class="loading-spinner"></div>
        <h2>Creating your soul profile...</h2>
        <p>We're processing your responses to create the perfect compatibility profile.</p>
      </div>

      <div class="error-content" *ngIf="hasError">
        <div class="error-icon">⚠️</div>
        <h2>Something went wrong</h2>
        <p>{{ errorMessage }}</p>
        <button class="btn btn-outline" (click)="retrySubmission()">
          Try Again
        </button>
      </div>
    </div>
  `,
  styles: [`
    .onboarding-complete {
      max-width: 600px;
      margin: 0 auto;
      padding: 2rem;
      text-align: center;
    }

    .completion-content {
      animation: fadeIn 0.5s ease-in;
    }

    .success-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
      animation: bounce 1s ease-in-out;
    }

    .onboarding-complete h1 {
      color: #1f2937;
      font-size: 2rem;
      font-weight: 600;
      margin-bottom: 1rem;
    }

    .welcome-message {
      color: #6b7280;
      font-size: 1.125rem;
      line-height: 1.6;
      margin-bottom: 2rem;
      max-width: 500px;
      margin-left: auto;
      margin-right: auto;
    }

    .profile-summary {
      background: linear-gradient(135deg, #fce7f3, #ede9fe);
      padding: 1.5rem;
      border-radius: 1rem;
      margin-bottom: 2rem;
      text-align: left;
    }

    .profile-summary h3 {
      color: #374151;
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 1rem;
      text-align: center;
    }

    .profile-features {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .profile-features li {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.3);
    }

    .profile-features li:last-child {
      border-bottom: none;
    }

    .feature-icon {
      font-size: 1.25rem;
      width: 2rem;
      text-align: center;
    }

    .next-steps {
      margin-bottom: 2rem;
    }

    .next-steps h3 {
      color: #374151;
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 1.5rem;
    }

    .steps-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .step-card {
      background: white;
      padding: 1.5rem;
      border-radius: 0.75rem;
      border: 1px solid #e5e7eb;
      transition: transform 0.2s;
    }

    .step-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    .step-number {
      width: 2rem;
      height: 2rem;
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      margin: 0 auto 0.75rem auto;
    }

    .step-card h4 {
      color: #374151;
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .step-card p {
      color: #6b7280;
      font-size: 0.875rem;
      line-height: 1.4;
    }

    .completion-actions {
      margin-top: 2rem;
    }

    .btn {
      padding: 0.75rem 1.5rem;
      border-radius: 0.5rem;
      font-weight: 500;
      transition: all 0.2s;
      border: none;
      cursor: pointer;
      font-size: 1rem;
    }

    .btn-primary {
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    .btn-large {
      padding: 1rem 2rem;
      font-size: 1.125rem;
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .submitting-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 3rem 1rem;
    }

    .loading-spinner {
      width: 3rem;
      height: 3rem;
      border: 3px solid #e5e7eb;
      border-top: 3px solid #ec4899;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    .error-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 3rem 1rem;
    }

    .error-icon {
      font-size: 3rem;
      color: #ef4444;
    }

    .btn-outline {
      background: white;
      border: 1px solid #d1d5db;
      color: #374151;
    }

    .btn-outline:hover {
      background: #f9fafb;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes bounce {
      0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-10px); }
      60% { transform: translateY(-5px); }
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    @media (max-width: 640px) {
      .onboarding-complete {
        padding: 1rem;
      }
      
      .steps-grid {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class OnboardingCompleteComponent implements OnInit {
  isSubmitting = false;
  hasError = false;
  errorMessage = '';
  totalInterests = 0;

  constructor(
    private router: Router,
    private authService: AuthService,
    private revelationService: RevelationService,
    private storage: StorageService
  ) {}

  ngOnInit(): void {
    this.calculateProfileStats();
  }

  private calculateProfileStats(): void {
    // Get interest count from stored data
    const interests = this.storage.getJson<{interests: string[]}>('onboarding_interests');
    if (interests) {
      this.totalInterests = interests.interests?.length || 0;
    }
  }

  completeOnboarding(): void {
    this.isSubmitting = true;
    this.hasError = false;

    // Collect all onboarding data
    const emotionalData = this.storage.getJson<any>('onboarding_emotional');
    const personalityData = this.storage.getJson<any>('onboarding_personality');
    const interestData = this.storage.getJson<{interests: string[]}>('onboarding_interests');

    // Combine into emotional onboarding payload
    const onboardingPayload: EmotionalOnboarding = {
      relationship_values: emotionalData?.relationship_values || '',
      ideal_evening: emotionalData?.ideal_evening || '',
      feeling_understood: emotionalData?.feeling_understood || '',
      core_values: {
        relationship_values: emotionalData?.relationship_values,
        ideal_evening: emotionalData?.ideal_evening,
        feeling_understood: emotionalData?.feeling_understood,
        selected_values: personalityData?.relationship_values || []
      },
      personality_traits: {
        connection_style: personalityData?.connection_style,
        social_energy: personalityData?.social_energy,
        traits: personalityData?.personality_traits || []
      },
      communication_style: {
        connection_style: personalityData?.connection_style,
        social_energy: personalityData?.social_energy
      },
      interests: interestData?.interests || []
    };

    // Submit to backend
    this.revelationService.completeEmotionalOnboarding(onboardingPayload)
      .pipe(
        finalize(() => this.isSubmitting = false)
      )
      .subscribe({
        next: (updatedUser) => {
          // Clear stored onboarding data
          this.clearOnboardingData();
          
          // Set onboarding completion flag
          this.storage.setItem('onboarding_completed', 'true');
          
          // Update current user with backend response
          this.authService.updateCurrentUser(updatedUser);

          // Navigate to discovery after a short delay
          setTimeout(() => {
            this.router.navigate(['/discover']);
          }, 1000);
        },
        error: (error) => {
          this.hasError = true;
          this.errorMessage = error.message || 'Failed to complete onboarding. Please try again.';
        }
      });
  }

  retrySubmission(): void {
    this.hasError = false;
    this.completeOnboarding();
  }

  private clearOnboardingData(): void {
    this.storage.removeItem('onboarding_emotional');
    this.storage.removeItem('onboarding_personality');
    this.storage.removeItem('onboarding_interests');
  }
}