import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-soul-loading',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div 
      class="soul-loading-container" 
      [ngClass]="[size, variant]"
      role="status"
      [attr.aria-label]="getLoadingAriaLabel()"
      aria-live="polite">
      
      <div class="loading-content">
        <!-- Soul Energy Orb Animation -->
        <div class="soul-energy-orb">
          <svg 
            class="energy-svg" 
            [attr.width]="orbSize" 
            [attr.height]="orbSize" 
            viewBox="0 0 200 200"
            aria-hidden="true">
            
            <defs>
              <!-- Soul energy gradient -->
              <radialGradient id="soul-energy-gradient" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>
                <stop offset="30%" stop-color="#ffd700" stop-opacity="0.9"/>
                <stop offset="60%" stop-color="#ff6b9d" stop-opacity="0.7"/>
                <stop offset="100%" stop-color="#c084fc" stop-opacity="0.3"/>
              </radialGradient>
              
              <!-- Energy ring gradient -->
              <linearGradient id="ring-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#60a5fa" stop-opacity="0.8"/>
                <stop offset="50%" stop-color="#34d399" stop-opacity="0.6"/>
                <stop offset="100%" stop-color="#fbbf24" stop-opacity="0.4"/>
              </linearGradient>
              
              <!-- Glow filter -->
              <filter id="soul-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge> 
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            <!-- Background aura -->
            <circle 
              cx="100" cy="100" r="80"
              fill="url(#soul-energy-gradient)"
              class="soul-aura"
              filter="url(#soul-glow)">
            </circle>
            
            <!-- Energy rings -->
            <circle 
              cx="100" cy="100" r="60"
              fill="none" 
              stroke="url(#ring-gradient)"
              stroke-width="3"
              class="energy-ring ring-1">
            </circle>
            
            <circle 
              cx="100" cy="100" r="40"
              fill="none" 
              stroke="url(#ring-gradient)"
              stroke-width="2"
              class="energy-ring ring-2">
            </circle>
            
            <circle 
              cx="100" cy="100" r="20"
              fill="none" 
              stroke="url(#ring-gradient)"
              stroke-width="1"
              class="energy-ring ring-3">
            </circle>
            
            <!-- Central core -->
            <circle 
              cx="100" cy="100" r="12"
              fill="#ffffff"
              class="soul-core"
              filter="url(#soul-glow)">
            </circle>
            
            <!-- Floating energy particles -->
            <g class="energy-particles">
              <circle cx="130" cy="70" r="2" fill="#ffd700" class="particle particle-1"/>
              <circle cx="70" cy="130" r="1.5" fill="#ff6b9d" class="particle particle-2"/>
              <circle cx="160" cy="140" r="1" fill="#60a5fa" class="particle particle-3"/>
              <circle cx="40" cy="60" r="2.5" fill="#34d399" class="particle particle-4"/>
              <circle cx="140" cy="160" r="1.8" fill="#c084fc" class="particle particle-5"/>
              <circle cx="60" cy="40" r="1.2" fill="#fbbf24" class="particle particle-6"/>
            </g>
          </svg>
        </div>
        
        <!-- Loading Message -->
        <div class="loading-message" *ngIf="showMessage">
          <h3 class="loading-title">{{ getLoadingTitle() }}</h3>
          <p class="loading-subtitle" *ngIf="subtitle">{{ subtitle }}</p>
          
          <!-- Progress indicator dots -->
          <div class="progress-dots" *ngIf="showProgress">
            <span 
              class="dot" 
              *ngFor="let dot of progressDots; let i = index"
              [class.active]="i <= currentProgress">
            </span>
          </div>
        </div>
      </div>
      
      <!-- Soul energy waves -->
      <div class="energy-waves" *ngIf="variant === 'immersive'">
        <div class="wave wave-1"></div>
        <div class="wave wave-2"></div>
        <div class="wave wave-3"></div>
      </div>
    </div>
  `,
  styles: [`
    .soul-loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 200px;
      padding: 2rem;
      position: relative;
      overflow: hidden;
    }
    
    .loading-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      z-index: 2;
      position: relative;
    }
    
    /* Soul Energy Orb */
    .soul-energy-orb {
      margin-bottom: 2rem;
      position: relative;
    }
    
    .energy-svg {
      filter: drop-shadow(0 8px 24px rgba(255, 107, 157, 0.3));
    }
    
    /* Size variants */
    .small .energy-svg { width: 120px; height: 120px; }
    .medium .energy-svg { width: 160px; height: 160px; }
    .large .energy-svg { width: 200px; height: 200px; }
    
    /* Soul Energy Animations */
    .soul-aura {
      animation: soul-pulse 3s ease-in-out infinite;
      transform-origin: center;
    }
    
    .soul-core {
      animation: core-breathe 2s ease-in-out infinite;
      transform-origin: center;
    }
    
    .energy-ring {
      animation-duration: 4s;
      animation-timing-function: linear;
      animation-iteration-count: infinite;
      transform-origin: center;
      stroke-dasharray: 20 10;
    }
    
    .ring-1 {
      animation-name: ring-rotate;
      animation-delay: 0s;
    }
    
    .ring-2 {
      animation-name: ring-rotate-reverse;
      animation-delay: 0.5s;
    }
    
    .ring-3 {
      animation-name: ring-rotate;
      animation-delay: 1s;
    }
    
    /* Energy Particles */
    .energy-particles .particle {
      animation: particle-orbit 6s ease-in-out infinite;
      transform-origin: 100px 100px;
    }
    
    .particle-1 { animation-delay: 0s; }
    .particle-2 { animation-delay: 1s; }
    .particle-3 { animation-delay: 2s; }
    .particle-4 { animation-delay: 3s; }
    .particle-5 { animation-delay: 4s; }
    .particle-6 { animation-delay: 5s; }
    
    /* Loading Message */
    .loading-message {
      max-width: 400px;
    }
    
    .loading-title {
      color: var(--text-primary);
      font-size: 1.5rem;
      font-weight: 600;
      margin: 0 0 0.5rem 0;
      background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      animation: text-shimmer 3s ease-in-out infinite;
    }
    
    .loading-subtitle {
      color: var(--text-secondary);
      font-size: 1rem;
      margin: 0 0 1.5rem 0;
      line-height: 1.5;
    }
    
    /* Progress Dots */
    .progress-dots {
      display: flex;
      gap: 0.5rem;
      justify-content: center;
      margin-top: 1rem;
    }
    
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--surface-secondary);
      transition: all 0.3s ease;
      
      &.active {
        background: var(--primary-color);
        transform: scale(1.2);
        box-shadow: 0 0 12px rgba(255, 107, 157, 0.6);
      }
    }
    
    /* Energy Waves for Immersive Variant */
    .energy-waves {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 1;
      pointer-events: none;
    }
    
    .wave {
      position: absolute;
      border-radius: 50%;
      border: 2px solid;
      animation: wave-expand 4s ease-out infinite;
      opacity: 0;
    }
    
    .wave-1 {
      border-color: rgba(255, 215, 0, 0.3);
      animation-delay: 0s;
    }
    
    .wave-2 {
      border-color: rgba(255, 107, 157, 0.3);
      animation-delay: 1.3s;
    }
    
    .wave-3 {
      border-color: rgba(96, 165, 250, 0.3);
      animation-delay: 2.6s;
    }
    
    /* Keyframe Animations */
    @keyframes soul-pulse {
      0%, 100% { 
        transform: scale(1); 
        opacity: 0.8; 
      }
      50% { 
        transform: scale(1.1); 
        opacity: 1; 
      }
    }
    
    @keyframes core-breathe {
      0%, 100% { 
        transform: scale(1); 
        opacity: 1; 
      }
      50% { 
        transform: scale(1.3); 
        opacity: 0.8; 
      }
    }
    
    @keyframes ring-rotate {
      0% { 
        transform: rotate(0deg); 
        stroke-dashoffset: 0; 
      }
      100% { 
        transform: rotate(360deg); 
        stroke-dashoffset: 100; 
      }
    }
    
    @keyframes ring-rotate-reverse {
      0% { 
        transform: rotate(360deg); 
        stroke-dashoffset: 100; 
      }
      100% { 
        transform: rotate(0deg); 
        stroke-dashoffset: 0; 
      }
    }
    
    @keyframes particle-orbit {
      0% { 
        transform: rotate(0deg) translateX(60px) rotate(0deg); 
        opacity: 0; 
      }
      10% { opacity: 1; }
      90% { opacity: 1; }
      100% { 
        transform: rotate(360deg) translateX(60px) rotate(-360deg); 
        opacity: 0; 
      }
    }
    
    @keyframes text-shimmer {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.8; }
    }
    
    @keyframes wave-expand {
      0% {
        width: 0;
        height: 0;
        top: 50%;
        left: 50%;
        opacity: 0;
      }
      10% {
        opacity: 0.8;
      }
      50% {
        opacity: 0.4;
      }
      100% {
        width: 400px;
        height: 400px;
        top: calc(50% - 200px);
        left: calc(50% - 200px);
        opacity: 0;
      }
    }
    
    /* Variant Styles */
    .minimal {
      min-height: 120px;
      padding: 1rem;
      
      .loading-message {
        margin-top: 1rem;
      }
      
      .loading-title {
        font-size: 1.2rem;
      }
    }
    
    .standard {
      min-height: 200px;
      padding: 1.5rem;
    }
    
    .immersive {
      min-height: 300px;
      padding: 3rem;
      background: radial-gradient(circle at center, rgba(255, 107, 157, 0.05) 0%, transparent 70%);
      
      .loading-title {
        font-size: 1.8rem;
      }
    }
    
    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .soul-aura,
      .soul-core,
      .energy-ring,
      .particle,
      .wave {
        animation: none !important;
      }
      
      .loading-title {
        animation: none !important;
      }
    }
    
    /* Dark theme adaptation */
    .dark-theme {
      .loading-title {
        color: var(--text-primary);
      }
      
      .loading-subtitle {
        color: var(--text-secondary);
      }
      
      .dot {
        background: var(--surface-tertiary);
        
        &.active {
          background: var(--primary-color);
        }
      }
    }
    
    /* Mobile optimizations */
    @media (max-width: 768px) {
      .soul-loading-container {
        padding: 1rem;
        min-height: 160px;
      }
      
      .small .energy-svg { width: 100px; height: 100px; }
      .medium .energy-svg { width: 130px; height: 130px; }
      .large .energy-svg { width: 160px; height: 160px; }
      
      .loading-title {
        font-size: 1.3rem;
      }
      
      .loading-subtitle {
        font-size: 0.9rem;
      }
      
      .immersive {
        min-height: 240px;
        padding: 2rem;
      }
    }
  `]
})
export class SoulLoadingComponent implements OnInit {
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() variant: 'minimal' | 'standard' | 'immersive' = 'standard';
  @Input() title?: string;
  @Input() subtitle?: string;
  @Input() showMessage: boolean = true;
  @Input() showProgress: boolean = false;
  @Input() progressSteps: number = 3;
  @Input() currentProgress: number = 0;
  
  progressDots: number[] = [];

  get orbSize(): number {
    const sizes = { small: 120, medium: 160, large: 200 };
    return sizes[this.size];
  }

  ngOnInit() {
    if (this.showProgress) {
      this.progressDots = Array(this.progressSteps).fill(0).map((_, i) => i);
    }
  }

  getLoadingTitle(): string {
    if (this.title) {
      return this.title;
    }

    const titles = {
      minimal: 'Loading...',
      standard: 'Connecting souls...',
      immersive: 'Discovering your soul connections...'
    };

    return titles[this.variant];
  }

  getLoadingAriaLabel(): string {
    const title = this.getLoadingTitle();
    const progressInfo = this.showProgress 
      ? ` Step ${this.currentProgress + 1} of ${this.progressSteps}.` 
      : '';
    
    return `${title}${progressInfo} Please wait while we prepare your experience.`;
  }

  /**
   * Update progress for multi-step loading
   */
  updateProgress(step: number): void {
    this.currentProgress = Math.min(step, this.progressSteps - 1);
  }

  /**
   * Set custom loading message
   */
  setMessage(title: string, subtitle?: string): void {
    this.title = title;
    this.subtitle = subtitle;
  }

  /**
   * Complete the loading animation
   */
  complete(): void {
    if (this.showProgress) {
      this.currentProgress = this.progressSteps - 1;
    }
  }
}