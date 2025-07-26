import { Component, Input, OnInit, OnDestroy, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SoulOrbComponent } from '../soul-orb/soul-orb.component';
import { SoulConnectionComponent } from '../soul-connection/soul-connection.component';

@Component({
  selector: 'app-match-celebration',
  standalone: true,
  imports: [CommonModule, SoulOrbComponent, SoulConnectionComponent],
  template: `
    <div class="celebration-overlay" [class.active]="isActive" (click)="onOverlayClick()">
      <div class="celebration-container" [ngClass]="celebrationType">
        
        <!-- Celebration background effects -->
        <div class="celebration-bg">
          <!-- Confetti particles -->
          <div class="confetti-container" *ngIf="showConfetti">
            <div 
              *ngFor="let confetti of confettiParticles; trackBy: trackConfetti"
              class="confetti-piece"
              [style.left.%]="confetti.x"
              [style.animation-delay]="confetti.delay + 's'"
              [style.animation-duration]="confetti.duration + 's'"
              [style.background-color]="confetti.color">
            </div>
          </div>

          <!-- Sparkle effects -->
          <div class="sparkles-container" *ngIf="showSparkles">
            <div 
              *ngFor="let sparkle of sparkleParticles; trackBy: trackSparkle"
              class="sparkle"
              [style.left.%]="sparkle.x"
              [style.top.%]="sparkle.y"
              [style.animation-delay]="sparkle.delay + 's'">
              ✨
            </div>
          </div>

          <!-- Heart shower for high compatibility -->
          <div class="hearts-container" *ngIf="showHearts">
            <div 
              *ngFor="let heart of heartParticles; trackBy: trackHeart"
              class="floating-heart"
              [style.left.%]="heart.x"
              [style.animation-delay]="heart.delay + 's'"
              [style.animation-duration]="heart.duration + 's'">
              {{heart.emoji}}
            </div>
          </div>
        </div>

        <!-- Main celebration content -->
        <div class="celebration-content">
          
          <!-- Header -->
          <div class="celebration-header">
            <h2 class="celebration-title">{{celebrationTitle}}</h2>
            <p class="celebration-subtitle">{{celebrationSubtitle}}</p>
          </div>

          <!-- Soul connection visualization -->
          <div class="soul-connection-display">
            <app-soul-connection
              [leftSoul]="leftSoul"
              [rightSoul]="rightSoul"
              [compatibilityScore]="compatibilityScore"
              [connectionState]="'matched'"
              [orbSize]="'large'"
              [showCompatibility]="true"
              [showCompatibilityMeter]="true"
              [statusMessage]="connectionMessage">
            </app-soul-connection>
          </div>

          <!-- Compatibility highlights -->
          <div class="compatibility-highlights" *ngIf="showHighlights">
            <h3 class="highlights-title">Your Strongest Connections</h3>
            <div class="highlights-grid">
              <div 
                *ngFor="let highlight of compatibilityHighlights; trackBy: trackHighlight"
                class="highlight-item"
                [ngClass]="highlight.level">
                <div class="highlight-icon">{{highlight.icon}}</div>
                <div class="highlight-content">
                  <span class="highlight-label">{{highlight.label}}</span>
                  <span class="highlight-score">{{highlight.score}}%</span>
                </div>
                <div class="highlight-bar">
                  <div 
                    class="highlight-fill" 
                    [style.width.%]="highlight.score"
                    [style.background-color]="highlight.color">
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="celebration-actions">
            <button 
              class="action-btn primary"
              (click)="onStartConversation()"
              [disabled]="isProcessing">
              <span class="btn-icon">💬</span>
              <span class="btn-text">Start Soul Conversation</span>
            </button>
            
            <button 
              class="action-btn secondary"
              (click)="onViewProfile()"
              [disabled]="isProcessing">
              <span class="btn-icon">👤</span>
              <span class="btn-text">Explore Their Soul</span>
            </button>
            
            <button 
              class="action-btn tertiary"
              (click)="onDismiss()"
              [disabled]="isProcessing">
              <span class="btn-text">Continue Discovering</span>
            </button>
          </div>

          <!-- Fun facts or connection insights -->
          <div class="connection-insights" *ngIf="showInsights">
            <h4 class="insights-title">Soul Connection Insights</h4>
            <div class="insights-list">
              <div 
                *ngFor="let insight of connectionInsights; trackBy: trackInsight"
                class="insight-item">
                <span class="insight-icon">{{insight.icon}}</span>
                <span class="insight-text">{{insight.text}}</span>
              </div>
            </div>
          </div>

        </div>

        <!-- Close button -->
        <button class="close-btn" (click)="onDismiss()" aria-label="Close celebration">
          <span>×</span>
        </button>

      </div>
    </div>
  `,
  styles: [`
    .celebration-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
      padding: 1rem;
    }

    .celebration-overlay.active {
      opacity: 1;
      visibility: visible;
    }

    .celebration-container {
      position: relative;
      background: var(--background-color, #ffffff);
      border-radius: 24px;
      max-width: 600px;
      width: 100%;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      transform: scale(0.8) translateY(20px);
      transition: transform 0.3s ease;
    }

    .celebration-overlay.active .celebration-container {
      transform: scale(1) translateY(0);
    }

    .celebration-bg {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      overflow: hidden;
      border-radius: 24px;
      pointer-events: none;
    }

    /* Confetti animation */
    .confetti-container {
      position: absolute;
      top: -10px;
      left: 0;
      right: 0;
      height: 110%;
    }

    .confetti-piece {
      position: absolute;
      width: 8px;
      height: 8px;
      animation: confetti-fall 3s linear infinite;
    }

    .sparkles-container {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
    }

    .sparkle {
      position: absolute;
      font-size: 1.5rem;
      animation: sparkle-twinkle 2s ease-in-out infinite;
    }

    .hearts-container {
      position: absolute;
      top: -10px;
      left: 0;
      right: 0;
      height: 110%;
    }

    .floating-heart {
      position: absolute;
      font-size: 1.2rem;
      animation: heart-float 4s ease-in-out infinite;
    }

    .celebration-content {
      position: relative;
      z-index: 1;
      padding: 2rem;
    }

    .celebration-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .celebration-title {
      font-size: 2rem;
      font-weight: bold;
      margin: 0 0 0.5rem 0;
      background: linear-gradient(135deg, #ffd700, #ff6b9d, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      animation: title-glow 2s ease-in-out infinite alternate;
    }

    .celebration-subtitle {
      font-size: 1.1rem;
      color: var(--text-secondary, #6b7280);
      margin: 0;
      animation: subtitle-fade-in 1s ease-out 0.5s both;
    }

    .soul-connection-display {
      margin: 2rem 0;
      padding: 1.5rem;
      background: var(--surface-color, #f8fafc);
      border-radius: 16px;
      border: 2px solid var(--primary-color, #ec4899);
      animation: connection-highlight 3s ease-in-out infinite;
    }

    .compatibility-highlights {
      margin: 2rem 0;
    }

    .highlights-title {
      font-size: 1.3rem;
      font-weight: 600;
      color: var(--text-primary, #1f2937);
      text-align: center;
      margin: 0 0 1.5rem 0;
    }

    .highlights-grid {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .highlight-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background: var(--surface-color, #f8fafc);
      border-radius: 12px;
      border-left: 4px solid;
      animation: highlight-slide-in 0.5s ease-out;
    }

    .highlight-item.high { border-left-color: #ffd700; }
    .highlight-item.excellent { border-left-color: #ff6b9d; }
    .highlight-item.perfect { border-left-color: #c084fc; }

    .highlight-icon {
      font-size: 1.5rem;
      flex-shrink: 0;
    }

    .highlight-content {
      display: flex;
      flex-direction: column;
      min-width: 100px;
    }

    .highlight-label {
      font-weight: 500;
      color: var(--text-primary, #1f2937);
    }

    .highlight-score {
      font-size: 0.9rem;
      color: var(--primary-color, #ec4899);
      font-weight: 600;
    }

    .highlight-bar {
      flex: 1;
      height: 6px;
      background: var(--border-color, #e5e7eb);
      border-radius: 3px;
      overflow: hidden;
    }

    .highlight-fill {
      height: 100%;
      border-radius: 3px;
      animation: bar-fill 1s ease-out 0.5s both;
    }

    .celebration-actions {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin: 2rem 0;
    }

    .action-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 1rem 1.5rem;
      border: none;
      border-radius: 12px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .action-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .action-btn.primary {
      background: linear-gradient(135deg, #ffd700, #ff6b9d);
      color: white;
      box-shadow: 0 4px 15px rgba(255, 107, 157, 0.3);
    }

    .action-btn.primary:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(255, 107, 157, 0.4);
    }

    .action-btn.secondary {
      background: var(--surface-color, #f8fafc);
      color: var(--text-primary, #1f2937);
      border: 2px solid var(--primary-color, #ec4899);
    }

    .action-btn.secondary:hover:not(:disabled) {
      background: var(--primary-color, #ec4899);
      color: white;
    }

    .action-btn.tertiary {
      background: transparent;
      color: var(--text-secondary, #6b7280);
      border: 1px solid var(--border-color, #e5e7eb);
    }

    .action-btn.tertiary:hover:not(:disabled) {
      background: var(--surface-color, #f8fafc);
    }

    .btn-icon {
      font-size: 1.2rem;
    }

    .connection-insights {
      margin: 2rem 0 1rem 0;
      padding: 1.5rem;
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 107, 157, 0.1));
      border-radius: 16px;
    }

    .insights-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary, #1f2937);
      margin: 0 0 1rem 0;
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
      font-size: 0.9rem;
      color: var(--text-primary, #1f2937);
    }

    .insight-icon {
      font-size: 1.2rem;
      flex-shrink: 0;
    }

    .close-btn {
      position: absolute;
      top: 1rem;
      right: 1rem;
      width: 40px;
      height: 40px;
      border: none;
      background: var(--surface-color, #f8fafc);
      border-radius: 50%;
      font-size: 1.5rem;
      color: var(--text-secondary, #6b7280);
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .close-btn:hover {
      background: var(--border-color, #e5e7eb);
      transform: scale(1.1);
    }

    /* Celebration type variations */
    .good-match .celebration-title {
      background: linear-gradient(135deg, #34d399, #10b981);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .great-match .celebration-title {
      background: linear-gradient(135deg, #ffd700, #ff6b9d);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .perfect-match .celebration-title {
      background: linear-gradient(135deg, #ffd700, #ff6b9d, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    /* Animations */
    @keyframes confetti-fall {
      0% { transform: translateY(-100vh) rotate(0deg); }
      100% { transform: translateY(100vh) rotate(720deg); }
    }

    @keyframes sparkle-twinkle {
      0%, 100% { opacity: 0; transform: scale(0); }
      50% { opacity: 1; transform: scale(1); }
    }

    @keyframes heart-float {
      0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
      10% { opacity: 1; }
      90% { opacity: 1; }
      100% { transform: translateY(-20px) rotate(360deg); opacity: 0; }
    }

    @keyframes title-glow {
      0% { filter: brightness(1); }
      100% { filter: brightness(1.2); }
    }

    @keyframes subtitle-fade-in {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes connection-highlight {
      0%, 100% { border-color: var(--primary-color, #ec4899); }
      50% { border-color: #ffd700; }
    }

    @keyframes highlight-slide-in {
      from { opacity: 0; transform: translateX(-20px); }
      to { opacity: 1; transform: translateX(0); }
    }

    @keyframes bar-fill {
      from { width: 0%; }
      to { width: var(--target-width, 100%); }
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
      .celebration-overlay {
        padding: 0.5rem;
      }

      .celebration-content {
        padding: 1.5rem;
      }

      .celebration-title {
        font-size: 1.6rem;
      }

      .celebration-subtitle {
        font-size: 1rem;
      }

      .action-btn {
        padding: 0.875rem 1.25rem;
        font-size: 0.95rem;
      }

      .highlights-grid {
        gap: 0.5rem;
      }

      .highlight-item {
        padding: 0.75rem;
        gap: 0.75rem;
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .confetti-piece, .sparkle, .floating-heart,
      .celebration-title, .soul-connection-display,
      .highlight-fill, .action-btn {
        animation: none !important;
      }
    }

    /* Dark theme */
    .dark-theme .celebration-container {
      background: var(--background-color, #111827);
    }

    .dark-theme .soul-connection-display,
    .dark-theme .highlight-item,
    .dark-theme .connection-insights {
      background: var(--surface-color, #1f2937);
    }
  `]
})
export class MatchCelebrationComponent implements OnInit, OnDestroy {
  @Input() isActive: boolean = false;
  @Input() compatibilityScore: number = 85;
  @Input() leftSoul: any = { type: 'primary', state: 'matched', energy: 5, label: 'You' };
  @Input() rightSoul: any = { type: 'secondary', state: 'matched', energy: 5, label: 'Match' };
  @Input() matchData: any = {};
  @Input() showConfetti: boolean = true;
  @Input() showSparkles: boolean = true;
  @Input() showHearts: boolean = true;
  @Input() showHighlights: boolean = true;
  @Input() showInsights: boolean = true;

