import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StorageService } from '../../../core/services/storage.service';
import { SkeletonLoaderComponent } from '@shared/components/skeleton-loader/skeleton-loader.component';

@Component({
  selector: 'app-emotional-questions',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, SkeletonLoaderComponent],
  template: `
    <div class="emotional-questions">
      <div class="question-header">
        <h2>Let's explore your emotional landscape</h2>
        <p>These questions help us understand what truly matters to you in connections.</p>
      </div>

      <div class="swipe-container">
      <form [formGroup]="emotionalForm" (ngSubmit)="onSubmit()">
        <app-skeleton-loader type="text" width="70%" *ngIf="isSaving"></app-skeleton-loader>
        <div class="question-group">
          <label class="question-label">
            <span class="question-number">1</span>
            What do you value most in a relationship?
          </label>
          <textarea
            formControlName="relationship_values"
            placeholder="Share what's most important to you when connecting with someone special..."
            rows="4"
            class="form-textarea">
          </textarea>
          <p class="hint">Think about loyalty, growth, adventure, stability, independence, or family values.</p>
        </div>

        <div class="question-group">
          <label class="question-label">
            <span class="question-number">2</span>
            Describe your ideal evening with someone special
          </label>
          <textarea
            formControlName="ideal_evening"
            placeholder="Paint a picture of your perfect evening together..."
            rows="4"
            class="form-textarea">
          </textarea>
          <p class="hint">This helps us understand your connection style and preferences.</p>
        </div>

        <div class="question-group">
          <label class="question-label">
            <span class="question-number">3</span>
            What makes you feel truly understood?
          </label>
          <textarea
            formControlName="feeling_understood"
            placeholder="Describe moments when you feel most seen and appreciated..."
            rows="4"
            class="form-textarea">
          </textarea>
          <p class="hint">Think about communication styles, gestures, or deeper connections.</p>
        </div>

        <div class="form-actions">
          <button
            type="submit"
            class="btn btn-primary btn-full"
            [disabled]="!emotionalForm.valid || isSaving">
            Continue to Personality Assessment
          </button>
        </div>
      </form>
      </div>
    </div>
  `,
  styles: [`
    .emotional-questions {
      max-width: 100%;
    }

    .question-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .question-header h2 {
      color: #1f2937;
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .question-header p {
      color: #6b7280;
    }

    .question-group {
      margin-bottom: 2rem;
    }

    .question-label {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      font-weight: 500;
      color: #374151;
      margin-bottom: 0.75rem;
    }

    .question-number {
      background: linear-gradient(90deg, #ec4899, #8b5cf6);
      color: white;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.875rem;
      font-weight: 600;
      flex-shrink: 0;
    }

    .form-textarea {
      width: 100%;
      padding: 0.75rem;
      border: 1px solid #d1d5db;
      border-radius: 0.5rem;
      font-size: 1rem;
      line-height: 1.5;
      transition: border-color 0.2s;
      resize: vertical;
      min-height: 100px;
    }

    .form-textarea:focus {
      outline: none;
      border-color: #ec4899;
      box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.1);
    }

    .hint {
      color: #9ca3af;
      font-size: 0.875rem;
      margin-top: 0.5rem;
      font-style: italic;
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

    @media (max-width: 640px) {
      .question-label {
        flex-direction: column;
        gap: 0.5rem;
      }
    }
  `]
})
export class EmotionalQuestionsComponent implements OnInit {
  @Output() stepCompleted = new EventEmitter<any>();

  emotionalForm!: FormGroup;
  isSaving = false;
  private autosaveTimer: any;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private storage: StorageService
  ) {}

  ngOnInit(): void {
    this.initializeForm();
    this.loadExistingData();
  }

  private initializeForm(): void {
    this.emotionalForm = this.fb.group({
      relationship_values: ['', [Validators.required, Validators.minLength(20)]],
      ideal_evening: ['', [Validators.required, Validators.minLength(20)]],
      feeling_understood: ['', [Validators.required, Validators.minLength(20)]]
    });

    // Emit step completion status when form validity changes
    this.emotionalForm.statusChanges.subscribe(status => {
      if (status === 'VALID') {
        this.stepCompleted.emit(this.emotionalForm.value);
      }
    });

    // Autosave form changes
    this.emotionalForm.valueChanges.subscribe(val => {
      clearTimeout(this.autosaveTimer);
      this.autosaveTimer = setTimeout(() => {
        this.storage.setJson('onboarding_emotional', val);
      }, 300);
    });
  }

  private loadExistingData(): void {
    const existingData = this.storage.getJson<any>('onboarding_emotional');
    if (existingData) {
      this.emotionalForm.patchValue(existingData);
    }
  }

  onSwipeNext(): void {
    if (this.emotionalForm.valid) {
      this.onSubmit();
    }
  }

  onSwipePrev(): void {
    // Navigate back to previous app route if exists
    this.router.navigate(['/onboarding']);
  }

  onSubmit(): void {
    if (this.emotionalForm.valid) {
      this.isSaving = true;
      // Store form data for later submission
      const emotionalData = this.emotionalForm.value;
      console.log('Saving emotional data:', emotionalData);
      this.storage.setJson('onboarding_emotional', emotionalData);

      // Verify data was saved
      const savedData = this.storage.getJson('onboarding_emotional');
      console.log('Verified saved emotional data:', savedData);

      // Navigate to next step
      setTimeout(() => {
        this.isSaving = false;
        this.router.navigate(['/onboarding/personality-assessment']);
      }, 600);
    }
  }

  getFieldError(fieldName: string): string | null {
    const field = this.emotionalForm.get(fieldName);
    if (field?.errors && field.touched) {
      if (field.errors['required']) {
        return 'This question is required to help us understand you better.';
      }
      if (field.errors['minlength']) {
        return 'Please share a bit more to help create meaningful connections.';
      }
    }
    return null;
  }
}
