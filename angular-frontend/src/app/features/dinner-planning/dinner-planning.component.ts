import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { DfButtonDirective, DfChipComponent, DfInputDirective } from '../../shared/ui';

const CUISINE_SUGGESTIONS: { label: string; icon: string }[] = [
  { label: 'Italian',       icon: 'local_pizza' },
  { label: 'Japanese',      icon: 'ramen_dining' },
  { label: 'French',        icon: 'wine_bar' },
  { label: 'Mexican',       icon: 'breakfast_dining' },
  { label: 'Mediterranean', icon: 'kebab_dining' },
  { label: 'Vegan',         icon: 'eco' },
];

@Component({
  selector: 'app-dinner-planning',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatIconModule,
    MatSnackBarModule,
    DfButtonDirective,
    DfChipComponent,
    DfInputDirective,
  ],
  template: `
    <div class="dinner-planning-page">
      <header class="page-header">
        <button mat-icon-button type="button" aria-label="Go back" (click)="goBack()">
          <mat-icon>arrow_back</mat-icon>
        </button>
        <div>
          <h1>Plan Your First Dinner</h1>
          <p class="subtitle">The soul journey ends with a real first dinner. Make it special.</p>
        </div>
      </header>

      <!-- Cuisine Suggestions -->
      <mat-card class="suggestions-card">
        <mat-card-header>
          <mat-icon mat-card-avatar aria-hidden="true">restaurant</mat-icon>
          <mat-card-title>What sounds good?</mat-card-title>
          <mat-card-subtitle>Pick a vibe for the evening</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div class="cuisine-chips" role="group" aria-label="Cuisine options">
            <df-chip
              *ngFor="let c of cuisines"
              purpose="interest"
              [class.is-selected]="selectedCuisine === c.label"
              [attr.aria-pressed]="selectedCuisine === c.label"
              role="button"
              tabindex="0"
              (click)="selectCuisine(c.label)"
              (keydown.enter)="selectCuisine(c.label)">
              <mat-icon aria-hidden="true">{{ c.icon }}</mat-icon>
              {{ c.label }}
            </df-chip>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Dinner Form -->
      <mat-card class="form-card">
        <mat-card-header>
          <mat-icon mat-card-avatar aria-hidden="true">calendar_today</mat-icon>
          <mat-card-title>Pick a date</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <form [formGroup]="dinnerForm" (ngSubmit)="onSubmit()" class="dinner-form">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Date</mat-label>
              <input
                matInput
                [matDatepicker]="datepicker"
                formControlName="date"
                [min]="minDate"
                placeholder="Choose a date"
                aria-label="Dinner date">
              <mat-datepicker-toggle matIconSuffix [for]="datepicker"></mat-datepicker-toggle>
              <mat-datepicker #datepicker></mat-datepicker>
              <mat-error *ngIf="dinnerForm.get('date')?.errors?.['required']">Please choose a date</mat-error>
            </mat-form-field>

            <label class="dinner-form__field">
              <span class="dinner-form__field-label">Notes (optional)</span>
              <textarea
                dfInput
                formControlName="notes"
                rows="3"
                placeholder="Anything special to plan for — dietary needs, occasion, vibe..."
                aria-label="Dinner notes">
              </textarea>
            </label>

            <button
              dfButton
              variant="primary"
              size="md"
              type="submit"
              class="dinner-form__submit"
              [disabled]="dinnerForm.invalid || isSubmitting"
              aria-label="Send dinner plan to partner">
              <mat-icon>send</mat-icon>
              {{ isSubmitting ? 'Sending...' : 'Share with your match' }}
            </button>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .dinner-planning-page { padding: 16px; max-width: 600px; margin: 0 auto; }
    .page-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 16px; }
    .page-header h1 { margin: 0 0 4px; font-size: 1.5rem; color: var(--color-text); }
    .subtitle { margin: 0; color: var(--color-text-muted); font-size: 0.875rem; }
    .suggestions-card, .form-card { margin-bottom: 16px; }
    .cuisine-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    df-chip { cursor: pointer; display: inline-flex; align-items: center; gap: 4px; }
    df-chip.is-selected { background: var(--color-primary); color: var(--color-surface); }
    .dinner-form { display: flex; flex-direction: column; gap: 12px; padding-top: 8px; }
    .full-width { width: 100%; }
    .dinner-form__field { display: flex; flex-direction: column; gap: var(--space-1); }
    .dinner-form__field-label { font-size: var(--type-small-size); color: var(--color-text-muted); }
    .dinner-form__submit { width: 100%; margin-top: 4px; }
    .dinner-form__submit mat-icon { margin-right: 6px; vertical-align: middle; }
  `]
})
export class DinnerPlanningComponent implements OnInit, OnDestroy {
  dinnerForm: FormGroup;
  selectedCuisine: string | null = null;
  isSubmitting = false;
  minDate = new Date();
  cuisines = CUISINE_SUGGESTIONS;

  private connectionId: number | null = null;
  private submitTimer?: ReturnType<typeof setTimeout>;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.dinnerForm = this.fb.group({
      date: [null, Validators.required],
      notes: ['']
    });
  }

  ngOnDestroy(): void {
    clearTimeout(this.submitTimer);
  }

  ngOnInit(): void {
    const id = this.route.snapshot.queryParamMap.get('connectionId');
    this.connectionId = id ? Number(id) : null;
  }

  selectCuisine(label: string): void {
    this.selectedCuisine = this.selectedCuisine === label ? null : label;
  }

  onSubmit(): void {
    if (this.dinnerForm.invalid) return;
    this.isSubmitting = true;
    // Stub: production would POST to /api/v1/dinner-plans
    this.submitTimer = setTimeout(() => {
      this.isSubmitting = false;
      this.snackBar.open('Dinner plan shared with your match!', 'Great', { duration: 3000 });
      if (this.connectionId) {
        this.router.navigate(['/chat'], { queryParams: { connectionId: this.connectionId } });
      }
    }, 800);
  }

  goBack(): void {
    this.router.navigate(['/conversations']);
  }
}
