import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map, switchMap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User } from '../interfaces/auth.interfaces';
import { AuthService } from './auth.service';

export interface UserProfileData {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  gender?: string;
  bio?: string;
  location?: string;
  profile_picture?: string;
  interests?: string[];
  dietary_preferences?: string[];
  is_profile_complete: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProfileUpdateData {
  first_name?: string;
  last_name?: string;
  bio?: string;
  location?: string;
  interests?: string[];
  dietary_preferences?: string[];
  gender?: string;
  date_of_birth?: string;
}

export interface ProfilePictureResponse {
  message: string;
  profile_picture_url: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProfileService {
  private readonly apiUrl = environment.apiUrl;

  constructor(
    private readonly http: HttpClient,
    private readonly authService: AuthService
  ) {}

  // Get current user's profile data from the user endpoint
  getProfile(): Observable<UserProfileData> {
    return this.http.get<User>(`${this.apiUrl}/users/me`);
  }

  // Update user profile information
  updateProfile(profileData: ProfileUpdateData): Observable<UserProfileData> {
    return this.http.put<User>(`${this.apiUrl}/users/me`, profileData).pipe(
      map(updatedUser => {
        // Update the auth service's current user
        this.authService.updateCurrentUser(updatedUser);
        return updatedUser;
      })
    );
  }

  // Upload profile picture
  uploadProfilePicture(file: File): Observable<ProfilePictureResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<ProfilePictureResponse>(`${this.apiUrl}/users/me/profile-picture`, formData);
  }

  // Calculate profile completion percentage
  calculateProfileCompletion(user: UserProfileData): number {
    const requiredFields = [
      'first_name',
      'last_name', 
      'date_of_birth',
      'gender',
      'location',
      'bio'
    ];
    
    const optionalFields = [
      'interests',
      'dietary_preferences',
      'profile_picture'
    ];

    let completedRequired = 0;
    let completedOptional = 0;

    // Check required fields
    requiredFields.forEach(field => {
      const value = user[field as keyof UserProfileData];
      if (value && (typeof value === 'string' ? value.trim() : value)) {
        completedRequired++;
      }
    });

    // Check optional fields  
    optionalFields.forEach(field => {
      const value = user[field as keyof UserProfileData];
      if (value && (Array.isArray(value) ? value.length > 0 : value)) {
        completedOptional++;
      }
    });

    // Required fields worth 70%, optional fields worth 30%
    const requiredPercentage = (completedRequired / requiredFields.length) * 70;
    const optionalPercentage = (completedOptional / optionalFields.length) * 30;
    
    return Math.round(requiredPercentage + optionalPercentage);
  }
}
