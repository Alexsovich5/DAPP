import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { ABTestingService, ABTestConfig } from '../../core/services/ab-testing.service';
import { ABAnalyticsService, ABTestMetrics } from '../../core/services/ab-analytics.service';

@Component({
  selector: 'app-ab-testing-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatTableModule,
    MatProgressBarModule,
    MatChipsModule,
    MatDialogModule
  ],
  template: `
    <div class="dashboard-container">
      <header class="dashboard-header">
        <h1>A/B Testing Dashboard</h1>
        <p>Monitor and analyze ongoing experiments for UX optimization</p>
      </header>

      <mat-tab-group class="dashboard-tabs">
        <!-- Active Tests Tab -->
        <mat-tab label="Active Tests">
          <div class="tab-content">
            <div class="tests-grid">
              <mat-card *ngFor="let test of activeTests" class="test-card">
                <mat-card-header>
                  <mat-card-title>{{ test.name }}</mat-card-title>
                  <mat-card-subtitle>{{ test.description }}</mat-card-subtitle>
                </mat-card-header>
                
                <mat-card-content>
                  <div class="test-status">
                    <mat-chip-set>
                      <mat-chip [color]="getStatusColor(test)" selected>
                        {{ test.isActive ? 'Active' : 'Inactive' }}
                      </mat-chip>
                      <mat-chip>{{ getTestDuration(test) }}</mat-chip>
                    </mat-chip-set>
                  </div>

                  <div class="variants-section">
                    <h4>Variants ({{ test.variants.length }})</h4>
                    <div class="variants-list">
                      <div *ngFor="let variant of test.variants" class="variant-item">
                        <span class="variant-name">{{ variant.name }}</span>
                        <span class="variant-allocation">{{ test.allocation[variant.id] || 0 }}%</span>
                        <mat-chip *ngIf="variant.isControl" color="accent" selected>Control</mat-chip>
                      </div>
                    </div>
                  </div>

                  <div class="metrics-preview">
                    <h4>Primary Metric: {{ test.primaryMetric }}</h4>
                    <div class="metric-value">
                      <span class="participants">{{ getParticipantCount(test.id) }} participants</span>
                    </div>
                  </div>
                </mat-card-content>

                <mat-card-actions>
                  <button mat-button (click)="viewAnalytics(test.id)">
                    <mat-icon>analytics</mat-icon>
                    View Analytics
                  </button>
                  <button mat-button (click)="exportData(test.id)">
                    <mat-icon>download</mat-icon>
                    Export
                  </button>
                  <button mat-button [color]="test.isActive ? 'warn' : 'primary'" 
                          (click)="toggleTest(test.id)">
                    <mat-icon>{{ test.isActive ? 'pause' : 'play_arrow' }}</mat-icon>
                    {{ test.isActive ? 'Pause' : 'Resume' }}
                  </button>
                </mat-card-actions>
              </mat-card>
            </div>
          </div>
        </mat-tab>

        <!-- Analytics Tab -->
        <mat-tab label="Analytics">
          <div class="tab-content">
            <div class="analytics-section" *ngFor="let analytics of testAnalytics">
              <mat-card class="analytics-card">
                <mat-card-header>
                  <mat-card-title>{{ analytics.testName }}</mat-card-title>
                  <mat-card-subtitle>
                    {{ analytics.totalParticipants }} participants • 
                    {{ analytics.statisticalSignificance }}% confidence
                  </mat-card-subtitle>
                </mat-card-header>

                <mat-card-content>
                  <!-- Primary Metric Results -->
                  <div class="primary-metric">
                    <h4>{{ analytics.primaryMetric.name }}</h4>
                    <div class="metric-results">
                      <div *ngFor="let variant of analytics.primaryMetric.variants" 
                           class="variant-result"
                           [class.winner]="variant.variantId === analytics.primaryMetric.winner">
                        <div class="variant-header">
                          <span class="variant-name">{{ getVariantName(analytics.testId, variant.variantId) }}</span>
                          <mat-chip *ngIf="variant.variantId === analytics.primaryMetric.winner" 
                                   color="primary" selected>
                            <mat-icon>emoji_events</mat-icon>
                            Winner
                          </mat-chip>
                        </div>
                        <div class="variant-metrics">
                          <div class="metric-value-large">{{ variant.value.toFixed(2) }}%</div>
                          <div class="metric-details">
                            <span>{{ variant.sampleSize }} samples</span>
                            <span>±{{ variant.standardError.toFixed(2) }}% SE</span>
                          </div>
                        </div>
                        <mat-progress-bar 
                          mode="determinate" 
                          [value]="variant.value"
                          [color]="variant.variantId === analytics.primaryMetric.winner ? 'primary' : 'accent'">
                        </mat-progress-bar>
                      </div>
                    </div>
                    
                    <div class="improvement-summary" *ngIf="analytics.primaryMetric.improvement">
                      <mat-icon>trending_up</mat-icon>
                      <span>{{ analytics.primaryMetric.improvement.toFixed(1) }}% improvement over control</span>
                    </div>
                  </div>

                  <!-- Secondary Metrics -->
                  <div class="secondary-metrics" *ngIf="analytics.secondaryMetrics.length > 0">
                    <h4>Secondary Metrics</h4>
                    <div class="secondary-metrics-grid">
                      <div *ngFor="let metric of analytics.secondaryMetrics" class="secondary-metric">
                        <h5>{{ metric.name }}</h5>
                        <div class="metric-variants">
                          <div *ngFor="let variant of metric.variants" class="variant-summary">
                            <span class="variant-name">{{ getVariantName(analytics.testId, variant.variantId) }}</span>
                            <span class="variant-value">{{ variant.value.toFixed(2) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Recommendation -->
                  <div class="recommendation">
                    <h4>Recommendation</h4>
                    <mat-chip-set>
                      <mat-chip [color]="getRecommendationColor(analytics.recommendedAction)" selected>
                        <mat-icon>{{ getRecommendationIcon(analytics.recommendedAction) }}</mat-icon>
                        {{ getRecommendationText(analytics.recommendedAction) }}
                      </mat-chip>
                    </mat-chip-set>
                    <p class="recommendation-details">
                      {{ getRecommendationDescription(analytics.recommendedAction, analytics.statisticalSignificance) }}
                    </p>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </div>
        </mat-tab>

        <!-- Test History Tab -->
        <mat-tab label="Test History">
          <div class="tab-content">
            <mat-card class="history-card">
              <mat-card-header>
                <mat-card-title>Test History</mat-card-title>
                <mat-card-subtitle>All completed and archived tests</mat-card-subtitle>
              </mat-card-header>
              <mat-card-content>
                <p class="coming-soon">Test history feature coming soon...</p>
              </mat-card-content>
            </mat-card>
          </div>
        </mat-tab>

        <!-- Settings Tab -->
        <mat-tab label="Settings">
          <div class="tab-content">
            <mat-card class="settings-card">
              <mat-card-header>
                <mat-card-title>A/B Testing Settings</mat-card-title>
                <mat-card-subtitle>Configure testing parameters and preferences</mat-card-subtitle>
              </mat-card-header>
              <mat-card-content>
                <div class="settings-section">
                  <h4>Debug Tools</h4>
                  <div class="debug-actions">
                    <button mat-stroked-button (click)="resetAllAssignments()">
                      <mat-icon>refresh</mat-icon>
                      Reset All Assignments
                    </button>
                    <button mat-stroked-button (click)="clearEventData()">
                      <mat-icon>clear_all</mat-icon>
                      Clear Event Data
                    </button>
                    <button mat-stroked-button (click)="downloadEventData()">
                      <mat-icon>download</mat-icon>
                      Download Raw Events
                    </button>
                  </div>
                </div>

                <div class="settings-section">
                  <h4>Force Assignment (Testing)</h4>
                  <div class="force-assignment">
                    <p>Force assign current user to specific variants for testing:</p>
                    <div class="assignment-controls" *ngFor="let test of activeTests">
                      <h5>{{ test.name }}</h5>
                      <div class="variant-buttons">
                        <button *ngFor="let variant of test.variants" 
                                mat-stroked-button
                                [color]="isCurrentVariant(test.id, variant.id) ? 'primary' : ''"
                                (click)="forceAssignment(test.id, variant.id)">
                          {{ variant.name }}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .dashboard-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem;
    }

    .dashboard-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .dashboard-header h1 {
      font-size: 2.5rem;
      font-weight: 300;
      color: #333;
      margin-bottom: 0.5rem;
    }

    .dashboard-header p {
      color: #666;
      font-size: 1.1rem;
    }

    .dashboard-tabs {
      min-height: 600px;
    }

    .tab-content {
      padding: 2rem 0;
    }

    /* Test Cards */
    .tests-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 2rem;
    }

    .test-card {
      min-height: 350px;
    }

    .test-status {
      margin-bottom: 1rem;
    }

    .variants-section {
      margin: 1rem 0;
    }

    .variants-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .variant-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.5rem;
      background: #f5f5f5;
      border-radius: 4px;
    }

    .variant-name {
      flex: 1;
      font-weight: 500;
    }

    .variant-allocation {
      font-weight: bold;
      color: #666;
    }

    .metrics-preview {
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid #eee;
    }

    .participants {
      color: #666;
      font-size: 0.9rem;
    }

    /* Analytics */
    .analytics-card {
      margin-bottom: 2rem;
    }

    .primary-metric h4 {
      color: #333;
      margin-bottom: 1rem;
    }

    .metric-results {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .variant-result {
      padding: 1rem;
      border: 2px solid #eee;
      border-radius: 8px;
      transition: all 0.3s ease;
    }

    .variant-result.winner {
      border-color: #3f51b5;
      background: #f3f4ff;
    }

    .variant-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }

    .variant-name {
      font-weight: 500;
    }

    .metric-value-large {
      font-size: 2rem;
      font-weight: bold;
      color: #333;
      margin-bottom: 0.5rem;
    }

    .metric-details {
      display: flex;
      gap: 1rem;
      font-size: 0.9rem;
      color: #666;
      margin-bottom: 1rem;
    }

    .improvement-summary {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #4caf50;
      font-weight: 500;
      margin-top: 1rem;
    }

    .secondary-metrics {
      margin-top: 2rem;
      padding-top: 2rem;
      border-top: 1px solid #eee;
    }

    .secondary-metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1rem;
    }

    .secondary-metric {
      padding: 1rem;
      background: #f9f9f9;
      border-radius: 8px;
    }

    .secondary-metric h5 {
      margin-bottom: 0.5rem;
      color: #333;
    }

    .metric-variants {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .variant-summary {
      display: flex;
      justify-content: space-between;
      font-size: 0.9rem;
    }

    .recommendation {
      margin-top: 2rem;
      padding-top: 2rem;
      border-top: 1px solid #eee;
    }

    .recommendation-details {
      margin-top: 0.5rem;
      color: #666;
    }

    /* Settings */
    .settings-section {
      margin-bottom: 2rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid #eee;
    }

    .settings-section:last-child {
      border-bottom: none;
    }

    .debug-actions, .variant-buttons {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .assignment-controls {
      margin-bottom: 1rem;
    }

    .assignment-controls h5 {
      margin-bottom: 0.5rem;
      color: #333;
    }

    .coming-soon {
      text-align: center;
      color: #666;
      font-style: italic;
      padding: 2rem;
    }

    .history-card {
      min-height: 200px;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .dashboard-container {
        padding: 1rem;
      }

      .tests-grid {
        grid-template-columns: 1fr;
      }

      .metric-results {
        grid-template-columns: 1fr;
      }

      .secondary-metrics-grid {
        grid-template-columns: 1fr;
      }

      .debug-actions, .variant-buttons {
        flex-direction: column;
        align-items: stretch;
      }
    }
  `]
})
export class ABTestingDashboardComponent implements OnInit {
  activeTests: ABTestConfig[] = [];
  testAnalytics: ABTestMetrics[] = [];

