import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  EmotionalDepthService,
  EmotionalDepthSummary
} from '../../../core/services/emotional-depth.service';

@Component({
  selector: 'app-emotional-depth-display',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatProgressBarModule,
    MatIconModule,
    MatChipsModule,
    MatButtonModule,
    MatTooltipModule
  ],
  template: `
    <mat-card class="emotional-depth-card" *ngIf="depthSummary">
      <!-- Header -->
      <mat-card-header class="depth-header">
        <div mat-card-avatar class="depth-avatar">
          <mat-icon [style.color]="getDepthLevelColor()">psychology</mat-icon>
        </div>
        <mat-card-title>Emotional Depth Profile</mat-card-title>
        <mat-card-subtitle>
          {{ depthSummary.emotional_depth_summary.depth_level_description }}
        </mat-card-subtitle>
      </mat-card-header>

      <mat-card-content class="depth-content">
        <!-- Overall Depth Score -->
        <div class="depth-score-section">
          <div class="score-container">
            <div class="score-circle" [style.border-color]="getDepthLevelColor()">
              <span class="score-value">{{ formatScore(depthSummary.emotional_depth_summary.overall_depth) }}</span>
              <span class="score-label">Depth</span>
            </div>
            <div class="depth-level-badge" [style.background-color]="getDepthLevelColor()">
              {{ depthSummary.emotional_depth_summary.depth_level | titlecase }}
            </div>
          </div>
        </div>

        <!-- Key Metrics -->
        <div class="metrics-grid" *ngIf="showDetailedMetrics">
          <div class="metric-item">
            <mat-icon [matTooltip]="getVocabularyTooltip()">record_voice_over</mat-icon>
            <span class="metric-label">Emotional Vocabulary</span>
            <span class="metric-value">{{ depthSummary.emotional_depth_summary.emotional_vocabulary_richness }}</span>
          </div>

          <div class="metric-item">
            <mat-icon [matTooltip]="getVulnerabilityTooltip()">favorite_border</mat-icon>
            <span class="metric-label">Vulnerability Comfort</span>
            <span class="metric-value">{{ getVulnerabilityLevel() }}</span>
          </div>

          <div class="metric-item">
            <mat-icon [matTooltip]="getAuthenticityTooltip()">verified</mat-icon>
            <span class="metric-label">Authenticity</span>
            <span class="metric-value">{{ getAuthenticityLevel() }}</span>
          </div>
        </div>

        <!-- Key Strengths -->
        <div class="strengths-section" *ngIf="hasStrengths()">
          <h4 class="section-title">
            <mat-icon>star</mat-icon>
            Key Strengths
          </h4>
          <div class="chips-container">
            <mat-chip-set>
              <mat-chip
                *ngFor="let strength of depthSummary.emotional_depth_summary.key_strengths"
                class="strength-chip">
                {{ strength }}
              </mat-chip>
            </mat-chip-set>
          </div>
        </div>

        <!-- Personal Insights -->
        <div class="insights-section" *ngIf="hasInsights()">
          <h4 class="section-title">
            <mat-icon>lightbulb</mat-icon>
            Personal Insights
          </h4>
          <ul class="insights-list">
            <li *ngFor="let insight of depthSummary.personal_insights" class="insight-item">
              {{ insight }}
            </li>
          </ul>
        </div>

        <!-- Growth Areas -->
        <div class="growth-section" *ngIf="hasGrowthAreas()">
          <h4 class="section-title">
            <mat-icon>trending_up</mat-icon>
            Growth Opportunities
          </h4>
          <ul class="growth-list">
            <li *ngFor="let area of depthSummary.emotional_depth_summary.growth_areas" class="growth-item">
              {{ area }}
            </li>
          </ul>
        </div>

        <!-- Recommendations -->
        <div class="recommendations-section" *ngIf="hasRecommendations()">
          <h4 class="section-title">
            <mat-icon>tips_and_updates</mat-icon>
            Recommendations
          </h4>
          <ul class="recommendations-list">
            <li *ngFor="let recommendation of depthSummary.recommendations" class="recommendation-item">
              {{ recommendation }}
            </li>
          </ul>
        </div>

        <!-- Profile Completeness -->
        <div class="completeness-section" *ngIf="showProfileCompleteness">
          <h4 class="section-title">
            <mat-icon>assignment_turned_in</mat-icon>
            Profile Analysis
          </h4>

          <div class="completeness-bar">
            <span class="completeness-label">Analysis Confidence</span>
            <mat-progress-bar
              mode="determinate"
              [value]="depthSummary.profile_completeness.confidence"
              [color]="getConfidenceColor()">
            </mat-progress-bar>
            <span class="completeness-value">{{ formatScore(depthSummary.profile_completeness.confidence) }}</span>
          </div>

          <div class="text-quality-indicator">
            <span class="quality-label">Response Quality:</span>
            <span class="quality-value" [class]="getQualityClass()">
              {{ depthSummary.profile_completeness.text_quality | titlecase }}
            </span>
          </div>

          <!-- Improvement Suggestions -->
          <div class="suggestions-section" *ngIf="hasSuggestions()">
            <h5 class="suggestions-title">Suggestions for Better Analysis:</h5>
            <ul class="suggestions-list">
              <li *ngFor="let suggestion of depthSummary.profile_completeness.suggestions" class="suggestion-item">
                {{ suggestion }}
              </li>
            </ul>
          </div>
        </div>
      </mat-card-content>

      <!-- Actions -->
      <mat-card-actions *ngIf="showActions" class="depth-actions">
        <button mat-button (click)="onRefreshAnalysis()" [disabled]="isLoading">
          <mat-icon>refresh</mat-icon>
          Refresh Analysis
        </button>
        <button mat-button (click)="onViewDetailedAnalysis()" *ngIf="allowDetailedView">
          <mat-icon>analytics</mat-icon>
          Detailed Analysis
        </button>
      </mat-card-actions>
    </mat-card>

    <!-- Loading State -->
    <mat-card *ngIf="isLoading && !depthSummary" class="loading-card">
      <mat-card-content class="loading-content">
        <mat-progress-bar mode="indeterminate"></mat-progress-bar>
        <p>Analyzing emotional depth...</p>
      </mat-card-content>
    </mat-card>

    <!-- No Data State -->
    <mat-card *ngIf="!depthSummary && !isLoading" class="no-data-card">
      <mat-card-content class="no-data-content">
        <mat-icon class="no-data-icon">psychology_alt</mat-icon>
        <h3>No Depth Analysis Available</h3>
        <p>Complete your profile responses to generate an emotional depth analysis.</p>
        <button mat-raised-button color="primary" (click)="onCompleteProfile()" *ngIf="showCompleteProfileAction">
          Complete Profile
        </button>
      </mat-card-content>
    </mat-card>
  `,
  styleUrls: ['./emotional-depth-display.component.scss']
})
export class EmotionalDepthDisplayComponent implements OnInit, OnDestroy {
  @Input() depthSummary: EmotionalDepthSummary | null = null;
  @Input() showDetailedMetrics: boolean = true;
  @Input() showProfileCompleteness: boolean = true;
  @Input() showActions: boolean = true;
  @Input() allowDetailedView: boolean = false;
  @Input() showCompleteProfileAction: boolean = true;
  @Input() isLoading: boolean = false;

