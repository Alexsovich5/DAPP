import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SoulOrbComponent } from '../soul-orb/soul-orb.component';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule, SoulOrbComponent],
  template: `
    <div 
      class="empty-state-container" 
      [ngClass]="[theme, size]"
      role="region"
      [attr.aria-label]="getAriaLabel()"
      [attr.aria-describedby]="descriptionId">
      
      <!-- Animated illustration -->
      <div 
        class="empty-state-illustration"
        role="img"
        [attr.aria-label]="getIllustrationAriaLabel()"
        aria-hidden="false">
        <!-- Soul orb animation for some states -->
        <div 
          *ngIf="showSoulOrb" 
          class="soul-orb-display"
          role="img"
          aria-label="Soul energy visualization">
          <app-soul-orb
            [type]="soulOrbType"
            [size]="soulOrbSize"
            [state]="soulOrbState"
            [energyLevel]="soulOrbEnergy"
            [showParticles]="showParticles"
            [showSparkles]="showSparkles">
          </app-soul-orb>
        </div>

        <!-- SVG illustrations for different states -->
        <div 
          *ngIf="illustration" 
          class="svg-illustration"
          role="img"
          [attr.aria-label]="getIllustrationAriaLabel()">
          <svg 
            [attr.width]="illustrationSize" 
            [attr.height]="illustrationSize" 
            viewBox="0 0 200 200"
            role="img"
            [attr.aria-label]="getIllustrationAriaLabel()">
            
            <!-- Discovery illustration -->
            <g *ngIf="illustration === 'discovery'">
              <defs>
                <radialGradient id="search-gradient" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stop-color="#ffd700" stop-opacity="0.8"/>
                  <stop offset="100%" stop-color="#ff6b9d" stop-opacity="0.3"/>
                </radialGradient>
              </defs>
              <circle cx="100" cy="100" r="80" fill="url(#search-gradient)" class="search-pulse"/>
              <circle cx="100" cy="100" r="40" fill="#ffffff" stroke="#ff6b9d" stroke-width="3"/>
              <path d="M 120 120 L 140 140" stroke="#ff6b9d" stroke-width="4" stroke-linecap="round" class="search-handle"/>
              <text x="100" y="106" text-anchor="middle" font-size="24" fill="#ff6b9d" aria-hidden="true">🔍</text>
            </g>

            <!-- Conversations illustration -->
            <g *ngIf="illustration === 'conversations'">
              <defs>
                <linearGradient id="message-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#60a5fa"/>
                  <stop offset="100%" stop-color="#34d399"/>
                </linearGradient>
              </defs>
              <rect x="40" y="60" width="120" height="80" rx="20" fill="url(#message-gradient)" opacity="0.8"/>
              <rect x="60" y="40" width="120" height="80" rx="20" fill="#ffffff" stroke="#60a5fa" stroke-width="2"/>
              <line x1="80" y1="60" x2="160" y2="60" stroke="#60a5fa" stroke-width="2"/>
              <line x1="80" y1="80" x2="140" y2="80" stroke="#60a5fa" stroke-width="2"/>
              <line x1="80" y1="100" x2="120" y2="100" stroke="#60a5fa" stroke-width="2"/>
              <text x="190" y="50" text-anchor="middle" font-size="16" fill="#34d399" aria-hidden="true">💬</text>
            </g>

            <!-- Revelations illustration -->
            <g *ngIf="illustration === 'revelations'">
              <defs>
                <radialGradient id="revelation-gradient" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stop-color="#ffd700" stop-opacity="1"/>
                  <stop offset="70%" stop-color="#c084fc" stop-opacity="0.6"/>
                  <stop offset="100%" stop-color="#c084fc" stop-opacity="0.2"/>
                </radialGradient>
              </defs>
              <circle cx="100" cy="100" r="90" fill="url(#revelation-gradient)" class="revelation-glow"/>
              <path d="M 100 40 L 110 70 L 140 70 L 118 90 L 128 120 L 100 105 L 72 120 L 82 90 L 60 70 L 90 70 Z" 
                    fill="#ffd700" stroke="#ffffff" stroke-width="2" class="star-sparkle"/>
              <text x="100" y="170" text-anchor="middle" font-size="20" fill="#c084fc" aria-hidden="true">✨</text>
            </g>

            <!-- Profile illustration -->
            <g *ngIf="illustration === 'profile'">
              <defs>
                <linearGradient id="profile-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#ec4899"/>
                  <stop offset="100%" stop-color="#8b5cf6"/>
                </linearGradient>
              </defs>
              <circle cx="100" cy="80" r="35" fill="url(#profile-gradient)" opacity="0.8"/>
              <path d="M 60 140 Q 100 120 140 140 L 140 180 L 60 180 Z" fill="url(#profile-gradient)" opacity="0.8"/>
              <circle cx="100" cy="80" r="30" fill="#ffffff" stroke="#ec4899" stroke-width="3"/>
              <text x="100" y="88" text-anchor="middle" font-size="24" fill="#ec4899" aria-hidden="true">👤</text>
            </g>

          </svg>
        </div>

        <!-- Custom icon -->
        <div *ngIf="!illustration && !showSoulOrb && customIcon" class="custom-icon">
          <span [ngStyle]="{'font-size': iconSize + 'rem'}">{{customIcon}}</span>
        </div>
      </div>

      <!-- Content -->
      <div class="empty-state-content">
        <h2 
          class="empty-state-title"
          [id]="titleId">
          {{title}}
        </h2>
        <p 
          class="empty-state-description"
          [id]="descriptionId">
          {{description}}
        </p>
        
        <!-- Tips or additional info -->
        <div 
          *ngIf="tips?.length" 
          class="empty-state-tips"
          role="region"
          [attr.aria-labelledby]="tipsHeaderId">
          <h3 
            class="tips-title"
            [id]="tipsHeaderId">
            {{tipsTitle || 'Tips to get started:'}}
          </h3>
          <ul 
            class="tips-list"
            role="list"
            [attr.aria-describedby]="tipsHeaderId">
            <li 
              *ngFor="let tip of tips; trackBy: trackTip; let i = index" 
              class="tip-item"
              role="listitem"
              [attr.aria-label]="getTipAriaLabel(tip, i)">
              <span 
                class="tip-icon" 
                aria-hidden="true">
                {{tip.icon || '💡'}}
              </span>
              <span class="tip-text">{{tip.text}}</span>
            </li>
          </ul>
        </div>

        <!-- Progress indicator -->
        <div 
          *ngIf="showProgress" 
          class="progress-section"
          role="region"
          aria-label="Progress information">
          <div 
            class="progress-bar"
            role="progressbar"
            [attr.aria-valuenow]="progressValue"
            aria-valuemin="0"
            aria-valuemax="100"
            [attr.aria-valuetext]="getProgressAriaText()">
            <div 
              class="progress-fill" 
              [style.width.%]="progressValue"
              aria-hidden="true">
            </div>
          </div>
          <p 
            class="progress-text"
            [id]="progressTextId"
            aria-live="polite">
            {{progressText}}
          </p>
        </div>

        <!-- Action buttons -->
        <div 
          class="empty-state-actions" 
          *ngIf="primaryAction || secondaryAction"
          role="group"
          aria-label="Available actions">
          <button 
            *ngIf="primaryAction"
            type="button"
            class="action-btn primary"
            [attr.aria-describedby]="primaryAction.description ? primaryActionDescId : null"
            [attr.aria-label]="getPrimaryActionAriaLabel()"
            (click)="onPrimaryAction()"
            (keydown)="handleActionKeydown($event, 'primary')"
            [disabled]="primaryActionDisabled">
            <span 
              *ngIf="primaryAction.icon" 
              class="btn-icon"
              aria-hidden="true">
              {{primaryAction.icon}}
            </span>
            <span class="btn-text">{{primaryAction.text}}</span>
          </button>
          
          <button 
            *ngIf="secondaryAction"
            type="button"
            class="action-btn secondary"
            [attr.aria-describedby]="secondaryAction.description ? secondaryActionDescId : null"
            [attr.aria-label]="getSecondaryActionAriaLabel()"
            (click)="onSecondaryAction()"
            (keydown)="handleActionKeydown($event, 'secondary')"
            [disabled]="secondaryActionDisabled">
            <span 
              *ngIf="secondaryAction.icon" 
              class="btn-icon"
              aria-hidden="true">
              {{secondaryAction.icon}}
            </span>
            <span class="btn-text">{{secondaryAction.text}}</span>
          </button>
        </div>
      </div>

    </div>
  `,
  styles: [`
    .empty-state-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 3rem 2rem;
      min-height: 400px;
      background: var(--background-color, #ffffff);
      border-radius: 16px;
      position: relative;
    }

    .small { min-height: 300px; padding: 2rem 1.5rem; }
    .medium { min-height: 400px; padding: 3rem 2rem; }
    .large { min-height: 500px; padding: 4rem 2.5rem; }

    /* Theme variations */
    .discovery {
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.05), rgba(255, 107, 157, 0.05));
    }

    .conversations {
      background: linear-gradient(135deg, rgba(96, 165, 250, 0.05), rgba(52, 211, 153, 0.05));
    }

    .revelations {
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.05), rgba(192, 132, 252, 0.05));
    }

    .profile {
      background: linear-gradient(135deg, rgba(236, 72, 153, 0.05), rgba(139, 92, 246, 0.05));
    }

    .neutral {
      background: var(--surface-color, #f8fafc);
    }

    /* Illustration section */
    .empty-state-illustration {
      margin-bottom: 2rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .svg-illustration {
      opacity: 0.8;
      animation: float 6s ease-in-out infinite;
    }

    .soul-orb-display {
      animation: gentle-pulse 4s ease-in-out infinite;
    }

    .custom-icon {
      opacity: 0.7;
      animation: bounce 2s ease-in-out infinite;
    }

    /* Content section */
    .empty-state-content {
      max-width: 500px;
      width: 100%;
    }

    .empty-state-title {
      font-size: 1.8rem;
      font-weight: 600;
      color: var(--text-primary, #1f2937);
      margin: 0 0 1rem 0;
      line-height: 1.3;
    }

    .empty-state-description {
      font-size: 1.1rem;
      color: var(--text-secondary, #6b7280);
      margin: 0 0 2rem 0;
      line-height: 1.6;
    }

    /* Tips section */
    .empty-state-tips {
      background: var(--surface-color, #f8fafc);
      border-radius: 12px;
      padding: 1.5rem;
      margin: 2rem 0;
      text-align: left;
    }

    .tips-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary, #1f2937);
      margin: 0 0 1rem 0;
    }

    .tips-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .tip-item {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
      padding: 0.5rem 0;
    }

    .tip-item:last-child {
      margin-bottom: 0;
    }

    .tip-icon {
      font-size: 1.2rem;
      flex-shrink: 0;
      margin-top: 0.1rem;
    }

    .tip-text {
      color: var(--text-primary, #1f2937);
      line-height: 1.5;
    }

    /* Progress section */
    .progress-section {
      margin: 2rem 0;
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background: var(--border-color, #e5e7eb);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 0.5rem;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #ffd700, #ff6b9d);
      border-radius: 4px;
      transition: width 1s ease-out;
    }

    .progress-text {
      font-size: 0.9rem;
      color: var(--text-secondary, #6b7280);
      margin: 0;
    }

    /* Action buttons */
    .empty-state-actions {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-top: 2rem;
    }

    .action-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 1rem 2rem;
      border: none;
      border-radius: 12px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      min-height: 48px;
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
      border: 2px solid var(--border-color, #e5e7eb);
    }

    .action-btn.secondary:hover:not(:disabled) {
      background: var(--border-color, #e5e7eb);
      border-color: var(--primary-color, #ec4899);
    }

    .btn-icon {
      font-size: 1.2rem;
    }

    /* Animations */
    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-10px); }
    }

    @keyframes gentle-pulse {
      0%, 100% { transform: scale(1); opacity: 0.8; }
      50% { transform: scale(1.05); opacity: 1; }
    }

    @keyframes bounce {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-5px); }
    }

    @keyframes search-pulse {
      0%, 100% { transform: scale(1); opacity: 0.6; }
      50% { transform: scale(1.1); opacity: 0.8; }
    }

    @keyframes revelation-glow {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 0.9; }
    }

    @keyframes star-sparkle {
      0%, 100% { transform: scale(1) rotate(0deg); }
      50% { transform: scale(1.1) rotate(180deg); }
    }

    .search-pulse {
      animation: search-pulse 3s ease-in-out infinite;
    }

    .search-handle {
      animation: float 2s ease-in-out infinite;
    }

    .revelation-glow {
      animation: revelation-glow 4s ease-in-out infinite;
    }

    .star-sparkle {
      animation: star-sparkle 6s ease-in-out infinite;
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
      .empty-state-container {
        padding: 2rem 1rem;
        min-height: 300px;
      }

      .empty-state-title {
        font-size: 1.5rem;
      }

      .empty-state-description {
        font-size: 1rem;
      }

      .empty-state-actions {
        flex-direction: column;
      }

      .action-btn {
        padding: 0.875rem 1.5rem;
        font-size: 0.95rem;
      }

      .empty-state-tips {
        padding: 1rem;
      }

      .tip-item {
        gap: 0.5rem;
      }
    }

    @media (max-width: 480px) {
      .empty-state-container {
        padding: 1.5rem 0.75rem;
      }

      .empty-state-title {
        font-size: 1.3rem;
      }

      .illustration-size {
        width: 120px;
        height: 120px;
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .svg-illustration, .soul-orb-display, .custom-icon,
      .search-pulse, .search-handle, .revelation-glow, .star-sparkle {
        animation: none !important;
      }
    }

    /* Dark theme */
    .dark-theme .empty-state-tips {
      background: var(--surface-color, #1f2937);
    }

    .dark-theme .action-btn.secondary {
      background: var(--surface-color, #1f2937);
      border-color: var(--border-color, #374151);
    }

    .dark-theme .action-btn.secondary:hover:not(:disabled) {
      background: var(--border-color, #374151);
    }
  `]
})
export class EmptyStateComponent {
  @Input() theme: 'discovery' | 'conversations' | 'revelations' | 'profile' | 'neutral' = 'neutral';
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() title: string = 'Nothing here yet';
  @Input() description: string = 'Content will appear here when available.';
  
