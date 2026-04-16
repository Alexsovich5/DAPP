import { Component, Input, OnInit, OnDestroy, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SoulOrbComponent } from '../soul-orb/soul-orb.component';
import { ScreenReaderService } from '../../../core/services/screen-reader.service';
import { SoulConfig } from '../../models/soul-types';

@Component({
  selector: 'app-soul-connection',
  standalone: true,
  imports: [CommonModule, SoulOrbComponent],
  template: `
    <div
      class="soul-connection-container"
      [ngClass]="[layout, connectionState]"
      role="region"
      [attr.aria-label]="getConnectionAriaLabel()"
      [attr.aria-describedby]="'connection-description-' + connectionId"
      tabindex="0"
      (keydown)="handleKeydown($event)"
      (focus)="announceConnectionDetails()"
    >

      <!-- Hidden description for screen readers -->
      <div
        [id]="'connection-description-' + connectionId"
        class="sr-only"
        [attr.aria-live]="announceChanges ? 'polite' : 'off'"
      >
        {{getDetailedConnectionDescription()}}
      </div>

      <!-- First Soul -->
      <div
        class="soul-position left"
        role="group"
        [attr.aria-labelledby]="'left-soul-label-' + connectionId"
        [attr.aria-describedby]="'left-soul-desc-' + connectionId"
      >
        <app-soul-orb
          [type]="leftSoul.type"
          [size]="orbSize"
          [state]="leftSoul.state"
          [energyLevel]="leftSoul.energy"
          [compatibilityScore]="compatibilityScore"
          [showCompatibility]="showCompatibility && isLeftSelected"
          [showParticles]="leftSoul.showParticles ?? true"
          [showSparkles]="leftSoul.showSparkles ?? true"
          [ariaLabel]="getLeftSoulAriaLabel()"
        >
        </app-soul-orb>
        <div
          class="soul-label"
          *ngIf="leftSoul.label"
          [id]="'left-soul-label-' + connectionId"
        >
          {{leftSoul.label}}
        </div>
        <div
          [id]="'left-soul-desc-' + connectionId"
          class="sr-only"
        >
          {{getLeftSoulDescription()}}
        </div>
      </div>

      <!-- Connection Visualization -->
      <div
        class="connection-area"
        role="img"
        [attr.aria-label]="getConnectionVisualizationLabel()"
        [attr.aria-describedby]="'connection-viz-desc-' + connectionId"
      >
        <div
          [id]="'connection-viz-desc-' + connectionId"
          class="sr-only"
        >
          {{getConnectionVisualizationDescription()}}
        </div>
        <svg
          class="connection-svg"
          viewBox="0 0 200 100"
          preserveAspectRatio="xMidYMid meet"
          [attr.aria-hidden]="true"
          role="presentation"
        >
          <defs>
            <!-- Connection gradient -->
            <linearGradient id="connection-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" [attr.stop-color]="connectionColors.start" stop-opacity="0.8"/>
              <stop offset="50%" [attr.stop-color]="connectionColors.middle" stop-opacity="1"/>
              <stop offset="100%" [attr.stop-color]="connectionColors.end" stop-opacity="0.8"/>
            </linearGradient>

            <!-- Pulse gradient -->
            <linearGradient id="pulse-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" [attr.stop-color]="pulseColor" stop-opacity="0"/>
              <stop offset="50%" [attr.stop-color]="pulseColor" stop-opacity="1"/>
              <stop offset="100%" [attr.stop-color]="pulseColor" stop-opacity="0"/>
            </linearGradient>

            <!-- Glow filter -->
            <filter id="connection-glow" x="-50%" y="-200%" width="200%" height="400%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          <!-- Base connection line -->
          <path
            [attr.d]="connectionPath"
            stroke="url(#connection-gradient)"
            [attr.stroke-width]="connectionWidth"
            fill="none"
            filter="url(#connection-glow)"
            class="connection-line"
            [class.pulsing]="isConnecting || isMatched">
          </path>

          <!-- Energy pulse -->
          <path
            *ngIf="showEnergyPulse"
            [attr.d]="connectionPath"
            stroke="url(#pulse-gradient)"
            [attr.stroke-width]="pulseWidth"
            fill="none"
            class="energy-pulse"
            [style.animation-duration]="pulseSpeed + 's'">
          </path>

          <!-- Floating energy particles -->
          <g class="energy-particles" *ngIf="showEnergyParticles">
            <circle
              *ngFor="let particle of connectionParticles; trackBy: trackConnectionParticle"
              [attr.cx]="particle.x"
              [attr.cy]="particle.y"
              [attr.r]="particle.size"
              [attr.fill]="particle.color"
              fill-opacity="0.8"
              class="connection-particle"
              [style.animation-delay]="particle.delay + 's'"
              [style.animation-duration]="particle.duration + 's'">
            </circle>
          </g>

          <!-- Heart symbols for strong connections -->
          <g class="connection-hearts" *ngIf="compatibilityScore >= 80">
            <text
              *ngFor="let heart of connectionHearts; trackBy: trackConnectionHeart"
              [attr.x]="heart.x"
              [attr.y]="heart.y"
              font-family="sans-serif"
              font-size="12"
              fill="#ff6b9d"
              text-anchor="middle"
              class="connection-heart"
              [style.animation-delay]="heart.delay + 's'">
              &#x2665;
            </text>
          </g>
        </svg>

        <!-- Compatibility display -->
        <div
          class="compatibility-meter"
          *ngIf="showCompatibilityMeter"
          role="meter"
          [attr.aria-label]="'Soul compatibility: ' + compatibilityScore + ' percent'"
          [attr.aria-valuenow]="compatibilityScore"
          [attr.aria-valuemin]="0"
          [attr.aria-valuemax]="100"
          [attr.aria-valuetext]="compatibilityScore + '% - ' + compatibilityText"
          [attr.aria-describedby]="'compatibility-desc-' + connectionId"
        >
          <div
            [id]="'compatibility-desc-' + connectionId"
            class="sr-only"
          >
            {{getCompatibilityDescription()}}
          </div>
          <div class="compatibility-bar" aria-hidden="true">
            <div
              class="compatibility-fill"
              [style.width.%]="compatibilityScore"
              [ngClass]="compatibilityLevel">
            </div>
          </div>
          <div class="compatibility-info" aria-hidden="true">
            <span class="score">{{compatibilityScore}}%</span>
            <span class="level">{{compatibilityText}}</span>
          </div>
        </div>
      </div>

      <!-- Second Soul -->
      <div
        class="soul-position right"
        role="group"
        [attr.aria-labelledby]="'right-soul-label-' + connectionId"
        [attr.aria-describedby]="'right-soul-desc-' + connectionId"
      >
        <app-soul-orb
          [type]="rightSoul.type"
          [size]="orbSize"
          [state]="rightSoul.state"
          [energyLevel]="rightSoul.energy"
          [compatibilityScore]="compatibilityScore"
          [showCompatibility]="showCompatibility && !isLeftSelected"
          [showParticles]="rightSoul.showParticles ?? true"
          [showSparkles]="rightSoul.showSparkles ?? true"
          [ariaLabel]="getRightSoulAriaLabel()"
        >
        </app-soul-orb>
        <div
          class="soul-label"
          *ngIf="rightSoul.label"
          [id]="'right-soul-label-' + connectionId"
        >
          {{rightSoul.label}}
        </div>
        <div
          [id]="'right-soul-desc-' + connectionId"
          class="sr-only"
        >
          {{getRightSoulDescription()}}
        </div>
      </div>

      <!-- Connection status message -->
      <div
        class="connection-status"
        *ngIf="statusMessage"
        role="status"
        [attr.aria-live]="announceChanges ? 'polite' : 'off'"
        [attr.aria-atomic]="true"
      >
        <p class="status-text">{{statusMessage}}</p>
      </div>

    </div>
  `,
  styles: [`
    .soul-connection-container {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 2rem;
      position: relative;
      min-height: 200px;
    }

    /* Layout variants */
    .horizontal {
      flex-direction: row;
    }

    .vertical {
      flex-direction: column;
      min-height: 400px;
    }

    .soul-position {
      display: flex;
      flex-direction: column;
      align-items: center;
      z-index: 2;
    }

    .soul-label {
      margin-top: 0.5rem;
      font-size: 0.9rem;
      color: var(--text-secondary, #6b7280);
      text-align: center;
      font-weight: 500;
    }

    .connection-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
      z-index: 1;
    }

    .connection-svg {
      width: 100%;
      height: 100px;
      max-width: 300px;
    }

    .vertical .connection-svg {
      height: 200px;
      transform: rotate(90deg);
    }

    /* Connection animations */
    .connection-line.pulsing {
      animation: connection-pulse 2s ease-in-out infinite;
    }

    .energy-pulse {
      animation: energy-flow 3s linear infinite;
    }

    .connection-particle {
      animation: particle-travel 4s ease-in-out infinite;
    }

    .connection-heart {
      animation: heart-float 3s ease-in-out infinite;
    }

    /* Compatibility meter */
    .compatibility-meter {
      margin-top: 1rem;
      width: 100%;
      max-width: 250px;
    }

    .compatibility-bar {
      width: 100%;
      height: 8px;
      background: var(--border-color, #e5e7eb);
      border-radius: 4px;
      overflow: hidden;
      position: relative;
    }

    .compatibility-fill {
      height: 100%;
      border-radius: 4px;
      transition: width 1s ease-out;
      position: relative;
    }

    .compatibility-fill.low {
      background: linear-gradient(90deg, #fbbf24, #f59e0b);
    }

    .compatibility-fill.medium {
      background: linear-gradient(90deg, #34d399, #10b981);
    }

    .compatibility-fill.high {
      background: linear-gradient(90deg, #f472b6, #ec4899);
    }

    .compatibility-fill.perfect {
      background: linear-gradient(90deg, #ffd700, #ff6b9d, #c084fc);
      animation: perfect-shimmer 2s ease-in-out infinite;
    }

    .compatibility-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 0.5rem;
      font-size: 0.8rem;
    }

    .score {
      font-weight: bold;
      color: var(--primary-color, #ec4899);
    }

    .level {
      color: var(--text-secondary, #6b7280);
      font-style: italic;
    }

    .connection-status {
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      text-align: center;
    }

    .status-text {
      font-size: 0.9rem;
      color: var(--text-secondary, #6b7280);
      margin: 0;
      padding: 0.5rem 1rem;
      background: var(--background-color, #ffffff);
      border-radius: 20px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    /* Connection state variations */
    .discovering .connection-line {
      stroke-dasharray: 5, 5;
      animation: discovering-dash 2s linear infinite;
    }

    .connecting .connection-area {
      animation: connecting-glow 1.5s ease-in-out infinite;
    }

    .matched .connection-area {
      animation: matched-celebration 3s ease-out;
    }

    .strong-match .connection-line {
      filter: drop-shadow(0 0 8px currentColor);
    }

    /* Keyframe animations */
    @keyframes connection-pulse {
      0%, 100% { stroke-opacity: 0.6; }
      50% { stroke-opacity: 1; }
    }

    @keyframes energy-flow {
      0% { stroke-dasharray: 0, 200; }
      50% { stroke-dasharray: 100, 200; }
      100% { stroke-dasharray: 200, 200; }
    }

    @keyframes particle-travel {
      0% { transform: translateX(-50px); opacity: 0; }
      10% { opacity: 1; }
      90% { opacity: 1; }
      100% { transform: translateX(250px); opacity: 0; }
    }

    @keyframes heart-float {
      0%, 100% { transform: translateY(0) scale(1); opacity: 0.7; }
      50% { transform: translateY(-10px) scale(1.2); opacity: 1; }
    }

    @keyframes discovering-dash {
      0% { stroke-dashoffset: 0; }
      100% { stroke-dashoffset: -20; }
    }

    @keyframes connecting-glow {
      0%, 100% { filter: brightness(1); }
      50% { filter: brightness(1.2) saturate(1.3); }
    }

    @keyframes matched-celebration {
      0% { transform: scale(1); }
      25% { transform: scale(1.05); }
      50% { transform: scale(1.02); }
      100% { transform: scale(1); }
    }

    @keyframes perfect-shimmer {
      0%, 100% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
      .soul-connection-container {
        padding: 1rem;
        min-height: 150px;
      }

      .connection-svg {
        height: 80px;
        max-width: 200px;
      }

      .soul-label {
        font-size: 0.8rem;
      }

      .compatibility-meter {
        max-width: 180px;
      }

      .status-text {
        font-size: 0.8rem;
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .connection-line, .energy-pulse, .connection-particle,
      .connection-heart, .compatibility-fill {
        animation: none !important;
      }
    }

    /* Dark theme */
    .dark-theme .compatibility-bar {
      background: var(--border-color, #374151);
    }

    .dark-theme .status-text {
      background: var(--surface-color, #1f2937);
    }
  `]
})
export class SoulConnectionComponent implements OnInit, OnDestroy, OnChanges {
  @Input() leftSoul: SoulConfig = {
    type: 'primary',
    state: 'active',
    energy: 3,
    label: 'You',
    showParticles: true,
    showSparkles: true
  };

