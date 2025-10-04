import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSliderModule } from '@angular/material/slider';
import { MatChipsModule } from '@angular/material/chips';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { ProfileService, UserProfileData } from '../../core/services/profile.service';
import { AuthService } from '../../core/services/auth.service';

interface ProfilePictureResponse {
  message: string;
  profile_picture_url: string;
}

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatProgressBarModule,
    MatSelectModule,
    MatSliderModule,
    MatChipsModule,
    MatSlideToggleModule
  ]
})
export class ProfileComponent implements OnInit {
  profileForm: FormGroup;
  isLoading = false;
  isUploading = false;
  error: string | null = null;
  uploadError: string | null = null;
  successMessage: string | null = null;
  currentUser: UserProfileData | null = null;

  readonly dietaryOptions = [
    'vegetarian', 'vegan', 'pescatarian', 'gluten-free',
    'dairy-free', 'kosher', 'halal', 'keto', 'paleo',
    'no restrictions', 'other'
  ];

  readonly genderOptions = ['male', 'female', 'non-binary'];

  constructor(
    private readonly fb: FormBuilder,
    private readonly profileService: ProfileService,
    private readonly authService: AuthService
  ) {
    this.profileForm = this.fb.group({
      firstName: ['', [Validators.required]],
      lastName: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      bio: ['', [Validators.maxLength(500)]],
      profilePicture: [null],
      interests: [[]],
      dietaryPreferences: [[]],

      // Soul Before Skin fields
      soulProfileVisibility: ['discovery'],
      photoSharingConsent: [false],
      coreValues: this.fb.group({
        relationshipValues: [''],
        idealEvening: [''],
        feelingUnderstood: ['']
      }),
      communicationStyle: this.fb.group({
        preferredStyle: ['deep_conversation'],
        responsePreference: ['flexible']
      }),

      locationPreferences: this.fb.group({
        city: ['', [Validators.required]],
        maxDistance: [30, [Validators.min(5), Validators.max(100)]]
      }),
      matchPreferences: this.fb.group({
        ageRange: this.fb.group({
          min: [21, [Validators.required, Validators.min(18)]],
          max: [65, [Validators.required, Validators.max(99)]]
        }),
        genders: [[]]
      })
    });
  }

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile(): void {
    this.isLoading = true;
    this.profileService.getProfile().subscribe({
      next: (profile) => {
        this.currentUser = profile;

        // Map profile data to form structure
        const formData = {
          ...profile,
          firstName: profile.first_name,
          lastName: profile.last_name,
          soulProfileVisibility: profile.soul_profile_visibility || 'discovery',
          photoSharingConsent: profile.photo_sharing_consent || false,
          coreValues: {
            relationshipValues: profile.emotional_responses?.relationship_values || '',
            idealEvening: profile.emotional_responses?.ideal_evening || '',
            feelingUnderstood: profile.emotional_responses?.feeling_understood || ''
          },
          communicationStyle: {
            preferredStyle: profile.communication_style?.preferred_style || 'deep_conversation',
            responsePreference: profile.communication_style?.response_preference || 'flexible'
          }
        };

        this.profileForm.patchValue(formData);
      },
      error: (err) => {
        this.error = err.message ?? 'Failed to load profile';
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }

  addInterest(interest: string): void {
    if (!interest.trim()) return;
    const interests = this.profileForm.get('interests')?.value ?? [];
    if (!interests.includes(interest.trim())) {
      this.profileForm.patchValue({
        interests: [...interests, interest.trim()]
      });
    }
  }

  removeInterest(interest: string): void {
    const interests = this.profileForm.get('interests')?.value ?? [];
    this.profileForm.patchValue({
      interests: interests.filter((i: string) => i !== interest)
    });
  }

  onSubmit(): void {
    if (this.profileForm.valid) {
      this.isLoading = true;
      this.error = null;
      this.successMessage = null;

      // Convert form data to ProfileUpdateData format
      const formValue = this.profileForm.value;
      const profileData = {
        first_name: formValue.firstName,
        last_name: formValue.lastName,
        bio: formValue.bio,
        location: formValue.locationPreferences?.city,
        interests: formValue.interests || [],
        dietary_preferences: formValue.dietaryPreferences || [],
        gender: formValue.gender,
        date_of_birth: formValue.dateOfBirth,

        // Soul Before Skin fields
        emotional_responses: {
          relationship_values: formValue.coreValues?.relationshipValues,
          ideal_evening: formValue.coreValues?.idealEvening,
          feeling_understood: formValue.coreValues?.feelingUnderstood
        },
        communication_style: {
          preferred_style: formValue.communicationStyle?.preferredStyle,
          response_preference: formValue.communicationStyle?.responsePreference
        },
        soul_profile_visibility: formValue.soulProfileVisibility,
        photo_sharing_consent: formValue.photoSharingConsent
      };

      this.profileService.updateProfile(profileData).subscribe({
        next: () => {
          this.successMessage = 'Profile updated successfully';
        },
        error: (err) => {
          this.error = err.message ?? 'Failed to update profile';
        },
        complete: () => {
          this.isLoading = false;
        }
      });
    }
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        this.uploadError = 'File size must be less than 5MB';
        return;
      }

      this.isUploading = true;
      this.uploadError = null;

      this.profileService.uploadProfilePicture(file).subscribe({
        next: (response: ProfilePictureResponse) => {
          this.profileForm.patchValue({ profilePicture: response.profile_picture_url });
          this.isUploading = false;
        },
        error: (error: Error) => {
          this.uploadError = error.message ?? 'Failed to upload image';
          this.isUploading = false;
        }
      });
    }
  }

  getFileName(value: string | File): string {
    if (value instanceof File) {
      return value.name;
    }
    return value.split('/').pop() ?? 'No file selected';
  }

  getDepthScoreDescription(score: number): string {
    if (score >= 90) return 'Exceptional emotional depth and self-awareness';
    if (score >= 80) return 'High emotional intelligence and introspection';
    if (score >= 70) return 'Good emotional awareness and connection ability';
    if (score >= 60) return 'Developing emotional depth and understanding';
    if (score >= 50) return 'Basic emotional awareness with room for growth';
    return 'Early stages of emotional self-discovery';
  }
}
