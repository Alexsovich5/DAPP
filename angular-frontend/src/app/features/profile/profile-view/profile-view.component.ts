import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Observable } from 'rxjs';

import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatBadgeModule } from '@angular/material/badge';

import { AuthService } from '../../../core/services/auth.service';
import { ProfileService, UserProfileData } from '../../../core/services/profile.service';
import { User } from '../../../core/interfaces/auth.interfaces';

@Component({
  selector: 'app-profile-view',
  templateUrl: './profile-view.component.html',
  styleUrls: ['./profile-view.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatChipsModule,
    MatDividerModule,
    MatBadgeModule
  ]
})
export class ProfileViewComponent implements OnInit {
  currentUser$: Observable<User | null>;
  profileData: UserProfileData | null = null;
  profileCompletion = 0;
  isLoading = true;
  error: string | null = null;

  constructor(
    private readonly authService: AuthService,
    private readonly profileService: ProfileService,
    private readonly router: Router
  ) {
    this.currentUser$ = this.authService.currentUser$;
  }

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile(): void {
    this.isLoading = true;
    this.error = null;

    this.profileService.getProfile().subscribe({
      next: (profileData) => {
        this.profileData = profileData;
        this.profileCompletion = this.profileService.calculateProfileCompletion(profileData);
        this.isLoading = false;
      },
      error: (err) => {
        this.error = err.message || 'Failed to load profile';
        this.isLoading = false;
      }
    });
  }

  editProfile(): void {
    this.router.navigate(['/profile/edit']);
  }

  getAgeFromBirthDate(dateOfBirth: string): number | null {
    if (!dateOfBirth) return null;
    
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    
    return age;
  }

  getCompletionMessage(): string {
    if (this.profileCompletion >= 90) {
      return 'Your profile is looking great! 🎉';
    } else if (this.profileCompletion >= 70) {
      return 'Almost there! A few more details would help.';
    } else if (this.profileCompletion >= 50) {
      return 'Good start! Consider adding more information.';
    } else {
      return 'Let\'s complete your profile to attract better matches.';
    }
  }

  getCompletionColor(): string {
    if (this.profileCompletion >= 80) return 'primary';
    if (this.profileCompletion >= 60) return 'accent'; 
    return 'warn';
  }
}