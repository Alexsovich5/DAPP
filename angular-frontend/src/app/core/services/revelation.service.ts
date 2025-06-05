import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import {
  DailyRevelation,
  DailyRevelationCreate,
  DailyRevelationUpdate,
  RevelationTimelineResponse,
  RevelationPrompt,
  RevelationType,
  EmotionalOnboarding,
  OnboardingResponse
} from '../interfaces/revelation.interfaces';

@Injectable({
  providedIn: 'root'
})
export class RevelationService {
  private readonly apiUrl = environment.apiUrl;
  private currentTimelineSubject = new BehaviorSubject<RevelationTimelineResponse | null>(null);
  readonly currentTimeline$ = this.currentTimelineSubject.asObservable();

  constructor(private readonly http: HttpClient) {}

  /**
   * Get all revelation prompts for the 7-day cycle
   */
  getRevelationPrompts(): Observable<RevelationPrompt[]> {
    return this.http.get<RevelationPrompt[]>(`${this.apiUrl}/revelations/prompts`);
  }

  /**
   * Get revelation prompt for a specific day
   */
  getRevelationPrompt(dayNumber: number): Observable<RevelationPrompt> {
    return this.http.get<RevelationPrompt>(`${this.apiUrl}/revelations/prompts/${dayNumber}`);
  }

  /**
   * Create a new daily revelation
   */
  createRevelation(revelationData: DailyRevelationCreate): Observable<DailyRevelation> {
    return this.http.post<DailyRevelation>(`${this.apiUrl}/revelations/create`, revelationData)
      .pipe(
        tap(() => this.refreshTimeline(revelationData.connection_id))
      );
  }

  /**
   * Get revelation timeline for a soul connection
   */
  getRevelationTimeline(connectionId: number): Observable<RevelationTimelineResponse> {
    return this.http.get<RevelationTimelineResponse>(`${this.apiUrl}/revelations/timeline/${connectionId}`)
      .pipe(
        tap(timeline => this.currentTimelineSubject.next(timeline))
      );
  }

  /**
   * Update a revelation (mark as read, edit content)
   */
  updateRevelation(revelationId: number, updateData: DailyRevelationUpdate): Observable<DailyRevelation> {
    return this.http.put<DailyRevelation>(`${this.apiUrl}/revelations/${revelationId}`, updateData);
  }

  /**
   * Mark revelation as read
   */
  markAsRead(revelationId: number): Observable<DailyRevelation> {
    return this.updateRevelation(revelationId, { is_read: true });
  }

  /**
   * Complete emotional onboarding
   */
  completeEmotionalOnboarding(onboardingData: EmotionalOnboarding): Observable<OnboardingResponse> {
    return this.http.post<OnboardingResponse>(`${this.apiUrl}/onboarding/complete`, onboardingData);
  }

  /**
   * Get emotional onboarding status
   */
  getOnboardingStatus(): Observable<OnboardingResponse> {
    return this.http.get<OnboardingResponse>(`${this.apiUrl}/onboarding/status`);
  }

  /**
   * Refresh timeline for a connection (internal helper)
   */
  private refreshTimeline(connectionId: number): void {
    this.getRevelationTimeline(connectionId).subscribe();
  }

  /**
   * Get revelation type display name
   */
  getRevelationTypeDisplayName(type: RevelationType): string {
    const typeNames: Record<RevelationType, string> = {
      personal_value: 'Personal Value',
      meaningful_experience: 'Meaningful Experience',
      hope_or_dream: 'Hope or Dream',
      what_makes_laugh: 'What Makes You Laugh',
      challenge_overcome: 'Challenge Overcome',
      ideal_connection: 'Ideal Connection',
      photo_reveal: 'Photo Reveal'
    };
    return typeNames[type] || type;
  }

  /**
   * Get revelation type icon
   */
  getRevelationTypeIcon(type: RevelationType): string {
    const typeIcons: Record<RevelationType, string> = {
      personal_value: '💎',
      meaningful_experience: '🌟',
      hope_or_dream: '✨',
      what_makes_laugh: '😊',
      challenge_overcome: '💪',
      ideal_connection: '💝',
      photo_reveal: '📸'
    };
    return typeIcons[type] || '💭';
  }

  /**
   * Get progress percentage for revelation cycle
   */
  getProgressPercentage(timeline: RevelationTimelineResponse): number {
    if (timeline.is_cycle_complete) return 100;
    
    const totalDays = environment.soulBeforeSkin.revelationCycleDays;
    const currentDay = Math.min(timeline.current_day, totalDays);
    return Math.round((currentDay / totalDays) * 100);
  }

  /**
   * Check if user can share revelation for specific day
   */
  canShareRevelation(timeline: RevelationTimelineResponse, dayNumber: number, userId: number): boolean {
    // Can share if it's the current day or earlier, and user hasn't shared for this day yet
    if (dayNumber > timeline.current_day) return false;
    
    const existingRevelation = timeline.revelations.find(
      r => r.day_number === dayNumber && r.sender_id === userId
    );
    
    return !existingRevelation;
  }

  /**
   * Get next action for user in revelation cycle
   */
  getNextAction(timeline: RevelationTimelineResponse, userId: number): string {
    if (timeline.is_cycle_complete) {
      return 'Revelation cycle complete! Time for your first dinner.';
    }

    const currentDay = timeline.current_day;
    const userRevelationForToday = timeline.revelations.find(
      r => r.day_number === currentDay && r.sender_id === userId
    );

    if (!userRevelationForToday) {
      const prompt = this.getRevelationTypeDisplayName(timeline.next_revelation_type!);
      return `Share your Day ${currentDay} revelation: ${prompt}`;
    }

    const otherUserRevelation = timeline.revelations.find(
      r => r.day_number === currentDay && r.sender_id !== userId
    );

    if (!otherUserRevelation) {
      return `Waiting for your connection to share their Day ${currentDay} revelation.`;
    }

    if (currentDay < 7) {
      return `Both Day ${currentDay} revelations shared! Day ${currentDay + 1} begins tomorrow.`;
    }

    return 'All revelations shared! Ready for photo reveal and dinner planning.';
  }

  /**
   * Validate revelation content
   */
  validateRevelationContent(content: string): { valid: boolean; message?: string } {
    if (!content || content.trim().length === 0) {
      return { valid: false, message: 'Revelation content cannot be empty.' };
    }

    if (content.length < 10) {
      return { valid: false, message: 'Please share at least 10 characters to create a meaningful revelation.' };
    }

    if (content.length > 1000) {
      return { valid: false, message: 'Revelation content must be 1000 characters or less.' };
    }

    return { valid: true };
  }
}