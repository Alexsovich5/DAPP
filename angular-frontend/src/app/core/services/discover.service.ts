import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { BaseService } from './base.service';

export interface PotentialMatch {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  bio: string;
  profile_picture: string;
  interests: string[];
  dietary_preferences: string[];
  location: string;
  matchPercentage?: number;
  lastActive?: Date;
}

@Injectable({
  providedIn: 'root'
})
export class DiscoverService extends BaseService {
  private apiUrl = `${environment.apiUrl}/users`;

  constructor(private http: HttpClient) {
    super();
  }

  getProfiles(): Observable<PotentialMatch[]> {
    return this.http.get<PotentialMatch[]>(`${this.apiUrl}/potential-matches`).pipe(
      map(profiles => profiles.map(profile => ({
        ...profile,
        lastActive: profile.lastActive ? new Date(profile.lastActive) : undefined
      }))),
      catchError(this.handleError<PotentialMatch[]>('load potential matches', []))
    );
  }

  likeProfile(profileId: string): Observable<void> {
    return this.http.post<void>(`${environment.apiUrl}/matches`, {
      receiver_id: parseInt(profileId),
      restaurant_preference: '',
      proposed_date: null
    }).pipe(
      tap(() => this.notificationService.showSuccess('Profile liked successfully!')),
      catchError(this.handleError<void>('like profile'))
    );
  }

  dislikeProfile(profileId: string): Observable<void> {
    // No backend endpoint for dislike - just return success
    // This could be enhanced to track dislikes locally or add backend support
    return of(undefined);
  }

  // Additional methods for future implementation
  getMatches(): Observable<PotentialMatch[]> {
    return this.http.get<PotentialMatch[]>(`${environment.apiUrl}/matches/sent`);
  }

  getMutualInterests(profileId: string): Observable<string[]> {
    // TODO: Implement backend endpoint for mutual interests
    return of([]);
  }

  getMatchPercentage(profileId: string): Observable<number> {
    // TODO: Implement backend endpoint for match percentage calculation
    return of(0);
  }
}