  constructor(
    private abTestingService: ABTestingService,
    private abAnalyticsService: ABAnalyticsService
  ) {}

  ngOnInit(): void {
    this.loadActiveTests();
    this.loadAnalytics();
  }

  loadActiveTests(): void {
    this.activeTests = this.abTestingService.getActiveTests();
  }

  loadAnalytics(): void {
    this.testAnalytics = this.abAnalyticsService.getAllTestAnalytics();
  }

  getStatusColor(test: ABTestConfig): string {
    return test.isActive ? 'primary' : 'warn';
  }

  getTestDuration(test: ABTestConfig): string {
    const now = new Date();
    const start = test.startDate;
    const diffTime = Math.abs(now.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return `${diffDays} days`;
  }

  getParticipantCount(testId: string): number {
    const analytics = this.testAnalytics.find(a => a.testId === testId);
    return analytics?.totalParticipants || 0;
  }

  getVariantName(testId: string, variantId: string): string {
    const test = this.activeTests.find(t => t.id === testId);
    const variant = test?.variants.find(v => v.id === variantId);
    return variant?.name || variantId;
  }

  getRecommendationColor(action: string): string {
    switch (action) {
      case 'conclude_winner': return 'primary';
      case 'conclude_no_winner': return 'accent';
      case 'extend_test': return 'warn';
      default: return '';
    }
  }

  getRecommendationIcon(action: string): string {
    switch (action) {
      case 'conclude_winner': return 'emoji_events';
      case 'conclude_no_winner': return 'balance';
      case 'extend_test': return 'schedule';
      default: return 'play_arrow';
    }
  }

  getRecommendationText(action: string): string {
    switch (action) {
      case 'conclude_winner': return 'Conclude with Winner';
      case 'conclude_no_winner': return 'No Clear Winner';
      case 'extend_test': return 'Extend Test Duration';
      default: return 'Continue Testing';
    }
  }

  getRecommendationDescription(action: string, significance: number): string {
    switch (action) {
      case 'conclude_winner':
        return `Statistical significance is high (${significance}%) and there's a clear winning variant. Consider implementing the winner.`;
      case 'conclude_no_winner':
        return `No variant shows significant improvement over the control. Consider implementing the control or designing new variants.`;
      case 'extend_test':
        return `Statistical significance is low (${significance}%). Continue testing to gather more data for reliable results.`;
      default:
        return `Test is progressing normally. Continue collecting data to reach statistical significance.`;
    }
  }

  viewAnalytics(testId: string): void {
    // Navigate to detailed analytics view
    console.log('View analytics for test:', testId);
  }

  exportData(testId: string): void {
    const csvData = this.abAnalyticsService.exportTestData(testId);
    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ab-test-${testId}-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  toggleTest(testId: string): void {
    // Implementation would toggle test active status
    console.log('Toggle test:', testId);
  }

  resetAllAssignments(): void {
    this.abTestingService.resetAssignments();
    alert('All A/B test assignments have been reset. Refresh the page to see new assignments.');
  }

  clearEventData(): void {
    localStorage.removeItem('ab_test_events');
    alert('All A/B test event data has been cleared.');
    this.loadAnalytics();
  }

  downloadEventData(): void {
    const events = localStorage.getItem('ab_test_events');
    if (!events) {
      alert('No event data available.');
      return;
    }

    const blob = new Blob([events], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ab-test-events-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  forceAssignment(testId: string, variantId: string): void {
    const success = this.abTestingService.forceAssignment(testId, variantId);
    if (success) {
      alert(`Assigned to variant: ${variantId}. Refresh affected pages to see changes.`);
    } else {
      alert('Failed to assign variant. Please check the test configuration.');
    }
  }

  isCurrentVariant(testId: string, variantId: string): boolean {
    return this.abTestingService.isInVariant(testId, variantId);
  }
}