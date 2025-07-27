import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, state, style, animate, transition, keyframes } from '@angular/animations';
import { Observable, Subscription, timer } from 'rxjs';
import { takeWhile } from 'rxjs/operators';

export interface TypingUser {
  id: string;
  name: string;
  avatar?: string;
  connectionStage?: 'soul_discovery' | 'revelation_sharing' | 'photo_reveal' | 'deeper_connection';
  emotionalState?: 'contemplative' | 'romantic' | 'energetic' | 'peaceful' | 'sophisticated';
  compatibilityScore?: number;
}

@Component({
  selector: 'app-typing-indicator',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div 
      class="typing-indicator" 
      *ngIf="isVisible"
      [@fadeInOut]="isVisible ? 'visible' : 'hidden'"
      [attr.aria-live]="ariaLive"
      [attr.aria-label]="getAriaLabel()">
      
      <div class="typing-content">
        <!-- User Avatar(s) -->
        <div class="typing-avatars">
          <div 
            *ngFor="let user of typingUsers; trackBy: trackUser; let i = index"
            class="typing-avatar"
            [style.z-index]="typingUsers.length - i"
            [style.transform]="getAvatarTransform(i)"
            [@avatarPulse]="'pulse'">
            
            <div class="avatar-circle" [style.background]="getAvatarGradient(user.id)">
              {{ user.name.charAt(0).toUpperCase() }}
            </div>
            
            <!-- Online indicator -->
            <div class="online-dot" [@onlinePulse]="'active'"></div>
          </div>
        </div>

        <!-- Typing Animation -->
        <div class="typing-animation">
          <div class="typing-bubble" [@bubbleAnimation]="'typing'">
            <div class="typing-dots">
              <div 
                *ngFor="let dot of dots; let i = index"
                class="typing-dot"
                [style.animation-delay]="getDotDelay(i)"
                [@dotBounce]="'bounce'">
              </div>
            </div>
          </div>
        </div>

        <!-- Soul Typing Text -->
        <div class="typing-text" [@textFade]="'visible'">
          <span class="typing-label">{{ getSoulTypingText() }}</span>
          <span class="typing-ellipsis" [@ellipsisAnimation]="'animate'">{{ getTypingEllipsis() }}</span>
          <div class="connection-energy" *ngIf="showConnectionEnergy()" [@energyPulse]="'pulse'">
            ✨
          </div>
        </div>

        <!-- Emotional State Indicator -->
        <div class="emotional-state" *ngIf="getEmotionalState()" [@emotionalGlow]="'glow'">
          <span class="state-emoji">{{ getEmotionalEmoji() }}</span>
          <span class="state-label">{{ getEmotionalState() }}</span>
        </div>
      </div>

      <!-- Emotional Energy Flow -->
      <div class="energy-flow" *ngIf="showEnergyFlow">
        <div 
          *ngFor="let particle of energyParticles; let i = index"
          class="energy-particle"
          [style.animation-delay]="getParticleDelay(i)"
          [@energyFlow]="'flow'">
        </div>
      </div>
    </div>
  `,
  styles: [`
    .typing-indicator {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 20px 20px 4px 20px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
      margin: 0.5rem 0;
      position: relative;
      backdrop-filter: blur(8px);
      border: 1px solid rgba(147, 51, 234, 0.1);
      max-width: 280px;
    }

    .typing-content {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      width: 100%;
    }

    /* Avatar Styling */
    .typing-avatars {
      position: relative;
      display: flex;
      align-items: center;
    }

    .typing-avatar {
      position: relative;
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .typing-avatar:not(:first-child) {
      margin-left: -8px;
    }

    .avatar-circle {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 600;
      font-size: 0.9rem;
      border: 2px solid white;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      position: relative;
    }

    .online-dot {
      position: absolute;
      bottom: -1px;
      right: -1px;
      width: 10px;
      height: 10px;
      background: var(--trust-forest-500, #22c55e);
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    /* Typing Animation */
    .typing-animation {
      display: flex;
      align-items: center;
    }

    .typing-bubble {
      background: linear-gradient(135deg, 
        var(--soul-purple-100, #f3e8ff) 0%, 
        var(--emotion-rose-100, #ffe4e6) 100%);
      border-radius: 12px;
      padding: 0.5rem 0.75rem;
      position: relative;
    }

    .typing-dots {
      display: flex;
      gap: 0.25rem;
      align-items: center;
    }

    .typing-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--soul-purple-500, #a855f7);
      animation: typing-bounce 1.4s ease-in-out infinite;
    }

    /* Soul Typing Text */
    .typing-text {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      color: var(--text-secondary, #6b7280);
      font-size: 0.85rem;
      position: relative;
    }

    .typing-label {
      font-weight: 500;
      color: var(--soul-purple-600, #9333ea);
      background: linear-gradient(135deg, 
        var(--soul-purple-600, #9333ea) 0%, 
        var(--emotion-rose-600, #e11d48) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .typing-ellipsis {
      color: var(--soul-purple-400, #c084fc);
      font-weight: bold;
      font-size: 1.1rem;
    }

    .connection-energy {
      font-size: 0.9rem;
      margin-left: 0.25rem;
      opacity: 0.8;
    }

    /* Emotional State Indicator */
    .emotional-state {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      margin-top: 0.25rem;
      padding: 0.25rem 0.5rem;
      background: rgba(147, 51, 234, 0.1);
      border-radius: 12px;
      border: 1px solid rgba(147, 51, 234, 0.2);
    }

    .state-emoji {
      font-size: 0.8rem;
    }

    .state-label {
      font-size: 0.7rem;
      color: var(--soul-purple-700, #7c3aed);
      font-weight: 500;
      text-transform: capitalize;
    }

    /* Energy Flow Effects */
    .energy-flow {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      pointer-events: none;
      overflow: hidden;
      border-radius: 20px 20px 4px 20px;
    }

    .energy-particle {
      position: absolute;
      width: 4px;
      height: 4px;
      background: var(--soul-purple-400, #c084fc);
      border-radius: 50%;
      opacity: 0.6;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .typing-indicator {
        max-width: 240px;
        padding: 0.5rem 0.75rem;
        gap: 0.5rem;
      }

      .typing-content {
        gap: 0.5rem;
      }

      .avatar-circle {
        width: 28px;
        height: 28px;
        font-size: 0.8rem;
      }

      .typing-text {
        font-size: 0.8rem;
      }
    }

    /* Dark Theme Support */
    .dark-theme .typing-indicator {
      background: rgba(31, 41, 55, 0.95);
      border-color: rgba(147, 51, 234, 0.2);
    }

    .dark-theme .typing-bubble {
      background: linear-gradient(135deg, 
        rgba(147, 51, 234, 0.2) 0%, 
        rgba(244, 63, 94, 0.2) 100%);
    }

    .dark-theme .typing-text {
      color: var(--text-secondary-dark, #d1d5db);
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .typing-indicator,
      .typing-dot,
      .energy-particle {
        animation: none !important;
      }

      .typing-bubble {
        background: var(--soul-purple-100, #f3e8ff);
      }
    }

    /* Keyframe Animations */
    @keyframes typing-bounce {
      0%, 80%, 100% {
        transform: scale(1) translateY(0);
        opacity: 0.7;
      }
      40% {
        transform: scale(1.2) translateY(-4px);
        opacity: 1;
      }
    }

    @keyframes energy-float {
      0% {
        transform: translateX(-100%) translateY(50%);
        opacity: 0;
      }
      20% {
        opacity: 0.6;
      }
      80% {
        opacity: 0.6;
      }
      100% {
        transform: translateX(200%) translateY(-50%);
        opacity: 0;
      }
    }
  `],
  animations: [
    trigger('fadeInOut', [
      state('visible', style({ opacity: 1, transform: 'translateY(0)' })),
      state('hidden', style({ opacity: 0, transform: 'translateY(10px)' })),
      transition('hidden => visible', animate('300ms cubic-bezier(0.4, 0, 0.2, 1)')),
      transition('visible => hidden', animate('200ms ease-in'))
    ]),
    trigger('bubbleAnimation', [
      state('typing', style({ transform: 'scale(1)' })),
      transition('* => typing', [
        animate('600ms ease-in-out', keyframes([
          style({ transform: 'scale(0.95)', offset: 0 }),
          style({ transform: 'scale(1.02)', offset: 0.5 }),
          style({ transform: 'scale(1)', offset: 1 })
        ]))
      ])
    ]),
    trigger('dotBounce', [
      state('bounce', style({ transform: 'scale(1)' })),
      transition('* => bounce', [
        animate('1.4s ease-in-out infinite', keyframes([
          style({ transform: 'scale(1) translateY(0)', opacity: 0.7, offset: 0 }),
          style({ transform: 'scale(1.2) translateY(-4px)', opacity: 1, offset: 0.4 }),
          style({ transform: 'scale(1) translateY(0)', opacity: 0.7, offset: 0.8 }),
          style({ transform: 'scale(1) translateY(0)', opacity: 0.7, offset: 1 })
        ]))
      ])
    ]),
    trigger('avatarPulse', [
      state('pulse', style({ transform: 'scale(1)' })),
      transition('* => pulse', [
        animate('2s ease-in-out infinite', keyframes([
          style({ transform: 'scale(1)', offset: 0 }),
          style({ transform: 'scale(1.05)', offset: 0.5 }),
          style({ transform: 'scale(1)', offset: 1 })
        ]))
      ])
    ]),
    trigger('onlinePulse', [
      state('active', style({ opacity: 1 })),
      transition('* => active', [
        animate('2s ease-in-out infinite', keyframes([
          style({ opacity: 1, transform: 'scale(1)', offset: 0 }),
          style({ opacity: 0.7, transform: 'scale(1.2)', offset: 0.5 }),
          style({ opacity: 1, transform: 'scale(1)', offset: 1 })
        ]))
      ])
    ]),
    trigger('textFade', [
      state('visible', style({ opacity: 1 })),
      transition(':enter', [
        style({ opacity: 0, transform: 'translateX(-10px)' }),
        animate('400ms 200ms cubic-bezier(0.4, 0, 0.2, 1)', 
          style({ opacity: 1, transform: 'translateX(0)' }))
      ])
    ]),
    trigger('ellipsisAnimation', [
      state('animate', style({ opacity: 1 })),
      transition('* => animate', [
        animate('1.5s ease-in-out infinite', keyframes([
          style({ opacity: 1, offset: 0 }),
          style({ opacity: 0.3, offset: 0.33 }),
          style({ opacity: 0.6, offset: 0.66 }),
          style({ opacity: 1, offset: 1 })
        ]))
      ])
    ]),
    trigger('energyFlow', [
      state('flow', style({ opacity: 0 })),
      transition('* => flow', [
        animate('3s linear infinite', keyframes([
          style({ 
            transform: 'translateX(-100%) translateY(50%)', 
            opacity: 0, 
            offset: 0 
          }),
          style({ 
            opacity: 0.6, 
            offset: 0.2 
          }),
          style({ 
            opacity: 0.6, 
            offset: 0.8 
          }),
          style({ 
            transform: 'translateX(200%) translateY(-50%)', 
            opacity: 0, 
            offset: 1 
          })
        ]))
      ])
    ]),
    trigger('energyPulse', [
      state('pulse', style({ opacity: 1 })),
      transition('* => pulse', [
        animate('2s ease-in-out infinite', keyframes([
          style({ opacity: 0.6, transform: 'scale(1)', offset: 0 }),
          style({ opacity: 1, transform: 'scale(1.2)', offset: 0.5 }),
          style({ opacity: 0.6, transform: 'scale(1)', offset: 1 })
        ]))
      ])
    ]),
    trigger('emotionalGlow', [
      state('glow', style({ opacity: 1 })),
      transition('* => glow', [
        animate('3s ease-in-out infinite', keyframes([
          style({ 
            opacity: 0.7, 
            transform: 'scale(1)', 
            filter: 'brightness(1)', 
            offset: 0 
          }),
          style({ 
            opacity: 1, 
            transform: 'scale(1.02)', 
            filter: 'brightness(1.1)', 
            offset: 0.5 
          }),
          style({ 
            opacity: 0.7, 
            transform: 'scale(1)', 
            filter: 'brightness(1)', 
            offset: 1 
          })
        ]))
      ])
    ])
  ]
})
export class TypingIndicatorComponent implements OnInit, OnDestroy {
  @Input() typingUsers: TypingUser[] = [];
  @Input() showEnergyFlow = true;
  @Input() autoHideDelay = 0; // Auto-hide after X seconds (0 = no auto-hide)
  @Input() ariaLive: 'polite' | 'assertive' = 'polite';

  isVisible = false;
  dots = [1, 2, 3]; // For typing dots animation
  energyParticles = [1, 2, 3, 4]; // For energy flow effects
  
  private autoHideSubscription?: Subscription;

  ngOnInit(): void {
    this.updateVisibility();
  }

  ngOnDestroy(): void {
    this.autoHideSubscription?.unsubscribe();
  }

  ngOnChanges(): void {
    this.updateVisibility();
  }

  private updateVisibility(): void {
    const shouldShow = this.typingUsers.length > 0;
    
    if (shouldShow !== this.isVisible) {
      this.isVisible = shouldShow;
      
      if (shouldShow && this.autoHideDelay > 0) {
        this.startAutoHideTimer();
      } else {
        this.clearAutoHideTimer();
      }
    }
  }

  private startAutoHideTimer(): void {
    this.clearAutoHideTimer();
    
    this.autoHideSubscription = timer(this.autoHideDelay * 1000)
      .pipe(takeWhile(() => this.isVisible))
      .subscribe(() => {
        this.isVisible = false;
      });
  }

  private clearAutoHideTimer(): void {
    this.autoHideSubscription?.unsubscribe();
    this.autoHideSubscription = undefined;
  }

  getSoulTypingText(): string {
    if (this.typingUsers.length === 0) return '';
    
    const user = this.typingUsers[0];
    const connectionStage = user.connectionStage || 'soul_discovery';
    
    if (this.typingUsers.length === 1) {
      return this.getSoulTypingMessage(user.name, connectionStage);
    } else if (this.typingUsers.length === 2) {
      return `${user.name} and ${this.typingUsers[1].name}'s souls are connecting`;
    } else {
      return `${user.name} and ${this.typingUsers.length - 1} souls are sharing energy`;
    }
  }

  private getSoulTypingMessage(name: string, stage: string): string {
    switch (stage) {
      case 'soul_discovery':
        return `${name}'s soul is opening`;
      case 'revelation_sharing':
        return `${name} is sharing their essence`;
      case 'photo_reveal':
        return `${name} is preparing to reveal`;
      case 'deeper_connection':
        return `${name}'s heart is speaking`;
      default:
        return `${name}'s soul is reaching out`;
    }
  }

  getTypingEllipsis(): string {
    const stages = ['✧', '✧✧', '✧✧✧'];
    const currentStage = Math.floor(Date.now() / 500) % stages.length;
    return stages[currentStage];
  }

  showConnectionEnergy(): boolean {
    return this.typingUsers.some(user => 
      user.connectionStage === 'deeper_connection' || 
      user.compatibilityScore && user.compatibilityScore > 80
    );
  }

  getEmotionalState(): string {
    if (this.typingUsers.length === 0) return '';
    
    const user = this.typingUsers[0];
    if (!user.emotionalState) return '';
    
    const stateMap = {
      contemplative: 'deep in thought',
      romantic: 'feeling connected',
      energetic: 'full of excitement',
      peaceful: 'centered and calm',
      sophisticated: 'thoughtfully composed'
    };
    
    return stateMap[user.emotionalState] || '';
  }

  getEmotionalEmoji(): string {
    if (this.typingUsers.length === 0) return '';
    
    const user = this.typingUsers[0];
    if (!user.emotionalState) return '';
    
    const emojiMap = {
      contemplative: '🧘',
      romantic: '💕',
      energetic: '⚡',
      peaceful: '🌿',
      sophisticated: '🎭'
    };
    
    return emojiMap[user.emotionalState] || '✨';
  }

  getAriaLabel(): string {
    const typingText = this.getSoulTypingText();
    const emotionalState = this.getEmotionalState();
    const baseText = `${typingText}. Soul connection in progress.`;
    
    if (emotionalState) {
      return `${baseText} Emotional state: ${emotionalState}.`;
    }
    
    return baseText;
  }

  getAvatarGradient(userId: string): string {
    // Generate consistent gradient based on user ID
    const colors = [
      'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
      'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
      'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
      'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
      'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)'
    ];
    
    const hash = userId.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    
    return colors[Math.abs(hash) % colors.length];
  }

  getAvatarTransform(index: number): string {
    if (this.typingUsers.length === 1) return 'translateX(0)';
    
    // Stagger avatars slightly for multiple users
    const offset = index * 2;
    return `translateX(${offset}px)`;
  }

  getDotDelay(index: number): string {
    return `${index * 0.2}s`;
  }

  getParticleDelay(index: number): string {
    return `${index * 0.5}s`;
  }

  trackUser(index: number, user: TypingUser): string {
    return user.id;
  }
}