import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { FormsModule } from '@angular/forms';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { Subscription } from 'rxjs';
import { ColorPsychologyService, MoodState } from '@core/services/color-psychology.service';
import { HapticFeedbackService } from '@core/services/haptic-feedback.service';

@Component({
  selector: 'app-mood-selector',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatSlideToggleModule,
    FormsModule
  ],
  template: `
    <div
      class="mood-selector"
      [class.expanded]="isExpanded"
      [@selectorAnimation]="isExpanded ? 'expanded' : 'collapsed'"
      role="toolbar"
      aria-label="Emotional mood selector">

      <!-- Mood Toggle Button -->
      <button
        class="mood-toggle"
        type="button"
        [attr.aria-expanded]="isExpanded"
        aria-controls="mood-options"
        [attr.aria-label]="'Current mood: ' + currentMood.name + '. Click to change mood.'"
        (click)="toggleSelector()"
        (keydown.enter)="toggleSelector()"
        (keydown.space)="toggleSelector(); $event.preventDefault()"
        matTooltip="Change your emotional mood">

        <div class="current-mood-indicator">
          <div
            class="mood-orb"
            [style.background]="currentMood.colorPalette.primary"
            [style.box-shadow]="getCurrentMoodGlow()"
            [@orbPulse]="'pulse'">
          </div>
          <span class="mood-icon">{{ getMoodIcon(currentMood) }}</span>
        </div>

        <div class="mood-info">
          <span class="mood-name">{{ currentMood.name }}</span>
          <span class="mood-description">{{ currentMood.description }}</span>
        </div>

        <mat-icon
          class="toggle-icon"
          [class.rotated]="isExpanded"
          aria-hidden="true">
          expand_more
        </mat-icon>
      </button>

      <!-- Mood Options Panel -->
      <div
        class="mood-options"
        *ngIf="isExpanded"
        id="mood-options"
        [@optionsAnimation]="'visible'"
        role="menu">

        <!-- Adaptive Mode Toggle -->
        <div class="adaptive-mode">
          <mat-slide-toggle
            [(ngModel)]="adaptiveMode"
            (change)="onAdaptiveModeChange()"
            id="adaptive-toggle"
            aria-labelledby="adaptive-label">
          </mat-slide-toggle>
          <div class="adaptive-info">
            <label id="adaptive-label" for="adaptive-toggle">Smart Color Adaptation</label>
            <small>Automatically adjust colors based on time and context</small>
          </div>
        </div>

        <!-- Mood Grid -->
        <div class="mood-grid" role="group" aria-label="Available mood options">
          <button
            *ngFor="let mood of availableMoods; trackBy: trackMood"
            class="mood-option"
            type="button"
            [class.active]="mood.id === currentMood.id"
            [class.recommended]="isRecommendedMood(mood)"
            role="menuitem"
            [attr.aria-label]="getMoodAriaLabel(mood)"
            (click)="selectMood(mood)"
            (keydown.enter)="selectMood(mood)"
            (keydown.space)="selectMood(mood); $event.preventDefault()"
            [matTooltip]="getMoodTooltip(mood)">

            <!-- Mood Preview -->
            <div class="mood-preview">
              <div
                class="preview-orb"
                [style.background]="mood.colorPalette.primary"
                [style.box-shadow]="getMoodPreviewGlow(mood)">
              </div>
              <div
                class="preview-gradient"
                [style.background]="mood.colorPalette.background">
              </div>
            </div>

            <!-- Mood Details -->
            <div class="mood-details">
              <div class="mood-header">
                <span class="mood-emoji">{{ getMoodIcon(mood) }}</span>
                <span class="mood-name">{{ mood.name }}</span>
              </div>
              <span class="mood-intensity">{{ mood.intensity }}</span>
            </div>

            <!-- Emotional Effects -->
            <div class="emotional-effects" *ngIf="mood.id === currentMood.id">
              <ul class="effects-list">
                <li *ngFor="let effect of mood.psychologicalEffects.slice(0, 2)">
                  {{ effect }}
                </li>
              </ul>
            </div>

            <!-- Recommended Badge -->
            <div class="recommended-badge" *ngIf="isRecommendedMood(mood)">
              <mat-icon class="badge-icon">auto_awesome</mat-icon>
              <span>Recommended</span>
            </div>
          </button>
        </div>

        <!-- Time-Based Suggestion -->
        <div class="time-suggestion" *ngIf="timeBasedSuggestion">
          <mat-icon class="suggestion-icon">schedule</mat-icon>
          <div class="suggestion-content">
            <span class="suggestion-text">
              Based on the time of day, {{ timeBasedSuggestion.name }} mood might enhance your experience
            </span>
            <button
              class="suggestion-button"
              type="button"
              (click)="selectMood(timeBasedSuggestion)"
              [attr.aria-label]="'Apply suggested ' + timeBasedSuggestion.name + ' mood'">
              Apply
            </button>
          </div>
        </div>

        <!-- Color Preview -->
        <div class="color-preview" *ngIf="currentMood">
          <h4 class="preview-title">Current Emotional Palette</h4>
          <div class="color-swatches">
            <div
              class="color-swatch primary"
              [style.background]="currentMood.colorPalette.primary"
              [attr.aria-label]="'Primary color: ' + currentMood.colorPalette.primary"
              matTooltip="Primary emotional color">
            </div>
            <div
              class="color-swatch secondary"
              [style.background]="currentMood.colorPalette.secondary"
              [attr.aria-label]="'Secondary color: ' + currentMood.colorPalette.secondary"
              matTooltip="Secondary emotional color">
            </div>
            <div
              class="color-swatch accent"
              [style.background]="currentMood.colorPalette.accent"
              [attr.aria-label]="'Accent color: ' + currentMood.colorPalette.accent"
              matTooltip="Accent emotional color">
            </div>
          </div>
        </div>

        <!-- Theme Preview Apply -->
        <div class="theme-apply">
          <button type="button" class="apply-btn" (click)="applyAppTheme()">Apply as App Theme</button>
        </div>
      </div>

      <!-- Close Overlay -->
      <div
        class="mood-overlay"
        *ngIf="isExpanded"
        (click)="closeSelector()"
        [@overlayAnimation]="'visible'"
        aria-hidden="true">
      </div>
    </div>
  `,
  styles: [`
    .mood-selector {
      position: relative;
      z-index: 1000;
    }

    /* Mood Toggle Button */
    .mood-toggle {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.75rem 1rem;
      background: var(--surface-color);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      min-width: 200px;

      &:hover {
        background: var(--surface-secondary);
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
      }

      &:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
      }
    }

    .current-mood-indicator {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .mood-orb {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      position: relative;
      transition: all 0.3s ease;
    }

    .mood-icon {
      position: absolute;
      font-size: 1.2rem;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 1;
    }

    .mood-info {
      flex: 1;
      text-align: left;
    }

    .mood-name {
      display: block;
      font-weight: 600;
      color: var(--text-primary);
      font-size: 0.9rem;
    }

    .mood-description {
      display: block;
      font-size: 0.75rem;
      color: var(--text-secondary);
      opacity: 0.8;
    }

    .toggle-icon {
      transition: transform 0.3s ease;
      color: var(--text-secondary);

      &.rotated {
        transform: rotate(180deg);
      }
    }

    /* Mood Options Panel */
    .mood-options {
      position: absolute;
      top: calc(100% + 0.5rem);
      left: 0;
      right: 0;
      background: var(--surface-color);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 1.5rem;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
      backdrop-filter: blur(8px);
      z-index: 1001;
      min-width: 400px;
    }

    /* Adaptive Mode */
    .adaptive-mode {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background: var(--surface-secondary);
      border-radius: 12px;
      margin-bottom: 1.5rem;
    }

    .adaptive-info {
      flex: 1;
    }

    .adaptive-info label {
      display: block;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 0.25rem;
      cursor: pointer;
    }

    .adaptive-info small {
      color: var(--text-secondary);
      font-size: 0.8rem;
    }

    /* Mood Grid */
    .mood-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .mood-option {
      position: relative;
      padding: 1rem;
      background: var(--surface-secondary);
      border: 2px solid transparent;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      text-align: left;

      &:hover {
        background: var(--surface-tertiary);
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
      }

      &:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
      }

      &.active {
        border-color: var(--primary-color);
        background: rgba(255, 107, 157, 0.05);
        box-shadow: 0 4px 20px rgba(255, 107, 157, 0.2);
      }

      &.recommended {
        border-color: var(--accent-color);

        &::before {
          content: '';
          position: absolute;
          top: -2px;
          left: -2px;
          right: -2px;
          bottom: -2px;
          background: linear-gradient(45deg, var(--accent-color), var(--primary-color));
          border-radius: 14px;
          z-index: -1;
        }
      }
    }

    /* Mood Preview */
    .mood-preview {
      position: relative;
      height: 40px;
      border-radius: 8px;
      margin-bottom: 0.75rem;
      overflow: hidden;
    }

    .preview-orb {
      position: absolute;
      top: 4px;
      left: 4px;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      z-index: 2;
    }

    .preview-gradient {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      opacity: 0.3;
      border-radius: 8px;
    }

    /* Mood Details */
    .mood-details {
      margin-bottom: 0.5rem;
    }

    .mood-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.25rem;
    }

    .mood-option .mood-name {
      font-weight: 600;
      color: var(--text-primary);
      font-size: 0.9rem;
    }

    .mood-emoji {
      font-size: 1.1rem;
    }

    .mood-intensity {
      font-size: 0.75rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 500;
    }

    /* Emotional Effects */
    .emotional-effects {
      margin-top: 0.75rem;
      padding-top: 0.75rem;
      border-top: 1px solid var(--border-color);
    }

    .effects-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .effects-list li {
      font-size: 0.8rem;
      color: var(--text-secondary);
      margin-bottom: 0.25rem;

      &:before {
        content: '✓ ';
        color: var(--primary-color);
        font-weight: bold;
      }
    }

    /* Recommended Badge */
    .recommended-badge {
      position: absolute;
      top: -8px;
      right: -8px;
      background: var(--accent-color);
      color: white;
      padding: 0.25rem 0.5rem;
      border-radius: 12px;
      font-size: 0.7rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.25rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    .badge-icon {
      font-size: 0.9rem;
    }

    /* Time Suggestion */
    .time-suggestion {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background: rgba(96, 165, 250, 0.1);
      border: 1px solid rgba(96, 165, 250, 0.3);
      border-radius: 12px;
      margin-bottom: 1.5rem;
    }

    .suggestion-icon {
      color: var(--trust-ocean-600);
      flex-shrink: 0;
    }

    .suggestion-content {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .suggestion-text {
      font-size: 0.85rem;
      color: var(--text-primary);
    }

    .suggestion-button {
      padding: 0.5rem 1rem;
      background: var(--trust-ocean-600);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;

      &:hover {
        background: var(--trust-ocean-700);
        transform: translateY(-1px);
      }
    }

    /* Color Preview */
    .color-preview {
      text-align: center;
    }

    .preview-title {
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 1rem 0;
    }

    .color-swatches {
      display: flex;
      justify-content: center;
      gap: 0.75rem;
    }

    .color-swatch {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      border: 2px solid white;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
      cursor: pointer;
      transition: transform 0.2s ease;

      &:hover {
        transform: scale(1.1);
      }
    }

    /* Overlay */
    .mood-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.1);
      z-index: 999;
    }

    /* Animations */
    @keyframes moodPulse {
      0%, 100% {
        transform: scale(1);
        opacity: 1;
      }
      50% {
        transform: scale(1.05);
        opacity: 0.9;
      }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .mood-options {
        min-width: calc(100vw - 2rem);
        left: 1rem;
        right: 1rem;
        width: auto;
      }

      .mood-grid {
        grid-template-columns: 1fr;
      }

      .suggestion-content {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }
    }

    /* Dark theme */
    .dark-theme {
      .mood-toggle {
        background: var(--surface-color);
        border-color: var(--border-color);
      }

      .mood-options {
        background: var(--surface-color);
        border-color: var(--border-color);
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .mood-orb,
      .mood-option,
      .toggle-icon {
        transition: none !important;
        animation: none !important;
      }
    }
  `],
  animations: [
    trigger('selectorAnimation', [
      state('collapsed', style({ transform: 'scale(1)' })),
      state('expanded', style({ transform: 'scale(1.02)' })),
      transition('collapsed <=> expanded', animate('200ms ease-out'))
    ]),
    trigger('optionsAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px) scale(0.95)' }),
        animate('300ms cubic-bezier(0.4, 0, 0.2, 1)',
          style({ opacity: 1, transform: 'translateY(0) scale(1)' }))
      ]),
      transition(':leave', [
        animate('200ms ease-in',
          style({ opacity: 0, transform: 'translateY(-10px) scale(0.95)' }))
      ])
    ]),
    trigger('overlayAnimation', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('200ms ease-out', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate('150ms ease-in', style({ opacity: 0 }))
      ])
    ]),
    trigger('orbPulse', [
      state('pulse', style({ transform: 'scale(1)' })),
      transition('* => pulse', [
        animate('1s ease-in-out', style({ transform: 'scale(1.1)' })),
        animate('1s ease-in-out', style({ transform: 'scale(1)' }))
      ])
    ])
  ]
})
export class MoodSelectorComponent implements OnInit, OnDestroy {
  isExpanded = false;
  currentMood: MoodState;
  availableMoods: MoodState[] = [];
  adaptiveMode = true;
  timeBasedSuggestion: MoodState | null = null;

