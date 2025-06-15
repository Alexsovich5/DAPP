import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { BaseService } from './base.service';
import {
  SoulConnection,
  SoulConnectionCreate,
  SoulConnectionUpdate,
  DiscoveryRequest,
  DiscoveryResponse,
  CompatibilityResponse
} from '../interfaces/soul-connection.interfaces';

@Injectable({
  providedIn: 'root'
})
export class SoulConnectionService extends BaseService {
  private readonly apiUrl = environment.apiUrl;
  private activeConnectionsSubject = new BehaviorSubject<SoulConnection[]>([]);
  readonly activeConnections$ = this.activeConnectionsSubject.asObservable();

  constructor(private readonly http: HttpClient) {
    super();
  }

  /**
   * Discover potential soul connections using local compatibility algorithms
   */
  discoverSoulConnections(request: DiscoveryRequest = {}): Observable<DiscoveryResponse[]> {
    let params = new HttpParams();
    
    if (request.max_results) {
      params = params.set('max_results', request.max_results.toString());
    }
    if (request.min_compatibility) {
      params = params.set('min_compatibility', request.min_compatibility.toString());
    }
    if (request.hide_photos !== undefined) {
      params = params.set('hide_photos', request.hide_photos.toString());
    }
    if (request.age_range_min) {
      params = params.set('age_range_min', request.age_range_min.toString());
    }
    if (request.age_range_max) {
      params = params.set('age_range_max', request.age_range_max.toString());
    }

    return this.http.get<DiscoveryResponse[]>(`${this.apiUrl}/soul-connections/discover`, { params }).pipe(
      catchError(this.handleError<DiscoveryResponse[]>('discover soul connections', []))
    );
  }

  /**
   * Initiate a new soul connection with another user
   */
  initiateSoulConnection(connectionData: SoulConnectionCreate): Observable<SoulConnection> {
    return this.http.post<SoulConnection>(`${this.apiUrl}/soul-connections/initiate`, connectionData)
      .pipe(
        tap(() => this.refreshActiveConnections()),
        tap(this.handleSuccess('Soul connection initiated', true)),
        catchError(this.handleError<SoulConnection>('initiate soul connection'))
      );
  }

  /**
   * Get all active soul connections for the current user
   */
  getActiveConnections(): Observable<SoulConnection[]> {
    return this.http.get<SoulConnection[]>(`${this.apiUrl}/soul-connections/active`)
      .pipe(
        tap(connections => this.activeConnectionsSubject.next(connections))
      );
  }

  /**
   * Get details of a specific soul connection
   */
  getSoulConnection(connectionId: number): Observable<SoulConnection> {
    return this.http.get<SoulConnection>(`${this.apiUrl}/soul-connections/${connectionId}`);
  }

  /**
   * Update a soul connection (progression, consent, etc.)
   */
  updateSoulConnection(connectionId: number, updateData: SoulConnectionUpdate): Observable<SoulConnection> {
    return this.http.put<SoulConnection>(`${this.apiUrl}/soul-connections/${connectionId}`, updateData)
      .pipe(
        tap(() => this.refreshActiveConnections())
      );
  }

  /**
   * Progress a connection to the next stage
   */
  progressConnectionStage(connectionId: number, newStage: string): Observable<SoulConnection> {
    return this.updateSoulConnection(connectionId, { connection_stage: newStage as any });
  }

  /**
   * Give consent for mutual photo reveal
   */
  giveRevealConsent(connectionId: number): Observable<SoulConnection> {
    return this.updateSoulConnection(connectionId, { mutual_reveal_consent: true });
  }

  /**
   * Mark first dinner as completed
   */
  completeDinner(connectionId: number): Observable<SoulConnection> {
    return this.updateSoulConnection(connectionId, { first_dinner_completed: true });
  }

  /**
   * Refresh active connections (internal helper)
   */
  private refreshActiveConnections(): void {
    this.getActiveConnections().subscribe();
  }

  /**
   * Get compatibility explanation for a given score
   */
  getCompatibilityExplanation(compatibility: CompatibilityResponse): string {
    const score = compatibility.total_compatibility;
    
    if (score >= 80) {
      return `Exceptional soul connection! ${compatibility.explanation}`;
    } else if (score >= 70) {
      return `Strong compatibility potential. ${compatibility.explanation}`;
    } else if (score >= 60) {
      return `Good foundation for connection. ${compatibility.explanation}`;
    } else if (score >= 50) {
      return `Moderate compatibility. ${compatibility.explanation}`;
    } else {
      return `Worth exploring further. ${compatibility.explanation}`;
    }
  }

  /**
   * Get match quality color for UI display
   */
  getMatchQualityColor(score: number): string {
    if (score >= 80) return '#4ade80'; // green-400
    if (score >= 70) return '#60a5fa'; // blue-400
    if (score >= 60) return '#a78bfa'; // violet-400
    if (score >= 50) return '#fb7185'; // rose-400
    return '#94a3b8'; // slate-400
  }

  /**
   * Check if user needs emotional onboarding
   */
  needsEmotionalOnboarding(user: any): boolean {
    return !user?.emotional_onboarding_completed || 
           !user?.core_values || 
           !user?.interests?.length;
  }
}