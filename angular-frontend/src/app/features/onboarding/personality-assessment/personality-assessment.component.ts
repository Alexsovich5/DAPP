import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-personality-assessment',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="personality-assessment">
      <div class="assessment-header">
        <h2>Your Personality & Communication Style</h2>
        <p>Help us understand how you connect and communicate with others.</p>
      </div>

      <form [formGroup]="personalityForm" (ngSubmit)="onSubmit()">
        <div class="assessment-section">
          <h3>Communication Preferences</h3>
          
          <div class="question-group">
            <label class="question-label">How do you prefer to connect with someone?</label>
            <div class="radio-group">
              <label class="radio-option">
                <input type="radio" formControlName="connection_style" value="deep_talks">
                <span class="radio-content">
                  <strong>Deep Conversations</strong>
                  <small>Meaningful discussions about life, dreams, and philosophy</small>
                </span>
              </label>
              
              <label class="radio-option">
                <input type="radio" formControlName="connection_style" value="shared_activities">
                <span class="radio-content">
                  <strong>Shared Activities</strong>
                  <small>Bonding through experiences, hobbies, and adventures</small>
                </span>
              </label>
              
              <label class="radio-option">
                <input type="radio" formControlName="connection_style" value="quality_time">
                <span class="radio-content">
                  <strong>Quality Time</strong>
                  <small>Being present and focused on each other</small>
                </span>
              </label>
            </div>
          </div>

          <div class="question-group">
            <label class="question-label">Your social energy style</label>
            <div class="slider-group">
              <div class="slider-labels">
                <span>Introvert</span>
                <span>Extrovert</span>
              </div>
              <input 
                type="range" 
                min="1" 
                max="10" 
                formControlName="social_energy"
                class="slider">
              <small class="slider-hint">How do you recharge and gain energy?</small>
            </div>
          </div>
        </div>

        <div class="assessment-section">
          <h3>Relationship Values</h3>
          
          <div class="question-group">
            <label class="question-label">What's most important in a partnership?</label>
            <div class="checkbox-group">
              <label class="checkbox-option" *ngFor="let value of relationshipValues">
                <input 
                  type="checkbox" 
                  [value]="value.key"
                  (change)="onValueChange($event)">
                <span class="checkbox-content">
                  <strong>{{ value.label }}</strong>
                  <small>{{ value.description }}</small>
                </span>
              </label>
            </div>
          </div>
        </div>

        <div class="assessment-section">
          <h3>Personal Traits</h3>
          
          <div class="question-group">
            <label class="question-label">How would close friends describe you?</label>
            <div class="trait-selector">
              <div class="trait-grid">
                <button 
                  type="button"
                  *ngFor="let trait of personalityTraits"
                  class="trait-tag"
                  [class.selected]="isTraitSelected(trait)"
                  (click)="toggleTrait(trait)">
                  {{ trait }}
                </button>
              </div>
              <small class="trait-hint">Select 3-5 traits that best describe you</small>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button 
            type="submit" 
            class="btn btn-primary btn-full"
            [disabled]="!personalityForm.valid || selectedTraits.length < 3">
            Continue to Interests
          </button>
        </div>
      </form>
    </div>
  `,
  styles: [`
    .personality-assessment {
      max-width: 100%;
    }

    .assessment-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .assessment-header h2 {
      color: #1f2937;
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .assessment-section {
      margin-bottom: 2.5rem;
      padding: 1.5rem;
      border: 1px solid #e5e7eb;
      border-radius: 0.75rem;
      background: #fafafa;
    }

    .assessment-section h3 {
      color: #374151;
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 1.5rem;
    }

    .question-group {
      margin-bottom: 1.5rem;
    }

    .question-label {
      display: block;
      font-weight: 500;
      color: #374151;
      margin-bottom: 1rem;
    }

    .radio-group {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .radio-option {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 1rem;
      border: 1px solid #d1d5db;
      border-radius: 0.5rem;
      cursor: pointer;
      transition: all 0.2s;
      background: white;
    }

    .radio-option:hover {
      border-color: #ec4899;
    }

    .radio-option input[type="radio"] {
      margin-top: 0.25rem;
    }

    .radio-content {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .radio-content small {
      color: #6b7280;
    }

    .slider-group {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .slider-labels {
      display: flex;
      justify-content: space-between;
      font-size: 0.875rem;
      color: #6b7280;
    }

    .slider {
      width: 100%;
      height: 6px;
      border-radius: 3px;
      background: #e5e7eb;
      outline: none;
      -webkit-appearance: none;
    }

    .slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      cursor: pointer;
    }

    .slider-hint {
      color: #9ca3af;
      font-style: italic;
      text-align: center;
    }

    .checkbox-group {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .checkbox-option {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 0.75rem;
      border: 1px solid #d1d5db;
      border-radius: 0.5rem;
      cursor: pointer;
      transition: all 0.2s;
      background: white;
    }

    .checkbox-option:hover {
      border-color: #ec4899;
    }

    .checkbox-content {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .checkbox-content small {
      color: #6b7280;
    }

    .trait-selector {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .trait-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 0.75rem;
    }

    .trait-tag {
      padding: 0.75rem 1rem;
      border: 1px solid #d1d5db;
      border-radius: 2rem;
      background: white;
      color: #374151;
      font-size: 0.875rem;
      cursor: pointer;
      transition: all 0.2s;
    }

    .trait-tag:hover {
      border-color: #ec4899;
    }

    .trait-tag.selected {
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      color: white;
      border-color: transparent;
    }

    .trait-hint {
      color: #9ca3af;
      font-style: italic;
      text-align: center;
    }

    .form-actions {
      margin-top: 2rem;
      text-align: center;
    }

    .btn {
      padding: 0.75rem 1.5rem;
      border-radius: 0.5rem;
      font-weight: 500;
      transition: all 0.2s;
      border: none;
      cursor: pointer;
    }

    .btn-primary {
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    .btn-full {
      width: 100%;
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `]
})
export class PersonalityAssessmentComponent implements OnInit {
  @Output() stepCompleted = new EventEmitter<any>();

  personalityForm!: FormGroup;
  selectedTraits: string[] = [];
  selectedValues: string[] = [];

  relationshipValues = [
    { key: 'loyalty', label: 'Loyalty & Trust', description: 'Being faithful and dependable' },
    { key: 'growth', label: 'Personal Growth', description: 'Learning and evolving together' },
    { key: 'adventure', label: 'Adventure & Fun', description: 'Exploring and trying new things' },
    { key: 'stability', label: 'Stability & Security', description: 'Consistent and reliable partnership' },
    { key: 'independence', label: 'Independence', description: 'Maintaining individual identity' },
    { key: 'family', label: 'Family Values', description: 'Building a family or strong community' }
  ];

  personalityTraits = [
    'Empathetic', 'Adventurous', 'Analytical', 'Creative', 'Optimistic',
    'Calm', 'Spontaneous', 'Organized', 'Humorous', 'Thoughtful',
    'Passionate', 'Patient', 'Curious', 'Supportive', 'Independent',
    'Romantic', 'Practical', 'Artistic', 'Athletic', 'Spiritual'
  ];

  constructor(
    private fb: FormBuilder,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initializeForm();
  }

  private initializeForm(): void {
    this.personalityForm = this.fb.group({
      connection_style: ['', Validators.required],
      social_energy: [5, Validators.required],
      relationship_values: [[], Validators.required],
      personality_traits: [[], Validators.required]
    });
  }

  onValueChange(event: any): void {
    const value = event.target.value;
    const isChecked = event.target.checked;
    
    if (isChecked) {
      this.selectedValues.push(value);
    } else {
      this.selectedValues = this.selectedValues.filter(v => v !== value);
    }
    
    this.personalityForm.patchValue({ relationship_values: this.selectedValues });
  }

  toggleTrait(trait: string): void {
    const index = this.selectedTraits.indexOf(trait);
    if (index === -1) {
      this.selectedTraits.push(trait);
    } else {
      this.selectedTraits.splice(index, 1);
    }
    
    this.personalityForm.patchValue({ personality_traits: this.selectedTraits });
  }

  isTraitSelected(trait: string): boolean {
    return this.selectedTraits.includes(trait);
  }

  onSubmit(): void {
    if (this.personalityForm.valid && this.selectedTraits.length >= 3) {
      // Store form data for later submission
      const personalityData = this.personalityForm.value;
      localStorage.setItem('onboarding_personality', JSON.stringify(personalityData));
      
      // Navigate to next step
      this.router.navigate(['/onboarding/interest-selection']);
    }
  }
}