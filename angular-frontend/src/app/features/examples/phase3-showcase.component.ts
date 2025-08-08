/**
 * Phase 3 Showcase Component - Demonstrates all advanced mobile UX features
 * This component serves as a comprehensive example and testing ground
 */
import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

// Phase 3 Services
import { AdvancedSwipeService, SwipeAction, ElasticSwipeEvent } from '../../core/services/advanced-swipe.service';
import { ResponsiveDesignService, ViewportInfo } from '../../core/services/responsive-design.service';
import { SoulAnimationService, ConnectionEnergy } from '../../core/services/soul-animation.service';
import { HapticFeedbackService } from '../../core/services/haptic-feedback.service';

// Phase 3 Components
import { SoulTypingIndicatorComponent, SoulTypingConfig } from '../../shared/components/soul-typing-indicator.component';
import { RevelationTimelineComponent, RevelationTimelineData } from '../revelations/revelation-timeline.component';

// Phase 3 Directives
import { AdvancedSwipeDirective } from '../../shared/directives/advanced-swipe.directive';

// Mock data interfaces
import { TypingUser } from '../../core/services/chat.service';

@Component({
  selector: 'app-phase3-showcase',
  standalone: true,
  imports: [
    CommonModule,
    SoulTypingIndicatorComponent,
    RevelationTimelineComponent,
    AdvancedSwipeDirective
  ],
  template: `
    <div class="phase3-showcase-container" [attr.data-breakpoint]="currentViewport?.breakpoint">
      <header class="showcase-header">
        <h1>Phase 3: Mobile UX Showcase</h1>
        <div class="viewport-info">
          <span class="info-item">{{ currentViewport?.breakpoint | uppercase }}</span>
          <span class="info-item" *ngIf="currentViewport?.isMobile">📱 Mobile</span>
          <span class="info-item" *ngIf="currentViewport?.isTablet">📋 Tablet</span>
          <span class="info-item" *ngIf="currentViewport?.isDesktop">🖥️ Desktop</span>
          <span class="info-item" *ngIf="currentViewport?.supportsTouchscreen">👆 Touch</span>
        </div>
      </header>

      <!-- Advanced Swipe Gestures Demo -->
      <section class="demo-section">
        <h2>Enhanced Swipe Gestures</h2>
        <div class="demo-cards">
          <div 
            class="swipe-demo-card"
            *ngFor="let demo of swipeDemos; trackBy: trackDemo; let i = index"
            [appAdvancedSwipe]
            [swipeActions]="demo.actions"
            [connectionEnergy]="demo.energy"
            [soulTheme]="demo.theme"
            [compatibilityScore]="demo.compatibility"
            (actionTriggered)="onSwipeAction($event, demo)"
            (swipeMove)="onSwipeProgress($event, demo)"
          >
            <div class="card-energy-indicator" [attr.data-energy]="demo.energy">
              {{ getEnergyEmoji(demo.energy) }}
            </div>
            
            <h3>{{ demo.title }}</h3>
            <p>{{ demo.description }}</p>
            
            <div class="compatibility-bar">
              <div class="compatibility-fill" [style.width.%]="demo.compatibility">
                {{ demo.compatibility }}% Match
              </div>
            </div>
            
            <div class="swipe-hints">
              <span class="hint left">❌ Pass</span>
              <span class="hint right">💝 Connect</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Soul Typing Indicators Demo -->
      <section class="demo-section">
        <h2>Soul Typing Indicators</h2>
        <div class="typing-demos">
          <div 
            class="typing-demo" 
            *ngFor="let typing of typingDemos; trackBy: trackTyping"
          >
            <h4>{{ typing.title }}</h4>
            <app-soul-typing-indicator
              [typingUser]="typing.user"
              [config]="typing.config"
              [isVisible]="typing.isActive"
            ></app-soul-typing-indicator>
            
            <div class="typing-controls">
              <button 
                class="btn btn-sm btn-energy-medium"
                (click)="toggleTyping(typing)"
              >
                {{ typing.isActive ? 'Stop' : 'Start' }} Typing
              </button>
              <button 
                class="btn btn-sm btn-energy-low"
                (click)="changeTypingEnergy(typing)"
              >
                Change Energy
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Animation System Demo -->
      <section class="demo-section">
        <h2>Soul Animation System</h2>
        <div class="animation-demos">
          <div class="animation-controls">
            <button 
              class="btn btn-energy-medium"
              (click)="startBreathingAnimation()"
            >
              Start Breathing
            </button>
            <button 
              class="btn btn-energy-high"
              (click)="createParticleSystem()"
            >
              Create Particles
            </button>
            <button 
              class="btn btn-energy-soulmate"
              (click)="triggerCelebration()"
            >
              Celebrate! 🎉
            </button>
          </div>

          <div class="animation-targets">
            <div class="animation-target breathe-target" #breatheTarget>
              <div class="target-content">
                <span class="target-emoji">😌</span>
                <span class="target-label">Breathing</span>
              </div>
            </div>
            
            <div class="animation-target particle-container" #particleContainer>
              <div class="target-content">
                <span class="target-emoji">✨</span>
                <span class="target-label">Particles</span>
              </div>
            </div>
            
            <div class="animation-target celebration-target" #celebrationTarget>
              <div class="target-content">
                <span class="target-emoji">🎊</span>
                <span class="target-label">Celebrate</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Revelation Timeline Demo -->
      <section class="demo-section">
        <h2>Progressive Revelation Timeline</h2>
        <app-revelation-timeline
          [timelineData]="mockTimelineData"
          [partnerName]="'Alex'"
          [canShareToday]="true"
          (dayClicked)="onTimelineDayClick($event)"
          (shareRevelation)="onShareRevelation($event)"
          (viewRevelation)="onViewRevelation($event)"
          (photoConsentGiven)="onPhotoConsent()"
        ></app-revelation-timeline>
      </section>

      <!-- Responsive Design Demo -->
      <section class="demo-section">
        <h2>Responsive Design System</h2>
        <div class="responsive-grid grid-auto">
          <div class="responsive-card soul-card" *ngFor="let item of responsiveItems; trackBy: trackItem">
            <h4>{{ item.title }}</h4>
            <p>{{ item.description }}</p>
            <div class="responsive-info">
              <small>Columns: {{ currentConfig?.maxColumns }}</small>
              <small>Spacing: {{ currentConfig?.baseSpacing }}</small>
            </div>
          </div>
        </div>
      </section>

      <!-- Haptic Feedback Demo -->
      <section class="demo-section">
        <h2>Haptic Feedback</h2>
        <div class="haptic-demos">
          <button 
            class="btn btn-energy-low"
            (click)="triggerHaptic('light')"
          >
            Light Impact
          </button>
          <button 
            class="btn btn-energy-medium"
            (click)="triggerHaptic('medium')"
          >
            Medium Impact
          </button>
          <button 
            class="btn btn-energy-high"
            (click)="triggerHaptic('heavy')"
          >
            Heavy Impact
          </button>
          <button 
            class="btn btn-energy-soulmate"
            (click)="triggerHaptic('soulmate')"
          >
            Soulmate Energy
          </button>
        </div>
        
        <div class="haptic-status">
          <p>
            <strong>Haptic Support:</strong> 
            {{ hapticStatus?.supported ? '✅ Supported' : '❌ Not Supported' }}
          </p>
          <p>
            <strong>Mobile Device:</strong> 
            {{ hapticStatus?.mobile ? '✅ Yes' : '❌ No' }}
          </p>
        </div>
      </section>

      <!-- Performance Metrics -->
      <section class="demo-section">
        <h2>Performance Metrics</h2>
        <div class="performance-metrics">
          <div class="metric-item">
            <span class="metric-label">Active Animations:</span>
            <span class="metric-value">{{ activeAnimationCount }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Performance Mode:</span>
            <span class="metric-value">{{ performanceMode }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Reduced Motion:</span>
            <span class="metric-value">{{ prefersReducedMotion ? 'Yes' : 'No' }}</span>
          </div>
        </div>
      </section>
    </div>
  `,
  styles: [`
    .phase3-showcase-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: var(--component-padding);
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%);
      min-height: 100vh;
    }

    .showcase-header {
      text-align: center;
      margin-bottom: 3rem;
      padding: 2rem;
      background: white;
      border-radius: 16px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }

    .showcase-header h1 {
      margin: 0 0 1rem 0;
      background: var(--phase-discovery);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      font-size: 2.5rem;
      font-weight: bold;
    }

    .viewport-info {
      display: flex;
      justify-content: center;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .info-item {
      background: rgba(102, 126, 234, 0.1);
      padding: 0.25rem 0.75rem;
      border-radius: 16px;
      font-size: 0.875rem;
      font-weight: 600;
      color: #667eea;
    }

    .demo-section {
      margin-bottom: 3rem;
      background: white;
      border-radius: 16px;
      padding: 2rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    }

    .demo-section h2 {
      margin: 0 0 1.5rem 0;
      color: #2d3748;
      font-size: 1.75rem;
      font-weight: 600;
    }

    /* Swipe Demos */
    .demo-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
    }

    .swipe-demo-card {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.9) 100%);
      border: 1px solid rgba(102, 126, 234, 0.1);
      border-radius: 12px;
      padding: 1.5rem;
      position: relative;
      cursor: grab;
      transition: all 0.3s ease;
      backdrop-filter: blur(10px);
    }

    .swipe-demo-card:active {
      cursor: grabbing;
    }

    .card-energy-indicator {
      position: absolute;
      top: 1rem;
      right: 1rem;
      font-size: 1.5rem;
    }

    .swipe-demo-card h3 {
      margin: 0 0 0.5rem 0;
      color: #2d3748;
    }

    .swipe-demo-card p {
      margin: 0 0 1rem 0;
      color: #718096;
      line-height: 1.5;
    }

    .compatibility-bar {
      background: rgba(102, 126, 234, 0.1);
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 1rem;
    }

    .compatibility-fill {
      background: var(--phase-discovery);
      color: white;
      padding: 0.5rem;
      font-size: 0.875rem;
      font-weight: 600;
      text-align: center;
      transition: width 0.5s ease;
    }

    .swipe-hints {
      display: flex;
      justify-content: space-between;
      margin-top: 1rem;
    }

    .hint {
      font-size: 0.875rem;
      opacity: 0.7;
      font-weight: 600;
    }

    /* Typing Demos */
    .typing-demos {
      display: grid;
      gap: 2rem;
    }

    .typing-demo {
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.5rem;
      background: rgba(248, 250, 252, 0.5);
    }

    .typing-demo h4 {
      margin: 0 0 1rem 0;
      color: #2d3748;
    }

    .typing-controls {
      display: flex;
      gap: 0.75rem;
      margin-top: 1rem;
    }

    /* Animation Demos */
    .animation-controls {
      display: flex;
      gap: 1rem;
      margin-bottom: 2rem;
      flex-wrap: wrap;
    }

    .animation-targets {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 2rem;
    }

    .animation-target {
      aspect-ratio: 1;
      background: rgba(102, 126, 234, 0.1);
      border: 2px dashed rgba(102, 126, 234, 0.3);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }

    .target-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
    }

    .target-emoji {
      font-size: 2rem;
    }

    .target-label {
      font-size: 0.875rem;
      color: #667eea;
      font-weight: 600;
    }

    /* Responsive Grid */
    .responsive-card {
      min-height: 150px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .responsive-info {
      display: flex;
      justify-content: space-between;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid #e2e8f0;
    }

    .responsive-info small {
      color: #718096;
    }

    /* Haptic Demos */
    .haptic-demos {
      display: flex;
      gap: 1rem;
      margin-bottom: 2rem;
      flex-wrap: wrap;
    }

    .haptic-status {
      background: rgba(248, 250, 252, 0.8);
      padding: 1rem;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
    }

    .haptic-status p {
      margin: 0.5rem 0;
    }

    /* Performance Metrics */
    .performance-metrics {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
    }

    .metric-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem;
      background: rgba(102, 126, 234, 0.05);
      border-radius: 8px;
      border: 1px solid rgba(102, 126, 234, 0.1);
    }

    .metric-label {
      font-weight: 600;
      color: #4a5568;
    }

    .metric-value {
      font-weight: bold;
      color: #667eea;
      font-size: 1.1rem;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .showcase-header h1 {
        font-size: 2rem;
      }
      
      .demo-cards {
        grid-template-columns: 1fr;
      }
      
      .animation-controls {
        justify-content: center;
      }
      
      .haptic-demos {
        justify-content: center;
      }
    }

    /* Animation states */
    .breathing {
      animation: soulBreathe 3s ease-in-out infinite;
    }

    .celebrating {
      animation: celebrate 1.5s ease-in-out;
    }

    @keyframes celebrate {
      0%, 100% { transform: scale(1) rotate(0deg); }
      25% { transform: scale(1.1) rotate(5deg); }
      50% { transform: scale(1.2) rotate(-5deg); }
      75% { transform: scale(1.1) rotate(5deg); }
    }
  `]
})
export class Phase3ShowcaseComponent implements OnInit, OnDestroy {
  @ViewChild('breatheTarget') breatheTarget!: ElementRef<HTMLElement>;
  @ViewChild('particleContainer') particleContainer!: ElementRef<HTMLElement>;
  @ViewChild('celebrationTarget') celebrationTarget!: ElementRef<HTMLElement>;