  // Accessibility inputs
  @Input() ariaLabel?: string;
  @Input() headingLevel: 2 | 3 | 4 = 2;
  
  // Illustration options
  @Input() illustration?: 'discovery' | 'conversations' | 'revelations' | 'profile';
  @Input() customIcon?: string;
  @Input() iconSize: number = 4;
  
  // Soul orb options
  @Input() showSoulOrb: boolean = false;
  @Input() soulOrbType: 'primary' | 'secondary' | 'neutral' = 'primary';
  @Input() soulOrbSize: 'small' | 'medium' | 'large' = 'large';
  @Input() soulOrbState: 'active' | 'connecting' | 'matched' | 'dormant' = 'dormant';
  @Input() soulOrbEnergy: number = 2;
  @Input() showParticles: boolean = true;
  @Input() showSparkles: boolean = true;
  
  // Tips
  @Input() tips: Array<{icon?: string, text: string}> = [];
  @Input() tipsTitle?: string;
  
  // Progress
  @Input() showProgress: boolean = false;
  @Input() progressValue: number = 0;
  @Input() progressText: string = '';
  
  // Actions
  @Input() primaryAction?: {text: string, icon?: string, ariaLabel?: string, description?: string};
  @Input() secondaryAction?: {text: string, icon?: string, ariaLabel?: string, description?: string};
  @Input() primaryActionDisabled: boolean = false;
  @Input() secondaryActionDisabled: boolean = false;
  
