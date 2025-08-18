import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-compatibility-score',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div 
      class="compatibility-container" 
      [ngClass]="[size, getCompatibilityLevel()]"
      role="progressbar"
      [attr.aria-valuenow]="displayScore"
      aria-valuemin="0"
      aria-valuemax="100"
      [attr.aria-label]="getAriaLabel()"
      [attr.aria-describedby]="descriptionId">
      
      <!-- Circular Progress Ring -->
      <div class="score-circle" #scoreCircle>
        <svg 
          class="circle-svg" 
          [attr.width]="circleSize" 
          [attr.height]="circleSize" 
          viewBox="0 0 120 120"
          aria-hidden="true">
          
          <defs>
            <!-- Background gradient -->
            <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="var(--surface-secondary)" stop-opacity="0.3"/>
              <stop offset="100%" stop-color="var(--surface-tertiary)" stop-opacity="0.5"/>
            </linearGradient>
            
            <!-- Progress gradient based on compatibility level -->
            <linearGradient [id]="'progress-gradient-' + componentId" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" [attr.stop-color]="progressColors.start"/>
              <stop offset="50%" [attr.stop-color]="progressColors.middle"/>
              <stop offset="100%" [attr.stop-color]="progressColors.end"/>
            </linearGradient>
            
            <!-- Glow filter for high compatibility -->
            <filter [id]="'glow-' + componentId" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge> 
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          <!-- Background circle -->
          <circle
            cx="60" cy="60" [attr.r]="radius"
            fill="none"
            stroke="url(#bg-gradient)"
            stroke-width="8"
            class="background-circle">
          </circle>
          
          <!-- Progress circle -->
          <circle
            cx="60" cy="60" [attr.r]="radius"
            fill="none"
            [attr.stroke]="'url(#progress-gradient-' + componentId + ')'"
            stroke-width="8"
            stroke-linecap="round"
            [attr.stroke-dasharray]="circumference"
            [attr.stroke-dashoffset]="strokeDashoffset"
            [attr.filter]="getFilterUrl()"
            class="progress-circle"
            [class.animated]="animated"
            [class.pulsing]="shouldPulse()">
          </circle>
          
          <!-- Inner sparkles for high compatibility -->
          <g class="sparkles" *ngIf="score >= 80">
            <circle 
              *ngFor="let sparkle of sparkles; trackBy: trackSparkle"
              [attr.cx]="sparkle.x" 
              [attr.cy]="sparkle.y" 
              [attr.r]="sparkle.size"
              [attr.fill]="sparkle.color"
              class="sparkle"
              [style.animation-delay]="sparkle.delay + 's'">
            </circle>
          </g>
        </svg>
        
        <!-- Score Display -->
        <div class="score-content">
          <span 
            class="score-number" 
            [class.counting]="isAnimating"
            aria-hidden="true">{{ displayScore }}%</span>
          <span 
            class="score-label" 
            *ngIf="showLabel"
            aria-hidden="true">{{ getScoreLabel() }}</span>
        </div>
      </div>
      
      <!-- Compatibility Description -->
      <div 
        class="compatibility-description" 
        [id]="descriptionId"
        *ngIf="showDescription">
        <h4 class="compatibility-title">{{ getCompatibilityTitle() }}</h4>
        <p class="compatibility-text">{{ getCompatibilityDescription() }}</p>
        
        <!-- Connection strength indicators -->
        <div class="strength-indicators" *ngIf="showIndicators">
          <div class="indicator-row">
            <span class="indicator-label">Values Alignment</span>
            <div class="indicator-bar">
              <div 
                class="indicator-fill" 
                [style.width.%]="getIndicatorWidth('values')"
                [class]="getIndicatorClass('values')">
              </div>
            </div>
          </div>
          
          <div class="indicator-row">
            <span class="indicator-label">Shared Interests</span>
            <div class="indicator-bar">
              <div 
                class="indicator-fill" 
                [style.width.%]="getIndicatorWidth('interests')"
                [class]="getIndicatorClass('interests')">
              </div>
            </div>
          </div>
          
          <div class="indicator-row">
            <span class="indicator-label">Communication Style</span>
            <div class="indicator-bar">
              <div 
                class="indicator-fill" 
                [style.width.%]="getIndicatorWidth('communication')"
                [class]="getIndicatorClass('communication')">
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Floating hearts for high compatibility -->
      <div class="floating-hearts" *ngIf="score >= 90 && animated">
        <div class="heart heart-1">💖</div>
        <div class="heart heart-2">✨</div>
        <div class="heart heart-3">💫</div>
      </div>
    </div>
  `,
  styles: [`
    .compatibility-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
      max-width: 300px;
      margin: 0 auto;
    }
    
    /* Score Circle */
    .score-circle {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 1.5rem;
    }
    
    .circle-svg {
      transform: rotate(-90deg);
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.1));
    }
    
    /* Size variants */
    .small .circle-svg { width: 80px; height: 80px; }
    .medium .circle-svg { width: 120px; height: 120px; }
    .large .circle-svg { width: 160px; height: 160px; }
    
    /* Circle animations */
    .progress-circle {
      transition: stroke-dashoffset 2s cubic-bezier(0.4, 0, 0.2, 1);
      transform-origin: center;
    }
    
    .progress-circle.animated {
      animation: draw-progress 2s ease-out;
    }
    
    .progress-circle.pulsing {
      animation: compatibility-pulse 2s ease-in-out infinite;
    }
    
    /* Score Content */
    .score-content {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      pointer-events: none;
    }
    
    .score-number {
      display: block;
      font-weight: bold;
      color: var(--text-primary);
      line-height: 1;
      transition: all 0.3s ease;
    }
    
    .small .score-number { font-size: 1.2rem; }
    .medium .score-number { font-size: 1.8rem; }
    .large .score-number { font-size: 2.4rem; }
    
    .score-number.counting {
      transform: scale(1.1);
      filter: brightness(1.2);
    }
    
    .score-label {
      display: block;
      font-size: 0.7rem;
      color: var(--text-secondary);
      margin-top: 0.2rem;
      font-weight: 500;
      opacity: 0.8;
    }
    
    /* Compatibility levels */
    .soul-mate .progress-circle {
      filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.8));
    }
    
    .high-compatibility .progress-circle {
      filter: drop-shadow(0 0 15px rgba(255, 107, 157, 0.6));
    }
    
    .moderate-compatibility .progress-circle {
      filter: drop-shadow(0 0 10px rgba(96, 165, 250, 0.4));
    }
    
    /* Sparkles for high compatibility */
    .sparkle {
      animation: sparkle-twinkle 2s ease-in-out infinite;
    }
    
    /* Compatibility Description */
    .compatibility-description {
      text-align: center;
      max-width: 280px;
    }
    
    .compatibility-title {
      color: var(--text-primary);
      font-size: 1.1rem;
      font-weight: 600;
      margin: 0 0 0.5rem 0;
    }
    
    .compatibility-text {
      color: var(--text-secondary);
      font-size: 0.9rem;
      line-height: 1.5;
      margin: 0 0 1.5rem 0;
    }
    
    /* Strength Indicators */
    .strength-indicators {
      width: 100%;
      margin-top: 1rem;
    }
    
    .indicator-row {
      display: flex;
      align-items: center;
      margin-bottom: 0.75rem;
      gap: 1rem;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
    
    .indicator-label {
      flex: 0 0 120px;
      font-size: 0.8rem;
      color: var(--text-secondary);
      font-weight: 500;
    }
    
    .indicator-bar {
      flex: 1;
      height: 6px;
      background: var(--surface-secondary);
      border-radius: 3px;
      overflow: hidden;
      position: relative;
    }
    
    .indicator-fill {
      height: 100%;
      border-radius: 3px;
      transition: width 1.5s ease-out;
      animation: indicator-glow 3s ease-in-out infinite;
    }
    
    .indicator-fill.high {
      background: linear-gradient(90deg, #ff6b9d, #ffd700);
    }
    
    .indicator-fill.medium {
      background: linear-gradient(90deg, #60a5fa, #34d399);
    }
    
    .indicator-fill.low {
      background: linear-gradient(90deg, #94a3b8, #cbd5e1);
    }
    
    /* Floating Hearts */
    .floating-hearts {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      pointer-events: none;
      z-index: -1;
    }
    
    .heart {
      position: absolute;
      font-size: 1.5rem;
      opacity: 0;
      animation: float-heart 4s ease-in-out infinite;
    }
    
    .heart-1 {
      top: 20%;
      left: 20%;
      animation-delay: 0s;
    }
    
    .heart-2 {
      top: 30%;
      right: 20%;
      animation-delay: 1.3s;
    }
    
    .heart-3 {
      bottom: 20%;
      left: 50%;
      animation-delay: 2.6s;
    }
    
    /* Keyframe Animations */
    @keyframes draw-progress {
      from {
        stroke-dashoffset: 314; /* Full circumference */
      }
      to {
        stroke-dashoffset: var(--final-offset);
      }
    }
    
    @keyframes compatibility-pulse {
      0%, 100% { 
        transform: scale(1); 
        opacity: 1; 
      }
      50% { 
        transform: scale(1.05); 
        opacity: 0.9; 
      }
    }
    
    @keyframes sparkle-twinkle {
      0%, 100% { 
        opacity: 0; 
        transform: scale(0); 
      }
      50% { 
        opacity: 1; 
        transform: scale(1); 
      }
    }
    
    @keyframes indicator-glow {
      0%, 100% { 
        filter: brightness(1); 
      }
      50% { 
        filter: brightness(1.2); 
      }
    }
    
    @keyframes float-heart {
      0% { 
        opacity: 0; 
        transform: translateY(0) scale(0.5); 
      }
      20% { 
        opacity: 1; 
        transform: translateY(-10px) scale(1); 
      }
      80% { 
        opacity: 1; 
        transform: translateY(-30px) scale(1); 
      }
      100% { 
        opacity: 0; 
        transform: translateY(-50px) scale(0.5); 
      }
    }
    
    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .progress-circle,
      .sparkle,
      .heart,
      .indicator-fill {
        animation: none !important;
        transition: none !important;
      }
      
      .progress-circle.animated {
        animation: none;
      }
    }
    
    /* Dark theme adaptation */
    .dark-theme {
      .score-number {
        color: var(--text-primary);
      }
      
      .compatibility-title {
        color: var(--text-primary);
      }
      
      .compatibility-text,
      .indicator-label {
        color: var(--text-secondary);
      }
      
      .indicator-bar {
        background: var(--surface-tertiary);
      }
    }
    
    /* Mobile optimizations */
    @media (max-width: 768px) {
      .compatibility-container {
        max-width: 250px;
      }
      
      .small .circle-svg { width: 70px; height: 70px; }
      .medium .circle-svg { width: 100px; height: 100px; }
      .large .circle-svg { width: 130px; height: 130px; }
      
      .compatibility-title {
        font-size: 1rem;
      }
      
      .compatibility-text {
        font-size: 0.85rem;
      }
      
      .indicator-label {
        flex: 0 0 100px;
        font-size: 0.75rem;
      }
    }
  `]
})
export class CompatibilityScoreComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() score: number = 0;
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() animated: boolean = true;
  @Input() showLabel: boolean = true;
  @Input() showDescription: boolean = true;
  @Input() showIndicators: boolean = false;
  @Input() breakdown?: {
    values: number;
    interests: number;
    communication: number;
  };
  
  @ViewChild('scoreCircle', { static: false }) scoreCircle?: ElementRef;
  
  displayScore: number = 0;
  isAnimating: boolean = false;
  componentId: string = Math.random().toString(36).substr(2, 9);
  descriptionId: string = `compatibility-desc-${this.componentId}`;
  sparkles: any[] = [];
  
  private animationFrame?: number;
  private startTime?: number;

  get circleSize(): number {
    const sizes = { small: 80, medium: 120, large: 160 };
    return sizes[this.size];
  }

  get radius(): number {
    return (this.circleSize - 16) / 2; // Account for stroke width
  }

  get circumference(): number {
    return 2 * Math.PI * this.radius;
  }

  get strokeDashoffset(): number {
    const progress = this.displayScore / 100;
    return this.circumference - (progress * this.circumference);
  }

  get progressColors() {
    if (this.score >= 90) {
      return {
        start: '#ffd700',
        middle: '#ff6b9d',
        end: '#c084fc'
      };
    } else if (this.score >= 70) {
      return {
        start: '#ff6b9d',
        middle: '#ffd700',
        end: '#ff6b9d'
      };
    } else if (this.score >= 50) {
      return {
        start: '#60a5fa',
        middle: '#34d399',
        end: '#60a5fa'
      };
    } else {
      return {
        start: '#94a3b8',
        middle: '#cbd5e1',
        end: '#94a3b8'
      };
    }
  }

  ngOnInit() {
    this.generateSparkles();
  }

  ngAfterViewInit() {
    if (this.animated) {
      this.animateScore();
    } else {
      this.displayScore = this.score;
    }
  }

  ngOnDestroy() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
  }

  private generateSparkles() {
    this.sparkles = [];
    
    if (this.score >= 80) {
      const sparkleCount = 6;
      const centerX = this.circleSize / 2;
      const centerY = this.circleSize / 2;
      
      for (let i = 0; i < sparkleCount; i++) {
        const angle = (i / sparkleCount) * 2 * Math.PI;
        const distance = this.radius * 0.6;
        
        this.sparkles.push({
          id: i,
          x: centerX + Math.cos(angle) * distance,
          y: centerY + Math.sin(angle) * distance,
          size: 1 + Math.random() * 1.5,
          color: '#ffffff',
          delay: Math.random() * 2
        });
      }
    }
  }

  private animateScore() {
    this.isAnimating = true;
    this.startTime = performance.now();
    
    const animate = (currentTime: number) => {
      if (!this.startTime) return;
      
      const elapsed = currentTime - this.startTime;
      const duration = 2000; // 2 seconds
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function for smooth animation
      const easeOutCubic = 1 - Math.pow(1 - progress, 3);
      this.displayScore = Math.round(this.score * easeOutCubic);
      
      if (progress < 1) {
        this.animationFrame = requestAnimationFrame(animate);
      } else {
        this.isAnimating = false;
      }
    };
    
    this.animationFrame = requestAnimationFrame(animate);
  }

  getCompatibilityLevel(): string {
    if (this.score >= 90) return 'soul-mate';
    if (this.score >= 70) return 'high-compatibility';
    if (this.score >= 50) return 'moderate-compatibility';
    return 'low-compatibility';
  }

  getScoreLabel(): string {
    if (this.score >= 90) return 'Soul Mate';
    if (this.score >= 80) return 'Excellent';
    if (this.score >= 70) return 'Great';
    if (this.score >= 60) return 'Good';
    if (this.score >= 50) return 'Fair';
    return 'Low';
  }

  getCompatibilityTitle(): string {
    if (this.score >= 90) return '✨ Soul Connection';
    if (this.score >= 80) return '💖 Exceptional Match';
    if (this.score >= 70) return '💕 Strong Connection';
    if (this.score >= 60) return '💙 Good Harmony';
    if (this.score >= 50) return '💜 Potential Bond';
    return '💛 Growing Connection';
  }

  getCompatibilityDescription(): string {
    if (this.score >= 90) {
      return 'A rare and beautiful soul connection. Your values, dreams, and energy align in extraordinary harmony.';
    } else if (this.score >= 80) {
      return 'An exceptional match with deep compatibility. You share strong values and complementary perspectives.';
    } else if (this.score >= 70) {
      return 'A promising connection with solid compatibility. You have meaningful common ground to build upon.';
    } else if (this.score >= 60) {
      return 'Good compatibility with shared interests. This connection has potential for genuine understanding.';
    } else if (this.score >= 50) {
      return 'Moderate compatibility with some shared values. A foundation exists for meaningful connection.';
    } else {
      return 'While compatibility is lower, every connection teaches us something valuable about ourselves.';
    }
  }

  shouldPulse(): boolean {
    return this.score >= 80 && this.animated;
  }

  getFilterUrl(): string {
    return this.score >= 80 ? `url(#glow-${this.componentId})` : 'none';
  }

  getIndicatorWidth(type: 'values' | 'interests' | 'communication'): number {
    if (!this.breakdown) {
      // Simulate breakdown based on overall score
      const base = this.score;
      const variation = 15;
      
      switch (type) {
        case 'values': return Math.max(0, Math.min(100, base + (Math.random() - 0.5) * variation));
        case 'interests': return Math.max(0, Math.min(100, base + (Math.random() - 0.5) * variation));
        case 'communication': return Math.max(0, Math.min(100, base + (Math.random() - 0.5) * variation));
      }
    }
    
    return this.breakdown[type];
  }

  getIndicatorClass(type: 'values' | 'interests' | 'communication'): string {
    const width = this.getIndicatorWidth(type);
    
    if (width >= 70) return 'high';
    if (width >= 50) return 'medium';
    return 'low';
  }

  getAriaLabel(): string {
    const level = this.getScoreLabel();
    return `Compatibility score: ${this.displayScore}% - ${level} match`;
  }

  trackSparkle(index: number, sparkle: any): any {
    return sparkle.id;
  }

  /**
   * Trigger celebration animation for high scores
   */
  triggerCelebration(): void {
    if (this.score >= 80) {
      // Re-animate the score
      this.animateScore();
      
      // Add temporary celebration class
      const container = this.scoreCircle?.nativeElement?.parentElement;
      if (container) {
        container.classList.add('celebrating');
        
        setTimeout(() => {
          container.classList.remove('celebrating');
        }, 3000);
      }
    }
  }

  /**
   * Update score with smooth transition
   */
  updateScore(newScore: number): void {
    this.score = newScore;
    this.generateSparkles();
    
    if (this.animated) {
      this.animateScore();
    } else {
      this.displayScore = newScore;
    }
  }
}