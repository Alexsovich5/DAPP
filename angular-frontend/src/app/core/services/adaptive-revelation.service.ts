import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, of, interval } from 'rxjs';
import { map, catchError, switchMap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface AdaptiveRevelationPrompt {
  id?: number;
  text: string;
  theme: string;
  focus: string;
  emotional_depth: string;
  confidence: number;
  metadata?: any;
  timing_recommendation?: any;
  follow_up_suggestions?: string[];
}

export interface RevelationTheme {
  name: string;
  description: string;
  communication_style: string;
  requires_high_compatibility: boolean;
  emotional_intensity: number;
  sample_templates: string[];
}

export interface RevelationProgress {
  connection_id: number;
  current_revelation_day: number;
  user_progress: {
    completed_days: number[];
    total_completed: number;
    next_day?: number;
  };
  partner_progress: {
    completed_days: number[];
    total_completed: number;
    next_day?: number;
  };
  mutual_completion: {
    completed_together: number[];
    waiting_for_partner: number[];
    waiting_for_user: number[];
  };
  can_proceed_to_photo_reveal: boolean;
  days_until_photo_reveal: number;
}

export interface RevelationAnalytics {
  connection_id: number;
  completed_revelation_days: number;
  total_revelations_shared: number;
  average_words_per_revelation: number;
  theme_distribution: { [key: string]: number };
  engagement_trend: string;
  most_successful_themes: string[];
  overall_depth_score: number;
  personalization_effectiveness: number;
  next_recommended_theme?: string;
}

export interface TimingRecommendation {
  connection_id: number;
  recommended_hours: number[];
  optimal_day_time: string;
  reasoning: string;
  urgency: string;
  next_optimal_time?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AdaptiveRevelationService {
  private readonly apiUrl = `${environment.apiUrl}/adaptive-revelations`;
  
  // Real-time state management
  private currentPromptsSubject = new BehaviorSubject<AdaptiveRevelationPrompt[]>([]);
  private revelationProgressSubject = new BehaviorSubject<RevelationProgress | null>(null);
  private analyticsSubject = new BehaviorSubject<RevelationAnalytics | null>(null);

  // Public observables
  currentPrompts$ = this.currentPromptsSubject.asObservable();
  revelationProgress$ = this.revelationProgressSubject.asObservable();
  analytics$ = this.analyticsSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Generate adaptive revelation prompts for a connection
   */
  generateAdaptivePrompts(
    connectionId: number, 
    revelationDay: number, 
    count: number = 3
  ): Observable<AdaptiveRevelationPrompt[]> {
    const request = {
      connection_id: connectionId,
      revelation_day: revelationDay,
      count: count
    };

    return this.http.post<AdaptiveRevelationPrompt[]>(`${this.apiUrl}/generate`, request).pipe(
      map(prompts => {
        this.currentPromptsSubject.next(prompts);
        return prompts;
      }),
      catchError(this.handleError<AdaptiveRevelationPrompt[]>('generateAdaptivePrompts', []))
    );
  }

  /**
   * Get available revelation themes for a specific day
   */
  getRevelationThemes(revelationDay: number): Observable<RevelationTheme[]> {
    return this.http.get<RevelationTheme[]>(`${this.apiUrl}/themes/${revelationDay}`).pipe(
      catchError(this.handleError<RevelationTheme[]>('getRevelationThemes', []))
    );
  }

  /**
   * Get timing recommendations for revelations
   */
  getTimingRecommendations(connectionId: number): Observable<TimingRecommendation> {
    return this.http.get<TimingRecommendation>(`${this.apiUrl}/timing-recommendations/${connectionId}`).pipe(
      catchError(this.handleError<TimingRecommendation>('getTimingRecommendations'))
    );
  }

  /**
   * Submit feedback on revelation prompts
   */
  submitRevelationFeedback(feedback: {
    revelation_id: number;
    content_id: number;
    helpful_score: number;
    engagement_score: number;
    emotional_resonance: number;
    timing_appropriateness: number;
    comments?: string;
  }): Observable<any> {
    return this.http.post(`${this.apiUrl}/feedback`, feedback).pipe(
      catchError(this.handleError('submitRevelationFeedback'))
    );
  }

  /**
   * Get revelation analytics for a connection
   */
  getRevelationAnalytics(connectionId: number): Observable<RevelationAnalytics> {
    return this.http.get<RevelationAnalytics>(`${this.apiUrl}/analytics/${connectionId}`).pipe(
      map(analytics => {
        this.analyticsSubject.next(analytics);
        return analytics;
      }),
      catchError(this.handleError<RevelationAnalytics>('getRevelationAnalytics'))
    );
  }

  /**
   * Get revelation progress for a connection
   */
  getRevelationProgress(connectionId: number): Observable<RevelationProgress> {
    return this.http.get<RevelationProgress>(`${this.apiUrl}/progress/${connectionId}`).pipe(
      map(progress => {
        this.revelationProgressSubject.next(progress);
        return progress;
      }),
      catchError(this.handleError<RevelationProgress>('getRevelationProgress'))
    );
  }

  /**
   * Get the current revelation day for a connection
   */
  getCurrentRevelationDay(connectionId: number): Observable<number> {
    return this.getRevelationProgress(connectionId).pipe(
      map(progress => progress.current_revelation_day)
    );
  }

  /**
   * Check if both users have completed a specific revelation day
   */
  isMutuallyCompleted(connectionId: number, day: number): Observable<boolean> {
    return this.getRevelationProgress(connectionId).pipe(
      map(progress => progress.mutual_completion.completed_together.includes(day))
    );
  }

  /**
   * Get next recommended revelation day for user
   */
  getNextRevelationDay(connectionId: number): Observable<number | null> {
    return this.getRevelationProgress(connectionId).pipe(
      map(progress => progress.user_progress.next_day || null)
    );
  }

  /**
   * Check if user is ready for photo reveal
   */
  canProceedToPhotoReveal(connectionId: number): Observable<boolean> {
    return this.getRevelationProgress(connectionId).pipe(
      map(progress => progress.can_proceed_to_photo_reveal)
    );
  }

  /**
   * Get personalized insights for revelation improvement
   */
  getPersonalizedInsights(connectionId: number): Observable<any> {
    // This would call a more advanced analytics endpoint
    return this.getRevelationAnalytics(connectionId).pipe(
      map(analytics => this.generateInsights(analytics))
    );
  }

  /**
   * Generate insights from analytics data
   */
  private generateInsights(analytics: RevelationAnalytics): any {
    const insights = [];

    // Engagement trend insights
    if (analytics.engagement_trend === 'increasing') {
      insights.push({
        type: 'positive',
        title: 'Great Progress!',
        message: 'Your revelations are becoming more engaging over time.',
        suggestion: 'Keep exploring deeper themes to maintain this momentum.'
      });
    } else if (analytics.engagement_trend === 'decreasing') {
      insights.push({
        type: 'improvement',
        title: 'Consider Mixing Things Up',
        message: 'Try exploring different themes to reignite the connection.',
        suggestion: `Consider trying: ${analytics.most_successful_themes.join(', ')}`
      });
    }

    // Personalization effectiveness insights
    if (analytics.personalization_effectiveness > 0.8) {
      insights.push({
        type: 'positive',
        title: 'Perfect Personalization',
        message: 'The AI is learning your style well and generating great prompts.',
        suggestion: 'Continue providing feedback to maintain this quality.'
      });
    } else if (analytics.personalization_effectiveness < 0.6) {
      insights.push({
        type: 'improvement',
        title: 'Help Us Learn',
        message: 'More feedback will help us personalize better for you.',
        suggestion: 'Rate the next few prompts to improve future suggestions.'
      });
    }

    // Progress insights
    if (analytics.completed_revelation_days >= 5) {
      insights.push({
        type: 'milestone',
        title: 'Almost There!',
        message: 'You\'re close to completing the revelation journey.',
        suggestion: 'Prepare for your potential photo reveal and first meeting!'
      });
    }

    return insights;
  }

  /**
   * Get optimal revelation timing for user
   */
  getOptimalTiming(connectionId: number): Observable<string> {
    return this.getTimingRecommendations(connectionId).pipe(
      map(timing => {
        const currentHour = new Date().getHours();
        const isOptimalTime = timing.recommended_hours.includes(currentHour);
        
        if (isOptimalTime) {
          return 'Now is a great time to share your revelation!';
        } else {
          const nextOptimal = timing.recommended_hours.find(hour => hour > currentHour) 
                           || timing.recommended_hours[0];
          return `Consider sharing around ${nextOptimal}:00 ${timing.optimal_day_time}`;
        }
      })
    );
  }

  /**
   * Track revelation engagement metrics
   */
  trackEngagement(revelationId: number, metrics: {
    time_to_start?: number;
    completion_time?: number;
    word_count?: number;
    engagement_indicators?: any;
  }): void {
    // This would be sent to analytics service
    console.log('Tracking revelation engagement:', { revelationId, metrics });
  }

  /**
   * Prefetch prompts for next revelation day
   */
  prefetchNextDayPrompts(connectionId: number): Observable<AdaptiveRevelationPrompt[]> {
    return this.getNextRevelationDay(connectionId).pipe(
      switchMap(nextDay => {
        if (nextDay) {
          return this.generateAdaptivePrompts(connectionId, nextDay, 3);
        } else {
          return of([]);
        }
      })
    );
  }

  /**
   * Get real-time revelation updates
   */
  subscribeToRevelationUpdates(connectionId: number): Observable<any> {
    // This would connect to WebSocket for real-time updates
    // For now, polling the progress endpoint
    return interval(30000).pipe(
      switchMap(() => this.getRevelationProgress(connectionId))
    );
  }

  /**
   * Clear current state
   */
  clearState(): void {
    this.currentPromptsSubject.next([]);
    this.revelationProgressSubject.next(null);
    this.analyticsSubject.next(null);
  }

  /**
   * Error handler
   */
  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      console.error(`${operation} failed:`, error);
      
      // You could show user-friendly error messages here
      // this.snackBar.open(`Failed to ${operation}. Please try again.`, 'Close');
      
      return of(result as T);
    };
  }
}

