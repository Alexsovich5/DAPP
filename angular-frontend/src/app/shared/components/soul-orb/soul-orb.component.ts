import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-soul-orb',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div 
      class="soul-orb-container" 
      [ngClass]="[size, type, state]"
      role="img"
      [attr.aria-label]="getSoulOrbAriaLabel()"
      [attr.aria-describedby]="ariaDescribedBy">
      <svg 
        class="soul-orb-svg" 
        [attr.width]="svgSize" 
        [attr.height]="svgSize" 
        viewBox="0 0 120 120"
        aria-hidden="true">
        <!-- Outer aura glow -->
        <defs>
          <radialGradient [id]="'aura-gradient-' + orbId" cx="50%" cy="50%" r="50%">
            <stop offset="0%" [attr.stop-color]="auraColors.inner" stop-opacity="0.8"/>
            <stop offset="70%" [attr.stop-color]="auraColors.middle" stop-opacity="0.4"/>
            <stop offset="100%" [attr.stop-color]="auraColors.outer" stop-opacity="0.1"/>
          </radialGradient>
          
          <!-- Core gradient -->
          <radialGradient [id]="'core-gradient-' + orbId" cx="50%" cy="50%" r="50%">
            <stop offset="0%" [attr.stop-color]="coreColors.center" stop-opacity="1"/>
            <stop offset="60%" [attr.stop-color]="coreColors.middle" stop-opacity="0.9"/>
            <stop offset="100%" [attr.stop-color]="coreColors.edge" stop-opacity="0.7"/>
          </radialGradient>

          <!-- Particle gradient -->
          <radialGradient [id]="'particle-gradient-' + orbId" cx="50%" cy="50%" r="50%">
            <stop offset="0%" [attr.stop-color]="particleColor" stop-opacity="1"/>
            <stop offset="100%" [attr.stop-color]="particleColor" stop-opacity="0"/>
          </radialGradient>

          <!-- Glow filter -->
          <filter [id]="'glow-' + orbId" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge> 
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        <!-- Aura circle -->
        <circle 
          cx="60" cy="60" [attr.r]="auraRadius"
          [attr.fill]="'url(#aura-gradient-' + orbId + ')'"
          class="soul-aura"
          [class.pulsing]="isPulsing">
        </circle>

        <!-- Floating particles -->
        <g class="particles" *ngIf="showParticles">
          <circle 
            *ngFor="let particle of particles; trackBy: trackParticle"
            [attr.cx]="particle.x" 
            [attr.cy]="particle.y" 
            [attr.r]="particle.size"
            [attr.fill]="'url(#particle-gradient-' + orbId + ')'"
            class="particle"
            [style.animation-delay]="particle.delay + 's'"
            [style.animation-duration]="particle.duration + 's'">
          </circle>
        </g>

        <!-- Core orb -->
        <circle 
          cx="60" cy="60" [attr.r]="coreRadius"
          [attr.fill]="'url(#core-gradient-' + orbId + ')'"
          [attr.filter]="'url(#glow-' + orbId + ')'"
          class="soul-core"
          [class.breathing]="isBreathing">
        </circle>

        <!-- Inner sparkles -->
        <g class="sparkles" *ngIf="showSparkles">
          <circle 
            *ngFor="let sparkle of sparkles; trackBy: trackSparkle"
            [attr.cx]="sparkle.x" 
            [attr.cy]="sparkle.y" 
            [attr.r]="sparkle.size"
            [attr.fill]="sparkleColor"
            class="sparkle"
            [style.animation-delay]="sparkle.delay + 's'">
          </circle>
        </g>

        <!-- Energy rings -->
        <g class="energy-rings" *ngIf="energyLevel > 0">
          <circle 
            *ngFor="let ring of energyRings; let i = index"
            cx="60" cy="60" 
            [attr.r]="ring.radius"
            fill="none" 
            [attr.stroke]="ring.color"
            [attr.stroke-width]="ring.width"
            stroke-opacity="0.6"
            class="energy-ring"
            [style.animation-delay]="i * 0.3 + 's'">
          </circle>
        </g>
      </svg>

      <!-- Compatibility percentage overlay -->
      <div 
        class="compatibility-display" 
        *ngIf="showCompatibility && compatibilityScore > 0"
        role="status"
        [attr.aria-label]="getCompatibilityAriaLabel()"
        aria-live="polite">
        <span 
          class="compatibility-text"
          aria-hidden="true">{{compatibilityScore}}%</span>
        <span 
          class="compatibility-label"
          aria-hidden="true">Soul Match</span>
      </div>
    </div>
  `,
  styles: [`
    .soul-orb-container {
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin: 1rem;
    }

    .soul-orb-svg {
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
    }

    /* Size variants */
    .small .soul-orb-svg { width: 60px; height: 60px; }
    .medium .soul-orb-svg { width: 120px; height: 120px; }
    .large .soul-orb-svg { width: 180px; height: 180px; }
    .xlarge .soul-orb-svg { width: 240px; height: 240px; }

    /* Animations */
    .soul-aura.pulsing {
      animation: aura-pulse 3s ease-in-out infinite;
    }

    .soul-core.breathing {
      animation: core-breathe 4s ease-in-out infinite;
    }

    .particle {
      animation: particle-float 6s ease-in-out infinite;
    }

    .sparkle {
      animation: sparkle-twinkle 2s ease-in-out infinite;
    }

    .energy-ring {
      animation: energy-ripple 2s ease-out infinite;
    }

    /* Compatibility display */
    .compatibility-display {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      color: white;
      font-weight: bold;
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
      pointer-events: none;
    }

    .compatibility-text {
      display: block;
      font-size: 1.2rem;
      line-height: 1;
    }

    .compatibility-label {
      display: block;
      font-size: 0.7rem;
      opacity: 0.9;
      margin-top: 2px;
    }

    /* State variations */
    .connecting .soul-aura {
      animation: connecting-pulse 1.5s ease-in-out infinite;
    }

    .matched .soul-core {
      animation: matched-celebration 2s ease-out;
    }

    .dormant .soul-aura,
    .dormant .soul-core {
      opacity: 0.6;
      animation: dormant-slow-pulse 8s ease-in-out infinite;
    }

    /* Keyframe animations */
    @keyframes aura-pulse {
      0%, 100% { transform: scale(1); opacity: 0.6; }
      50% { transform: scale(1.1); opacity: 0.8; }
    }

    @keyframes core-breathe {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.05); }
    }

    @keyframes particle-float {
      0% { 
        transform: translateY(0) rotate(0deg); 
        opacity: 0; 
      }
      10% { opacity: 1; }
      90% { opacity: 1; }
      100% { 
        transform: translateY(-20px) rotate(360deg); 
        opacity: 0; 
      }
    }

    @keyframes sparkle-twinkle {
      0%, 100% { opacity: 0; transform: scale(0); }
      50% { opacity: 1; transform: scale(1); }
    }

    @keyframes energy-ripple {
      0% { 
        transform: scale(0.8); 
        stroke-opacity: 0.8; 
      }
      100% { 
        transform: scale(1.4); 
        stroke-opacity: 0; 
      }
    }

    @keyframes connecting-pulse {
      0%, 100% { opacity: 0.4; transform: scale(0.95); }
      50% { opacity: 1; transform: scale(1.05); }
    }

    @keyframes matched-celebration {
      0% { transform: scale(1); }
      25% { transform: scale(1.2) rotate(5deg); }
      50% { transform: scale(1.1) rotate(-3deg); }
      75% { transform: scale(1.15) rotate(2deg); }
      100% { transform: scale(1) rotate(0deg); }
    }

    @keyframes dormant-slow-pulse {
      0%, 100% { opacity: 0.3; }
      50% { opacity: 0.6; }
    }

    /* Dark theme adaptations */
    .dark-theme .compatibility-display {
      color: var(--text-primary, #f9fafb);
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .soul-aura, .soul-core, .particle, .sparkle, .energy-ring {
        animation: none !important;
      }
    }

    /* Mobile optimizations */
    @media (max-width: 768px) {
      .soul-orb-container {
        margin: 0.5rem;
      }
      
      .compatibility-text {
        font-size: 1rem;
      }
      
      .compatibility-label {
        font-size: 0.6rem;
      }
    }
  `]
})
export class SoulOrbComponent implements OnInit, OnDestroy {
  @Input() type: 'primary' | 'secondary' | 'neutral' = 'primary';
  @Input() size: 'small' | 'medium' | 'large' | 'xlarge' = 'medium';
  @Input() state: 'active' | 'connecting' | 'matched' | 'dormant' = 'active';
  @Input() energyLevel: number = 3; // 0-5 scale
  @Input() compatibilityScore: number = 0; // 0-100
  @Input() showCompatibility: boolean = false;
  @Input() showParticles: boolean = true;
  @Input() showSparkles: boolean = true;
  
  // Accessibility inputs
  @Input() ariaLabel?: string;
  @Input() ariaDescribedBy?: string;

  orbId: string = Math.random().toString(36).substr(2, 9);
  particles: any[] = [];
  sparkles: any[] = [];
  energyRings: any[] = [];
  
  private animationFrame?: number;

  get svgSize(): number {
    const sizes = { small: 60, medium: 120, large: 180, xlarge: 240 };
    return sizes[this.size];
  }

  get auraRadius(): number {
    const base = this.svgSize * 0.4;
    return base + (this.energyLevel * 3);
  }

  get coreRadius(): number {
    return this.svgSize * 0.25;
  }

  get isPulsing(): boolean {
    return this.state === 'active' || this.state === 'connecting';
  }

  get isBreathing(): boolean {
    return this.state === 'active' || this.state === 'matched';
  }

  get auraColors() {
    const colorSets = {
      primary: {
        inner: '#ffd700',
        middle: '#ff6b9d',
        outer: '#c084fc'
      },
      secondary: {
        inner: '#60a5fa',
        middle: '#34d399',
        outer: '#fbbf24'
      },
      neutral: {
        inner: '#e2e8f0',
        middle: '#cbd5e1',
        outer: '#94a3b8'
      }
    };
    return colorSets[this.type];
  }

  get coreColors() {
    const colorSets = {
      primary: {
        center: '#ffffff',
        middle: '#ffd700',
        edge: '#ff6b9d'
      },
      secondary: {
        center: '#ffffff',
        middle: '#60a5fa',
        edge: '#34d399'
      },
      neutral: {
        center: '#ffffff',
        middle: '#e2e8f0',
        edge: '#94a3b8'
      }
    };
    return colorSets[this.type];
  }

  get particleColor(): string {
    const colors = {
      primary: '#ffd700',
      secondary: '#60a5fa',
      neutral: '#cbd5e1'
    };
    return colors[this.type];
  }

  get sparkleColor(): string {
    return '#ffffff';
  }

  ngOnInit() {
    this.generateParticles();
    this.generateSparkles();
    this.generateEnergyRings();
    this.startAnimation();
  }

  ngOnDestroy() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
  }

  private generateParticles() {
    this.particles = [];
    const particleCount = this.energyLevel * 2 + 3;
    
    for (let i = 0; i < particleCount; i++) {
      this.particles.push({
        id: i,
        x: 40 + Math.random() * 40,
        y: 40 + Math.random() * 40,
        size: 1 + Math.random() * 2,
        delay: Math.random() * 3,
        duration: 4 + Math.random() * 4
      });
    }
  }

  private generateSparkles() {
    this.sparkles = [];
    const sparkleCount = Math.max(3, this.energyLevel);
    
    for (let i = 0; i < sparkleCount; i++) {
      this.sparkles.push({
        id: i,
        x: 30 + Math.random() * 60,
        y: 30 + Math.random() * 60,
        size: 0.5 + Math.random() * 1,
        delay: Math.random() * 2
      });
    }
  }

  private generateEnergyRings() {
    this.energyRings = [];
    
    for (let i = 0; i < this.energyLevel; i++) {
      this.energyRings.push({
        radius: 30 + (i * 8),
        color: this.auraColors.middle,
        width: 2 - (i * 0.2)
      });
    }
  }

  private startAnimation() {
    // Regenerate particles periodically for continuous effect
    const animate = () => {
      if (this.showParticles && Math.random() < 0.1) {
        this.generateParticles();
      }
      this.animationFrame = requestAnimationFrame(animate);
    };
    animate();
  }

  trackParticle(index: number, particle: any): any {
    return particle.id;
  }

  trackSparkle(index: number, sparkle: any): any {
    return sparkle.id;
  }

  getSoulOrbAriaLabel(): string {
    if (this.ariaLabel) {
      return this.ariaLabel;
    }

    const typeLabels = {
      primary: 'Soul energy orb',
      secondary: 'Connection energy orb', 
      neutral: 'Energy orb'
    };

    const stateLabels = {
      active: 'actively pulsing',
      connecting: 'connecting with another soul',
      matched: 'celebrating a soul connection',
      dormant: 'in peaceful dormant state'
    };

    const energyLabel = this.energyLevel > 0 ? ` with energy level ${this.energyLevel} out of 5` : '';
    const compatibilityLabel = this.showCompatibility && this.compatibilityScore > 0 
      ? ` showing ${this.compatibilityScore}% soul compatibility match` 
      : '';

    return `${typeLabels[this.type]} ${stateLabels[this.state]}${energyLabel}${compatibilityLabel}`;
  }

  getCompatibilityAriaLabel(): string {
    return `Soul compatibility match: ${this.compatibilityScore} percent`;
  }
}