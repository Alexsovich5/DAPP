import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';

interface InterestCategory {
  name: string;
  icon: string;
  interests: string[];
}

@Component({
  selector: 'app-interest-selection',
  template: `
    <div class="interest-selection">
      <div class="selection-header">
        <h2>What brings you joy?</h2>
        <p>Select interests that genuinely excite you. These help create natural conversation starters.</p>
        <div class="selection-counter">
          <span class="count">{{ selectedInterests.length }}</span> interests selected
          <small>(minimum 5 recommended)</small>
        </div>
      </div>

      <form [formGroup]="interestForm" (ngSubmit)="onSubmit()">
        <div class="interest-categories">
          <div 
            *ngFor="let category of interestCategories" 
            class="category-section">
            
            <h3 class="category-title">
              <span class="category-icon">{{ category.icon }}</span>
              {{ category.name }}
            </h3>
            
            <div class="interest-grid">
              <button 
                type="button"
                *ngFor="let interest of category.interests"
                class="interest-tag"
                [class.selected]="isInterestSelected(interest)"
                (click)="toggleInterest(interest)">
                {{ interest }}
              </button>
            </div>
          </div>
        </div>

        <div class="custom-interests">
          <h3>Add your own interests</h3>
          <div class="custom-input-group">
            <input 
              type="text" 
              #customInterestInput
              placeholder="Type an interest and press Enter"
              class="custom-input"
              (keyup.enter)="addCustomInterest(customInterestInput.value); customInterestInput.value = ''">
            <button 
              type="button" 
              class="add-btn"
              (click)="addCustomInterest(customInterestInput.value); customInterestInput.value = ''">
              Add
            </button>
          </div>
          
          <div class="custom-interests-list" *ngIf="customInterests.length > 0">
            <span 
              *ngFor="let interest of customInterests"
              class="custom-interest-tag">
              {{ interest }}
              <button 
                type="button" 
                class="remove-btn"
                (click)="removeCustomInterest(interest)">
                ×
              </button>
            </span>
          </div>
        </div>

        <div class="form-actions">
          <button 
            type="submit" 
            class="btn btn-primary btn-full"
            [disabled]="selectedInterests.length < 5">
            Complete Profile Setup
          </button>
          <small class="action-hint" *ngIf="selectedInterests.length < 5">
            Please select at least 5 interests to create meaningful connections
          </small>
        </div>
      </form>
    </div>
  `,
  styles: [`
    .interest-selection {
      max-width: 100%;
    }

    .selection-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .selection-header h2 {
      color: #1f2937;
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .selection-counter {
      margin-top: 1rem;
      padding: 0.75rem 1rem;
      background: linear-gradient(90deg, #fce7f3, #ede9fe);
      border-radius: 0.5rem;
      display: inline-block;
    }

    .count {
      font-weight: 600;
      color: #ec4899;
      font-size: 1.125rem;
    }

    .selection-counter small {
      display: block;
      color: #6b7280;
      font-size: 0.75rem;
      margin-top: 0.25rem;
    }

    .interest-categories {
      margin-bottom: 2rem;
    }

    .category-section {
      margin-bottom: 2rem;
    }

    .category-title {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      color: #374151;
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 1rem;
    }

    .category-icon {
      font-size: 1.25rem;
    }

    .interest-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 0.75rem;
    }

    .interest-tag {
      padding: 0.75rem 1rem;
      border: 1px solid #d1d5db;
      border-radius: 2rem;
      background: white;
      color: #374151;
      font-size: 0.875rem;
      cursor: pointer;
      transition: all 0.2s;
      text-align: center;
    }

    .interest-tag:hover {
      border-color: #ec4899;
      transform: translateY(-1px);
    }

    .interest-tag.selected {
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      color: white;
      border-color: transparent;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .custom-interests {
      margin-bottom: 2rem;
      padding: 1.5rem;
      border: 1px solid #e5e7eb;
      border-radius: 0.75rem;
      background: #fafafa;
    }

    .custom-interests h3 {
      color: #374151;
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 1rem;
    }

    .custom-input-group {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }

    .custom-input {
      flex: 1;
      padding: 0.75rem;
      border: 1px solid #d1d5db;
      border-radius: 0.5rem;
      font-size: 1rem;
    }

    .custom-input:focus {
      outline: none;
      border-color: #ec4899;
      box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.1);
    }

    .add-btn {
      padding: 0.75rem 1.5rem;
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      color: white;
      border: none;
      border-radius: 0.5rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }

    .add-btn:hover {
      transform: translateY(-1px);
    }

    .custom-interests-list {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .custom-interest-tag {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 0.75rem;
      background: white;
      border: 1px solid #d1d5db;
      border-radius: 1.5rem;
      font-size: 0.875rem;
    }

    .remove-btn {
      background: none;
      border: none;
      color: #6b7280;
      cursor: pointer;
      font-size: 1rem;
      line-height: 1;
      padding: 0;
      width: 16px;
      height: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .remove-btn:hover {
      color: #ef4444;
    }

    .form-actions {
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

    .action-hint {
      display: block;
      color: #9ca3af;
      margin-top: 0.75rem;
      font-style: italic;
    }

    @media (max-width: 640px) {
      .interest-grid {
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      }
      
      .custom-input-group {
        flex-direction: column;
      }
    }
  `]
})
export class InterestSelectionComponent implements OnInit {
  @Output() stepCompleted = new EventEmitter<any>();