  private destroy$ = new Subject<void>();

  // Component state
  currentViewport: ViewportInfo | null = null;
  currentConfig: any = null;
  activeAnimationCount = 0;
  performanceMode = 'medium';
  prefersReducedMotion = false;
  hapticStatus: { supported: boolean; mobile: boolean } | null = null;

  // Demo data
  swipeDemos = [
    {
      id: 1,
      title: 'Sarah, 28',
      description: 'Loves hiking and deep conversations about philosophy',
      energy: 'high' as ConnectionEnergy,
      theme: 'discovery',
      compatibility: 87,
      actions: this.createSwipeActions()
    },
    {
      id: 2,
      title: 'Emma, 25',
      description: 'Artist who believes in meaningful connections',
      energy: 'soulmate' as ConnectionEnergy,
      theme: 'connection',
      compatibility: 94,
      actions: this.createSwipeActions()
    },
    {
      id: 3,
      title: 'Jessica, 30',
      description: 'Yoga instructor with a passion for mindfulness',
      energy: 'medium' as ConnectionEnergy,
      theme: 'energy',
      compatibility: 72,
      actions: this.createSwipeActions()
    }
  ];

  typingDemos = [
    {
      id: 1,
      title: 'Soul Discovery Phase',
      user: { id: '1', name: 'Alex', avatar: '', connectionStage: 'soul_discovery' as const, emotionalState: 'contemplative' as const },
      config: {
        theme: 'discovery' as const,
        connectionStage: 'soul_discovery' as const,
        emotionalState: 'contemplative' as const,
        connectionEnergy: 'medium' as const,
        compatibilityScore: 85,
        showBreathing: true,
        showPulse: true,
        showParticles: false,
        animationSpeed: 1.0
      } as SoulTypingConfig,
      isActive: true
    },
    {
      id: 2,
      title: 'Revelation Sharing',
      user: { id: '2', name: 'Sarah', avatar: '', connectionStage: 'revelation_sharing' as const, emotionalState: 'romantic' as const },
      config: {
        theme: 'revelation' as const,
        connectionStage: 'revelation_sharing' as const,
        emotionalState: 'romantic' as const,
        connectionEnergy: 'high' as const,
        compatibilityScore: 92,
        showBreathing: true,
        showPulse: true,
        showParticles: true,
        animationSpeed: 1.2
      } as SoulTypingConfig,
      isActive: false
    }
  ];

