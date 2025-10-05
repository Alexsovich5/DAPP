import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { BaseService } from './base.service';

export interface OnboardingData {
  relationship_values: string;
  ideal_evening: string;
  feeling_understood: string;
  core_values: Record<string, unknown>;
  personality_traits: Record<string, unknown>;
  communication_style: Record<string, unknown>;
  interests: string[];
}

export interface OnboardingStatus {
  completed: boolean;
  has_interests: boolean;
  profile_complete: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class OnboardingApiService extends BaseService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {
    super();
  }

  /**
   * Complete emotional onboarding with backend API
   */
  completeOnboarding(onboardingData: OnboardingData): Observable<{ success: boolean; message?: string }> {
    const url = `${this.apiUrl}/onboarding/complete`;
    console.log('Completing onboarding API call to:', url, 'with data:', onboardingData);

    return this.http.post<{ success: boolean; message?: string }>(url, onboardingData).pipe(
      tap(response => {
        console.log('Onboarding API response:', response);
        // Mark onboarding as completed in localStorage for frontend state
        localStorage.setItem('onboarding_completed', 'true');
      }),
      catchError(err => {
        console.error('Onboarding API error:', err);
        return this.handleError<{ success: boolean; message?: string }>('complete onboarding')(err);
      })
    );
  }

  /**
   * Get current onboarding status
   */
  getOnboardingStatus(): Observable<OnboardingStatus> {
    const url = `${this.apiUrl}/onboarding/status`;
    return this.http.get<OnboardingStatus>(url).pipe(
      tap(status => console.log('Onboarding status:', status)),
      catchError(this.handleError<OnboardingStatus>('get onboarding status'))
    );
  }
}
