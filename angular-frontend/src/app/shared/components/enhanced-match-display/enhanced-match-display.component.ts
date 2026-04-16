import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';
import { Subject } from 'rxjs';

export interface EnhancedMatchQuality {
  user1_id: number;
  user2_id: number;
  comprehensive_analysis: {
    total_compatibility: number;
    match_quality_tier: string;
    connection_prediction: string;
    assessment_confidence: number;
    relationship_timeline: string;
  };
  component_scores: {
    soul_compatibility: {
      total_score: number;
      values_score: number;
      interests_score: number;
      personality_score: number;
      communication_score: number;
      emotional_resonance: number;
    };
    advanced_compatibility: {
      total_score: number;
      emotional_intelligence: number;
      temporal_compatibility: number;
      growth_potential: number;
      communication_rhythm: number;
    };
    emotional_depth: {
      compatibility_score: number;
      depth_harmony: number;
      vulnerability_match: number;
      growth_alignment: number;
    };
  };
  relationship_insights: {
    connection_strengths: string[];
    growth_opportunities: string[];
    potential_challenges: string[];
    recommended_approach: string;
  };
  interaction_guidance: {
    first_date_suggestion: string;
    conversation_starters: string[];
  };
  analysis_metadata: {
    algorithm_version: string;
    analysis_timestamp: string;
    assessment_confidence: number;
  };
}

