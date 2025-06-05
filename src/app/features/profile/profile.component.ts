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
import { ProfileService } from '../../core/services/profile.service';

interface ProfilePictureResponse {
  url: string;
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
    MatChipsModule
  ]
})
export class ProfileComponent implements OnInit {
  profileForm: FormGroup;
  isLoading = false;
  isUploading = false;
  error: string | null = null;
  uploadError: string | null = null;
  successMessage: string | null = null;

  readonly dietaryOptions = [
    'vegetarian', 'vegan', 'pescatarian', 'gluten-free',
    'dairy-free', 'kosher', 'halal', 'keto', 'paleo',
    'no restrictions', 'other'
  ];

  readonly genderOptions = ['male', 'female', 'non-binary'];

  constructor(private readonly fb: FormBuilder, private readonly profileService: ProfileService) {
    this.profileForm = this.fb.group({
      firstName: ['', [Validators.required]],
      lastName: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      bio: ['', [Validators.maxLength(500)]],
      profilePicture: [null],
      interests: [[]],
      dietaryPreferences: [[]],
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
        this.profileForm.patchValue(profile);
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

      const formData = new FormData();
      Object.entries(this.profileForm.value).forEach(([key, value]) => {
        if (key === 'locationPreferences' || key === 'matchPreferences') {
          formData.append(key, JSON.stringify(value));
        } else {
          formData.append(key, value as string | Blob);
        }
      });

      this.profileService.updateProfile(formData).subscribe({
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
          this.profileForm.patchValue({ profilePicture: response.url });
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
}