  private destroy$ = new Subject<void>();

  constructor(private emotionalDepthService: EmotionalDepthService) {}

  ngOnInit(): void {
    // Subscribe to loading state if no external loading control
    if (!this.isLoading) {
      this.emotionalDepthService.analysisLoading$
        .pipe(takeUntil(this.destroy$))
        .subscribe(loading => this.isLoading = loading);
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Formatting and display methods
  getDepthLevelColor(): string {
    if (!this.depthSummary) return '#6b7280';
    return this.emotionalDepthService.getDepthLevelColor(
      this.depthSummary.emotional_depth_summary.depth_level
    );
  }

  formatScore(score: number): string {
    return this.emotionalDepthService.formatScore(score);
  }

  getVulnerabilityLevel(): string {
    if (!this.depthSummary) return 'Unknown';
    const comfort = this.depthSummary.emotional_depth_summary.vulnerability_comfort;

    if (comfort.includes('very comfortable')) return 'High';
    if (comfort.includes('moderately comfortable')) return 'Moderate';
    if (comfort.includes('developing')) return 'Developing';
    return 'Private';
  }

  getAuthenticityLevel(): string {
    if (!this.depthSummary) return 'Unknown';
    const authenticity = this.depthSummary.emotional_depth_summary.authenticity_level;

    if (authenticity.includes('highly authentic')) return 'High';
    if (authenticity.includes('generally authentic')) return 'Good';
    if (authenticity.includes('moderately authentic')) return 'Moderate';
    return 'Developing';
  }

  getConfidenceColor(): 'primary' | 'accent' | 'warn' {
    if (!this.depthSummary) return 'primary';
    const confidence = this.depthSummary.profile_completeness.confidence;

    if (confidence >= 80) return 'primary';
    if (confidence >= 60) return 'accent';
    return 'warn';
  }

  getQualityClass(): string {
    if (!this.depthSummary) return '';
    const quality = this.depthSummary.profile_completeness.text_quality;

    return `quality-${quality.toLowerCase()}`;
  }

  // Tooltip methods
  getVocabularyTooltip(): string {
    return 'Measures the diversity and sophistication of emotional words used in responses';
  }

  getVulnerabilityTooltip(): string {
    return 'Indicates comfort level with sharing personal and emotional experiences';
  }

  getAuthenticityTooltip(): string {
    return 'Measures how genuine and authentic the emotional expression appears';
  }

  // Conditional display methods
  hasStrengths(): boolean {
    return this.depthSummary?.emotional_depth_summary.key_strengths?.length > 0;
  }

  hasInsights(): boolean {
    return this.depthSummary?.personal_insights?.length > 0;
  }

  hasGrowthAreas(): boolean {
    return this.depthSummary?.emotional_depth_summary.growth_areas?.length > 0;
  }

  hasRecommendations(): boolean {
    return this.depthSummary?.recommendations?.length > 0;
  }

  hasSuggestions(): boolean {
    return this.depthSummary?.profile_completeness.suggestions?.length > 0;
  }

  // Action handlers
  onRefreshAnalysis(): void {
    this.emotionalDepthService.refreshCurrentUserDepth();
  }

  onViewDetailedAnalysis(): void {
    // Emit event or navigate to detailed analysis
    console.log('View detailed analysis requested');
  }

  onCompleteProfile(): void {
    // Emit event or navigate to profile completion
    console.log('Complete profile requested');
  }
}
