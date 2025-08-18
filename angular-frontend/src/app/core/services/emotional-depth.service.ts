import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface EmotionalDepthMetrics {
  overall_depth: number;
  depth_level: string;
  emotional_vocabulary_count: number;
  vulnerability_score: number;
  authenticity_score: number;
  empathy_indicators: number;
  growth_mindset: number;
  emotional_availability: number;
  attachment_security: number;
  communication_depth: number;
  confidence: number;
  text_quality: string;
  response_richness: number;
}

export interface DepthInsights {
  vulnerability_types: string[];
  depth_indicators: string[];
  maturity_signals: string[];
  authenticity_markers: string[];
}

export interface EmotionalDepthAnalysis {
  user_id: number;
  emotional_depth: EmotionalDepthMetrics;
  insights: DepthInsights;
  analysis_metadata: {
    timestamp: string;
    algorithm_version: string;
    confidence_level: number;
  };
}

export interface DepthCompatibility {
  user1_id: number;
  user2_id: number;
  depth_compatibility: {
    overall_compatibility: number;
    depth_harmony: number;
    vulnerability_match: number;
    growth_alignment: number;
  };
  individual_depths: {
    user1: Partial<EmotionalDepthMetrics>;
    user2: Partial<EmotionalDepthMetrics>;
  };
  relationship_insights: {
    connection_potential: string;
    recommended_approach: string;
    depth_growth_timeline: string;
  };
  analysis_metadata: {
    timestamp: string;
    algorithm_version: string;
  };
}

export interface EmotionalDepthSummary {
  emotional_depth_summary: {
    overall_depth: number;
    depth_level: string;
    depth_level_description: string;
    key_strengths: string[];
    growth_areas: string[];
    emotional_vocabulary_richness: string;
    vulnerability_comfort: string;
    authenticity_level: string;
  };
  personal_insights: string[];
  recommendations: string[];
  profile_completeness: {
    confidence: number;
    text_quality: string;
    suggestions: string[];
  };
}

@Injectable({
  providedIn: 'root'
})
export class EmotionalDepthService {
  private readonly baseUrl = `${environment.apiUrl}/emotional-depth`;
  
  // State management
  private currentUserDepthSubject = new BehaviorSubject<EmotionalDepthSummary | null>(null);
  public currentUserDepth$ = this.currentUserDepthSubject.asObservable();

  private analysisLoadingSubject = new BehaviorSubject<boolean>(false);
  public analysisLoading$ = this.analysisLoadingSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Analyze emotional depth for a specific user
   */
  analyzeUserEmotionalDepth(userId: number): Observable<EmotionalDepthAnalysis> {
    this.analysisLoadingSubject.next(true);
    
    return this.http.get<EmotionalDepthAnalysis>(`${this.baseUrl}/analyze/${userId}`)
      .pipe(
        tap(() => this.analysisLoadingSubject.next(false)),
        catchError((error) => {
          this.analysisLoadingSubject.next(false);
          throw error;
        })
      );
  }

  /**
   * Analyze emotional depth compatibility between two users
   */
  analyzeDepthCompatibility(user1Id: number, user2Id: number): Observable<DepthCompatibility> {
    this.analysisLoadingSubject.next(true);
    
    return this.http.get<DepthCompatibility>(`${this.baseUrl}/compatibility/${user1Id}/${user2Id}`)
      .pipe(
        tap(() => this.analysisLoadingSubject.next(false)),
        catchError((error) => {
          this.analysisLoadingSubject.next(false);
          throw error;
        })
      );
  }

  /**
   * Get current user's emotional depth summary
   */
  getMyEmotionalDepthSummary(): Observable<EmotionalDepthSummary> {
    this.analysisLoadingSubject.next(true);
    
    return this.http.get<EmotionalDepthSummary>(`${this.baseUrl}/summary/me`)
      .pipe(
        tap((summary) => {
          this.currentUserDepthSubject.next(summary);
          this.analysisLoadingSubject.next(false);
        }),
        catchError((error) => {
          this.analysisLoadingSubject.next(false);
          throw error;
        })
      );
  }