  @Input() rightSoul: SoulConfig = {
    type: 'secondary',
    state: 'active',
    energy: 3,
    label: 'Match',
    showParticles: true,
    showSparkles: true
  };

  @Input() layout: 'horizontal' | 'vertical' = 'horizontal';
  @Input() orbSize: 'small' | 'medium' | 'large' = 'medium';
  @Input() compatibilityScore: number = 0;
  @Input() connectionState: 'discovering' | 'connecting' | 'matched' | 'strong-match' = 'discovering';
  @Input() showCompatibility: boolean = false;
  @Input() showCompatibilityMeter: boolean = true;
  @Input() showEnergyPulse: boolean = true;
  @Input() showEnergyParticles: boolean = true;
  @Input() statusMessage: string = '';
  @Input() connectionId: string = 'connection-' + Math.random().toString(36).substr(2, 9);
  @Input() announceChanges: boolean = true;

  connectionParticles: Array<{x: number; y: number; size: number; color: string; delay: number; duration: number}> = [];
  connectionHearts: Array<{x: number; y: number; delay: number}> = [];
  isLeftSelected: boolean = true;

  private animationFrame?: number;
  private previousCompatibilityScore: number = 0;
  private previousConnectionState: string = '';

  constructor(private screenReader: ScreenReaderService) {}