  responsiveItems = [
    { id: 1, title: 'Adaptive Layout', description: 'This grid adapts to your screen size automatically' },
    { id: 2, title: 'Touch Optimized', description: 'All interactions are optimized for touch devices' },
    { id: 3, title: 'Performance First', description: 'Animations adapt to device capabilities' },
    { id: 4, title: 'Accessible', description: 'Respects user motion preferences' },
    { id: 5, title: 'Soul Themed', description: 'Every element follows the soul-first design philosophy' }
  ];

  mockTimelineData: RevelationTimelineData = {
    connectionId: 1,
    currentDay: 3,
    completionPercentage: 42.8,
    timeline: [
      {
        day: 1,
        prompt: 'What do you value most in a relationship?',
        description: 'Share a personal value that guides your connections',
        isUnlocked: true,
        userShared: true,
        partnerShared: true,
        userContent: 'I deeply value authenticity and emotional honesty in all my relationships.',
        partnerContent: 'Trust and loyalty are the foundation of everything meaningful to me.',
        userSharedAt: '2024-01-15T10:30:00Z',
        partnerSharedAt: '2024-01-15T14:20:00Z'
      },
      {
        day: 2,
        prompt: 'Describe a meaningful experience that shaped who you are today',
        description: 'Tell about a moment that changed or defined you',
        isUnlocked: true,
        userShared: true,
        partnerShared: false,
        userContent: 'Traveling solo through Asia taught me that I\'m more resilient and adaptable than I ever imagined.',
        partnerContent: null,
        userSharedAt: '2024-01-16T09:15:00Z',
        partnerSharedAt: null
      },
      {
        day: 3,
        prompt: 'What\'s a hope or dream you hold close to your heart?',
        description: 'Share something you aspire to or dream about',
        isUnlocked: true,
        userShared: false,
        partnerShared: false,
        userContent: null,
        partnerContent: null,
        userSharedAt: null,
        partnerSharedAt: null
      }
    ],
    progress: {
      daysUnlocked: 3,
      userSharedCount: 2,
      partnerSharedCount: 1,
      mutualDays: 1,
      nextUnlockDay: 4
    },
    visualization: {
      completionRing: 42.8,
      phase: 'soul_discovery'
    }
  };