@Component({
  selector: 'app-enhanced-match-display',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatProgressBarModule,
    MatIconModule,
    MatChipsModule,
    MatButtonModule,
    MatTooltipModule,
    MatTabsModule,
    MatExpansionModule
  ],
  template: `
    <mat-card class="enhanced-match-card" *ngIf="matchData">
      <!-- Header with Overall Score -->
      <mat-card-header class="match-header">
        <div mat-card-avatar class="match-avatar">
          <div class="compatibility-circle" [style.border-color]="getQualityColor()">
            <span class="compatibility-score">{{ formatScore(matchData.comprehensive_analysis.total_compatibility) }}</span>
          </div>
        </div>
        <mat-card-title class="match-title">
          {{ getTierDisplayName() }}
        </mat-card-title>
        <mat-card-subtitle class="match-subtitle">
          {{ getConnectionDescription() }}
        </mat-card-subtitle>
      </mat-card-header>

      <mat-card-content class="match-content">
        <!-- Quality Tier Badge -->
        <div class="quality-badge-container">
          <div class="quality-badge" [style.background-color]="getQualityColor()">
            <mat-icon>{{ getQualityIcon() }}</mat-icon>
            <span>{{ matchData.comprehensive_analysis.match_quality_tier | titlecase }} Quality</span>
          </div>
          <div class="confidence-indicator">
            <span class="confidence-label">Confidence: </span>
            <span class="confidence-value">{{ formatScore(matchData.comprehensive_analysis.assessment_confidence) }}</span>
          </div>
        </div>

        <!-- Main Analysis Tabs -->
        <mat-tab-group class="analysis-tabs" [selectedIndex]="selectedTabIndex" (selectedTabChange)="onTabChange($event)">

          <!-- Overview Tab -->
          <mat-tab label="Overview">
            <div class="tab-content overview-tab">

              <!-- Relationship Timeline -->
              <div class="timeline-section">
                <h4 class="section-title">
                  <mat-icon>schedule</mat-icon>
                  Relationship Timeline
                </h4>
                <p class="timeline-text">{{ matchData.comprehensive_analysis.relationship_timeline }}</p>
              </div>

              <!-- Key Strengths -->
              <div class="strengths-section" *ngIf="hasStrengths()">
                <h4 class="section-title">
                  <mat-icon>star</mat-icon>
                  Connection Strengths
                </h4>
                <div class="chips-container">
                  <mat-chip-set>
                    <mat-chip
                      *ngFor="let strength of matchData.relationship_insights.connection_strengths"
                      class="strength-chip">
                      {{ strength }}
                    </mat-chip>
                  </mat-chip-set>
                </div>
              </div>

              <!-- Growth Opportunities -->
              <div class="opportunities-section" *ngIf="hasOpportunities()">
                <h4 class="section-title">
                  <mat-icon>trending_up</mat-icon>
                  Growth Opportunities
                </h4>
                <ul class="opportunities-list">
                  <li *ngFor="let opportunity of matchData.relationship_insights.growth_opportunities" class="opportunity-item">
                    {{ opportunity }}
                  </li>
                </ul>
              </div>

              <!-- Recommended Approach -->
              <div class="approach-section">
                <h4 class="section-title">
                  <mat-icon>lightbulb</mat-icon>
                  Recommended Approach
                </h4>
                <p class="approach-text">{{ matchData.relationship_insights.recommended_approach }}</p>
              </div>

            </div>
          </mat-tab>

          <!-- Compatibility Breakdown Tab -->
          <mat-tab label="Compatibility Details">
            <div class="tab-content breakdown-tab">

              <!-- Component Scores -->
              <div class="components-grid">

                <!-- Soul Compatibility -->
                <mat-card class="component-card soul-card">
                  <mat-card-header>
                    <mat-icon mat-card-avatar class="soul-icon">favorite</mat-icon>
                    <mat-card-title>Soul Connection</mat-card-title>
                    <mat-card-subtitle>{{ formatScore(matchData.component_scores.soul_compatibility.total_score) }}</mat-card-subtitle>
                  </mat-card-header>
                  <mat-card-content>
                    <div class="score-breakdown">
                      <div class="score-item">
                        <span class="score-label">Values</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.soul_compatibility.values_score"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.soul_compatibility.values_score) }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">Interests</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.soul_compatibility.interests_score"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.soul_compatibility.interests_score) }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">Communication</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.soul_compatibility.communication_score"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.soul_compatibility.communication_score) }}</span>
                      </div>
                    </div>
                  </mat-card-content>
                </mat-card>

                <!-- Advanced Compatibility -->
                <mat-card class="component-card advanced-card">
                  <mat-card-header>
                    <mat-icon mat-card-avatar class="advanced-icon">psychology</mat-icon>
                    <mat-card-title>Advanced Analysis</mat-card-title>
                    <mat-card-subtitle>{{ formatScore(matchData.component_scores.advanced_compatibility.total_score) }}</mat-card-subtitle>
                  </mat-card-header>
                  <mat-card-content>
                    <div class="score-breakdown">
                      <div class="score-item">
                        <span class="score-label">Emotional IQ</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.advanced_compatibility.emotional_intelligence"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.advanced_compatibility.emotional_intelligence) }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">Growth Potential</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.advanced_compatibility.growth_potential"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.advanced_compatibility.growth_potential) }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">Temporal Sync</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.advanced_compatibility.temporal_compatibility"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.advanced_compatibility.temporal_compatibility) }}</span>
                      </div>
                    </div>
                  </mat-card-content>
                </mat-card>

                <!-- Emotional Depth -->
                <mat-card class="component-card depth-card">
                  <mat-card-header>
                    <mat-icon mat-card-avatar class="depth-icon">explore</mat-icon>
                    <mat-card-title>Emotional Depth</mat-card-title>
                    <mat-card-subtitle>{{ formatScore(matchData.component_scores.emotional_depth.compatibility_score) }}</mat-card-subtitle>
                  </mat-card-header>
                  <mat-card-content>
                    <div class="score-breakdown">
                      <div class="score-item">
                        <span class="score-label">Depth Harmony</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.emotional_depth.depth_harmony"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.emotional_depth.depth_harmony) }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">Vulnerability Match</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.emotional_depth.vulnerability_match"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.emotional_depth.vulnerability_match) }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">Growth Alignment</span>
                        <mat-progress-bar mode="determinate" [value]="matchData.component_scores.emotional_depth.growth_alignment"></mat-progress-bar>
                        <span class="score-value">{{ formatScore(matchData.component_scores.emotional_depth.growth_alignment) }}</span>
                      </div>
                    </div>
                  </mat-card-content>
                </mat-card>

              </div>
            </div>
          </mat-tab>

          <!-- Interaction Guidance Tab -->
          <mat-tab label="Interaction Guide">
            <div class="tab-content interaction-tab">

              <!-- First Date Suggestion -->
              <div class="date-suggestion-section">
                <h4 class="section-title">
                  <mat-icon>restaurant</mat-icon>
                  First Date Suggestion
                </h4>
                <div class="date-suggestion-card">
                  <p class="date-suggestion-text">{{ matchData.interaction_guidance.first_date_suggestion }}</p>
                </div>
              </div>

              <!-- Conversation Starters -->
              <div class="conversation-section" *ngIf="hasConversationStarters()">
                <h4 class="section-title">
                  <mat-icon>chat</mat-icon>
                  Conversation Starters
                </h4>
                <div class="conversation-starters">
                  <mat-expansion-panel
                    *ngFor="let starter of matchData.interaction_guidance.conversation_starters; let i = index"
                    class="starter-panel">
                    <mat-expansion-panel-header>
                      <mat-panel-title>
                        <mat-icon>question_answer</mat-icon>
                        Starter {{ i + 1 }}
                      </mat-panel-title>
                    </mat-expansion-panel-header>
                    <p class="starter-text">{{ starter }}</p>
                    <mat-action-row>
                      <button mat-button (click)="copyToClipboard(starter)">
                        <mat-icon>content_copy</mat-icon>
                        Copy
                      </button>
                    </mat-action-row>
                  </mat-expansion-panel>
                </div>
              </div>

              <!-- Potential Challenges -->
              <div class="challenges-section" *ngIf="hasChallenges()">
                <h4 class="section-title">
                  <mat-icon>warning_amber</mat-icon>
                  Areas to Navigate
                </h4>
                <ul class="challenges-list">
                  <li *ngFor="let challenge of matchData.relationship_insights.potential_challenges" class="challenge-item">
                    {{ challenge }}
                  </li>
                </ul>
              </div>

            </div>
          </mat-tab>

        </mat-tab-group>

      </mat-card-content>

      <!-- Actions -->
      <mat-card-actions *ngIf="showActions" class="match-actions">
        <button mat-button (click)="onRefreshAnalysis()" [disabled]="isLoading">
          <mat-icon>refresh</mat-icon>
          Refresh Analysis
        </button>
        <button mat-raised-button color="primary" (click)="onProceedWithConnection()" *ngIf="allowConnectionAction">
          <mat-icon>favorite</mat-icon>
          Connect
        </button>
      </mat-card-actions>

      <!-- Analysis Metadata -->
      <div class="metadata-section" *ngIf="showMetadata">
        <div class="metadata-content">
          <span class="metadata-item">
            <mat-icon>engineering</mat-icon>
            Algorithm: {{ matchData.analysis_metadata.algorithm_version }}
          </span>
          <span class="metadata-item">
            <mat-icon>schedule</mat-icon>
            Analyzed: {{ formatTimestamp(matchData.analysis_metadata.analysis_timestamp) }}
          </span>
        </div>
      </div>

    </mat-card>

    <!-- Loading State -->
    <mat-card *ngIf="isLoading && !matchData" class="loading-card">
      <mat-card-content class="loading-content">
        <mat-progress-bar mode="indeterminate" color="primary"></mat-progress-bar>
        <h3>Analyzing Match Quality</h3>
        <p>Running comprehensive compatibility assessment...</p>
      </mat-card-content>
    </mat-card>

    <!-- No Data State -->
    <mat-card *ngIf="!matchData && !isLoading" class="no-data-card">
      <mat-card-content class="no-data-content">
        <mat-icon class="no-data-icon">psychology_alt</mat-icon>
        <h3>No Match Analysis Available</h3>
        <p>Complete profiles are needed to generate a comprehensive match analysis.</p>
      </mat-card-content>
    </mat-card>
  `,
  styleUrls: ['./enhanced-match-display.component.scss']
})
export class EnhancedMatchDisplayComponent implements OnInit, OnDestroy {
  @Input() matchData: EnhancedMatchQuality | null = null;
  @Input() showActions: boolean = true;
  @Input() showMetadata: boolean = false;
  @Input() allowConnectionAction: boolean = true;
  @Input() isLoading: boolean = false;