  get connectionPath(): string {
    if (this.layout === 'vertical') {
      return 'M 100 10 Q 100 50 100 90';
    }
    return 'M 20 50 Q 100 30 180 50';
  }

  get connectionWidth(): number {
    const baseWidth = 3;
    const energyBonus = Math.max(this.leftSoul.energy, this.rightSoul.energy);
    return baseWidth + (energyBonus * 0.5);
  }

  get pulseWidth(): number {
    return this.connectionWidth + 2;
  }

  get pulseSpeed(): number {
    return Math.max(1, 4 - (this.compatibilityScore / 25));
  }

  get connectionColors() {
    const compatibility = this.compatibilityScore;
    if (compatibility >= 90) {
      return { start: '#ffd700', middle: '#ff6b9d', end: '#c084fc' };
    } else if (compatibility >= 70) {
      return { start: '#f472b6', middle: '#ec4899', end: '#be185d' };
    } else if (compatibility >= 50) {
      return { start: '#34d399', middle: '#10b981', end: '#059669' };
    } else {
      return { start: '#fbbf24', middle: '#f59e0b', end: '#d97706' };
    }
  }

  get pulseColor(): string {
    return this.connectionColors.middle;
  }

  get isConnecting(): boolean {
    return this.connectionState === 'connecting';
  }