  private subscription = new Subscription();

  constructor(
    private colorPsychologyService: ColorPsychologyService,
    private hapticFeedbackService: HapticFeedbackService
  ) {
    this.currentMood = this.colorPsychologyService.getCurrentMood();
  }

  applyAppTheme(): void {
    // Apply mood palette as dynamic theme variables
    const p = this.currentMood.colorPalette;
    document.documentElement.style.setProperty('--primary-color', p.primary);
    document.documentElement.style.setProperty('--accent-color', p.accent);
    document.documentElement.style.setProperty('--background-color', p.background);
    document.documentElement.style.setProperty('--surface-color', p.background);
    this.hapticFeedbackService.triggerSuccessFeedback();
  }

  ngOnInit(): void {
    // Subscribe to mood changes
    this.subscription.add(
      this.colorPsychologyService.currentMood$.subscribe(mood => {
        this.currentMood = mood;
      })
    );

    // Subscribe to adaptive mode changes
    this.subscription.add(
      this.colorPsychologyService.adaptiveColors$.subscribe(adaptive => {
        this.adaptiveMode = adaptive;
      })
    );

    // Load available moods
    this.availableMoods = this.colorPsychologyService.getAvailableMoods();

    // Get time-based suggestion
    this.updateTimeBasedSuggestion();

    // Update suggestion every hour
    setInterval(() => {
      this.updateTimeBasedSuggestion();
    }, 60 * 60 * 1000);
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  toggleSelector(): void {
    this.isExpanded = !this.isExpanded;
    this.hapticFeedbackService.triggerSelectionFeedback();

    if (this.isExpanded) {
      // Focus first mood option for keyboard navigation
      setTimeout(() => {
        const firstOption = document.querySelector('.mood-option') as HTMLElement;
        firstOption?.focus();
      }, 100);
    }
  }

  closeSelector(): void {
    this.isExpanded = false;
  }

  selectMood(mood: MoodState): void {
    if (mood.id !== this.currentMood.id) {
      this.colorPsychologyService.setMood(mood.id);
      this.hapticFeedbackService.triggerSuccessFeedback();

      // Announce mood change
      this.announceMoodChange(mood);
    }

    this.closeSelector();
  }

  onAdaptiveModeChange(): void {
    this.colorPsychologyService.toggleAdaptiveColors(this.adaptiveMode);
    this.hapticFeedbackService.triggerSelectionFeedback();
  }

  getMoodIcon(mood: MoodState): string {
    const iconMap: { [key: string]: string } = {
      contemplative: '🧘',
      romantic: '💕',
      energetic: '⚡',
      peaceful: '🌿',
      sophisticated: '🎭'
    };
    return iconMap[mood.id] || '✨';
  }

  getCurrentMoodGlow(): string {
    return `${this.currentMood.colorPalette.glow}, 0 0 20px ${this.currentMood.colorPalette.primary}33`;
  }

  getMoodPreviewGlow(mood: MoodState): string {
    return `0 0 12px ${mood.colorPalette.primary}44`;
  }

  getMoodAriaLabel(mood: MoodState): string {
    const recommended = this.isRecommendedMood(mood) ? ' (Recommended)' : '';
    return `Select ${mood.name} mood: ${mood.description}. Intensity: ${mood.intensity}${recommended}`;
  }

  getMoodTooltip(mood: MoodState): string {
    const effects = mood.psychologicalEffects.slice(0, 2).join('. ');
    return `${mood.description}. ${effects}`;
  }

  isRecommendedMood(mood: MoodState): boolean {
    return mood.id === this.timeBasedSuggestion?.id;
  }

  trackMood(index: number, mood: MoodState): string {
    return mood.id;
  }

  private updateTimeBasedSuggestion(): void {
    const hour = new Date().getHours();
    let suggestedMoodId: string;

    if (hour >= 6 && hour < 12) {
      suggestedMoodId = 'energetic';
    } else if (hour >= 12 && hour < 17) {
      suggestedMoodId = 'sophisticated';
    } else if (hour >= 17 && hour < 20) {
      suggestedMoodId = 'romantic';
    } else {
      suggestedMoodId = 'contemplative';
    }

    // Only suggest if it's different from current mood
    if (suggestedMoodId !== this.currentMood.id) {
      this.timeBasedSuggestion = this.availableMoods.find(m => m.id === suggestedMoodId) || null;
    } else {
      this.timeBasedSuggestion = null;
    }
  }

  private announceMoodChange(mood: MoodState): void {
    // Create screen reader announcement
    const announcement = `Mood changed to ${mood.name}. ${mood.description}`;

    // Create and trigger announcement element
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');
    announcer.classList.add('sr-only');
    announcer.textContent = announcement;

    document.body.appendChild(announcer);

    setTimeout(() => {
      document.body.removeChild(announcer);
    }, 1000);
  }
}
