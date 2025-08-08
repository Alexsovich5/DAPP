/**
 * Progressive Revelation Timeline Component - Phase 3 Mobile UX
 * Interactive timeline showing the 7-day soul revelation journey
 */
import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ChangeDetectionStrategy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, interval, takeUntil, animationFrameScheduler } from 'rxjs';
import { HapticFeedbackService } from '../../core/services/haptic-feedback.service';

export interface RevelationTimelineData {
  connectionId: number;
  currentDay: number;
  timeline: RevelationDayData[];
  completionPercentage: number;
  progress: {
    daysUnlocked: number;
    userSharedCount: number;
    partnerSharedCount: number;
    mutualDays: number;
    nextUnlockDay: number | null;
  };
  visualization: {
    completionRing: number;
    phase: 'soul_discovery' | 'deeper_connection' | 'photo_reveal';
  };
}

export interface RevelationDayData {
  day: number;
  prompt: string;
  description: string;
  isUnlocked: boolean;
  userShared: boolean;
  partnerShared: boolean;
  userContent: string | null;
  partnerContent: string | null;
  userSharedAt: string | null;
  partnerSharedAt: string | null;
}

@Component({
  selector: 'app-revelation-timeline',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="revelation-timeline-container" [attr.data-phase]="timelineData?.visualization.phase">
      <!-- Progress Header -->
      <div class="timeline-header">
        <div class="progress-summary">
          <div class="completion-ring" #completionRing>
            <svg width="120" height="120" viewBox="0 0 120 120">
              <!-- Background ring -->
              <circle 
                cx="60" cy="60" r="50" 
                stroke="rgba(102, 126, 234, 0.1)" 
                stroke-width="8" 
                fill="none"
              />
              <!-- Progress ring -->
              <circle 
                cx="60" cy="60" r="50" 
                stroke="url(#progressGradient)" 
                stroke-width="8" 
                fill="none"
                stroke-linecap="round"
                stroke-dasharray="314"
                [style.stroke-dashoffset]="getProgressOffset()"
                class="progress-circle"
              />
              <!-- Gradient definition -->
              <defs>
                <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" [style.stop-color]="getPhaseColor()" stop-opacity="0.8"/>
                  <stop offset="100%" [style.stop-color]="getPhaseColor()" stop-opacity="1"/>
                </linearGradient>
              </defs>
            </svg>
            
            <!-- Center content -->
            <div class="ring-center">
              <div class="completion-percent">{{ timelineData?.completionPercentage || 0 }}%</div>
              <div class="phase-label">{{ getPhaseLabel() }}</div>
            </div>
          </div>
          
          <div class="progress-stats">
            <div class="stat-item">
              <span class="stat-number">{{ timelineData?.progress.mutualDays || 0 }}</span>
              <span class="stat-label">Mutual Days</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ timelineData?.currentDay || 1 }}</span>
              <span class="stat-label">Current Day</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Interactive Timeline -->
      <div class="timeline-track" #timelineTrack>
        <div class="timeline-progress-bar">
          <div 
            class="progress-fill" 
            [style.width.%]="getTimelineProgress()"
            [style.background]="getTimelineGradient()"
          ></div>
        </div>

        <!-- Timeline Days -->
        <div 
          class="timeline-day" 
          *ngFor="let dayData of timelineData?.timeline; trackBy: trackDay; let i = index"
          [attr.data-day]="dayData.day"
          [class]="getDayClasses(dayData)"
          (click)="onDayClick(dayData)"
          [attr.aria-label]="getDayAriaLabel(dayData)"
          [attr.tabindex]="dayData.isUnlocked ? 0 : -1"
          (keydown.enter)="onDayClick(dayData)"
          (keydown.space)="onDayClick($event, dayData)"
        >
          <!-- Day number and status -->
          <div class="day-marker">
            <div class="day-number">{{ dayData.day }}</div>
            <div class="day-status">
              <div class="user-status" [class.completed]="dayData.userShared">
                {{ dayData.userShared ? '✨' : '○' }}
              </div>
              <div class="partner-status" [class.completed]="dayData.partnerShared">
                {{ dayData.partnerShared ? '💫' : '○' }}
              </div>
            </div>
          </div>

          <!-- Day content preview -->
          <div class="day-content" *ngIf="dayData.isUnlocked">
            <h4 class="day-title">{{ getDayTitle(dayData.day) }}</h4>
            <p class="day-prompt">{{ dayData.prompt }}</p>
            
            <!-- Revelation previews -->
            <div class="revelation-previews" *ngIf="dayData.userShared || dayData.partnerShared">
              <div class="user-revelation" *ngIf="dayData.userShared" (click)="viewRevelation(dayData, 'user')">
                <div class="revelation-snippet">
                  "{{ getSnippet(dayData.userContent) }}"
                </div>
                <div class="revelation-meta">
                  <span class="author">You</span>
                  <span class="timestamp">{{ formatTime(dayData.userSharedAt) }}</span>
                </div>
              </div>
              
              <div class="partner-revelation" *ngIf="dayData.partnerShared" (click)="viewRevelation(dayData, 'partner')">
                <div class="revelation-snippet">
                  "{{ getSnippet(dayData.partnerContent) }}"
                </div>
                <div class="revelation-meta">
                  <span class="author">{{ partnerName || 'Partner' }}</span>
                  <span class="timestamp">{{ formatTime(dayData.partnerSharedAt) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Locked day indicator -->
          <div class="day-locked" *ngIf="!dayData.isUnlocked">
            <div class="lock-icon">🔒</div>
            <div class="unlock-info">
              <span *ngIf="dayData.day === (timelineData?.currentDay || 1) + 1">
                Unlocks tomorrow
              </span>
              <span *ngIf="dayData.day > (timelineData?.currentDay || 1) + 1">
                Day {{ dayData.day }} revelation
              </span>
            </div>
          </div>

          <!-- Connection lines -->
          <div class="connection-line" *ngIf="i < (timelineData?.timeline.length || 0) - 1">
            <div class="line-segment" [class.active]="isConnectionActive(i)"></div>
          </div>
        </div>
      </div>

      <!-- Current Day Actions -->
      <div class="timeline-actions" *ngIf="canShareToday()">
        <div class="today-prompt">
          <h3>{{ getTodayPrompt() }}</h3>
          <p>{{ getTodayDescription() }}</p>
        </div>
        
        <button 
          class="share-revelation-btn"
          (click)="shareRevelation()"
          [disabled]="hasSharedToday()"
          [attr.aria-label]="getShareButtonLabel()"
        >
          <span class="btn-icon">✨</span>
          <span class="btn-text">
            {{ hasSharedToday() ? 'Shared Today' : 'Share Your Soul' }}
          </span>
        </button>
      </div>

      <!-- Photo Reveal Section -->
      <div class="photo-reveal-section" *ngIf="isPhotoRevealDay()">
        <div class="photo-reveal-card">
          <div class="reveal-header">
            <h3>Photo Reveal Day! 📸</h3>
            <p>After sharing your souls this week, are you ready to see each other?</p>
          </div>
          
          <div class="mutual-consent" *ngIf="!isMutualConsentGiven()">
            <p>Both partners must consent to photo reveal</p>
            <button 
              class="consent-btn"
              (click)="givePhotoConsent()"
              [disabled]="hasGivenConsent()"
            >
              {{ hasGivenConsent() ? 'Consent Given ✓' : 'I\'m Ready to Reveal' }}
            </button>
          </div>
          
          <div class="photos-revealed" *ngIf="isMutualConsentGiven()">
            <div class="celebration">🎉 Photos Revealed! 🎉</div>
            <p>You can now see each other's photos in your connection.</p>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .revelation-timeline-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 1rem;
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%);
      border-radius: 16px;
      position: relative;
      overflow: hidden;
    }

    /* Phase-based theming */
    [data-phase="soul_discovery"] {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(164, 176, 190, 0.05) 100%);
    }

    [data-phase="deeper_connection"] {
      background: linear-gradient(135deg, rgba(232, 121, 249, 0.05) 0%, rgba(102, 126, 234, 0.05) 100%);
    }

    [data-phase="photo_reveal"] {
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.05) 0%, rgba(255, 165, 0, 0.05) 100%);
    }

    /* Progress Header */
    .timeline-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .progress-summary {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 2rem;
      flex-wrap: wrap;
    }

    .completion-ring {
      position: relative;
      display: inline-block;
    }

    .progress-circle {
      transition: stroke-dashoffset 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
      transform-origin: center;
      transform: rotate(-90deg);
    }

    .ring-center {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
    }

    .completion-percent {
      font-size: 1.5rem;
      font-weight: bold;
      color: #2d3748;
      margin-bottom: 0.25rem;
    }

    .phase-label {
      font-size: 0.8rem;
      color: #718096;
      text-transform: capitalize;
    }

    .progress-stats {
      display: flex;
      gap: 1.5rem;
    }

    .stat-item {
      text-align: center;
    }

    .stat-number {
      display: block;
      font-size: 1.25rem;
      font-weight: bold;
      color: #667eea;
      margin-bottom: 0.25rem;
    }

    .stat-label {
      font-size: 0.8rem;
      color: #718096;
    }

    /* Timeline Track */
    .timeline-track {
      position: relative;
      padding: 2rem 0;
    }

    .timeline-progress-bar {
      position: absolute;
      top: 60px;
      left: 0;
      right: 0;
      height: 4px;
      background: rgba(102, 126, 234, 0.1);
      border-radius: 2px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
      border-radius: 2px;
    }

    /* Timeline Days */
    .timeline-day {
      position: relative;
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 1.5rem;
      align-items: flex-start;
      margin-bottom: 3rem;
      cursor: pointer;
      transition: all 0.3s ease;
      border-radius: 12px;
      padding: 1rem;
    }

    .timeline-day:hover {
      background: rgba(102, 126, 234, 0.05);
      transform: translateY(-2px);
    }

    .timeline-day.unlocked {
      cursor: pointer;
    }

    .timeline-day.locked {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .timeline-day.current-day {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
      border: 2px solid rgba(102, 126, 234, 0.2);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
    }

    .timeline-day.completed {
      background: linear-gradient(135deg, rgba(72, 187, 120, 0.08) 0%, rgba(56, 178, 172, 0.08) 100%);
    }

    /* Day Marker */
    .day-marker {
      text-align: center;
      position: relative;
    }

    .day-number {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      font-size: 1.5rem;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 1rem auto;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
      position: relative;
      z-index: 2;
    }

    .day-status {
      display: flex;
      justify-content: center;
      gap: 0.5rem;
    }

    .user-status, .partner-status {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #f7fafc;
      border: 2px solid #e2e8f0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      transition: all 0.3s ease;
    }

    .user-status.completed, .partner-status.completed {
      background: linear-gradient(135deg, #ffd700, #ffa500);
      border-color: #ffd700;
      color: #744210;
      box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
    }

    /* Day Content */
    .day-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .day-title {
      font-size: 1.2rem;
      font-weight: 600;
      color: #2d3748;
      margin: 0;
    }

    .day-prompt {
      color: #4a5568;
      font-style: italic;
      margin: 0;
      line-height: 1.5;
    }

    /* Revelation Previews */
    .revelation-previews {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      margin-top: 1rem;
    }

    .user-revelation, .partner-revelation {
      background: white;
      padding: 1rem;
      border-radius: 8px;
      border-left: 4px solid;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .user-revelation {
      border-left-color: #667eea;
    }

    .partner-revelation {
      border-left-color: #e879f9;
    }

    .user-revelation:hover, .partner-revelation:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }

    .revelation-snippet {
      font-style: italic;
      color: #4a5568;
      margin-bottom: 0.5rem;
      line-height: 1.4;
    }

    .revelation-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8rem;
      color: #718096;
    }

    .author {
      font-weight: 600;
    }

    /* Locked Day */
    .day-locked {
      text-align: center;
      color: #a0aec0;
    }

    .lock-icon {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }

    .unlock-info {
      font-size: 0.9rem;
    }

    /* Connection Lines */
    .connection-line {
      position: absolute;
      top: 100px;
      left: 90px;
      width: 2px;
      height: calc(100% + 3rem);
      z-index: 1;
    }

    .line-segment {
      width: 100%;
      height: 100%;
      background: rgba(102, 126, 234, 0.2);
      transition: background-color 0.5s ease;
    }

    .line-segment.active {
      background: linear-gradient(to bottom, #667eea, #764ba2);
    }

    /* Timeline Actions */
    .timeline-actions {
      background: white;
      padding: 1.5rem;
      border-radius: 12px;
      margin-top: 2rem;
      border: 1px solid #e2e8f0;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }

    .today-prompt {
      margin-bottom: 1.5rem;
    }

    .today-prompt h3 {
      color: #2d3748;
      margin-bottom: 0.5rem;
    }

    .today-prompt p {
      color: #718096;
      margin: 0;
    }

    .share-revelation-btn {
      width: 100%;
      padding: 1rem 1.5rem;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }

    .share-revelation-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }

    .share-revelation-btn:disabled {
      background: #a0aec0;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }

    /* Photo Reveal Section */
    .photo-reveal-section {
      margin-top: 2rem;
    }

    .photo-reveal-card {
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 165, 0, 0.1) 100%);
      border: 2px solid rgba(255, 215, 0, 0.3);
      border-radius: 12px;
      padding: 1.5rem;
      text-align: center;
    }

    .reveal-header h3 {
      color: #744210;
      margin-bottom: 0.5rem;
    }

    .reveal-header p {
      color: #975a16;
      margin-bottom: 1.5rem;
    }

    .consent-btn {
      background: linear-gradient(135deg, #ffd700, #ffa500);
      color: #744210;
      border: none;
      padding: 1rem 2rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .consent-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
    }

    .consent-btn:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .celebration {
      font-size: 1.5rem;
      margin-bottom: 1rem;
      animation: celebrate 2s ease-in-out infinite;
    }

    @keyframes celebrate {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.05); }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .revelation-timeline-container {
        padding: 0.5rem;
      }

      .timeline-day {
        grid-template-columns: 80px 1fr;
        gap: 1rem;
        padding: 0.75rem;
      }

      .day-number {
        width: 50px;
        height: 50px;
        font-size: 1.2rem;
      }

      .progress-summary {
        flex-direction: column;
        gap: 1rem;
      }

      .revelation-previews {
        gap: 0.5rem;
      }

      .user-revelation, .partner-revelation {
        padding: 0.75rem;
      }
    }

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
      .progress-circle,
      .progress-fill,
      .timeline-day,
      .celebration {
        transition: none;
        animation: none;
      }
    }

    .timeline-day:focus {
      outline: 2px solid #667eea;
      outline-offset: 2px;
    }
  `]
})
export class RevelationTimelineComponent implements OnInit, OnDestroy {
  @Input() timelineData: RevelationTimelineData | null = null;
  @Input() partnerName: string | null = null;
  @Input() canShareToday = true;
  @Input() isPhotoRevealReady = false;

  @Output() dayClicked = new EventEmitter<RevelationDayData>();
  @Output() shareRevelation = new EventEmitter<number>();
  @Output() viewRevelation = new EventEmitter<{ dayData: RevelationDayData; type: 'user' | 'partner' }>();
  @Output() photoConsentGiven = new EventEmitter<void>();

  @ViewChild('completionRing', { static: false }) completionRingRef?: ElementRef;
  @ViewChild('timelineTrack', { static: false }) timelineTrackRef?: ElementRef;

  private destroy$ = new Subject<void>();

  constructor(private hapticService: HapticFeedbackService) {}

  ngOnInit(): void {
    // Animate progress ring on load
    setTimeout(() => {
      if (this.completionRingRef) {
        this.animateProgressRing();
      }
    }, 500);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private animateProgressRing(): void {
    if (!this.completionRingRef) return;

    const circle = this.completionRingRef.nativeElement.querySelector('.progress-circle') as SVGCircleElement;
    if (circle) {
      // Start from 0 and animate to current progress
      circle.style.strokeDashoffset = '314';
      setTimeout(() => {
        circle.style.strokeDashoffset = this.getProgressOffset();
      }, 100);
    }
  }

  getProgressOffset(): string {
    const completion = this.timelineData?.completionPercentage || 0;
    const circumference = 314; // 2 * π * r (r = 50)
    const offset = circumference - (circumference * completion / 100);
    return offset.toString();
  }

  getPhaseColor(): string {
    const phase = this.timelineData?.visualization.phase || 'soul_discovery';
    const colors = {
      soul_discovery: '#667eea',
      deeper_connection: '#e879f9',
      photo_reveal: '#ffd700'
    };
    return colors[phase];
  }

  getPhaseLabel(): string {
    const phase = this.timelineData?.visualization.phase || 'soul_discovery';
    return phase.replace('_', ' ');
  }

  getTimelineProgress(): number {
    if (!this.timelineData) return 0;
    return (this.timelineData.currentDay / 7) * 100;
  }

  getTimelineGradient(): string {
    const phase = this.timelineData?.visualization.phase || 'soul_discovery';
    const gradients = {
      soul_discovery: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
      deeper_connection: 'linear-gradient(90deg, #e879f9 0%, #667eea 100%)',
      photo_reveal: 'linear-gradient(90deg, #ffd700 0%, #ffa500 100%)'
    };
    return gradients[phase];
  }

  getDayClasses(dayData: RevelationDayData): string {
    const classes = [];
    
    if (dayData.isUnlocked) classes.push('unlocked');
    else classes.push('locked');
    
    if (dayData.day === this.timelineData?.currentDay) classes.push('current-day');
    
    if (dayData.userShared && dayData.partnerShared) classes.push('completed');
    
    return classes.join(' ');
  }

  getDayAriaLabel(dayData: RevelationDayData): string {
    let label = `Day ${dayData.day}: ${dayData.prompt}`;
    
    if (!dayData.isUnlocked) {
      label += ' - Locked';
    } else {
      const shared = [];
      if (dayData.userShared) shared.push('You shared');
      if (dayData.partnerShared) shared.push('Partner shared');
      
      if (shared.length > 0) {
        label += ` - ${shared.join(', ')}`;
      } else {
        label += ' - No revelations yet';
      }
    }
    
    return label;
  }

  getDayTitle(day: number): string {
    const titles = {
      1: 'Personal Values',
      2: 'Meaningful Experience',
      3: 'Hopes & Dreams',
      4: 'What Makes You Laugh',
      5: 'Overcoming Challenges',
      6: 'Ideal Connection',
      7: 'Photo Reveal'
    };
    return titles[day as keyof typeof titles] || `Day ${day}`;
  }

  isConnectionActive(index: number): boolean {
    const currentDay = this.timelineData?.currentDay || 1;
    return index < currentDay - 1;
  }

  onDayClick(event: Event | RevelationDayData, dayData?: RevelationDayData): void {
    // Handle both click and keyboard events
    const data = dayData || (event as RevelationDayData);
    
    if (!data.isUnlocked) {
      this.hapticService.triggerErrorFeedback();
      return;
    }

    this.hapticService.triggerSelectionFeedback();
    this.dayClicked.emit(data);
  }

  shareRevelation(): void {
    if (!this.canShareToday() || this.hasSharedToday()) return;
    
    this.hapticService.triggerRevelationFeedback();
    this.shareRevelation.emit(this.timelineData?.currentDay || 1);
  }

  viewRevelation(dayData: RevelationDayData, type: 'user' | 'partner'): void {
    this.hapticService.triggerSelectionFeedback();
    this.viewRevelation.emit({ dayData, type });
  }

  givePhotoConsent(): void {
    this.hapticService.triggerSuccessFeedback();
    this.photoConsentGiven.emit();
  }

  canShareToday(): boolean {
    return this.canShareToday && (this.timelineData?.currentDay || 1) <= 7;
  }

  hasSharedToday(): boolean {
    const currentDay = this.timelineData?.currentDay || 1;
    const todayData = this.timelineData?.timeline.find(d => d.day === currentDay);
    return todayData?.userShared || false;
  }

  getTodayPrompt(): string {
    const currentDay = this.timelineData?.currentDay || 1;
    const todayData = this.timelineData?.timeline.find(d => d.day === currentDay);
    return todayData?.prompt || '';
  }

  getTodayDescription(): string {
    const currentDay = this.timelineData?.currentDay || 1;
    const todayData = this.timelineData?.timeline.find(d => d.day === currentDay);
    return todayData?.description || '';
  }

  getShareButtonLabel(): string {
    if (this.hasSharedToday()) {
      return 'You have already shared your revelation today';
    }
    return `Share your Day ${this.timelineData?.currentDay || 1} revelation`;
  }

  isPhotoRevealDay(): boolean {
    return (this.timelineData?.currentDay || 1) === 7;
  }

  isMutualConsentGiven(): boolean {
    // This would be determined by the backend data
    return false; // Placeholder
  }

  hasGivenConsent(): boolean {
    // This would track user's consent status
    return false; // Placeholder
  }

  getSnippet(content: string | null): string {
    if (!content) return '';
    return content.length > 60 ? content.substring(0, 60) + '...' : content;
  }

  formatTime(timestamp: string | null): string {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = diff / (1000 * 60 * 60);
    
    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60));
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${Math.floor(hours)}h ago`;
    } else {
      const days = Math.floor(hours / 24);
      return `${days}d ago`;
    }
  }

  trackDay(index: number, dayData: RevelationDayData): number {
    return dayData.day;
  }
}