  interestForm!: FormGroup;
  selectedInterests: string[] = [];
  customInterests: string[] = [];

  interestCategories: InterestCategory[] = [
    {
      name: 'Food & Dining',
      icon: '🍽️',
      interests: ['Cooking', 'Fine Dining', 'Street Food', 'Wine Tasting', 'Coffee Culture', 'Vegetarian/Vegan', 'Food Photography', 'Farmers Markets']
    },
    {
      name: 'Arts & Culture',
      icon: '🎨',
      interests: ['Museums', 'Theater', 'Live Music', 'Art Galleries', 'Photography', 'Writing', 'Poetry', 'Film & Cinema']
    },
    {
      name: 'Outdoor & Adventure',
      icon: '🏔️',
      interests: ['Hiking', 'Rock Climbing', 'Cycling', 'Camping', 'Beach Activities', 'Skiing', 'Kayaking', 'Travel']
    },
    {
      name: 'Wellness & Mindfulness',
      icon: '🧘',
      interests: ['Yoga', 'Meditation', 'Fitness', 'Running', 'Mental Health', 'Spirituality', 'Healthy Living', 'Nature Walks']
    },
    {
      name: 'Learning & Growth',
      icon: '📚',
      interests: ['Reading', 'Podcasts', 'Languages', 'History', 'Science', 'Philosophy', 'Documentaries', 'Online Courses']
    },
    {
      name: 'Social & Games',
      icon: '🎲',
      interests: ['Board Games', 'Trivia', 'Dancing', 'Karaoke', 'Video Games', 'Social Causes', 'Volunteering', 'Community Events']
    }
  ];

  constructor(
    private fb: FormBuilder,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initializeForm();
  }

  private initializeForm(): void {
    this.interestForm = this.fb.group({
      interests: [[], [Validators.required, Validators.minLength(5)]]
    });
  }

  toggleInterest(interest: string): void {
    const index = this.selectedInterests.indexOf(interest);
    if (index === -1) {
      this.selectedInterests.push(interest);
    } else {
      this.selectedInterests.splice(index, 1);
    }
    
    this.updateFormValue();
  }

  isInterestSelected(interest: string): boolean {
    return this.selectedInterests.includes(interest);
  }

  addCustomInterest(interest: string): void {
    const trimmedInterest = interest.trim();
    if (trimmedInterest && !this.customInterests.includes(trimmedInterest) && !this.selectedInterests.includes(trimmedInterest)) {
      this.customInterests.push(trimmedInterest);
      this.selectedInterests.push(trimmedInterest);
      this.updateFormValue();
    }
  }

  removeCustomInterest(interest: string): void {
    this.customInterests = this.customInterests.filter(i => i !== interest);
    this.selectedInterests = this.selectedInterests.filter(i => i !== interest);
    this.updateFormValue();
  }

  private updateFormValue(): void {
    this.interestForm.patchValue({ interests: this.selectedInterests });
  }

  onSubmit(): void {
    if (this.interestForm.valid && this.selectedInterests.length >= 5) {
      // Store form data for final submission
      const interestData = this.interestForm.value;
      localStorage.setItem('onboarding_interests', JSON.stringify(interestData));
      
      // Navigate to completion step
      this.router.navigate(['/onboarding/complete']);
    }
  }
}