  @Output() startConversation = new EventEmitter<void>();
  @Output() viewProfile = new EventEmitter<void>();
  @Output() dismiss = new EventEmitter<void>();

  isProcessing: boolean = false;
  confettiParticles: any[] = [];
  sparkleParticles: any[] = [];
  heartParticles: any[] = [];
  compatibilityHighlights: any[] = [];
  connectionInsights: any[] = [];

  private animationFrame?: number;

  get celebrationType(): string {
    if (this.compatibilityScore >= 95) return 'perfect-match';
    if (this.compatibilityScore >= 80) return 'great-match';
    return 'good-match';
  }

  get celebrationTitle(): string {
    if (this.compatibilityScore >= 95) return 'Perfect Soul Match! 💫';
    if (this.compatibilityScore >= 85) return 'Exceptional Connection! ✨';
    if (this.compatibilityScore >= 75) return 'Strong Soul Bond! 💖';
    return 'Beautiful Match! 🌟';
  }

  get celebrationSubtitle(): string {
    if (this.compatibilityScore >= 95) return 'The stars have aligned for an extraordinary connection';
    if (this.compatibilityScore >= 85) return 'Your souls resonate on multiple levels';
    if (this.compatibilityScore >= 75) return 'Deep compatibility discovered across core values';
    return 'Meaningful connections await your exploration';
  }