  @Output() primaryActionClick = new EventEmitter<void>();
  @Output() secondaryActionClick = new EventEmitter<void>();

  // Generated IDs for accessibility
  readonly titleId = this.generateId('title');
  readonly descriptionId = this.generateId('description');
  readonly tipsHeaderId = this.generateId('tips-header');
  readonly progressTextId = this.generateId('progress-text');
  readonly primaryActionDescId = this.generateId('primary-action-desc');
  readonly secondaryActionDescId = this.generateId('secondary-action-desc');

  get illustrationSize(): number {
    const sizes = { small: 120, medium: 160, large: 200 };
    return sizes[this.size];
  }

  getAriaLabel(): string {
    return this.ariaLabel || `${this.title} - ${this.theme} empty state`;
  }

  getIllustrationAriaLabel(): string {
    const labels = {
      discovery: 'Search icon with magnifying glass indicating discovery of soul connections',
      conversations: 'Message bubbles indicating conversation and communication',
      revelations: 'Sparkling star indicating revelations and soul sharing',
      profile: 'User profile icon indicating personal profile information'
    };
    return this.illustration ? labels[this.illustration] : 'Decorative illustration';
  }

  getTipAriaLabel(tip: any, index: number): string {
    return `Tip ${index + 1}: ${tip.text}`;
  }

