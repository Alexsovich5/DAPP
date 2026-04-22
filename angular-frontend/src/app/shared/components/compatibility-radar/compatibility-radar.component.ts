import { Component, Input, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { Subscription } from 'rxjs';
import { CompatibilityBreakdown, CompatibilityResponse } from '../../../core/interfaces/soul-connection.interfaces';
import { SoulConnectionService } from '../../../core/services/soul-connection.service';

@Component({
  selector: 'app-compatibility-radar',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="compatibility-radar-container" [ngClass]="size">
      <div class="radar-header" *ngIf="showHeader">
        <h3 class="radar-title">Soul Compatibility Analysis</h3>
        <div class="overall-score" *ngIf="isDataAvailable">
          <span class="score-value">{{overallScore}}%</span>
          <span class="score-label">Overall Match</span>
        </div>
        <div class="loading-state" *ngIf="!isDataAvailable">
          <span class="loading-message">{{loadingMessage}}</span>
          <button
            *ngIf="hasError"
            class="retry-button"
            (click)="refreshData()"
            aria-label="Retry loading compatibility data">
            Retry
          </button>
        </div>
      </div>

      <div class="radar-chart-wrapper">
        <svg #radarSvg class="radar-chart" [attr.width]="svgSize" [attr.height]="svgSize" [attr.viewBox]="'0 0 ' + svgSize + ' ' + svgSize">
          <defs>
            <!-- Gradients for different compatibility areas -->
            <radialGradient id="compatibility-gradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stop-color="#ffd700" stop-opacity="0.3"/>
              <stop offset="50%" stop-color="#ff6b9d" stop-opacity="0.2"/>
              <stop offset="100%" stop-color="#c084fc" stop-opacity="0.1"/>
            </radialGradient>

            <!-- Glow filter -->
            <filter id="radar-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          <!-- Background grid circles -->
          <g class="radar-grid">
            <circle
              *ngFor="let ring of gridRings; let i = index"
              [attr.cx]="center.x"
              [attr.cy]="center.y"
              [attr.r]="ring.radius"
              fill="none"
              [attr.stroke]="gridColor"
              [attr.stroke-width]="ring.width"
              stroke-opacity="0.3">
            </circle>
          </g>

          <!-- Axis lines -->
          <g class="radar-axes">
            <line
              *ngFor="let axis of axes"
              [attr.x1]="center.x"
              [attr.y1]="center.y"
              [attr.x2]="axis.x"
              [attr.y2]="axis.y"
              [attr.stroke]="gridColor"
              stroke-width="1"
              stroke-opacity="0.4">
            </line>
          </g>

          <!-- Compatibility area -->
          <g class="compatibility-area">
            <path
              [attr.d]="compatibilityPath"
              fill="url(#compatibility-gradient)"
              [attr.stroke]="areaStroke"
              stroke-width="2"
              filter="url(#radar-glow)"
              class="compatibility-shape"
              [class.animated]="animateChart">
            </path>
          </g>

          <!-- Data points -->
          <g class="radar-points">
            <circle
              *ngFor="let point of dataPoints; trackBy: trackPoint"
              [attr.cx]="point.x"
              [attr.cy]="point.y"
              [attr.r]="pointRadius"
              [attr.fill]="point.color"
              [attr.stroke]="point.strokeColor"
              stroke-width="2"
              class="data-point"
              [class.pulsing]="point.highlight"
              (click)="onPointClick(point)"
              [style.cursor]="interactive ? 'pointer' : 'default'">
            </circle>
          </g>

          <!-- Labels -->
          <g class="radar-labels">
            <g *ngFor="let label of axisLabels; trackBy: trackLabel" class="label-group">
              <circle
                [attr.cx]="label.x"
                [attr.cy]="label.y"
                [attr.r]="labelBackgroundRadius"
                [attr.fill]="labelBackgroundColor"
                fill-opacity="0.9">
              </circle>
              <text
                [attr.x]="label.x"
                [attr.y]="label.y + 4"
                text-anchor="middle"
                [attr.font-size]="labelFontSize"
                [attr.fill]="labelColor"
                font-weight="500">
                {{label.text}}
              </text>
            </g>
          </g>
        </svg>

        <!-- Hover tooltip -->
        <div
          class="tooltip"
          *ngIf="hoveredPoint"
          [style.left.px]="tooltip.x"
          [style.top.px]="tooltip.y">
          <div class="tooltip-content">
            <div class="tooltip-title">{{hoveredPoint.category}}</div>
            <div class="tooltip-score">{{hoveredPoint.score}}% compatibility</div>
            <div class="tooltip-description">{{hoveredPoint.description}}</div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="compatibility-legend" *ngIf="showLegend">
        <button
          type="button"
          *ngFor="let item of legendItems; trackBy: trackLegendItem"
          class="legend-item"
          [class.highlighted]="item.highlighted"
          (click)="onLegendClick(item)"
          [style.cursor]="interactive ? 'pointer' : 'default'">
          <div class="legend-color" [style.background-color]="item.color"></div>
          <div class="legend-content">
            <span class="legend-label">{{item.label}}</span>
            <span class="legend-score">{{item.score}}%</span>
          </div>
          <div class="legend-bar">
            <div
              class="legend-fill"
              [style.width.%]="item.score"
              [style.background-color]="item.color">
            </div>
          </div>
        </button>
      </div>

      <!-- Insights -->
      <div class="compatibility-insights" *ngIf="showInsights">
        <h4 class="insights-title">Key Insights</h4>
        <div class="insights-list">
          <div
            *ngFor="let insight of insights; trackBy: trackInsight"
            class="insight-item"
            [ngClass]="insight.type">
            <div class="insight-icon"><mat-icon>{{insight.icon}}</mat-icon></div>
            <div class="insight-text">{{insight.text}}</div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .compatibility-radar-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
      background: var(--card-background, #ffffff);
      border-radius: 16px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    .small { max-width: 400px; }
    .medium { max-width: 600px; }
    .large { max-width: 800px; }

    .radar-header {
      text-align: center;
      margin-bottom: 1.5rem;
    }

    .radar-title {
      margin: 0 0 1rem 0;
      color: var(--primary-color, #ec4899);
      font-size: 1.5rem;
      font-weight: 600;
    }

    .overall-score {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .score-value {
      font-size: 2.5rem;
      font-weight: bold;
      background: linear-gradient(135deg, #ffd700, #ff6b9d, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .score-label {
      font-size: 0.9rem;
      color: var(--color-text-muted, #6b7280);
      margin-top: 0.25rem;
    }

    .loading-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
    }

    .loading-message {
      font-size: 1rem;
      color: var(--color-text-muted, #6b7280);
      text-align: center;
    }

    .retry-button {
      padding: 0.5rem 1rem;
      background: var(--primary-color, #ec4899);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 0.9rem;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }

    .retry-button:hover {
      background: var(--primary-color-hover, #db2777);
    }

    .retry-button:focus {
      outline: 2px solid var(--focus-ring-primary, #ec4899);
      outline-offset: 2px;
    }

    .radar-chart-wrapper {
      position: relative;
      margin-bottom: 1.5rem;
    }

    .radar-chart {
      max-width: 100%;
      height: auto;
    }

    .compatibility-shape {
      transition: all 0.3s ease;
    }

    .compatibility-shape.animated {
      animation: shape-pulse 3s ease-in-out infinite;
    }

    .data-point {
      transition: all 0.3s ease;
      cursor: pointer;
    }

    .data-point:hover {
      r: 6;
      filter: drop-shadow(0 0 6px currentColor);
    }

    .data-point.pulsing {
      animation: point-pulse 2s ease-in-out infinite;
    }

    .tooltip {
      position: absolute;
      background: var(--surface-color, #f8fafc);
      border: 1px solid var(--border-color, #e5e7eb);
      border-radius: 8px;
      padding: 0.75rem;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      pointer-events: none;
      z-index: 10;
      max-width: 200px;
    }

    .tooltip-title {
      font-weight: 600;
      margin-bottom: 0.25rem;
      color: var(--color-text, #1f2937);
    }

    .tooltip-score {
      font-size: 0.9rem;
      color: var(--primary-color, #ec4899);
      margin-bottom: 0.25rem;
    }

    .tooltip-description {
      font-size: 0.8rem;
      color: var(--color-text-muted, #6b7280);
      line-height: 1.4;
    }

    .compatibility-legend {
      width: 100%;
      max-width: 400px;
      margin-bottom: 1rem;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem;
      border-radius: 8px;
      transition: all 0.3s ease;
      margin-bottom: 0.5rem;
    }

    .legend-item:hover,
    .legend-item.highlighted {
      background: var(--surface-color, #f8fafc);
      transform: translateX(4px);
    }

    .legend-color {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .legend-content {
      display: flex;
      flex-direction: column;
      min-width: 120px;
    }

    .legend-label {
      font-size: 0.9rem;
      font-weight: 500;
      color: var(--color-text, #1f2937);
    }

    .legend-score {
      font-size: 0.8rem;
      color: var(--color-text-muted, #6b7280);
    }

    .legend-bar {
      flex: 1;
      height: 6px;
      background: var(--border-color, #e5e7eb);
      border-radius: 3px;
      overflow: hidden;
    }

    .legend-fill {
      height: 100%;
      border-radius: 3px;
      transition: width 1s ease-out;
    }

    .compatibility-insights {
      width: 100%;
      max-width: 500px;
    }

    .insights-title {
      margin: 0 0 1rem 0;
      color: var(--color-text, #1f2937);
      font-size: 1.2rem;
      font-weight: 600;
      text-align: center;
    }

    .insights-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .insight-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1rem;
      border-radius: 12px;
      border-left: 4px solid;
    }

    .insight-item.strength {
      background: rgba(52, 211, 153, 0.1);
      border-left-color: #34d399;
    }

    .insight-item.opportunity {
      background: rgba(251, 191, 36, 0.1);
      border-left-color: #fbbf24;
    }

    .insight-item.concern {
      background: rgba(248, 113, 113, 0.1);
      border-left-color: #f87171;
    }

    .insight-icon {
      font-size: 1.5rem;
      flex-shrink: 0;
    }

    .insight-text {
      font-size: 0.9rem;
      color: var(--color-text, #1f2937);
      line-height: 1.4;
    }

    /* Animations */
    @keyframes shape-pulse {
      0%, 100% { opacity: 0.8; }
      50% { opacity: 1; }
    }

    @keyframes point-pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.3); }
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
      .compatibility-radar-container {
        padding: 1rem;
      }

      .radar-title {
        font-size: 1.3rem;
      }

      .score-value {
        font-size: 2rem;
      }

      .legend-item {
        padding: 0.5rem;
        gap: 0.5rem;
      }

      .insights-title {
        font-size: 1.1rem;
      }

      .insight-item {
        padding: 0.75rem;
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .compatibility-shape, .data-point, .legend-fill {
        animation: none !important;
        transition: none !important;
      }
    }

    /* Dark theme */
    .dark-theme .tooltip {
      background: var(--surface-color, #1f2937);
      border-color: var(--border-color, #374151);
    }
  `]
})
export class CompatibilityRadarComponent implements OnInit, OnDestroy, AfterViewInit, OnChanges {
  @ViewChild('radarSvg', { static: false }) radarSvg!: ElementRef<SVGElement>;

  @Input() compatibilityData?: CompatibilityBreakdown | CompatibilityResponse;
  @Input() userId?: number; // For fetching live compatibility data
  @Input() connectionId?: number; // For existing connections
  @Input() autoRefresh: boolean = false; // Enable real-time updates
  @Input() refreshInterval: number = 30000; // 30 seconds default

  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() showHeader: boolean = true;
  @Input() showLegend: boolean = true;
  @Input() showInsights: boolean = true;
  @Input() animateChart: boolean = true;
  @Input() interactive: boolean = true;

  svgSize: number = 300;
  center = { x: 150, y: 150 };
  maxRadius: number = 120;
  gridRings: Array<{radius: number; value?: number; width?: number}> = [];
  axes: Array<{x: number; y: number}> = [];
  dataPoints: Array<{x: number; y: number; score: number; category: string; color: string; key?: string; strokeColor?: string; highlight?: boolean; description?: string}> = [];
  axisLabels: Array<{x: number; y: number; text: string; key?: string}> = [];
  legendItems: Array<{color: string; label: string; score: number; key?: string; highlighted?: boolean}> = [];
  insights: Array<{icon: string; text: string; type: string}> = [];

  hoveredPoint: {x: number; y: number; score: number; category: string; color: string; description?: string} | null = null;
  tooltip = { x: 0, y: 0 };

  // Real-time data management
  private subscriptions = new Subscription();
  private refreshTimer?: number;
  private currentCompatibility?: CompatibilityBreakdown;
  private isLoading = false;
  hasError = false;

  private readonly categories = [
    { key: 'values', label: 'Values', color: '#ffd700', angle: 0 },
    { key: 'interests', label: 'Interests', color: '#ff6b9d', angle: 72 },
    { key: 'communication', label: 'Communication', color: '#34d399', angle: 144 },
    { key: 'demographics', label: 'Demographics', color: '#60a5fa', angle: 216 },
    { key: 'personality', label: 'Personality', color: '#c084fc', angle: 288 }
  ];

  constructor(private soulConnectionService: SoulConnectionService) {}

  get overallScore(): number {
    if (!this.currentCompatibility) return 0;

    const scores = Object.values(this.currentCompatibility) as number[];
    return Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length);
  }

  get isDataAvailable(): boolean {
    return !!this.currentCompatibility && !this.isLoading;
  }

  get loadingMessage(): string {
    if (this.isLoading) return 'Analyzing soul compatibility...';
    if (this.hasError) return 'Unable to load compatibility data';
    if (!this.currentCompatibility) return 'No compatibility data available';
    return '';
  }

  get gridColor(): string {
    return 'var(--border-color, #e5e7eb)';
  }

  get areaStroke(): string {
    return 'var(--primary-color, #ec4899)';
  }

  get labelColor(): string {
    return 'var(--color-text, #1f2937)';
  }

  get labelBackgroundColor(): string {
    return 'var(--background-color, #ffffff)';
  }

  get labelBackgroundRadius(): number {
    return this.labelFontSize + 4;
  }

  get labelFontSize(): number {
    return this.size === 'small' ? 10 : this.size === 'medium' ? 12 : 14;
  }

  get pointRadius(): number {
    return this.size === 'small' ? 3 : this.size === 'medium' ? 4 : 5;
  }

  get compatibilityPath(): string {
    if (this.dataPoints.length === 0) return '';

    const pathData = this.dataPoints.map((point, index) => {
      const command = index === 0 ? 'M' : 'L';
      return `${command} ${point.x} ${point.y}`;
    }).join(' ');

    return pathData + ' Z';
  }

  ngAfterViewInit() {
    if (this.interactive) {
      this.setupInteractivity();
    }
  }

  private setupSizing() {
    const sizeMap = { small: 200, medium: 300, large: 400 };
    this.svgSize = sizeMap[this.size];
    this.center = { x: this.svgSize / 2, y: this.svgSize / 2 };
    this.maxRadius = (this.svgSize / 2) - 40;
  }

  private generateGridRings() {
    this.gridRings = [];
    for (let i = 1; i <= 5; i++) {
      this.gridRings.push({
        radius: (this.maxRadius / 5) * i,
        width: i === 5 ? 2 : 1
      });
    }
  }

  private generateAxes() {
    this.axes = [];
    this.categories.forEach(category => {
      const angle = (category.angle - 90) * Math.PI / 180;
      const x = this.center.x + this.maxRadius * Math.cos(angle);
      const y = this.center.y + this.maxRadius * Math.sin(angle);
      this.axes.push({ x, y });
    });
  }

  private calculateDataPoints() {
    this.dataPoints = [];
    if (!this.currentCompatibility) return;

    this.categories.forEach(category => {
      const score = this.currentCompatibility![category.key as keyof CompatibilityBreakdown] || 0;
      const radius = (score / 100) * this.maxRadius;
      const angle = (category.angle - 90) * Math.PI / 180;

      const x = this.center.x + radius * Math.cos(angle);
      const y = this.center.y + radius * Math.sin(angle);

      this.dataPoints.push({
        x,
        y,
        score,
        category: category.label,
        key: category.key,
        color: category.color,
        strokeColor: '#ffffff',
        highlight: score >= 85,
        description: this.getCategoryDescription(category.key, score)
      });
    });
  }

  private generateAxisLabels() {
    this.axisLabels = [];
    this.categories.forEach(category => {
      const labelRadius = this.maxRadius + 25;
      const angle = (category.angle - 90) * Math.PI / 180;
      const x = this.center.x + labelRadius * Math.cos(angle);
      const y = this.center.y + labelRadius * Math.sin(angle);

      this.axisLabels.push({
        x,
        y,
        text: category.label,
        key: category.key
      });
    });
  }

  private generateLegendItems() {
    this.legendItems = this.categories.map(category => ({
      label: category.label,
      color: category.color,
      score: this.currentCompatibility?.[category.key as keyof CompatibilityBreakdown] || 0,
      key: category.key,
      highlighted: false
    }));
  }

  private generateInsights() {
    this.insights = [];
    if (!this.currentCompatibility) return;

    const scores = this.categories.map(cat => ({
      ...cat,
      score: this.currentCompatibility![cat.key as keyof CompatibilityBreakdown] || 0
    }));

    // Find strengths (scores >= 80)
    const strengths = scores.filter(s => s.score >= 80);
    if (strengths.length > 0) {
      const topStrength = strengths.reduce((a, b) => a.score > b.score ? a : b);
      this.insights.push({
        type: 'strength',
        icon: 'auto_awesome',
        text: `Exceptional ${topStrength.label.toLowerCase()} compatibility (${topStrength.score}%) creates a strong foundation for soul connection.`
      });
    }

    // Find opportunities (scores 50-75)
    const opportunities = scores.filter(s => s.score >= 50 && s.score < 75);
    if (opportunities.length > 0) {
      const topOpportunity = opportunities.reduce((a, b) => a.score > b.score ? a : b);
      this.insights.push({
        type: 'opportunity',
        icon: 'spa',
        text: `Growing ${topOpportunity.label.toLowerCase()} alignment (${topOpportunity.score}%) offers potential for deeper soul connection.`
      });
    }

    // Find concerns (scores < 50)
    const concerns = scores.filter(s => s.score < 50);
    if (concerns.length > 0) {
      const topConcern = concerns.reduce((a, b) => a.score < b.score ? a : b);
      this.insights.push({
        type: 'concern',
        icon: 'chat_bubble',
        text: `Exploring ${topConcern.label.toLowerCase()} differences (${topConcern.score}%) through meaningful revelations could deepen understanding.`
      });
    }

    // Overall compatibility insight
    const overall = this.overallScore;
    if (overall >= 85) {
      this.insights.push({
        type: 'strength',
        icon: 'stars',
        text: `Outstanding overall compatibility (${overall}%) suggests a profound soul-level connection.`
      });
    } else if (overall >= 70) {
      this.insights.push({
        type: 'opportunity',
        icon: 'link',
        text: `Strong overall compatibility (${overall}%) indicates promising potential for lasting connection.`
      });
    }
  }

  private getCategoryDescription(key: string, score: number): string {
    const descriptions: Record<string, string> = {
      values: 'Shared beliefs and principles that guide life decisions and moral choices',
      interests: 'Common hobbies, activities, and passions that bring joy and fulfillment',
      communication: 'How naturally you understand and connect through meaningful conversation',
      demographics: 'Life stage, background, and practical compatibility factors',
      personality: 'Complementary traits and emotional resonance that create harmony'
    };

    const scoreContext = score >= 80 ? ' - Exceptional alignment' :
                        score >= 60 ? ' - Good compatibility' :
                        score >= 40 ? ' - Growing potential' :
                        ' - Opportunity for growth';

    return (descriptions[key] || 'Compatibility assessment for meaningful soul connection') + scoreContext;
  }

  private setupInteractivity() {
    // Add mouse event listeners for tooltip functionality
    if (this.radarSvg?.nativeElement) {
      this.radarSvg.nativeElement.addEventListener('mouseleave', () => {
        this.hoveredPoint = null;
      });
    }
  }

  onPointClick(point: {key?: string; highlight?: boolean}) {
    if (!this.interactive) return;

    // Toggle highlight for clicked point
    point.highlight = !point.highlight;

    // Update legend highlighting
    const legendItem = this.legendItems.find(item => item.label === point.key);
    if (legendItem) {
      legendItem.score = point.highlight ? 100 : legendItem.score;
    }
  }

  onLegendClick(item: {label: string; score: number; color: string; key?: string; highlighted?: boolean}) {
    if (!this.interactive) return;

    // Toggle highlighting
    const highlighted = item.score > 50;

    // Update corresponding data point
    const dataPoint = this.dataPoints.find(point => point.category === item.label);
    if (dataPoint) {
      dataPoint.score = highlighted ? dataPoint.score : 0;
    }
  }

  trackPoint(index: number, point: {x: number; y: number; score: number; category: string; color: string; key?: string; strokeColor?: string; highlight?: boolean; description?: string}): string {
    return point.category;
  }

  trackLabel(index: number, label: {x: number; y: number; text: string; key?: string}): string {
    return label.text;
  }

  trackLegendItem(index: number, item: {color: string; label: string; score: number; key?: string; highlighted?: boolean}): string {
    return item.label;
  }

  trackInsight(index: number, insight: {icon: string; text: string; type: string}): string {
    return insight.text;
  }

  /**
   * Enhanced lifecycle methods with real-time data support
   */
  ngOnChanges(changes: SimpleChanges) {
    if (changes['compatibilityData'] || changes['userId'] || changes['connectionId']) {
      this.processCompatibilityData();
    }

    if (changes['autoRefresh'] && this.autoRefresh) {
      this.setupAutoRefresh();
    } else if (changes['autoRefresh'] && !this.autoRefresh) {
      this.clearAutoRefresh();
    }
  }

  /**
   * Real-time data management methods
   */
  private processCompatibilityData() {
    if (this.compatibilityData) {
      // Direct data input
      this.currentCompatibility = this.extractCompatibilityBreakdown(this.compatibilityData);
    } else if (this.connectionId) {
      // Fetch from existing connection
      this.fetchConnectionCompatibility();
    } else if (this.userId) {
      // Fetch from discovery for specific user
      this.fetchUserCompatibility();
    } else {
      // No data source provided, use fallback
      this.currentCompatibility = this.getDefaultCompatibility();
    }

    this.updateVisualization();
  }

  private extractCompatibilityBreakdown(data: CompatibilityBreakdown | CompatibilityResponse): CompatibilityBreakdown {
    if ('breakdown' in data) {
      return data.breakdown;
    }
    return data as CompatibilityBreakdown;
  }

  private fetchConnectionCompatibility() {
    if (!this.connectionId) return;

    this.isLoading = true;
    this.hasError = false;

    const subscription = this.soulConnectionService.getSoulConnection(this.connectionId)
      .subscribe({
        next: (connection) => {
          if (connection.compatibility_breakdown) {
            this.currentCompatibility = connection.compatibility_breakdown;
            this.updateVisualization();
          }
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error fetching connection compatibility:', error);
          this.hasError = true;
          this.isLoading = false;
          this.currentCompatibility = this.getDefaultCompatibility();
          this.updateVisualization();
        }
      });

    this.subscriptions.add(subscription);
  }

  private fetchUserCompatibility() {
    if (!this.userId) return;

    this.isLoading = true;
    this.hasError = false;

    const subscription = this.soulConnectionService.discoverSoulConnections({ max_results: 1 })
      .subscribe({
        next: (discoveries) => {
          const userDiscovery = discoveries.find(d => d.user_id === this.userId);
          if (userDiscovery?.compatibility.breakdown) {
            this.currentCompatibility = userDiscovery.compatibility.breakdown;
            this.updateVisualization();
          }
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error fetching user compatibility:', error);
          this.hasError = true;
          this.isLoading = false;
          this.currentCompatibility = this.getDefaultCompatibility();
          this.updateVisualization();
        }
      });

    this.subscriptions.add(subscription);
  }

  private getDefaultCompatibility(): CompatibilityBreakdown {
    return {
      values: 75,
      interests: 68,
      communication: 82,
      demographics: 70,
      personality: 79
    };
  }

  private updateVisualization() {
    this.calculateDataPoints();
    this.generateLegendItems();
    this.generateInsights();
  }

  private setupAutoRefresh() {
    if (!this.autoRefresh || (!this.connectionId && !this.userId)) return;

    this.clearAutoRefresh();
    this.refreshTimer = window.setInterval(() => {
      this.processCompatibilityData();
    }, this.refreshInterval);
  }

  private clearAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = undefined;
    }
  }

  /**
   * Enhanced lifecycle methods
   */
  ngOnInit() {
    this.setupSizing();
    this.generateGridRings();
    this.generateAxes();
    this.generateAxisLabels();
    this.processCompatibilityData();
    this.setupAutoRefresh();
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
    this.clearAutoRefresh();
  }

  /**
   * Manual refresh method for user-triggered updates
   */
  refreshData() {
    this.processCompatibilityData();
  }
}