  constructor(
    private advancedSwipeService: AdvancedSwipeService,
    private responsiveService: ResponsiveDesignService,
    private animationService: SoulAnimationService,
    private hapticService: HapticFeedbackService
  ) {}

  ngOnInit(): void {
    this.subscribeToResponsiveChanges();
    this.initializeStatus();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private subscribeToResponsiveChanges(): void {
    this.responsiveService.viewport$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(viewport => {
      this.currentViewport = viewport;
    });

    this.responsiveService.config$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(config => {
      this.currentConfig = config;
    });
  }

  private initializeStatus(): void {
    this.hapticStatus = this.hapticService.getHapticStatus();
    this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.performanceMode = 'medium'; // Would come from animation service
    this.activeAnimationCount = this.animationService.getActiveAnimationsCount();
  }

  private createSwipeActions(): SwipeAction[] {
    return [
      {
        id: 'pass',
        direction: 'left',
        threshold: 100,
        icon: '❌',
        label: 'Pass',
        color: '#e53e3e',
        hapticPattern: [50, 30, 50],
        onActivate: (event) => {
          console.log('Passed profile', event);
        }
      },
      {
        id: 'connect',
        direction: 'right',
        threshold: 100,
        icon: '💝',
        label: 'Connect',
        color: '#38a169',
        hapticPattern: [100, 50, 150, 50, 100],
        onActivate: (event) => {
          console.log('Connected with profile', event);
        }
      }
    ];
  }

  // Event handlers
  onSwipeAction(event: { action: SwipeAction; event: ElasticSwipeEvent }, demo: any): void {
    console.log('Swipe action triggered:', event.action.id, 'on demo:', demo.title);
    
    if (event.action.id === 'connect') {
      this.hapticService.triggerConnectionSuccess();
    } else {
      this.hapticService.triggerPassFeedback();
    }
  }

  onSwipeProgress(event: ElasticSwipeEvent, demo: any): void {
    // Could update UI based on swipe progress
    if (event.shouldTriggerAction && event.elasticProgress > 0.7) {
      this.hapticService.triggerElasticTensionFeedback(event.elasticProgress);
    }
  }

  toggleTyping(typing: any): void {
    typing.isActive = !typing.isActive;
    this.hapticService.triggerSelectionFeedback();
  }

  changeTypingEnergy(typing: any): void {
    const energies: ConnectionEnergy[] = ['low', 'medium', 'high', 'soulmate'];
    const currentIndex = energies.indexOf(typing.config.connectionEnergy);
    const nextIndex = (currentIndex + 1) % energies.length;
    typing.config.connectionEnergy = energies[nextIndex];
    this.hapticService.triggerSelectionFeedback();
  }

  startBreathingAnimation(): void {
    if (this.breatheTarget) {
      this.animationService.createBreathingAnimation(
        this.breatheTarget.nativeElement,
        'medium'
      ).subscribe(() => {
        console.log('Breathing animation started');
      });
      
      this.breatheTarget.nativeElement.classList.add('breathing');
      this.hapticService.triggerBreathingFeedback();
    }
  }

  createParticleSystem(): void {
    if (this.particleContainer) {
      this.animationService.createParticleSystem(
        this.particleContainer.nativeElement,
        'high',
        5000
      ).subscribe((animations) => {
        console.log('Particle system created with', animations.length, 'particles');
      });
      
      this.hapticService.triggerSoulEnergyFeedback('high');
    }
  }

  triggerCelebration(): void {
    if (this.celebrationTarget) {
      this.animationService.createCelebrationAnimation(
        this.celebrationTarget.nativeElement,
        'soulmate'
      ).subscribe(() => {
        console.log('Celebration animation completed');
      });
      
      this.celebrationTarget.nativeElement.classList.add('celebrating');
      setTimeout(() => {
        this.celebrationTarget.nativeElement.classList.remove('celebrating');
      }, 1500);
      
      this.hapticService.triggerCelebrationBurst();
    }
  }

  triggerHaptic(type: 'light' | 'medium' | 'heavy' | 'soulmate'): void {
    switch (type) {
      case 'light':
        this.hapticService.triggerImpactFeedback('light');
        break;
      case 'medium':
        this.hapticService.triggerImpactFeedback('medium');
        break;
      case 'heavy':
        this.hapticService.triggerImpactFeedback('heavy');
        break;
      case 'soulmate':
        this.hapticService.triggerSoulEnergyFeedback('soulmate');
        break;
    }
  }

  onTimelineDayClick(dayData: any): void {
    console.log('Timeline day clicked:', dayData);
    this.hapticService.triggerSelectionFeedback();
  }

  onShareRevelation(day: number): void {
    console.log('Share revelation for day:', day);
    this.hapticService.triggerRevelationFeedback();
  }

  onViewRevelation(data: any): void {
    console.log('View revelation:', data);
    this.hapticService.triggerSelectionFeedback();
  }

  onPhotoConsent(): void {
    console.log('Photo consent given');
    this.hapticService.triggerSuccessFeedback();
  }

  getEnergyEmoji(energy: ConnectionEnergy): string {
    const emojis = {
      low: '💤',
      medium: '💙',
      high: '💜',
      soulmate: '✨'
    };
    return emojis[energy];
  }

  // Track by functions
  trackDemo(index: number, demo: any): number {
    return demo.id;
  }

  trackTyping(index: number, typing: any): number {
    return typing.id;
  }

  trackItem(index: number, item: any): number {
    return item.id;
  }
}