import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface PotentialMatch {
  _id: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  bio: string;
  profilePictures: string[];
  interests: string[];
  dietaryPreferences: string[];
  distance: number;
  matchPercentage?: number;
  lastActive?: Date;
}

@Injectable({
  providedIn: 'root'
})
export class DiscoverService {
  private apiUrl = `${environment.apiUrl}/discover`;

  constructor(private http: HttpClient) {}

  getProfiles(): Observable<PotentialMatch[]> {
    return this.http.get<PotentialMatch[]>(`${this.apiUrl}/profiles`).pipe(
      map(profiles => profiles.map(profile => ({
        ...profile,
        lastActive: profile.lastActive ? new Date(profile.lastActive) : undefined
      }))),
      catchError(error => {
        console.error('Error fetching profiles:', error);
        throw new Error('Failed to load potential matches');
      })
    );
  }

  likeProfile(profileId: string): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/like/${profileId}`, {}).pipe(
      catchError(error => {
        console.error('Error liking profile:', error);
        throw new Error('Failed to like profile');
      })
    );
  }

  dislikeProfile(profileId: string): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/dislike/${profileId}`, {}).pipe(
      catchError(error => {
        console.error('Error disliking profile:', error);
        throw new Error('Failed to pass on profile');
      })
    );
  }

  // Additional methods for future implementation
  getMatches(): Observable<PotentialMatch[]> {
    return this.http.get<PotentialMatch[]>(`${this.apiUrl}/matches`);
  }

  getMutualInterests(profileId: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/mutual-interests/${profileId}`);
  }

  getMatchPercentage(profileId: string): Observable<number> {
    return this.http.get<number>(`${this.apiUrl}/match-percentage/${profileId}`);
  }
}
