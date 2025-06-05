import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, ValidatorFn, AbstractControl } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { RegisterData } from '../../../core/interfaces/auth.interfaces';
import { StepperSelectionEvent } from '@angular/cdk/stepper';
import { HttpErrorResponse } from '@angular/common/http';

import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatStepperModule } from '@angular/material/stepper';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatCheckboxModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatProgressBarModule,
    MatDividerModule,
    MatStepperModule
  ]
})
export class RegisterComponent implements OnInit {
  accountForm!: FormGroup;
  personalForm!: FormGroup;
  preferencesForm!: FormGroup;
  isLoading = false;
  error: string | null = null;
  currentYear = new Date().getFullYear();
  hidePassword = true;
  hideConfirmPassword = true;

  readonly dietaryOptions = [
    'omnivore',
    'vegetarian',
    'vegan',
    'pescatarian',
    'keto',
    'paleo',
    'gluten-free',
    'other'
  ];

  readonly cuisineOptions = [
    'italian',
    'mexican',
    'chinese',
    'japanese',
    'indian',
    'thai',
    'mediterranean',
    'french',
    'american',
    'other'
  ];

  readonly genderOptions = [
    'male',
    'female',
    'non-binary',
    'other',
    'prefer-not-to-say'
  ];

  readonly lookingForOptions = [
    'men',
    'women',
    'everyone'
  ];

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly router: Router
  ) {
    this.initializeForms();
  }

  ngOnInit(): void {
    this.error = null;
  }

  private passwordMatchValidator(): ValidatorFn {
    return (control: AbstractControl): {[key: string]: any} | null => {
      const form = control as FormGroup;
      const password = form.get('password');
      const confirmPassword = form.get('confirmPassword');

      if (password && confirmPassword && password.value !== confirmPassword.value) {
        confirmPassword.setErrors({ mismatch: true });
        return { mismatch: true };
      }

      return null;
    };
  }

  private initializeForms(): void {
    const eighteenYearsAgo = new Date();
    eighteenYearsAgo.setFullYear(eighteenYearsAgo.getFullYear() - 18);

    // Use type-safe form initialization
    this.accountForm = this.fb.group<{
      email: any;
      username: any;
      password: any;
      confirmPassword: any;
    }>({
      email: ['', [Validators.required, Validators.email]],
      username: ['', [
        Validators.required, 
        Validators.minLength(3),
        Validators.pattern(/^[a-zA-Z0-9_]+$/)
      ]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', [Validators.required]]
    }, { validators: this.passwordMatchValidator() });

    this.personalForm = this.fb.group<{
      firstName: any;
      lastName: any;
      birthdate: any;
      gender: any;
    }>({
      firstName: ['', [Validators.required]],
      lastName: ['', [Validators.required]],
      birthdate: ['', [Validators.required, this.minimumAgeValidator(eighteenYearsAgo)]],
      gender: ['', [Validators.required]]
    });

    this.preferencesForm = this.fb.group<{
      dietaryPreferences: any;
      cuisinePreferences: any;
      location: any;
      lookingFor: any;
      agreeTerms: any;
    }>({
      dietaryPreferences: [[], [Validators.required]],
      cuisinePreferences: ['', [Validators.required]],
      location: ['', [Validators.required]],
      lookingFor: ['', [Validators.required]],
      agreeTerms: [false, [Validators.requiredTrue]]
    });
  }

  private minimumAgeValidator(minDate: Date) {
    return (control: { value: string | number | Date; }) => {
      if (!control.value) {
        return null;
      }
      const birthDate = new Date(control.value);
      return birthDate <= minDate ? null : { underage: true };
    };
  }

  onStepChange(event: StepperSelectionEvent): void {
    this.error = null;
    const previousForm = this.getFormForStep(event.previouslySelectedIndex);
    if (previousForm) {
      previousForm.markAllAsTouched();
    }
  }

  private getFormForStep(index: number): FormGroup {
    switch (index) {
      case 0:
        return this.accountForm;
      case 1:
        return this.personalForm;
      case 2:
        return this.preferencesForm;
      default:
        return this.accountForm;
    }
  }

  isStepValid(index: number): boolean {
    const form = this.getFormForStep(index);
    return form.valid;
  }

  togglePasswordVisibility(field: 'password' | 'confirmPassword'): void {
    if (field === 'password') {
      this.hidePassword = !this.hidePassword;
    } else {
      this.hideConfirmPassword = !this.hideConfirmPassword;
    }
  }

  navigateToLogin(): void {
    this.router.navigate(['/login']);
  }

  getProgressValue(currentStep: number): number {
    return ((currentStep + 1) / 3) * 100;
  }

  onSubmit(): void {
    if (this.accountForm.valid && this.personalForm.valid && this.preferencesForm.valid) {
      this.isLoading = true;
      this.error = null;

      // Format the date properly for the Python backend (YYYY-MM-DD)
      const birthdate = this.personalForm.get('birthdate')?.value;
      const formattedDate = birthdate instanceof Date
        ? birthdate.toISOString().split('T')[0]
        : birthdate;

      // Convert single cuisine preference to array for backend compatibility
      const cuisinePreference = this.preferencesForm.get('cuisinePreferences')?.value;
      const cuisinePreferencesArray = cuisinePreference ? [cuisinePreference] : [];

      const formData: RegisterData = {
        email: this.accountForm.get('email')?.value,
        username: this.accountForm.get('username')?.value,
        password: this.accountForm.get('password')?.value,
        first_name: this.personalForm.get('firstName')?.value,
        last_name: this.personalForm.get('lastName')?.value,
        date_of_birth: formattedDate,
        gender: this.personalForm.get('gender')?.value,
        dietary_preferences: this.preferencesForm.get('dietaryPreferences')?.value,
        cuisine_preferences: cuisinePreferencesArray,
        location: this.preferencesForm.get('location')?.value,
        looking_for: this.preferencesForm.get('lookingFor')?.value
      };

      console.log('Sending registration data to FastAPI backend:', formData);

      this.authService.register(formData).subscribe({
        next: (response) => {
          console.log('Registration successful:', response);
          this.isLoading = false;
          // The backend now returns LoginResponse, so user is automatically logged in
          this.router.navigate(['/dashboard'], {
            state: { message: 'Registration successful! Welcome to Dinner1!' }
          });
        },
        error: (err: Error) => {
          console.error('Registration error:', err);
          this.error = err.message;
          this.isLoading = false;
        }
      });
    } else {
      this.markAllFormsAsTouched();
    }
  }

  private markAllFormsAsTouched(): void {
    [this.accountForm, this.personalForm, this.preferencesForm].forEach(form => {
      Object.values(form.controls).forEach(control => {
        control.markAsTouched();
      });
    });
  }
}