  get isMatched(): boolean {
    return this.connectionState === 'matched' || this.connectionState === 'strong-match';
  }

  get compatibilityLevel(): string {
    const score = this.compatibilityScore;
    if (score >= 95) return 'perfect';
    if (score >= 80) return 'high';
    if (score >= 60) return 'medium';
    return 'low';
  }

  get compatibilityText(): string {
    const score = this.compatibilityScore;
    if (score >= 95) return 'Perfect Soul Match';
    if (score >= 85) return 'Exceptional Connection';
    if (score >= 75) return 'Strong Compatibility';
    if (score >= 65) return 'Good Match';
    if (score >= 50) return 'Potential Connection';
    return 'Exploring Compatibility';
  }

  ngOnChanges(changes: SimpleChanges): void {
    // Announce compatibility score changes
    if (changes['compatibilityScore'] && !changes['compatibilityScore'].firstChange) {
      const currentScore = changes['compatibilityScore'].currentValue;
      const previousScore = changes['compatibilityScore'].previousValue;

      if (Math.abs(currentScore - previousScore) >= 5) {
        this.screenReader.announceCompatibilityScore(currentScore, {
          values: Math.floor(currentScore * 0.3),
          interests: Math.floor(currentScore * 0.25),
          communication: Math.floor(currentScore * 0.45)
        });
      }
    }

    // Announce connection state changes
    if (changes['connectionState'] && !changes['connectionState'].firstChange) {
      const newState = changes['connectionState'].currentValue;
      this.announceConnectionStateChange(newState);
    }
  }