  selectedTabIndex: number = 0;
  private destroy$ = new Subject<void>();

  constructor() {}

  ngOnInit(): void {
    // Component uses input properties for initialization
    if (this.matchData) {
      this.selectedTabIndex = 0;
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Display formatting methods
  formatScore(score: number): string {
    return `${Math.round(score)}%`;
  }

  formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleDateString();
  }

  getTierDisplayName(): string {
    if (!this.matchData) return '';
    const tier = this.matchData.comprehensive_analysis.match_quality_tier;
    return tier.replace('_', ' ').split(' ').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ') + ' Connection';
  }

  getConnectionDescription(): string {
    if (!this.matchData) return '';
    const prediction = this.matchData.comprehensive_analysis.connection_prediction;
    return this.formatConnectionPrediction(prediction);
  }

  getQualityColor(): string {
    if (!this.matchData) return '#6b7280';
    const score = this.matchData.comprehensive_analysis.total_compatibility;

    if (score >= 95) return '#10b981'; // Emerald-500
    if (score >= 90) return '#059669'; // Emerald-600
    if (score >= 80) return '#3b82f6'; // Blue-500
    if (score >= 70) return '#8b5cf6'; // Violet-500
    if (score >= 60) return '#f59e0b'; // Amber-500
    if (score >= 50) return '#f97316'; // Orange-500
    return '#ef4444';                  // Red-500
  }

  getQualityIcon(): string {
    if (!this.matchData) return 'help';
    const tier = this.matchData.comprehensive_analysis.match_quality_tier;

    const icons: { [key: string]: string } = {
      'transcendent': 'auto_awesome',
      'exceptional': 'stars',
      'high': 'star',
      'good': 'thumb_up',
      'moderate': 'sentiment_neutral',
      'exploratory': 'explore',
      'limited': 'warning',
      'incompatible': 'block'
    };

    return icons[tier] || 'help';
  }

  // Content availability checks
  hasStrengths(): boolean {
    return (this.matchData?.relationship_insights?.connection_strengths?.length ?? 0) > 0;
  }

  hasOpportunities(): boolean {
    return (this.matchData?.relationship_insights?.growth_opportunities?.length ?? 0) > 0;
  }

  hasChallenges(): boolean {
    return (this.matchData?.relationship_insights?.potential_challenges?.length ?? 0) > 0;
  }

  hasConversationStarters(): boolean {
    return (this.matchData?.interaction_guidance?.conversation_starters?.length ?? 0) > 0;
  }

  // Event handlers
  onTabChange(event: {index: number}): void {
    this.selectedTabIndex = event.index;
  }

  onRefreshAnalysis(): void {
    // Emit refresh event or call service
    console.log('Refresh analysis requested');
  }

  onProceedWithConnection(): void {
    // Emit connection event
    console.log('Proceed with connection requested');
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      console.log('Text copied to clipboard');
      // Could show a snackbar notification here
    }).catch(err => {
      console.error('Failed to copy text: ', err);
    });
  }

  // Helper methods
  private formatConnectionPrediction(prediction: string): string {
    const formatted = prediction.replace(/_/g, ' ').toLowerCase();
    return formatted.split(' ').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  }
}
