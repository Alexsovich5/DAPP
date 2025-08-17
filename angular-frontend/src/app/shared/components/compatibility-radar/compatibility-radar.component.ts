import { Component, Input, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-compatibility-radar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="compatibility-radar-container" [ngClass]="size">
      <div class="radar-header" *ngIf="showHeader">
        <h3 class="radar-title">Soul Compatibility Analysis</h3>
        <div class="overall-score">
          <span class="score-value">{{overallScore}}%</span>
          <span class="score-label">Overall Match</span>
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
        <div 
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
        </div>
      </div>

      <!-- Insights -->
      <div class="compatibility-insights" *ngIf="showInsights">
        <h4 class="insights-title">Key Insights</h4>
        <div class="insights-list">
          <div 
            *ngFor="let insight of insights; trackBy: trackInsight"
            class="insight-item"
            [ngClass]="insight.type">
            <div class="insight-icon">{{insight.icon}}</div>
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
      color: var(--text-secondary, #6b7280);
      margin-top: 0.25rem;
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
      color: var(--text-primary, #1f2937);
    }

    .tooltip-score {
      font-size: 0.9rem;
      color: var(--primary-color, #ec4899);
      margin-bottom: 0.25rem;
    }

    .tooltip-description {
      font-size: 0.8rem;
      color: var(--text-secondary, #6b7280);
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
      color: var(--text-primary, #1f2937);
    }

    .legend-score {
      font-size: 0.8rem;
      color: var(--text-secondary, #6b7280);
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
      color: var(--text-primary, #1f2937);
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
      color: var(--text-primary, #1f2937);
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
export class CompatibilityRadarComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('radarSvg', { static: false }) radarSvg!: ElementRef<SVGElement>;

  @Input() compatibilityData: any = {
    values: 85,
    interests: 72,
    communication: 90,
    lifestyle: 68,
    goals: 78,
    personality: 82
  };

  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() showHeader: boolean = true;
  @Input() showLegend: boolean = true;
  @Input() showInsights: boolean = true;
  @Input() animateChart: boolean = true;
  @Input() interactive: boolean = true;

  svgSize: number = 300;
  center = { x: 150, y: 150 };
  maxRadius: number = 120;
  gridRings: any[] = [];
  axes: any[] = [];
  dataPoints: any[] = [];
  axisLabels: any[] = [];
  legendItems: any[] = [];
  insights: any[] = [];

  hoveredPoint: any = null;
  tooltip = { x: 0, y: 0 };

  private readonly categories = [
    { key: 'values', label: 'Values', color: '#ffd700', angle: 0 },
    { key: 'interests', label: 'Interests', color: '#ff6b9d', angle: 60 },
    { key: 'communication', label: 'Communication', color: '#34d399', angle: 120 },
    { key: 'lifestyle', label: 'Lifestyle', color: '#60a5fa', angle: 180 },
    { key: 'goals', label: 'Goals', color: '#c084fc', angle: 240 },
    { key: 'personality', label: 'Personality', color: '#fbbf24', angle: 300 }
  ];

  get overallScore(): number {
    const scores = Object.values(this.compatibilityData) as number[];
    return Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length);
  }

  get gridColor(): string {
    return 'var(--border-color, #e5e7eb)';
  }

  get areaStroke(): string {
    return 'var(--primary-color, #ec4899)';
  }

  get labelColor(): string {
    return 'var(--text-primary, #1f2937)';
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

  ngOnInit() {
    this.setupSizing();
    this.generateGridRings();
    this.generateAxes();
    this.calculateDataPoints();
    this.generateAxisLabels();
    this.generateLegendItems();
    this.generateInsights();
  }

  ngAfterViewInit() {
    if (this.interactive) {
      this.setupInteractivity();
    }
  }

  ngOnDestroy() {
    // Cleanup any event listeners if needed
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
    this.categories.forEach(category => {
      const score = this.compatibilityData[category.key] || 0;
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
      score: this.compatibilityData[category.key] || 0,
      key: category.key,
      highlighted: false
    }));
  }

  private generateInsights() {
    this.insights = [];
    const scores = this.categories.map(cat => ({
      ...cat,
      score: this.compatibilityData[cat.key] || 0
    }));

    // Find strengths (scores >= 80)
    const strengths = scores.filter(s => s.score >= 80);
    if (strengths.length > 0) {
      const topStrength = strengths.reduce((a, b) => a.score > b.score ? a : b);
      this.insights.push({
        type: 'strength',
        icon: '✨',
        text: `Exceptional ${topStrength.label.toLowerCase()} compatibility (${topStrength.score}%) creates a strong foundation for connection.`
      });
    }

    // Find opportunities (scores 50-75)
    const opportunities = scores.filter(s => s.score >= 50 && s.score < 75);
    if (opportunities.length > 0) {
      const topOpportunity = opportunities.reduce((a, b) => a.score > b.score ? a : b);
      this.insights.push({
        type: 'opportunity',
        icon: '🌱',
        text: `Growing ${topOpportunity.label.toLowerCase()} alignment (${topOpportunity.score}%) offers potential for deeper connection.`
      });
    }

    // Find concerns (scores < 50)
    const concerns = scores.filter(s => s.score < 50);
    if (concerns.length > 0) {
      const topConcern = concerns.reduce((a, b) => a.score < b.score ? a : b);
      this.insights.push({
        type: 'concern',
        icon: '💭',
        text: `Exploring ${topConcern.label.toLowerCase()} differences (${topConcern.score}%) through open conversation could bridge gaps.`
      });
    }
  }

  private getCategoryDescription(key: string, score: number): string {
    const descriptions: any = {
      values: 'Shared beliefs and principles that guide life decisions',
      interests: 'Common hobbies, activities, and passions you enjoy',
      communication: 'How well you understand and connect through conversation',
      lifestyle: 'Daily routines, habits, and life structure preferences',
      goals: 'Future aspirations and life direction alignment',
      personality: 'Complementary traits and emotional compatibility'
    };

    return descriptions[key] || 'Compatibility assessment for meaningful connection';
  }

  private setupInteractivity() {
    // Add mouse event listeners for tooltip functionality
    if (this.radarSvg?.nativeElement) {
      this.radarSvg.nativeElement.addEventListener('mouseleave', () => {
        this.hoveredPoint = null;
      });
    }
  }

  onPointClick(point: any) {
    if (!this.interactive) return;
    
    // Toggle highlight for clicked point
    point.highlight = !point.highlight;
    
    // Update legend highlighting
    const legendItem = this.legendItems.find(item => item.key === point.key);
    if (legendItem) {
      legendItem.highlighted = point.highlight;
    }
  }

  onLegendClick(item: any) {
    if (!this.interactive) return;
    
    // Toggle highlighting
    item.highlighted = !item.highlighted;
    
    // Update corresponding data point
    const dataPoint = this.dataPoints.find(point => point.key === item.key);
    if (dataPoint) {
      dataPoint.highlight = item.highlighted;
    }
  }

  trackPoint(index: number, point: any): any {
    return point.key;
  }

  trackLabel(index: number, label: any): any {
    return label.key;
  }

  trackLegendItem(index: number, item: any): any {
    return item.key;
  }

  trackInsight(index: number, insight: any): any {
    return insight.text;
  }
}