  ngOnInit() {
    this.generateConnectionParticles();
    this.generateConnectionHearts();
    this.startAnimation();

    // Toggle between souls for compatibility display
    setInterval(() => {
      this.isLeftSelected = !this.isLeftSelected;
    }, 3000);
  }

  ngOnDestroy() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
  }

  private generateConnectionParticles() {
    this.connectionParticles = [];
    if (!this.showEnergyParticles) return;

    const particleCount = Math.min(8, this.compatibilityScore / 10);

    for (let i = 0; i < particleCount; i++) {
      this.connectionParticles.push({
        x: 20 + Math.random() * 160,
        y: 45 + Math.random() * 10,
        size: 1 + Math.random() * 2,
        color: this.connectionColors.middle,
        delay: Math.random() * 2,
        duration: 3 + Math.random() * 2
      });
    }
  }

  private generateConnectionHearts() {
    this.connectionHearts = [];
    if (this.compatibilityScore < 80) return;

    const heartCount = Math.min(5, Math.floor(this.compatibilityScore / 20));

    for (let i = 0; i < heartCount; i++) {
      this.connectionHearts.push({
        x: 40 + Math.random() * 120,
        y: 45 + Math.random() * 10,
        delay: Math.random() * 3
      });
    }
  }

  private startAnimation() {
    const animate = () => {
      if (this.showEnergyParticles && Math.random() < 0.2) {
        this.generateConnectionParticles();
      }
      this.animationFrame = requestAnimationFrame(animate);
    };
    animate();
  }

  trackConnectionParticle(_index: number, particle: Record<string, unknown>): unknown {
    return particle['id'];
  }

  trackConnectionHeart(_index: number, heart: Record<string, unknown>): unknown {
    return heart['id'];
  }

  // Screen Reader Accessibility Methods

  getConnectionAriaLabel(): string {
    return `Soul connection between ${this.leftSoul.label || 'left soul'} and ${this.rightSoul.label || 'right soul'}, ${this.compatibilityScore}% compatibility`;
  }

  getDetailedConnectionDescription(): string {
    const stateDescriptions = {
      'discovering': 'Currently discovering potential connection through soul compatibility analysis',
      'connecting': 'Establishing soul connection with real-time energy synchronization',
      'matched': 'Successfully matched souls with confirmed compatibility',
      'strong-match': 'Exceptional soul match with powerful energy resonance'
    };

    const energyDescription = this.getEnergyDescription();
    const compatibilityDescription = this.getCompatibilityDescription();
    const stateDescription = stateDescriptions[this.connectionState] || 'Processing connection state';

    return `${stateDescription}. ${compatibilityDescription}. ${energyDescription}`;
  }

  getLeftSoulAriaLabel(): string {
    return `${this.leftSoul.label || 'Left soul'}, ${this.leftSoul.type} type, ${this.leftSoul.state} state, energy level ${this.leftSoul.energy}`;
  }

  getLeftSoulDescription(): string {
    const particleStatus = this.leftSoul.showParticles ? 'displaying energy particles' : 'particles hidden';
    const sparkleStatus = this.leftSoul.showSparkles ? 'with soul sparkles' : 'sparkles disabled';
    return `${this.leftSoul.label || 'Left soul'} is in ${this.leftSoul.state} state with energy level ${this.leftSoul.energy}, ${particleStatus} ${sparkleStatus}`;
  }

  getRightSoulAriaLabel(): string {
    return `${this.rightSoul.label || 'Right soul'}, ${this.rightSoul.type} type, ${this.rightSoul.state} state, energy level ${this.rightSoul.energy}`;
  }

  getRightSoulDescription(): string {
    const particleStatus = this.rightSoul.showParticles ? 'displaying energy particles' : 'particles hidden';
    const sparkleStatus = this.rightSoul.showSparkles ? 'with soul sparkles' : 'sparkles disabled';
    return `${this.rightSoul.label || 'Right soul'} is in ${this.rightSoul.state} state with energy level ${this.rightSoul.energy}, ${particleStatus} ${sparkleStatus}`;
  }

  getConnectionVisualizationLabel(): string {
    const visualElements = [];

    if (this.showEnergyPulse) visualElements.push('energy pulse');
    if (this.showEnergyParticles) visualElements.push('floating energy particles');
    if (this.compatibilityScore >= 80) visualElements.push('heart symbols for strong connection');

    const elementsText = visualElements.length > 0 ?
      ` showing ${visualElements.join(', ')}` :
      ' with basic connection line';

    return `Soul connection visualization${elementsText}`;
  }

  getConnectionVisualizationDescription(): string {
    const pulseDesc = this.showEnergyPulse ?
      `Energy pulse flowing at ${this.pulseSpeed} second intervals` :
      'No energy pulse animation';

    const particleDesc = this.showEnergyParticles ?
      `${this.connectionParticles.length} energy particles traveling along connection path` :
      'No particle effects';

    const heartDesc = this.compatibilityScore >= 80 ?
      `${this.connectionHearts.length} floating heart symbols indicating strong connection` :
      'No heart symbols displayed';

    return `Connection visualization: ${pulseDesc}. ${particleDesc}. ${heartDesc}`;
  }

  getCompatibilityDescription(): string {
    const level = this.compatibilityLevel;
    const score = this.compatibilityScore;

    const levelDescriptions = {
      'perfect': `Perfect soul match at ${score}% - exceptional alignment across all dimensions`,
      'high': `High compatibility at ${score}% - strong potential for deep connection`,
      'medium': `Medium compatibility at ${score}% - good foundation for relationship growth`,
      'low': `Exploring compatibility at ${score}% - discovering connection potential`
    };

    return levelDescriptions[level as keyof typeof levelDescriptions] || `Compatibility score: ${score}%`;
  }

  private getEnergyDescription(): string {
    const leftEnergy = this.leftSoul.energy;
    const rightEnergy = this.rightSoul.energy;
    const avgEnergy = (leftEnergy + rightEnergy) / 2;

    if (avgEnergy >= 4) return 'High energy levels creating dynamic soul interaction';
    if (avgEnergy >= 3) return 'Balanced energy levels supporting steady connection';
    if (avgEnergy >= 2) return 'Moderate energy levels with gentle soul resonance';
    return 'Lower energy levels in contemplative connection state';
  }

  announceConnectionDetails(): void {
    if (!this.announceChanges) return;

    const announcement = `${this.getConnectionAriaLabel()}. ${this.getCompatibilityDescription()}`;
    this.screenReader.announce(announcement, 'polite', 'soul-connection-focus');
  }

  private announceConnectionStateChange(newState: string): void {
    const stateMessages = {
      'discovering': 'Soul discovery in progress - analyzing compatibility potential',
      'connecting': 'Souls are connecting - energy synchronization beginning',
      'matched': 'Souls successfully matched - connection established',
      'strong-match': 'Exceptional soul match achieved - powerful connection formed'
    };

    const message = stateMessages[newState as keyof typeof stateMessages] || `Connection state changed to ${newState}`;
    this.screenReader.announce(message, 'assertive', 'connection-state-change');
  }

  handleKeydown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault();
        this.announceConnectionDetails();
        break;

      case 'c':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          this.announceCompatibilityDetails();
        }
        break;

      case 'e':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          this.announceEnergyLevels();
        }
        break;

      case 's':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          this.announceConnectionState();
        }
        break;
    }
  }

  private announceCompatibilityDetails(): void {
    const breakdown = {
      values: Math.floor(this.compatibilityScore * 0.3),
      interests: Math.floor(this.compatibilityScore * 0.25),
      communication: Math.floor(this.compatibilityScore * 0.45)
    };

    this.screenReader.announceCompatibilityScore(this.compatibilityScore, breakdown);
  }

  private announceEnergyLevels(): void {
    const message = `Energy levels: ${this.leftSoul.label || 'Left soul'} at level ${this.leftSoul.energy}, ${this.rightSoul.label || 'Right soul'} at level ${this.rightSoul.energy}`;
    this.screenReader.announce(message, 'polite', 'energy-levels');
  }

  private announceConnectionState(): void {
    const message = `Connection is currently in ${this.connectionState} state with ${this.compatibilityScore}% compatibility`;
    this.screenReader.announce(message, 'polite', 'connection-state');
  }
}