  get connectionMessage(): string {
    return `${this.compatibilityScore}% Soul Compatibility`;
  }

  ngOnInit() {
    if (this.isActive) {
      this.startCelebration();
    }
  }

  ngOnDestroy() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
  }

  private startCelebration() {
    this.generateParticles();
    this.generateHighlights();
    this.generateInsights();
    this.startParticleAnimation();
  }

  private generateParticles() {
    // Generate confetti
    this.confettiParticles = [];
    if (this.showConfetti) {
      const colors = ['#ffd700', '#ff6b9d', '#c084fc', '#34d399', '#60a5fa'];
      for (let i = 0; i < 30; i++) {
        this.confettiParticles.push({
          id: i,
          x: Math.random() * 100,
          delay: Math.random() * 3,
          duration: 3 + Math.random() * 2,
          color: colors[Math.floor(Math.random() * colors.length)]
        });
      }
    }

    // Generate sparkles
    this.sparkleParticles = [];
    if (this.showSparkles) {
      for (let i = 0; i < 15; i++) {
        this.sparkleParticles.push({
          id: i,
          x: Math.random() * 100,
          y: Math.random() * 100,
          delay: Math.random() * 2
        });
      }
    }

    // Generate hearts for high compatibility
    this.heartParticles = [];
    if (this.showHearts && this.compatibilityScore >= 80) {
      const heartEmojis = ['💖', '💕', '💗', '💘', '❤️'];
      for (let i = 0; i < 10; i++) {
        this.heartParticles.push({
          id: i,
          x: Math.random() * 100,
          delay: Math.random() * 4,
          duration: 4 + Math.random() * 2,
          emoji: heartEmojis[Math.floor(Math.random() * heartEmojis.length)]
        });
      }
    }
  }

  private generateHighlights() {
    this.compatibilityHighlights = [];
    if (!this.showHighlights) return;

    // Mock compatibility data - in real app, this would come from matchData
    const highlights = [
      { label: 'Core Values', score: 92, icon: '💎', color: '#ffd700' },
      { label: 'Life Goals', score: 88, icon: '🎯', color: '#ff6b9d' },
      { label: 'Communication', score: 85, icon: '💬', color: '#c084fc' }
    ].filter(h => h.score >= 80);

    this.compatibilityHighlights = highlights.map(h => ({
      ...h,
      level: h.score >= 95 ? 'perfect' : h.score >= 90 ? 'excellent' : 'high'
    }));
  }

  private generateInsights() {
    this.connectionInsights = [];
    if (!this.showInsights) return;

    const insights = [
      { icon: '🌟', text: 'You both value deep, meaningful conversations over small talk' },
      { icon: '🎭', text: 'Similar sense of humor creates natural chemistry' },
      { icon: '🌱', text: 'Shared growth mindset suggests lasting compatibility' },
      { icon: '💫', text: 'Both prioritize authenticity in relationships' }
    ];

    // Select 2-3 random insights
    const selectedInsights = insights.sort(() => 0.5 - Math.random()).slice(0, 3);
    this.connectionInsights = selectedInsights;
  }

  private startParticleAnimation() {
    let lastTime = 0;
    const animate = (currentTime: number) => {
      if (currentTime - lastTime > 5000) { // Regenerate every 5 seconds
        this.generateParticles();
        lastTime = currentTime;
      }
      this.animationFrame = requestAnimationFrame(animate);
    };
    animate(0);
  }

  onStartConversation() {
    this.isProcessing = true;
    this.startConversation.emit();
    setTimeout(() => {
      this.isProcessing = false;
      this.onDismiss();
    }, 1000);
  }

  onViewProfile() {
    this.isProcessing = true;
    this.viewProfile.emit();
    setTimeout(() => {
      this.isProcessing = false;
    }, 1000);
  }

  onDismiss() {
    this.dismiss.emit();
  }

  onOverlayClick() {
    // Close on overlay click, but not on content click
    this.onDismiss();
  }

  trackConfetti(index: number, item: any): any {
    return item.id;
  }

  trackSparkle(index: number, item: any): any {
    return item.id;
  }

  trackHeart(index: number, item: any): any {
    return item.id;
  }

  trackHighlight(index: number, item: any): any {
    return item.label;
  }

  trackInsight(index: number, item: any): any {
    return item.text;
  }
}