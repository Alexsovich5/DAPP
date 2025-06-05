import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSliderModule } from '@angular/material/slider';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { PreferencesService } from '../../core/services/preferences.service';

interface CuisineOption {
  value: string;
  label: string;
  description?: string;
}

@Component({
  selector: 'app-preferences',
  templateUrl: './preferences.component.html',
  styleUrls: ['./preferences.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSliderModule,
    MatButtonModule,
    MatProgressBarModule,
    MatIconModule
  ]
})
export class PreferencesComponent implements OnInit {
  preferencesForm!: FormGroup;
  isLoading = false;
  successMessage: string | null = null;
  error: string | null = null;

  readonly cuisineOptions: CuisineOption[] = [
    { value: 'italian', label: 'Italian', description: 'Pasta, Pizza, and Mediterranean flavors' },
    { value: 'japanese', label: 'Japanese', description: 'Sushi, Ramen, and more' },
    { value: 'mexican', label: 'Mexican', description: 'Tacos, Burritos, and spicy cuisine' },
    { value: 'indian', label: 'Indian', description: 'Curry, Tandoori, and aromatic spices' },
    { value: 'chinese', label: 'Chinese', description: 'Dim Sum, Noodles, and stir-fry' },
    { value: 'thai', label: 'Thai', description: 'Pad Thai, Curry, and Southeast Asian' },
    { value: 'french', label: 'French', description: 'Fine dining and classic cuisine' },
    { value: 'mediterranean', label: 'Mediterranean', description: 'Greek, Turkish, and Middle Eastern' },
    { value: 'vegetarian', label: 'Vegetarian', description: 'Plant-based dishes' },
    { value: 'vegan', label: 'Vegan', description: 'Strictly plant-based cuisine' }
  ];

  readonly dietaryRestrictions = [
    'None',
    'Vegetarian',
    'Vegan',
    'Pescatarian',
    'Gluten-Free',
    'Dairy-Free',
    'Kosher',
    'Halal',
    'Nut Allergy',
    'Shellfish Allergy'
  ];

  readonly priceRanges = [
    { value: '1', label: '$', description: 'Budget-friendly' },
    { value: '2', label: '$$', description: 'Moderate' },
    { value: '3', label: '$$$', description: 'Upscale' },
    { value: '4', label: '$$$$', description: 'Fine Dining' }
  ];

  readonly diningStyles = [
    'Casual Dining',
    'Fine Dining',
    'Fast Casual',
    'Food Trucks',
    'Cafes',
    'Bistros',
    'Pop-up Restaurants'
  ];

  readonly mealPreferences = [
    'Breakfast/Brunch',
    'Lunch',
    'Dinner',
    'Late Night'
  ];

  readonly atmospherePreferences = [
    'Quiet & Intimate',
    'Lively & Social',
    'Outdoor Seating',
    'Rooftop',
    'Live Music',
    'Sports Bar',
    'Wine Bar'
  ];

  constructor(
    private readonly fb: FormBuilder,
    private readonly preferencesService: PreferencesService
  ) {
    this.initializeForm();
  }

  ngOnInit(): void {
    this.loadPreferences();
  }

  private initializeForm(): void {
    this.preferencesForm = this.fb.group({
      cuisinePreferences: [[], [Validators.required, Validators.minLength(1)]],
      dietaryRestrictions: [[]],
      priceRanges: [[], [Validators.required, Validators.minLength(1)]],
      diningStyles: [[]],
      mealPreferences: [[]],
      atmospherePreferences: [[]],
      location: this.fb.group({
        city: ['', Validators.required],
        maxDistance: [10, [Validators.required, Validators.min(1), Validators.max(50)]]
      }),
      scheduling: this.fb.group({
        preferredDays: [[]],
        preferredTimes: [[]]
      }),
      matchPreferences: this.fb.group({
        ageRange: this.fb.group({
          min: [21, [Validators.required, Validators.min(18)]],
          max: [65, [Validators.required, Validators.max(99)]]
        }),
        genderPreference: [''],
        lookingFor: ['']
      })
    });
  }

  loadPreferences(): void {
    this.isLoading = true;
    this.error = null;

    this.preferencesService.getPreferences().subscribe({
      next: (preferences) => {
        this.preferencesForm.patchValue(preferences);
      },
      error: (err) => {
        this.error = err.message ?? 'Failed to load preferences';
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }

  onSubmit(): void {
    if (this.preferencesForm.valid) {
      this.isLoading = true;
      this.successMessage = null;
      this.error = null;

      this.preferencesService.updatePreferences(this.preferencesForm.value).subscribe({
        next: () => {
          this.successMessage = 'Your preferences have been updated successfully';
        },
        error: (err) => {
          this.error = err.message ?? 'Failed to update preferences';
        },
        complete: () => {
          this.isLoading = false;
        }
      });
    } else {
      this.error = 'Please fill in all required fields correctly';
      this.markFormGroupTouched(this.preferencesForm);
    }
  }

  isFieldInvalid(path: string): boolean {
    const field = this.preferencesForm.get(path);
    return !!field && field.invalid && (field.dirty || field.touched);
  }

  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.values(formGroup.controls).forEach(control => {
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
      control.markAsTouched();
    });
  }

  isDirty(): boolean {
    return this.preferencesForm.dirty;
  }

  reset(): void {
    this.loadPreferences();
  }
}