  /**
   * Get depth level color for UI display
   */
  getDepthLevelColor(depthLevel: string): string {
    const colors: { [key: string]: string } = {
      'surface': '#94a3b8',      // Slate-400
      'emerging': '#60a5fa',     // Blue-400
      'moderate': '#34d399',     // Emerald-400
      'deep': '#a78bfa',         // Violet-400
      'profound': '#f59e0b'      // Amber-500
    };
    
    return colors[depthLevel.toLowerCase()] || colors['moderate'];
  }

  /**
   * Get depth level description for display
   */
  getDepthLevelDescription(depthLevel: string): string {
    const descriptions: { [key: string]: string } = {
      'surface': 'Developing emotional awareness',
      'emerging': 'Growing emotional intelligence',
      'moderate': 'Good emotional depth',
      'deep': 'High emotional sophistication',
      'profound': 'Exceptional emotional wisdom'
    };
    
    return descriptions[depthLevel.toLowerCase()] || descriptions['moderate'];
  }

  /**
   * Get compatibility level description
   */
  getCompatibilityDescription(score: number): string {
    if (score >= 90) return 'Exceptional emotional compatibility';
    if (score >= 80) return 'Strong emotional connection potential';
    if (score >= 70) return 'Good emotional compatibility';
    if (score >= 60) return 'Moderate emotional alignment';
    return 'Limited emotional compatibility';
  }

  /**
   * Get compatibility color for UI
   */
  getCompatibilityColor(score: number): string {
    if (score >= 90) return '#10b981';  // Emerald-500
    if (score >= 80) return '#3b82f6';  // Blue-500
    if (score >= 70) return '#8b5cf6';  // Violet-500
    if (score >= 60) return '#f59e0b';  // Amber-500
    return '#ef4444';                   // Red-500
  }

  /**
   * Format score for display (with percentage)
   */
  formatScore(score: number): string {
    return `${Math.round(score)}%`;
  }

  /**
   * Get vocabulary richness icon
   */
  getVocabularyIcon(richness: string): string {
    const icons: { [key: string]: string } = {
      'limited': 'sentiment_dissatisfied',
      'developing': 'sentiment_neutral',
      'well-developed': 'sentiment_satisfied',
      'rich and sophisticated': 'sentiment_very_satisfied'
    };
    
    return icons[richness.toLowerCase()] || 'sentiment_neutral';
  }

  /**
   * Get vulnerability comfort icon
   */
  getVulnerabilityIcon(comfort: string): string {
    if (comfort.includes('very comfortable')) return 'favorite';
    if (comfort.includes('moderately comfortable')) return 'thumb_up';
    if (comfort.includes('developing')) return 'hourglass_empty';
    return 'lock';
  }

  /**
   * Refresh current user's depth data
   */
  refreshCurrentUserDepth(): void {
    this.getMyEmotionalDepthSummary().subscribe({
      next: (summary) => {
        console.log('Emotional depth summary refreshed:', summary);
      },
      error: (error) => {
        console.error('Error refreshing emotional depth:', error);
      }
    });
  }

  /**
   * Clear current user depth data
   */
  clearCurrentUserDepth(): void {
    this.currentUserDepthSubject.next(null);
  }

  /**
   * Check if user has sufficient depth data for analysis
   */
  hasSufficientDepthData(summary: EmotionalDepthSummary): boolean {
    return summary.profile_completeness.confidence >= 50 && 
           summary.profile_completeness.text_quality !== 'insufficient';
  }

  /**
   * Get recommendations for improving depth analysis
   */
  getImprovementRecommendations(summary: EmotionalDepthSummary): string[] {
    const recommendations: string[] = [];
    
    if (summary.profile_completeness.confidence < 60) {
      recommendations.push('Complete more detailed profile responses to improve analysis accuracy');
    }
    
    if (summary.profile_completeness.text_quality === 'limited') {
      recommendations.push('Share more personal experiences and feelings in your responses');
    }
    
    if (summary.emotional_depth_summary.emotional_vocabulary_richness === 'limited') {
      recommendations.push('Explore and use more diverse emotional words to express your feelings');
    }
    
    return recommendations.concat(summary.recommendations);
  }
}