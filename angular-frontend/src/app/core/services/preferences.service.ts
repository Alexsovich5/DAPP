import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PreferencesService {
  private reducedMotionSubject = new BehaviorSubject<boolean>(false);
  readonly reducedMotion$ = this.reducedMotionSubject.asObservable();

  private hapticsEnabledSubject = new BehaviorSubject<boolean>(true);
  readonly hapticsEnabled$ = this.hapticsEnabledSubject.asObservable();

  constructor(private http: HttpClient) {
    // Initialize from CSS/media queries
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.reducedMotionSubject.next(reduce);
  }

  getPreferences(): Observable<any> {
    return this.http.get(`${environment.apiUrl}/preferences`);
  }

  updatePreferences(preferences: any): Observable<any> {
    return this.http.put(`${environment.apiUrl}/preferences`, preferences);
  }

  setReducedMotion(enabled: boolean): void {
    this.reducedMotionSubject.next(enabled);
    document.documentElement.style.setProperty('--motion-ease', enabled ? 'linear' : 'cubic-bezier(0.22, 1, 0.36, 1)');
  }

  setHapticsEnabled(enabled: boolean): void {
    this.hapticsEnabledSubject.next(enabled);
  }
}
