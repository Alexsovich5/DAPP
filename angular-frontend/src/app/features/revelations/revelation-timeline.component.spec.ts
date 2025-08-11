/**
 * Comprehensive Revelation Timeline UI Tests - Maximum Coverage
 * Tests 7-day revelation cycle, timeline visualization, and emotional journey tracking
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ReactiveFormsModule } from '@angular/forms';
import { MatStepperModule } from '@angular/material/stepper';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatBadgeModule } from '@angular/material/badge';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { of, throwError, BehaviorSubject } from 'rxjs';

import { RevelationTimelineComponent } from './revelation-timeline.component';
import { RevelationService } from '../../core/services/revelation.service';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { ActivatedRoute } from '@angular/router';

interface RevelationDay {
  day_number: number;
  revelation_type: string;
  title: string;
  description: string;
  is_unlocked: boolean;
  unlock_date: string;
  user_revelation?: DailyRevelation;
  partner_revelation?: DailyRevelation;
  both_completed: boolean;
  is_current_day: boolean;
  emotional_theme: string;
  soul_connection_focus: string;
}

interface DailyRevelation {
  id: number;
  connection_id: number;
  sender_id: number;
  day_number: number;
  revelation_type: string;
  content: string;
  emotional_depth_score?: number;
  created_at: string;
  reactions?: RevelationReaction[];
  is_own_revelation: boolean;
  sender_name: string;
}

interface RevelationReaction {
  id: number;
  revelation_id: number;
  user_id: number;
  reaction_type: string;
  message?: string;
  created_at: string;
  user_name: string;
}

interface ConnectionProgress {
  connection_id: number;
  partner_name: string;
  compatibility_score: number;
  total_days: number;
  completed_days: number;
  current_day: number;
  days_remaining: number;
  completion_percentage: number;
  is_ahead: boolean;
  is_behind: boolean;
  next_unlock_time?: string;
  overall_emotional_depth: number;
  journey_insights: {
    strongest_connection_days: number[];
    emotional_growth_trend: number[];
    compatibility_evolution: number[];
    shared_themes: string[];
  };
}

describe('RevelationTimelineComponent', () => {
  let component: RevelationTimelineComponent;
  let fixture: ComponentFixture<RevelationTimelineComponent>;
  let revelationService: jasmine.SpyObj<RevelationService>;
  let soulConnectionService: jasmine.SpyObj<SoulConnectionService>;
  let authService: jasmine.SpyObj<AuthService>;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let webSocketService: jasmine.SpyObj<WebSocketService>;
  let dialog: jasmine.SpyObj<MatDialog>;

  const mockRevelationTimeline: RevelationDay[] = [
    {
      day_number: 1,
      revelation_type: 'personal_value',
      title: 'Share a Personal Value',
      description: 'What do you value most in relationships and life?',
      is_unlocked: true,
      unlock_date: '2025-01-15T00:00:00Z',
      user_revelation: {
        id: 1,
        connection_id: 1,
        sender_id: 1,
        day_number: 1,
        revelation_type: 'personal_value',
        content: 'Family and authenticity are the foundation of my life. I believe in being completely true to yourself and showing up for the people you love.',
        emotional_depth_score: 8.5,
        created_at: '2025-01-15T10:30:00Z',
        reactions: [
          {
            id: 1,
            revelation_id: 1,
            user_id: 2,
            reaction_type: 'heart',
            message: 'This really resonates with my own values',
            created_at: '2025-01-15T11:00:00Z',
            user_name: 'Emma'
          }
        ],
        is_own_revelation: true,
        sender_name: 'You'
      },
      partner_revelation: {
        id: 2,
        connection_id: 1,
        sender_id: 2,
        day_number: 1,
        revelation_type: 'personal_value',
        content: 'Authentic connection and personal growth drive everything I do. I value vulnerability as a strength and believe in supporting each other\'s dreams.',
        emotional_depth_score: 9.0,
        created_at: '2025-01-15T14:20:00Z',
        reactions: [
          {
            id: 2,
            revelation_id: 2,
            user_id: 1,
            reaction_type: 'inspiring',
            message: 'Beautiful perspective on vulnerability',
            created_at: '2025-01-15T14:45:00Z',
            user_name: 'You'
          }
        ],
        is_own_revelation: false,
        sender_name: 'Emma'
      },
      both_completed: true,
      is_current_day: false,
      emotional_theme: 'Foundation & Values',
      soul_connection_focus: 'Core beliefs and what drives you'
    },
    {
      day_number: 2,
      revelation_type: 'meaningful_experience',
      title: 'Share a Meaningful Experience',
      description: 'Describe an experience that shaped who you are today',
      is_unlocked: true,
      unlock_date: '2025-01-16T00:00:00Z',
      user_revelation: {
        id: 3,
        connection_id: 1,
        sender_id: 1,
        day_number: 2,
        revelation_type: 'meaningful_experience',
        content: 'Volunteering at the homeless shelter taught me that everyone has a story worth hearing. It changed how I see humanity and connection.',
        emotional_depth_score: 8.8,
        created_at: '2025-01-16T09:15:00Z',
        reactions: [],
        is_own_revelation: true,
        sender_name: 'You'
      },
      partner_revelation: {
        id: 4,
        connection_id: 1,
        sender_id: 2,
        day_number: 2,
        revelation_type: 'meaningful_experience',
        content: 'Losing my grandfather taught me to cherish every moment and conversation. He showed me that love is shown through presence and listening.',
        emotional_depth_score: 9.2,
        created_at: '2025-01-16T16:30:00Z',
        reactions: [
          {
            id: 3,
            revelation_id: 4,
            user_id: 1,
            reaction_type: 'thoughtful',
            message: 'Thank you for sharing something so personal',
            created_at: '2025-01-16T16:45:00Z',
            user_name: 'You'
          }
        ],
        is_own_revelation: false,
        sender_name: 'Emma'
      },
      both_completed: true,
      is_current_day: false,
      emotional_theme: 'Life Lessons & Growth',
      soul_connection_focus: 'Formative experiences that shaped your soul'
    },
    {
      day_number: 3,
      revelation_type: 'hope_or_dream',
      title: 'Share a Hope or Dream',
      description: 'What do you hope for in the future?',
      is_unlocked: true,
      unlock_date: '2025-01-17T00:00:00Z',
      user_revelation: {
        id: 5,
        connection_id: 1,
        sender_id: 1,
        day_number: 3,
        revelation_type: 'hope_or_dream',
        content: 'I dream of building a life where I can balance meaningful work with deep relationships. A home filled with laughter, growth, and authentic connection.',
        emotional_depth_score: 8.2,
        created_at: '2025-01-17T11:00:00Z',
        reactions: [],
        is_own_revelation: true,
        sender_name: 'You'
      },
      partner_revelation: undefined,
      both_completed: false,
      is_current_day: false,
      emotional_theme: 'Future & Aspirations',
      soul_connection_focus: 'Dreams and hopes for your journey ahead'
    },
    {
      day_number: 4,
      revelation_type: 'humor_source',
      title: 'Share What Makes You Laugh',
      description: 'What brings joy and laughter to your life?',
      is_unlocked: true,
      unlock_date: '2025-01-18T00:00:00Z',
      user_revelation: undefined,
      partner_revelation: undefined,
      both_completed: false,
      is_current_day: true,
      emotional_theme: 'Joy & Lightness',
      soul_connection_focus: 'The lighter side of your personality'
    },
    {
      day_number: 5,
      revelation_type: 'challenge_overcome',
      title: 'Share a Challenge You\'ve Overcome',
      description: 'Describe a difficulty you conquered and what you learned',
      is_unlocked: false,
      unlock_date: '2025-01-19T00:00:00Z',
      user_revelation: undefined,
      partner_revelation: undefined,
      both_completed: false,
      is_current_day: false,
      emotional_theme: 'Resilience & Strength',
      soul_connection_focus: 'Your ability to grow through challenges'
    },
    {
      day_number: 6,
      revelation_type: 'ideal_connection',
      title: 'Describe Your Ideal Connection',
      description: 'What does the perfect relationship mean to you?',
      is_unlocked: false,
      unlock_date: '2025-01-20T00:00:00Z',
      user_revelation: undefined,
      partner_revelation: undefined,
      both_completed: false,
      is_current_day: false,
      emotional_theme: 'Love & Partnership',
      soul_connection_focus: 'Your vision of deep connection'
    },
    {
      day_number: 7,
      revelation_type: 'photo_reveal',
      title: 'Photo Reveal Day',
      description: 'Share your face after sharing your soul',
      is_unlocked: false,
      unlock_date: '2025-01-21T00:00:00Z',
      user_revelation: undefined,
      partner_revelation: undefined,
      both_completed: false,
      is_current_day: false,
      emotional_theme: 'Soul Before Skin',
      soul_connection_focus: 'Revealing your physical self after emotional connection'
    }
  ];

  const mockConnectionProgress: ConnectionProgress = {
    connection_id: 1,
    partner_name: 'Emma',
    compatibility_score: 88.5,
    total_days: 7,
    completed_days: 2,
    current_day: 4,
    days_remaining: 3,
    completion_percentage: 40, // 2 days both completed out of 7
    is_ahead: true, // User completed day 3, partner hasn't
    is_behind: false,
    next_unlock_time: '2025-01-19T00:00:00Z',
    overall_emotional_depth: 8.7,
    journey_insights: {
      strongest_connection_days: [1, 2],
      emotional_growth_trend: [8.5, 8.8, 8.2],
      compatibility_evolution: [85, 88, 86],
      shared_themes: ['authenticity', 'growth', 'connection']
    }
  };

  beforeEach(async () => {
    const revelationSpy = jasmine.createSpyObj('RevelationService', [
      'getRevelationTimeline',
      'createRevelation',
      'reactToRevelation',
      'getRevelationPrompt',
      'validateRevelationContent',
      'getConnectionProgress',
      'getEmotionalInsights'
    ]);

    const soulConnectionSpy = jasmine.createSpyObj('SoulConnectionService', [
      'getConnectionInfo',
      'updateConnectionStage'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser'
    ]);

    const notificationSpy = jasmine.createSpyObj('NotificationService', [
      'showSuccess',
      'showError',
      'showInfo',
      'showWarning'
    ]);

    const webSocketSpy = jasmine.createSpyObj('WebSocketService', [
      'connect',
      'onMessage',
      'onRevelationUpdate'
    ]);

    const dialogSpy = jasmine.createSpyObj('MatDialog', [
      'open'
    ]);

    await TestBed.configureTestingModule({
      declarations: [RevelationTimelineComponent],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NoopAnimationsModule,
        ReactiveFormsModule,
        MatStepperModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatProgressBarModule,
        MatChipsModule,
        MatExpansionModule,
        MatTooltipModule,
        MatBadgeModule,
        MatDialogModule
      ],
      providers: [
        { provide: RevelationService, useValue: revelationSpy },
        { provide: SoulConnectionService, useValue: soulConnectionSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notificationSpy },
        { provide: WebSocketService, useValue: webSocketSpy },
        { provide: MatDialog, useValue: dialogSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            params: of({ connectionId: '1' }),
            queryParams: of({})
          }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RevelationTimelineComponent);
    component = fixture.componentInstance;

    revelationService = TestBed.inject(RevelationService) as jasmine.SpyObj<RevelationService>;
    soulConnectionService = TestBed.inject(SoulConnectionService) as jasmine.SpyObj<SoulConnectionService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;
    webSocketService = TestBed.inject(WebSocketService) as jasmine.SpyObj<WebSocketService>;
    dialog = TestBed.inject(MatDialog) as jasmine.SpyObj<MatDialog>;

    // Default mock returns
    authService.getCurrentUser.and.returnValue(of({
      id: 1,
      email: 'test@example.com',
      first_name: 'Test'
    }));
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with loading state', () => {
      expect(component.isLoading).toBe(true);
      expect(component.revelationTimeline).toEqual([]);
      expect(component.connectionProgress).toBeUndefined();
    });

    it('should load revelation timeline on init', fakeAsync(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      expect(revelationService.getRevelationTimeline).toHaveBeenCalledWith(1);
      expect(component.revelationTimeline).toEqual(mockRevelationTimeline);
      expect(component.connectionProgress).toEqual(mockConnectionProgress);
      expect(component.isLoading).toBe(false);
    }));

    it('should handle timeline loading errors', fakeAsync(() => {
      revelationService.getRevelationTimeline.and.returnValue(
        throwError({ error: { detail: 'Timeline unavailable' } })
      );

      fixture.detectChanges();
      tick();

      expect(component.loadingError).toBeTruthy();
      expect(notificationService.showError).toHaveBeenCalledWith(
        'Unable to load revelation timeline. Please try again later.'
      );
    }));

    it('should establish WebSocket connection for real-time updates', fakeAsync(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      expect(webSocketService.connect).toHaveBeenCalled();
    }));
  });

  describe('Timeline Visualization', () => {
    beforeEach(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));
    });

    it('should display all 7 days in timeline', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const dayCards = fixture.debugElement.queryAll(By.css('.day-card'));
      expect(dayCards.length).toBe(7);

      dayCards.forEach((card, index) => {
        expect(card.nativeElement.textContent).toContain(`Day ${index + 1}`);
      });
    }));

    it('should show different states for each day', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const completedDays = fixture.debugElement.queryAll(By.css('.day-card.completed'));
      const currentDay = fixture.debugElement.query(By.css('.day-card.current'));
      const lockedDays = fixture.debugElement.queryAll(By.css('.day-card.locked'));

      expect(completedDays.length).toBe(2); // Days 1 and 2 both completed
      expect(currentDay).toBeTruthy(); // Day 4 is current
      expect(lockedDays.length).toBe(3); // Days 5, 6, 7 are locked
    }));

    it('should display revelation types and themes', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const themeElements = fixture.debugElement.queryAll(By.css('.emotional-theme'));
      expect(themeElements.length).toBe(7);

      expect(themeElements[0].nativeElement.textContent).toContain('Foundation & Values');
      expect(themeElements[1].nativeElement.textContent).toContain('Life Lessons & Growth');
    }));

    it('should show progress indicators', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const progressBar = fixture.debugElement.query(By.css('.overall-progress'));
      expect(progressBar).toBeTruthy();
      expect(progressBar.nativeElement.getAttribute('value')).toBe('40'); // 40% completion

      const dayProgress = fixture.debugElement.queryAll(By.css('.day-progress'));
      expect(dayProgress.length).toBe(7);
    }));

    it('should display completion status for each day', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      // Day 1: Both completed
      const day1 = fixture.debugElement.query(By.css('.day-card[data-day="1"]'));
      const day1Status = day1.query(By.css('.completion-status'));
      expect(day1Status.nativeElement.textContent).toContain('Both completed');

      // Day 3: Only user completed
      const day3 = fixture.debugElement.query(By.css('.day-card[data-day="3"]'));
      const day3Status = day3.query(By.css('.completion-status'));
      expect(day3Status.nativeElement.textContent).toContain('You completed');
    }));

    it('should show emotional depth scores', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const depthScores = fixture.debugElement.queryAll(By.css('.emotional-depth-score'));
      expect(depthScores.length).toBeGreaterThan(0);

      const firstScore = depthScores[0];
      expect(firstScore.nativeElement.textContent).toContain('8.5');
    }));

    it('should display unlock times for locked days', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const lockedDays = fixture.debugElement.queryAll(By.css('.day-card.locked'));
      lockedDays.forEach(day => {
        const unlockTime = day.query(By.css('.unlock-time'));
        expect(unlockTime).toBeTruthy();
        expect(unlockTime.nativeElement.textContent).toContain('Unlocks');
      });
    }));

    it('should highlight current day', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const currentDay = fixture.debugElement.query(By.css('.day-card.current'));
      expect(currentDay).toBeTruthy();
      expect(currentDay.nativeElement.classList).toContain('pulse');
    }));
  });

  describe('Revelation Content Display', () => {
    beforeEach(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));
    });

    it('should display user revelations', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const userRevelations = fixture.debugElement.queryAll(By.css('.user-revelation'));
      expect(userRevelations.length).toBe(3); // User has completed days 1, 2, 3

      const firstRevelation = userRevelations[0];
      expect(firstRevelation.nativeElement.textContent).toContain('Family and authenticity');
    }));

    it('should display partner revelations', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const partnerRevelations = fixture.debugElement.queryAll(By.css('.partner-revelation'));
      expect(partnerRevelations.length).toBe(2); // Partner completed days 1, 2

      const firstPartnerRevelation = partnerRevelations[0];
      expect(firstPartnerRevelation.nativeElement.textContent).toContain('Authentic connection');
    }));

    it('should show revelation reactions', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const reactionButtons = fixture.debugElement.queryAll(By.css('.reaction-button'));
      expect(reactionButtons.length).toBeGreaterThan(0);

      const heartReactions = fixture.debugElement.queryAll(By.css('.reaction-heart'));
      expect(heartReactions.length).toBeGreaterThan(0);
    }));

    it('should display reaction messages', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const reactionMessages = fixture.debugElement.queryAll(By.css('.reaction-message'));
      expect(reactionMessages.length).toBeGreaterThan(0);

      expect(reactionMessages[0].nativeElement.textContent).toContain('This really resonates');
    }));

    it('should show character count and emotional depth', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const depthScores = fixture.debugElement.queryAll(By.css('.depth-score'));
      expect(depthScores.length).toBeGreaterThan(0);

      const characterCounts = fixture.debugElement.queryAll(By.css('.character-count'));
      expect(characterCounts.length).toBeGreaterThan(0);
    }));

    it('should handle long revelation content with read more/less', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const longRevelation = fixture.debugElement.query(By.css('.revelation-content.long'));
      if (longRevelation) {
        const readMoreButton = longRevelation.query(By.css('.read-more'));
        expect(readMoreButton).toBeTruthy();

        readMoreButton.triggerEventHandler('click', {});
        fixture.detectChanges();

        const readLessButton = longRevelation.query(By.css('.read-less'));
        expect(readLessButton).toBeTruthy();
      }
    }));

    it('should display revelation timestamps', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const timestamps = fixture.debugElement.queryAll(By.css('.revelation-timestamp'));
      expect(timestamps.length).toBeGreaterThan(0);

      expect(component.formatRevelationTime(mockRevelationTimeline[0].user_revelation!.created_at))
        .toContain('ago');
    }));
  });

  describe('Creating New Revelations', () => {
    beforeEach(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));
    });

    it('should show create revelation button for current day', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const currentDayCard = fixture.debugElement.query(By.css('.day-card.current'));
      const createButton = currentDayCard.query(By.css('.create-revelation-button'));
      
      expect(createButton).toBeTruthy();
      expect(createButton.nativeElement.textContent).toContain('Share Your');
    }));

    it('should open revelation creation dialog', fakeAsync(() => {
      const dialogRef = { afterClosed: () => of(null) };
      dialog.open.and.returnValue(dialogRef as any);
      revelationService.getRevelationPrompt.and.returnValue({
        day: 4,
        type: 'humor_source',
        title: 'Share What Makes You Laugh',
        prompt: 'What brings joy and laughter to your life?',
        examples: ['Silly pet antics', 'Dad jokes'],
        character_guidance: {
          min_length: 50,
          suggested_length: 200,
          tone: 'lighthearted'
        }
      });

      fixture.detectChanges();
      tick();

      const createButton = fixture.debugElement.query(By.css('.create-revelation-button'));
      createButton.triggerEventHandler('click', {});

      expect(dialog.open).toHaveBeenCalled();
      expect(revelationService.getRevelationPrompt).toHaveBeenCalledWith(4);
    }));

    it('should validate revelation content', fakeAsync(() => {
      revelationService.validateRevelationContent.and.returnValue({
        isValid: false,
        errors: ['Content too short'],
        suggestions: ['Add more personal details']
      });

      fixture.detectChanges();
      tick();

      const shortContent = 'Too short';
      const validation = component.validateRevelationContent(shortContent);

      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Content too short');
    }));

    it('should submit new revelation', fakeAsync(() => {
      revelationService.createRevelation.and.returnValue(of({
        id: 6,
        day_number: 4,
        revelation_type: 'humor_source',
        content: 'My dog\'s confused expression when I sing in the shower brings me endless joy',
        emotional_depth_score: 7.8,
        created_at: new Date().toISOString()
      }));

      fixture.detectChanges();
      tick();

      const revelationContent = 'My dog\'s confused expression when I sing in the shower brings me endless joy';
      component.submitRevelation(4, 'humor_source', revelationContent);

      expect(revelationService.createRevelation).toHaveBeenCalledWith(
        1, 4, 'humor_source', revelationContent
      );
      expect(notificationService.showSuccess).toHaveBeenCalledWith(
        'Day 4 revelation shared! 🌟'
      );
    }));

    it('should handle revelation submission errors', fakeAsync(() => {
      revelationService.createRevelation.and.returnValue(
        throwError({ error: { detail: 'Revelation already exists for this day' } })
      );

      fixture.detectChanges();
      tick();

      component.submitRevelation(4, 'humor_source', 'Test content');

      expect(notificationService.showError).toHaveBeenCalledWith(
        'Failed to share revelation: Revelation already exists for this day'
      );
    }));

    it('should show writing guidance and examples', fakeAsync(() => {
      const dialogRef = { afterClosed: () => of(null) };
      dialog.open.and.returnValue(dialogRef as any);

      fixture.detectChanges();
      tick();

      component.showWritingGuidance('humor_source');

      const dialogConfig = dialog.open.calls.mostRecent().args[1];
      expect(dialogConfig.data.type).toBe('humor_source');
    }));

    it('should provide real-time character count and feedback', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const testContent = 'This is a test revelation content that is getting longer';
      component.onRevelationContentChange(testContent);

      expect(component.currentCharacterCount).toBe(testContent.length);
      expect(component.getRevelationQuality(testContent)).toBeDefined();
    }));
  });

  describe('Revelation Reactions', () => {
    beforeEach(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));
    });

    it('should show reaction options', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const revelationCard = fixture.debugElement.query(By.css('.partner-revelation'));
      const reactionButton = revelationCard.query(By.css('.add-reaction'));
      
      reactionButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const reactionOptions = fixture.debugElement.queryAll(By.css('.reaction-option'));
      expect(reactionOptions.length).toBeGreaterThan(0);

      const reactionTypes = reactionOptions.map(option => option.nativeElement.textContent);
      expect(reactionTypes).toContain('❤️'); // Heart
      expect(reactionTypes).toContain('🤔'); // Thoughtful
      expect(reactionTypes).toContain('✨'); // Inspiring
    }));

    it('should submit reaction to revelation', fakeAsync(() => {
      revelationService.reactToRevelation.and.returnValue(of({
        id: 4,
        revelation_id: 2,
        reaction_type: 'inspiring',
        message: 'This touched my heart deeply',
        created_at: new Date().toISOString()
      }));

      fixture.detectChanges();
      tick();

      component.reactToRevelation(2, 'inspiring', 'This touched my heart deeply');

      expect(revelationService.reactToRevelation).toHaveBeenCalledWith(
        2, 'inspiring', 'This touched my heart deeply'
      );
      expect(notificationService.showSuccess).toHaveBeenCalledWith(
        'Reaction shared with Emma 💫'
      );
    }));

    it('should display existing reactions with user names', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const existingReactions = fixture.debugElement.queryAll(By.css('.existing-reaction'));
      expect(existingReactions.length).toBeGreaterThan(0);

      const firstReaction = existingReactions[0];
      expect(firstReaction.nativeElement.textContent).toContain('Emma');
      expect(firstReaction.nativeElement.textContent).toContain('❤️');
    }));

    it('should show reaction messages in expandable format', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const reactionWithMessage = fixture.debugElement.query(By.css('.reaction-with-message'));
      expect(reactionWithMessage).toBeTruthy();

      const expandButton = reactionWithMessage.query(By.css('.expand-reaction'));
      expandButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const fullMessage = reactionWithMessage.query(By.css('.full-reaction-message'));
      expect(fullMessage).toBeTruthy();
    }));

    it('should handle reaction errors gracefully', fakeAsync(() => {
      revelationService.reactToRevelation.and.returnValue(
        throwError({ error: { detail: 'Cannot react to your own revelation' } })
      );

      fixture.detectChanges();
      tick();

      component.reactToRevelation(1, 'heart', 'Test reaction');

      expect(notificationService.showError).toHaveBeenCalledWith(
        'Unable to add reaction: Cannot react to your own revelation'
      );
    }));

    it('should show reaction analytics', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const reactionStats = fixture.debugElement.queryAll(By.css('.reaction-stats'));
      expect(reactionStats.length).toBeGreaterThan(0);

      expect(component.getTotalReactions()).toBeGreaterThan(0);
      expect(component.getMostCommonReaction()).toBeDefined();
    }));
  });

  describe('Progress Tracking and Insights', () => {
    beforeEach(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));
    });

    it('should display overall progress statistics', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const progressStats = fixture.debugElement.query(By.css('.progress-stats'));
      expect(progressStats).toBeTruthy();

      expect(progressStats.nativeElement.textContent).toContain('40%'); // Completion percentage
      expect(progressStats.nativeElement.textContent).toContain('2 of 7'); // Completed days
    }));

    it('should show compatibility evolution', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const compatibilityChart = fixture.debugElement.query(By.css('.compatibility-evolution'));
      expect(compatibilityChart).toBeTruthy();

      const evolutionPoints = fixture.debugElement.queryAll(By.css('.evolution-point'));
      expect(evolutionPoints.length).toBe(3); // Three data points in mock data
    }));

    it('should display emotional growth trend', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const emotionalGrowth = fixture.debugElement.query(By.css('.emotional-growth'));
      expect(emotionalGrowth).toBeTruthy();

      expect(component.getEmotionalGrowthTrend()).toEqual([8.5, 8.8, 8.2]);
    }));

    it('should show shared themes and insights', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const sharedThemes = fixture.debugElement.queryAll(By.css('.shared-theme'));
      expect(sharedThemes.length).toBe(3); // Three themes in mock data

      const themeTexts = sharedThemes.map(theme => theme.nativeElement.textContent);
      expect(themeTexts).toContain('authenticity');
      expect(themeTexts).toContain('growth');
    }));

    it('should highlight strongest connection days', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const strongestDays = fixture.debugElement.queryAll(By.css('.day-card.strongest-connection'));
      expect(strongestDays.length).toBe(2); // Days 1 and 2 in mock data

      strongestDays.forEach(day => {
        expect(day.nativeElement.classList).toContain('highlight');
      });
    }));

    it('should show next unlock countdown', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const countdown = fixture.debugElement.query(By.css('.next-unlock-countdown'));
      expect(countdown).toBeTruthy();

      expect(component.getTimeUntilNextUnlock()).toBeDefined();
    }));

    it('should provide journey insights summary', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const insightsSummary = fixture.debugElement.query(By.css('.journey-insights'));
      expect(insightsSummary).toBeTruthy();

      expect(insightsSummary.nativeElement.textContent).toContain('Your soul connection journey');
    }));
  });

  describe('Real-Time Updates', () => {
    beforeEach(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
    });

    it('should handle real-time revelation updates', fakeAsync(() => {
      const newRevelation: DailyRevelation = {
        id: 7,
        connection_id: 1,
        sender_id: 2,
        day_number: 3,
        revelation_type: 'hope_or_dream',
        content: 'I dream of traveling the world while building meaningful connections',
        emotional_depth_score: 8.9,
        created_at: new Date().toISOString(),
        reactions: [],
        is_own_revelation: false,
        sender_name: 'Emma'
      };

      const revelationUpdate = {
        type: 'new_revelation',
        revelation: newRevelation
      };

      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of(revelationUpdate));

      fixture.detectChanges();
      tick();

      expect(component.handleRevelationUpdate).toHaveBeenCalledWith(revelationUpdate);
      
      // Should update the timeline
      const day3 = component.revelationTimeline.find(day => day.day_number === 3);
      expect(day3?.partner_revelation).toEqual(newRevelation);
      expect(day3?.both_completed).toBe(true);
    }));

    it('should handle real-time reaction updates', fakeAsync(() => {
      const newReaction: RevelationReaction = {
        id: 5,
        revelation_id: 1,
        user_id: 2,
        reaction_type: 'thoughtful',
        message: 'This resonates deeply with my values',
        created_at: new Date().toISOString(),
        user_name: 'Emma'
      };

      const reactionUpdate = {
        type: 'new_reaction',
        reaction: newReaction
      };

      webSocketService.onMessage.and.returnValue(of(reactionUpdate));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      // Should add reaction to the appropriate revelation
      const day1UserRevelation = component.revelationTimeline[0].user_revelation;
      expect(day1UserRevelation?.reactions).toContain(newReaction);

      expect(notificationService.showInfo).toHaveBeenCalledWith(
        'Emma reacted to your Day 1 revelation 💫'
      );
    }));

    it('should update progress in real-time', fakeAsync(() => {
      const progressUpdate = {
        type: 'progress_update',
        connection_id: 1,
        completed_days: 3,
        completion_percentage: 60
      };

      webSocketService.onMessage.and.returnValue(of(progressUpdate));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      expect(component.connectionProgress?.completed_days).toBe(3);
      expect(component.connectionProgress?.completion_percentage).toBe(60);
    }));

    it('should handle day unlock notifications', fakeAsync(() => {
      const unlockUpdate = {
        type: 'day_unlocked',
        day_number: 5,
        unlock_time: new Date().toISOString()
      };

      webSocketService.onMessage.and.returnValue(of(unlockUpdate));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      expect(notificationService.showSuccess).toHaveBeenCalledWith(
        'Day 5 is now unlocked! Ready to share your next revelation? 🌟'
      );

      const day5 = component.revelationTimeline.find(day => day.day_number === 5);
      expect(day5?.is_unlocked).toBe(true);
    }));
  });

  describe('Mobile Responsiveness', () => {
    beforeEach(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));
    });

    it('should adapt layout for mobile screens', fakeAsync(() => {
      spyOnProperty(window, 'innerWidth').and.returnValue(375);
      
      fixture.detectChanges();
      tick();

      expect(component.isMobile).toBe(true);

      const mobileTimeline = fixture.debugElement.query(By.css('.mobile-timeline'));
      expect(mobileTimeline).toBeTruthy();
    }));

    it('should use vertical timeline on mobile', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const timelineContainer = fixture.debugElement.query(By.css('.timeline-container'));
      expect(timelineContainer.nativeElement.classList).toContain('vertical');
    }));

    it('should support swipe gestures for day navigation', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const swipeContainer = fixture.debugElement.query(By.css('.swipe-container'));
      expect(swipeContainer).toBeTruthy();

      // Simulate swipe left to next day
      swipeContainer.triggerEventHandler('swipeleft', {});
      expect(component.navigateToNextDay).toHaveBeenCalled();
    }));

    it('should optimize revelation cards for mobile', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const revelationCards = fixture.debugElement.queryAll(By.css('.revelation-card.mobile'));
      revelationCards.forEach(card => {
        expect(card.nativeElement.classList).toContain('compact');
      });
    }));

    it('should use bottom sheet for revelation creation on mobile', fakeAsync(() => {
      component.isMobile = true;
      const dialogRef = { afterClosed: () => of(null) };
      dialog.open.and.returnValue(dialogRef as any);

      fixture.detectChanges();
      tick();

      component.openRevelationCreator(4);

      const dialogConfig = dialog.open.calls.mostRecent().args[1];
      expect(dialogConfig.panelClass).toContain('mobile-bottom-sheet');
    }));
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));
    });

    it('should have proper ARIA labels for timeline steps', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const dayCards = fixture.debugElement.queryAll(By.css('.day-card'));
      dayCards.forEach((card, index) => {
        expect(card.nativeElement.getAttribute('aria-label')).toContain(`Day ${index + 1}`);
        expect(card.nativeElement.getAttribute('role')).toBe('article');
      });
    }));

    it('should support keyboard navigation', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const dayCards = fixture.debugElement.queryAll(By.css('.day-card'));
      const firstCard = dayCards[0];

      firstCard.triggerEventHandler('keydown.enter', {});
      expect(component.expandDay).toHaveBeenCalledWith(1);

      firstCard.triggerEventHandler('keydown.space', {});
      expect(component.toggleDayExpansion).toHaveBeenCalledWith(1);
    }));

    it('should announce progress updates to screen readers', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const progressAnnouncement = fixture.debugElement.query(By.css('[aria-live="polite"]'));
      expect(progressAnnouncement).toBeTruthy();

      component.announceProgress('Day 4 revelation completed');
      fixture.detectChanges();

      expect(progressAnnouncement.nativeElement.textContent).toContain('Day 4 revelation completed');
    }));

    it('should provide descriptive text for emotional depth scores', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const depthScores = fixture.debugElement.queryAll(By.css('.depth-score'));
      depthScores.forEach(score => {
        expect(score.nativeElement.getAttribute('aria-label')).toContain('emotional depth');
      });
    }));

    it('should have proper focus management in dialogs', fakeAsync(() => {
      const dialogRef = { afterClosed: () => of(null) };
      dialog.open.and.returnValue(dialogRef as any);

      fixture.detectChanges();
      tick();

      component.openRevelationCreator(4);

      const dialogConfig = dialog.open.calls.mostRecent().args[1];
      expect(dialogConfig.autoFocus).toBe(true);
      expect(dialogConfig.restoreFocus).toBe(true);
    }));
  });

  describe('Performance Optimizations', () => {
    it('should use virtual scrolling for large timelines', () => {
      const largeTimeline = Array.from({ length: 30 }, (_, i) => ({
        ...mockRevelationTimeline[0],
        day_number: i + 1
      }));

      revelationService.getRevelationTimeline.and.returnValue(of(largeTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));

      fixture.detectChanges();

      const virtualScroll = fixture.debugElement.query(By.css('cdk-virtual-scroll-viewport'));
      expect(virtualScroll).toBeTruthy();
    });

    it('should track timeline days by day number for ngFor performance', () => {
      expect(component.trackByDayNumber).toBeDefined();
      expect(component.trackByDayNumber(0, mockRevelationTimeline[0])).toBe(1);
    });

    it('should lazy load revelation details', fakeAsync(() => {
      revelationService.getEmotionalInsights.and.returnValue(of({
        themes: [],
        depth_analysis: {}
      }));

      fixture.detectChanges();
      tick();

      // Should not load insights initially
      expect(revelationService.getEmotionalInsights).not.toHaveBeenCalled();

      // Only load when day is expanded
      component.expandDay(1);
      expect(revelationService.getEmotionalInsights).toHaveBeenCalledWith(1, 1);
    }));

    it('should implement intersection observer for progressive loading', fakeAsync(() => {
      spyOn(component, 'observeTimelineVisibility').and.callThrough();

      fixture.detectChanges();
      tick();

      expect(component.observeTimelineVisibility).toHaveBeenCalled();
    }));

    it('should debounce revelation content validation', fakeAsync(() => {
      spyOn(component, 'performValidation').and.callThrough();

      fixture.detectChanges();
      tick();

      // Rapid content changes
      component.onRevelationContentChange('Test 1');
      component.onRevelationContentChange('Test 2');
      component.onRevelationContentChange('Test 3');

      tick(300); // Debounce delay

      expect(component.performValidation).toHaveBeenCalledTimes(1);
    }));
  });

  describe('Error Handling', () => {
    it('should handle individual day loading failures', fakeAsync(() => {
      const partialTimeline = mockRevelationTimeline.slice(0, 3); // Only first 3 days
      revelationService.getRevelationTimeline.and.returnValue(of(partialTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onRevelationUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      // Should show available days and indicate missing ones
      const dayCards = fixture.debugElement.queryAll(By.css('.day-card'));
      expect(dayCards.length).toBe(3);

      const missingDaysMessage = fixture.debugElement.query(By.css('.missing-days-notice'));
      expect(missingDaysMessage).toBeTruthy();
    }));

    it('should retry failed revelation submissions', fakeAsync(() => {
      let callCount = 0;
      revelationService.createRevelation.and.callFake(() => {
        callCount++;
        if (callCount === 1) {
          return throwError({ error: { detail: 'Network error' } });
        }
        return of({ id: 6, day_number: 4, content: 'Success', created_at: new Date().toISOString() });
      });

      fixture.detectChanges();
      tick();

      component.submitRevelation(4, 'humor_source', 'Test content');
      tick(2000); // Wait for retry

      expect(callCount).toBe(2);
      expect(notificationService.showSuccess).toHaveBeenCalled();
    }));

    it('should handle WebSocket disconnection gracefully', fakeAsync(() => {
      revelationService.getRevelationTimeline.and.returnValue(of(mockRevelationTimeline));
      revelationService.getConnectionProgress.and.returnValue(of(mockConnectionProgress));
      webSocketService.onMessage.and.returnValue(
        throwError({ error: 'WebSocket connection lost' })
      );
      webSocketService.onRevelationUpdate.and.returnValue(of({}));

      fixture.detectChanges();
      tick();

      const offlineIndicator = fixture.debugElement.query(By.css('.offline-indicator'));
      expect(offlineIndicator).toBeTruthy();
      expect(offlineIndicator.nativeElement.textContent).toContain('Connection issues');
    }));

    it('should validate revelation content before submission', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const invalidContent = 'Too short';
      const validationResult = component.validateRevelationContent(invalidContent);

      expect(validationResult.isValid).toBe(false);
      expect(component.canSubmitRevelation(invalidContent)).toBe(false);

      // Should show validation errors
      const errorMessages = fixture.debugElement.queryAll(By.css('.validation-error'));
      expect(errorMessages.length).toBeGreaterThan(0);
    }));
  });
});