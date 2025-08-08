/**
 * Soul Typing Indicator Component - Advanced Phase 3 Implementation
 * Enhanced typing indicators with soul themes and emotional context
 */
import { Component, Input, OnInit, OnDestroy, ChangeDetectionStrategy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, interval, takeUntil, animationFrameScheduler } from 'rxjs';
import { TypingUser } from '../../core/services/chat.service';

export interface SoulTypingConfig {
  theme: 'discovery' | 'revelation' | 'connection' | 'energy';
  connectionStage: 'soul_discovery' | 'revelation_sharing' | 'photo_reveal' | 'deeper_connection';
  emotionalState: 'contemplative' | 'romantic' | 'energetic' | 'peaceful' | 'sophisticated';
  connectionEnergy: 'low' | 'medium' | 'high' | 'soulmate';
  compatibilityScore: number;
  showBreathing: boolean;
  showPulse: boolean;
  showParticles: boolean;
  animationSpeed: number; // 0.5 - 2.0
}

@Component({
  selector: 'app-soul-typing-indicator',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div 
      class="soul-typing-container"
      [class]="getContainerClasses()"
      [attr.aria-label]="getAriaLabel()"
      [attr.aria-live]="isVisible ? 'polite' : 'off'"
      #container
    >
      <!-- Soul Energy Aura -->
      <div class="soul-aura" [style.--connection-energy]="connectionEnergy">
        <div class="aura-ring aura-ring-1"></div>
        <div class="aura-ring aura-ring-2"></div>
        <div class="aura-ring aura-ring-3"></div>
      </div>

      <!-- Connection Particles (for high energy connections) -->
      <div class="particle-system" *ngIf="config.showParticles">
        <div 
          class="particle" 
          *ngFor="let particle of particles; trackBy: trackParticle"
          [style.--delay]="particle.delay + 's'"
          [style.--duration]="particle.duration + 's'"
          [style.--angle]="particle.angle + 'deg'"
        ></div>
      </div>

      <!-- Main Typing Display -->
      <div class="typing-content">
        <!-- Avatar with breathing animation -->
        <div class="soul-avatar" [class.breathing]="config.showBreathing">
          <div class="avatar-circle" [style.background]="getAvatarGradient()">
            <span class="avatar-initial">{{ typingUser?.name?.charAt(0) || '?' }}</span>
          </div>
          
          <!-- Connection stage indicator -->
          <div class="stage-indicator" [attr.data-stage]="config.connectionStage">
            {{ getStageEmoji() }}
          </div>
        </div>

        <!-- Enhanced typing dots with soul theme -->
        <div class="soul-typing-dots" [attr.data-theme]="config.theme">
          <div 
            class="soul-dot" 
            *ngFor="let dot of dots; trackBy: trackDot; let i = index"
            [style.--dot-delay]="dot.delay + 's'"
            [style.--dot-scale]="dot.scale"
            [style.--dot-color]="dot.color"
            [class]="'dot-' + i + ' ' + dot.className"
          ></div>
        </div>

        <!-- Emotional context message -->
        <div class="emotional-context" [attr.data-emotion]="config.emotionalState">
          <span class="context-text">{{ getEmotionalMessage() }}</span>
          <div class="compatibility-indicator" *ngIf="config.compatibilityScore >= 70">
            <span class="compatibility-glow">{{ config.compatibilityScore }}% ✨</span>
          </div>
        </div>
      </div>

      <!-- Pulse effect overlay -->
      <div class="soul-pulse" *ngIf="config.showPulse" [style.--pulse-color]="getPulseColor()"></div>
    </div>
  `,
  styles: [`
    .soul-typing-container {
      position: relative;
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.75rem 1rem;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(102, 126, 234, 0.1);
      transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      overflow: hidden;
    }

    /* Theme-based styling */
    .theme-discovery {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(164, 176, 190, 0.08) 100%);
    }

    .theme-revelation {
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.08) 0%, rgba(255, 165, 0, 0.08) 100%);
    }

    .theme-connection {
      background: linear-gradient(135deg, rgba(232, 121, 249, 0.08) 0%, rgba(102, 126, 234, 0.08) 100%);
    }

    .theme-energy {
      background: linear-gradient(135deg, rgba(72, 187, 120, 0.08) 0%, rgba(56, 178, 172, 0.08) 100%);
    }

    /* Soul Aura System */
    .soul-aura {
      position: absolute;
      top: 50%;
      left: 0;
      transform: translateY(-50%);
      width: 60px;
      height: 60px;
      pointer-events: none;
    }

    .aura-ring {
      position: absolute;
      top: 50%;
      left: 50%;
      border-radius: 50%;
      border: 2px solid;
      transform: translate(-50%, -50%);
      opacity: 0.6;
    }

    .aura-ring-1 {
      width: 40px;
      height: 40px;
      border-color: var(--connection-energy, #667eea);
      animation: auraRing1 2s ease-in-out infinite;
    }

    .aura-ring-2 {
      width: 50px;
      height: 50px;
      border-color: var(--connection-energy, #667eea);
      animation: auraRing2 2.5s ease-in-out infinite;
      animation-delay: 0.3s;
    }

    .aura-ring-3 {
      width: 60px;
      height: 60px;
      border-color: var(--connection-energy, #667eea);
      animation: auraRing3 3s ease-in-out infinite;
      animation-delay: 0.6s;
    }

    @keyframes auraRing1 {
      0%, 100% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; }
      50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.4; }
    }

    @keyframes auraRing2 {
      0%, 100% { transform: translate(-50%, -50%) scale(0.9); opacity: 0.6; }
      50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.2; }
    }

    @keyframes auraRing3 {
      0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.4; }
      50% { transform: translate(-50%, -50%) scale(1.3); opacity: 0.1; }
    }

    /* Particle System */
    .particle-system {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      pointer-events: none;
      overflow: hidden;
    }

    .particle {
      position: absolute;
      top: 50%;
      left: 20%;
      width: 3px;
      height: 3px;
      background: radial-gradient(circle, #667eea, transparent);
      border-radius: 50%;
      animation: particleFloat var(--duration, 4s) ease-in-out infinite;
      animation-delay: var(--delay, 0s);
      transform-origin: center;
    }

    @keyframes particleFloat {
      0% {
        transform: translate(0, 0) rotate(0deg) scale(0);
        opacity: 0;
      }
      20% {
        opacity: 1;
        transform: translate(10px, -5px) rotate(90deg) scale(1);
      }
      50% {
        transform: translate(40px, -10px) rotate(180deg) scale(1.2);
      }
      80% {
        opacity: 0.8;
        transform: translate(70px, -5px) rotate(270deg) scale(0.8);
      }
      100% {
        transform: translate(100px, 0) rotate(360deg) scale(0);
        opacity: 0;
      }
    }

    /* Avatar and content */
    .typing-content {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      position: relative;
      z-index: 2;
    }

    .soul-avatar {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .soul-avatar.breathing {
      animation: soulBreathe 3s ease-in-out infinite;
    }

    @keyframes soulBreathe {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.05); }
    }

    .avatar-circle {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 600;
      font-size: 1.1rem;
      position: relative;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .stage-indicator {
      position: absolute;
      bottom: -2px;
      right: -2px;
      width: 16px;
      height: 16px;
      background: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.6rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }

    /* Enhanced typing dots */
    .soul-typing-dots {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      margin-left: 0.5rem;
    }

    .soul-dot {
      width: 6px;
      height: 6px;
      background: var(--dot-color, #667eea);
      border-radius: 50%;
      animation: soulDotPulse 1.4s ease-in-out infinite;
      animation-delay: var(--dot-delay, 0s);
      transform: scale(var(--dot-scale, 1));
      box-shadow: 0 0 10px var(--dot-color, #667eea);
    }

    .theme-revelation .soul-dot {
      background: linear-gradient(45deg, #ffd700, #ffa500);
      box-shadow: 0 0 15px #ffd700;
    }

    .theme-connection .soul-dot {
      background: linear-gradient(45deg, #e879f9, #667eea);
      box-shadow: 0 0 12px #e879f9;
    }

    .theme-energy .soul-dot {
      background: linear-gradient(45deg, #48bb78, #38b2ac);
      box-shadow: 0 0 12px #48bb78;
    }

    @keyframes soulDotPulse {
      0%, 80%, 100% {
        transform: scale(0.8);
        opacity: 0.5;
      }
      40% {
        transform: scale(1.2);
        opacity: 1;
      }
    }

    /* Emotional context */
    .emotional-context {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .context-text {
      font-size: 0.85rem;
      color: #667eea;
      font-style: italic;
      opacity: 0.8;
      animation: contextFade 2s ease-in-out infinite;
    }

    .compatibility-indicator {
      display: flex;
      align-items: center;
    }

    .compatibility-glow {
      font-size: 0.75rem;
      color: #ffd700;
      font-weight: 600;
      text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
      animation: compatibilityGlow 2s ease-in-out infinite;
    }

    @keyframes contextFade {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 1; }
    }

    @keyframes compatibilityGlow {
      0%, 100% { text-shadow: 0 0 8px rgba(255, 215, 0, 0.6); }
      50% { text-shadow: 0 0 15px rgba(255, 215, 0, 0.9); }
    }

    /* Pulse overlay */
    .soul-pulse {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: radial-gradient(circle, var(--pulse-color, rgba(102, 126, 234, 0.1)), transparent);
      border-radius: 20px;
      animation: soulPulseOverlay 3s ease-in-out infinite;
      pointer-events: none;
    }

    @keyframes soulPulseOverlay {
      0%, 100% { opacity: 0; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.05); }
    }

    /* Connection energy variants */
    .energy-low .soul-aura { --connection-energy: #a0aec0; }
    .energy-medium .soul-aura { --connection-energy: #667eea; }
    .energy-high .soul-aura { --connection-energy: #e879f9; }
    .energy-soulmate .soul-aura { --connection-energy: #ffd700; }

    /* Responsive design */
    @media (max-width: 768px) {
      .soul-typing-container {
        padding: 0.5rem 0.75rem;
        gap: 0.5rem;
      }

      .avatar-circle {
        width: 32px;
        height: 32px;
        font-size: 0.9rem;
      }

      .stage-indicator {
        width: 14px;
        height: 14px;
        font-size: 0.5rem;
      }

      .emotional-context {
        font-size: 0.8rem;
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .soul-aura *, 
      .particle,
      .soul-avatar.breathing,
      .soul-dot,
      .context-text,
      .compatibility-glow,
      .soul-pulse {
        animation: none;
      }
    }
  `]
})
export class SoulTypingIndicatorComponent implements OnInit, OnDestroy {
  @Input() typingUser: TypingUser | null = null;
  @Input() config: SoulTypingConfig = {
    theme: 'discovery',
    connectionStage: 'soul_discovery',
    emotionalState: 'contemplative',
    connectionEnergy: 'medium',
    compatibilityScore: 0,
    showBreathing: true,
    showPulse: true,
    showParticles: false,
    animationSpeed: 1.0
  };
  @Input() isVisible = true;
  
  @ViewChild('container', { static: false }) containerRef?: ElementRef<HTMLElement>;

  dots: Array<{ delay: number; scale: number; color: string; className: string }> = [];
  particles: Array<{ delay: number; duration: number; angle: number; id: number }> = [];
  
  private destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.initializeDots();
    this.initializeParticles();
    this.startAnimationLoop();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeDots(): void {
    const dotCount = this.getDotCountForTheme();
    this.dots = Array(dotCount).fill(0).map((_, i) => ({
      delay: i * 0.2,
      scale: 0.8 + Math.random() * 0.4,
      color: this.getDotColorForTheme(),
      className: this.getDotClassForEmotion()
    }));
  }

  private initializeParticles(): void {
    if (!this.config.showParticles) return;
    
    const particleCount = this.getParticleCountForEnergy();
    this.particles = Array(particleCount).fill(0).map((_, i) => ({
      delay: Math.random() * 4,
      duration: 3 + Math.random() * 2,
      angle: Math.random() * 360,
      id: i
    }));
  }

  private startAnimationLoop(): void {
    // Refresh particles periodically for dynamic effect
    interval(5000).pipe(
      takeUntil(this.destroy$)
    ).subscribe(() => {
      if (this.config.showParticles && this.config.connectionEnergy !== 'low') {
        this.initializeParticles();
      }
    });
  }

  getContainerClasses(): string {
    return `
      theme-${this.config.theme}
      stage-${this.config.connectionStage}
      emotion-${this.config.emotionalState}
      energy-${this.config.connectionEnergy}
    `.trim().replace(/\s+/g, ' ');
  }

  getAriaLabel(): string {
    const userName = this.typingUser?.name || 'Someone';
    const context = this.getEmotionalMessage();
    return `${userName} is typing... ${context}`;
  }

  getAvatarGradient(): string {
    const energyColors = {
      low: 'linear-gradient(135deg, #a0aec0, #718096)',
      medium: 'linear-gradient(135deg, #667eea, #764ba2)',
      high: 'linear-gradient(135deg, #e879f9, #667eea)',
      soulmate: 'linear-gradient(135deg, #ffd700, #f093fb)'
    };
    
    return energyColors[this.config.connectionEnergy];
  }

  getStageEmoji(): string {
    const stageEmojis = {
      soul_discovery: '🔍',
      revelation_sharing: '✨',
      photo_reveal: '📸',
      deeper_connection: '💫'
    };
    
    return stageEmojis[this.config.connectionStage];
  }

  getEmotionalMessage(): string {
    const messages = {
      contemplative: 'sharing deep thoughts...',
      romantic: 'expressing feelings...',
      energetic: 'full of excitement...',
      peaceful: 'in thoughtful reflection...',
      sophisticated: 'crafting something special...'
    };
    
    return messages[this.config.emotionalState];
  }

  getPulseColor(): string {
    const colors = {
      discovery: 'rgba(102, 126, 234, 0.1)',
      revelation: 'rgba(255, 215, 0, 0.1)',
      connection: 'rgba(232, 121, 249, 0.1)',
      energy: 'rgba(72, 187, 120, 0.1)'
    };
    
    return colors[this.config.theme];
  }

  private getDotCountForTheme(): number {
    const counts = {
      discovery: 3,
      revelation: 5,
      connection: 4,
      energy: 6
    };
    
    return counts[this.config.theme];
  }

  private getDotColorForTheme(): string {
    const colors = {
      discovery: '#667eea',
      revelation: '#ffd700',
      connection: '#e879f9',
      energy: '#48bb78'
    };
    
    return colors[this.config.theme];
  }

  private getDotClassForEmotion(): string {
    return `emotion-${this.config.emotionalState}`;
  }

  private getParticleCountForEnergy(): number {
    const counts = {
      low: 0,
      medium: 3,
      high: 6,
      soulmate: 10
    };
    
    return counts[this.config.connectionEnergy];
  }

  trackDot(index: number, dot: any): number {
    return index;
  }

  trackParticle(index: number, particle: any): number {
    return particle.id;
  }
}