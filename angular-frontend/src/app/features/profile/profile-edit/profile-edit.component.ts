import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { ProfileService, UserProfileData, ProfileUpdateData } from '../../../core/services/profile.service';

@Component({
  selector: 'app-profile-edit',
  templateUrl: './profile-edit.component.html',
  styleUrls: ['./profile-edit.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatChipsModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule
  ]
})
export class ProfileEditComponent implements OnInit {
  profileForm!: FormGroup;
  isLoading = true;
  isSaving = false;
  isUploading = false;
  error: string | null = null;
  uploadError: string | null = null;

  readonly genderOptions = [
    'male',
    'female', 
    'non-binary',
    'other',
    'prefer-not-to-say'
  ];

  readonly dietaryOptions = [
    'omnivore',
    'vegetarian',
    'vegan',
    'pescatarian',
    'keto',
    'paleo',
    'gluten-free',
    'dairy-free',
    'halal',
    'kosher',
    'other'
  ];

  availableInterests: string[] = [
    'cooking', 'wine tasting', 'fine dining', 'street food', 'baking',
    'cocktails', 'coffee', 'farmers markets', 'food photography', 'nutrition',
    'travel', 'music', 'movies', 'books', 'art', 'fitness', 'yoga',
    'hiking', 'swimming', 'dancing', 'photography', 'gaming', 'technology'
  ];

  constructor(
    private readonly fb: FormBuilder,
    private readonly profileService: ProfileService,
    private readonly router: Router,
    private readonly snackBar: MatSnackBar
  ) {
    this.initializeForm();
  }

  ngOnInit(): void {
    this.loadProfile();
  }

  private initializeForm(): void {
    this.profileForm = this.fb.group({
      first_name: ['', [Validators.required, Validators.minLength(2)]],
      last_name: ['', [Validators.required, Validators.minLength(2)]],
      date_of_birth: ['', [Validators.required, this.minimumAgeValidator()]],
      gender: ['', [Validators.required]],
      location: ['', [Validators.required]],
      bio: ['', [Validators.maxLength(500)]],
      interests: [[]],
      dietary_preferences: [[]]
    });
  }

  private minimumAgeValidator() {
    return (control: any) => {
      if (!control.value) return null;
      
      const birthDate = new Date(control.value);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        return age < 18 ? { underage: true } : null;
      }
      
      return age < 18 ? { underage: true } : null;
    };
  }

  loadProfile(): void {
    this.isLoading = true;
    this.error = null;

    this.profileService.getProfile().subscribe({
      next: (profileData) => {
        this.populateForm(profileData);
        this.isLoading = false;
      },
      error: (err) => {
        this.error = err.message || 'Failed to load profile';
        this.isLoading = false;
      }
    });
  }

  private populateForm(profileData: UserProfileData): void {
    this.profileForm.patchValue({
      first_name: profileData.first_name || '',
      last_name: profileData.last_name || '',
      date_of_birth: profileData.date_of_birth ? new Date(profileData.date_of_birth) : '',
      gender: profileData.gender || '',
      location: profileData.location || '',
      bio: profileData.bio || '',
      interests: profileData.interests || [],
      dietary_preferences: profileData.dietary_preferences || []
    });
  }

  addInterest(interest: string): void {
    if (!interest.trim()) return;
    
    const currentInterests = this.profileForm.get('interests')?.value || [];
    const interestToAdd = interest.trim().toLowerCase();
    
    if (!currentInterests.includes(interestToAdd)) {
      this.profileForm.patchValue({
        interests: [...currentInterests, interestToAdd]
      });
    }
  }

  removeInterest(interest: string): void {
    const currentInterests = this.profileForm.get('interests')?.value || [];
    this.profileForm.patchValue({
      interests: currentInterests.filter((i: string) => i !== interest)
    });
  }

  addInterestFromList(interest: string): void {
    this.addInterest(interest);
  }

  onSubmit(): void {
    if (this.profileForm.valid) {
      this.isSaving = true;
      this.error = null;

      const formData = this.profileForm.value;
      
      // Format date for backend
      if (formData.date_of_birth instanceof Date) {
        formData.date_of_birth = formData.date_of_birth.toISOString().split('T')[0];
      }

      const updateData: ProfileUpdateData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        date_of_birth: formData.date_of_birth,
        gender: formData.gender,
        location: formData.location,
        bio: formData.bio,
        interests: formData.interests,
        dietary_preferences: formData.dietary_preferences
      };

      this.profileService.updateProfile(updateData).subscribe({
        next: () => {
          this.snackBar.open('Profile updated successfully!', 'Close', {
            duration: 3000,
            panelClass: ['success-snackbar']
          });
          this.router.navigate(['/profile']);
        },
        error: (err) => {
          this.error = err.message || 'Failed to update profile';
          this.isSaving = false;
        }
      });
    } else {
      this.markFormGroupTouched();
    }
  }

  private markFormGroupTouched(): void {
    Object.keys(this.profileForm.controls).forEach(field => {
      const control = this.profileForm.get(field);
      control?.markAsTouched({ onlySelf: true });
    });
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      
      // Validate file type
      if (!file.type.startsWith('image/')) {
        this.uploadError = 'Please select an image file';
        return;
      }
      
      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        this.uploadError = 'File size must be less than 5MB';
        return;
      }

      this.isUploading = true;
      this.uploadError = null;

      this.profileService.uploadProfilePicture(file).subscribe({
        next: (response) => {
          this.snackBar.open('Profile picture uploaded successfully!', 'Close', {
            duration: 3000,
            panelClass: ['success-snackbar']
          });
          this.isUploading = false;
        },
        error: (err) => {
          this.uploadError = err.message || 'Failed to upload image';
          this.isUploading = false;
        }
      });
    }
  }

  cancel(): void {
    this.router.navigate(['/profile']);
  }
}