  getProgressAriaText(): string {
    return `${this.progressValue} percent complete. ${this.progressText}`;
  }

  getPrimaryActionAriaLabel(): string {
    return this.primaryAction?.ariaLabel || this.primaryAction?.text || 'Primary action';
  }

  getSecondaryActionAriaLabel(): string {
    return this.secondaryAction?.ariaLabel || this.secondaryAction?.text || 'Secondary action';
  }

  onPrimaryAction() {
    this.primaryActionClick.emit();
  }

  onSecondaryAction() {
    this.secondaryActionClick.emit();
  }

  trackTip(index: number, tip: any): string {
    return tip.text;
  }

  private generateId(prefix: string): string {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Handle keyboard navigation for action buttons
   */
  handleActionKeydown(event: KeyboardEvent, actionType: 'primary' | 'secondary'): void {
    const actionContainer = (event.target as HTMLElement).closest('.empty-state-actions');
    const actionButtons = Array.from(actionContainer?.querySelectorAll('.action-btn') || []) as HTMLElement[];
    const currentButtonIndex = actionButtons.findIndex(btn => btn.contains(event.target as Node));

    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (actionType === 'primary') {
          this.onPrimaryAction();
        } else {
          this.onSecondaryAction();
        }
        this.announceAction(`${actionType} action activated`);
        break;
        
      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        const prevButton = actionButtons[currentButtonIndex - 1] || actionButtons[actionButtons.length - 1];
        prevButton?.focus();
        this.announceAction('Previous action button');
        break;
        
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        const nextButton = actionButtons[currentButtonIndex + 1] || actionButtons[0];
        nextButton?.focus();
        this.announceAction('Next action button');
        break;
        
      case 'Home':
        event.preventDefault();
        actionButtons[0]?.focus();
        this.announceAction('First action button');
        break;
        
      case 'End':
        event.preventDefault();
        actionButtons[actionButtons.length - 1]?.focus();
        this.announceAction('Last action button');
        break;
    }
  }

  /**
   * Announce actions to screen readers
   */
  private announceAction(message: string): void {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      if (announcement.parentNode) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  }
}