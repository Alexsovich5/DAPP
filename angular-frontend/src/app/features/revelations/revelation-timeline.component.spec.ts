/**
 * Revelation Timeline Component Tests
 * Tests for interactive 7-day revelation journey visualization
 *
 * NOTE: This is a presentation component that receives data via @Input() and emits events via @Output().
 * It doesn't load its own data - parent components handle data loading.
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RevelationTimelineComponent, RevelationTimelineData, RevelationDayData } from './revelation-timeline.component';
import { HapticFeedbackService } from '../../core/services/haptic-feedback.service';

describe('RevelationTimelineComponent', () => {
  let component: RevelationTimelineComponent;
  let fixture: ComponentFixture<RevelationTimelineComponent>;
  let hapticService: jasmine.SpyObj<HapticFeedbackService>;

  const mockDayData: RevelationDayData = {
    day: 1,
    prompt: 'Share a personal value',
    description: 'What matters most to you?',
    isUnlocked: true,
    userShared: false,
    partnerShared: false,
    userContent: null,
    partnerContent: null,
    userSharedAt: null,
    partnerSharedAt: null
  };

  const mockTimelineData: RevelationTimelineData = {
    connectionId: 1,
    currentDay: 1,
    timeline: [mockDayData],
    completionPercentage: 14,
    progress: {
      daysUnlocked: 1,
      userSharedCount: 0,
      partnerSharedCount: 0,
      mutualDays: 0,
      nextUnlockDay: 2
    },
    visualization: {
      completionRing: 14,
      phase: 'soul_discovery'
    }
  };

  beforeEach(async () => {
    const hapticSpy = jasmine.createSpyObj('HapticFeedbackService', [
      'triggerRevelationUnlock',
      'triggerRevelationComplete',
      'triggerPhaseTransition',
      'triggerRevelationFeedback',
      'triggerSelectionFeedback',
      'triggerErrorFeedback',
      'triggerSuccessFeedback'
    ]);

    await TestBed.configureTestingModule({
      imports: [RevelationTimelineComponent],
      providers: [
        { provide: HapticFeedbackService, useValue: hapticSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RevelationTimelineComponent);
    component = fixture.componentInstance;
    hapticService = TestBed.inject(HapticFeedbackService) as jasmine.SpyObj<HapticFeedbackService>;
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should have default input values', () => {
      expect(component.timelineData).toBeNull();
      expect(component.partnerName).toBeNull();
      expect(component.canShareTodayInput).toBe(true);
      expect(component.isPhotoRevealReady).toBe(false);
      expect(component.connectionData).toBeNull();
      expect(component.currentUserId).toBeNull();
    });

    it('should have output emitters', () => {
      expect(component.dayClicked).toBeDefined();
      expect(component.shareRevelationEmit).toBeDefined();
      expect(component.viewRevelationEmit).toBeDefined();
      expect(component.photoConsentGiven).toBeDefined();
    });
  });

  describe('Input Binding', () => {
    it('should accept timelineData input', () => {
      component.timelineData = mockTimelineData;
      expect(component.timelineData).toEqual(mockTimelineData);
    });

    it('should accept partnerName input', () => {
      component.partnerName = 'Emma';
      expect(component.partnerName).toBe('Emma');
    });

    it('should accept canShareTodayInput input', () => {
      component.canShareTodayInput = false;
      expect(component.canShareTodayInput).toBe(false);
    });

    it('should accept isPhotoRevealReady input', () => {
      component.isPhotoRevealReady = true;
      expect(component.isPhotoRevealReady).toBe(true);
    });
  });

  describe('Progress Calculation', () => {
    it('should calculate progress offset', () => {
      component.timelineData = mockTimelineData;
      const offset = component.getProgressOffset();
      expect(typeof offset).toBe('string');
    });

    it('should return timeline progress', () => {
      component.timelineData = mockTimelineData;
      const progress = component.getTimelineProgress();
      expect(progress).toBeGreaterThanOrEqual(0);
      expect(progress).toBeLessThanOrEqual(100);
    });

    it('should return 0 progress when no timeline data', () => {
      component.timelineData = null;
      const progress = component.getTimelineProgress();
      expect(progress).toBe(0);
    });
  });

  describe('Phase Management', () => {
    it('should get phase color for soul_discovery', () => {
      component.timelineData = mockTimelineData;
      const color = component.getPhaseColor();
      expect(color).toBe('#667eea');
    });

    it('should get phase color for deeper_connection', () => {
      component.timelineData = {
        ...mockTimelineData,
        visualization: { ...mockTimelineData.visualization, phase: 'deeper_connection' }
      };
      const color = component.getPhaseColor();
      expect(color).toBe('#e879f9');
    });

    it('should get phase color for photo_reveal', () => {
      component.timelineData = {
        ...mockTimelineData,
        visualization: { ...mockTimelineData.visualization, phase: 'photo_reveal' }
      };
      const color = component.getPhaseColor();
      expect(color).toBe('#ffd700');
    });

    it('should get phase label', () => {
      component.timelineData = mockTimelineData;
      const label = component.getPhaseLabel();
      expect(typeof label).toBe('string');
      expect(label.length).toBeGreaterThan(0);
    });
  });

  describe('Day Management', () => {
    it('should get day classes for locked day', () => {
      const lockedDay: RevelationDayData = { ...mockDayData, isUnlocked: false };
      const classes = component.getDayClasses(lockedDay);
      expect(classes).toContain('locked');
    });

    it('should get day classes for unlocked day', () => {
      component.timelineData = mockTimelineData;
      const unlockedDay: RevelationDayData = { ...mockDayData, isUnlocked: true };
      const classes = component.getDayClasses(unlockedDay);
      expect(classes).toContain('unlocked');
    });

    it('should get day classes for completed day', () => {
      component.timelineData = mockTimelineData;
      const completedDay: RevelationDayData = {
        ...mockDayData,
        userShared: true,
        partnerShared: true
      };
      const classes = component.getDayClasses(completedDay);
      expect(classes).toContain('completed');
    });

    it('should get day ARIA label', () => {
      const label = component.getDayAriaLabel(mockDayData);
      expect(typeof label).toBe('string');
      expect(label.length).toBeGreaterThan(0);
    });

    it('should get day title for each day', () => {
      const day1Title = component.getDayTitle(1);
      expect(day1Title).toBe('Personal Values');

      const day7Title = component.getDayTitle(7);
      expect(day7Title).toBe('Photo Reveal');
    });
  });

  describe('Event Emissions', () => {
    it('should emit dayClicked when day is clicked', () => {
      spyOn(component.dayClicked, 'emit');
      component.onDayClick(mockDayData);
      expect(component.dayClicked.emit).toHaveBeenCalledWith(mockDayData);
    });

    it('should not emit for locked days', () => {
      spyOn(component.dayClicked, 'emit');
      const lockedDay: RevelationDayData = { ...mockDayData, isUnlocked: false };
      component.onDayClick(lockedDay);
      expect(component.dayClicked.emit).not.toHaveBeenCalled();
    });

    it('should emit shareRevelationEmit when share button clicked', () => {
      spyOn(component.shareRevelationEmit, 'emit');
      component.timelineData = mockTimelineData;
      component.canShareTodayInput = true;
      component.shareRevelation();
      expect(component.shareRevelationEmit.emit).toHaveBeenCalledWith(1);
    });

    it('should emit viewRevelationEmit when viewing a revelation', () => {
      spyOn(component.viewRevelationEmit, 'emit');
      const dayWithContent: RevelationDayData = {
        ...mockDayData,
        userShared: true,
        userContent: 'My personal values...'
      };
      component.viewRevelation(dayWithContent, 'user');
      expect(component.viewRevelationEmit.emit).toHaveBeenCalledWith({
        dayData: dayWithContent,
        type: 'user'
      });
    });

    it('should emit photoConsentGiven when giving consent', () => {
      spyOn(component.photoConsentGiven, 'emit');
      component.connectionData = { hasGivenPhotoConsent: false };
      component.givePhotoConsent();
      expect(component.photoConsentGiven.emit).toHaveBeenCalled();
    });
  });

  describe('Share Status Checking', () => {
    it('should check if can share today', () => {
      component.canShareTodayInput = true;
      expect(component.canShareToday()).toBe(true);
    });

    it('should check if has shared today', () => {
      component.timelineData = {
        ...mockTimelineData,
        timeline: [{ ...mockDayData, userShared: true }]
      };
      const hasShared = component.hasSharedToday();
      expect(typeof hasShared).toBe('boolean');
    });

    it('should get today prompt', () => {
      component.timelineData = mockTimelineData;
      const prompt = component.getTodayPrompt();
      expect(prompt).toBe('Share a personal value');
    });

    it('should get today description', () => {
      component.timelineData = mockTimelineData;
      const description = component.getTodayDescription();
      expect(description).toBe('What matters most to you?');
    });

    it('should get share button label', () => {
      component.timelineData = mockTimelineData;
      const label = component.getShareButtonLabel();
      expect(typeof label).toBe('string');
      expect(label.length).toBeGreaterThan(0);
    });
  });

  describe('Consent Management', () => {
    it('should check if has given consent', () => {
      component.currentUserId = 1;
      component.connectionData = { user1_id: 1, user1_photo_consent: true, user2_id: 2, user2_photo_consent: false };
      const hasConsent = component.hasGivenConsent();
      expect(hasConsent).toBe(true);
    });

    it('should return false if no connection data', () => {
      component.connectionData = null;
      const hasConsent = component.hasGivenConsent();
      expect(hasConsent).toBe(false);
    });
  });

  describe('Utility Methods', () => {
    it('should track days by day number', () => {
      const result = component.trackDay(0, mockDayData);
      expect(result).toBe(1);
    });

    it('should get timeline gradient', () => {
      component.timelineData = mockTimelineData;
      const gradient = component.getTimelineGradient();
      expect(typeof gradient).toBe('string');
      expect(gradient).toContain('linear-gradient');
    });

    it('should check if connection is active', () => {
      const isActive = component.isConnectionActive(0);
      expect(typeof isActive).toBe('boolean');
    });

    it('should get snippet from content', () => {
      const content = 'This is a long revelation that should be truncated';
      const snippet = component.getSnippet(content);
      expect(typeof snippet).toBe('string');
    });

    it('should format time', () => {
      const timestamp = '2025-01-20T10:30:00Z';
      const formatted = component.formatTime(timestamp);
      expect(typeof formatted).toBe('string');
    });
  });

  describe('Lifecycle Hooks', () => {
    it('should implement OnInit', () => {
      expect(component.ngOnInit).toBeDefined();
      expect(() => component.ngOnInit()).not.toThrow();
    });

    it('should implement OnDestroy', () => {
      expect(component.ngOnDestroy).toBeDefined();
      expect(() => component.ngOnDestroy()).not.toThrow();
    });
  });

  describe('ViewChild References', () => {
    it('should have completion ring ref', () => {
      expect(component.completionRingRef).toBeUndefined(); // Until view is initialized
    });

    it('should have timeline track ref', () => {
      expect(component.timelineTrackRef).toBeUndefined(); // Until view is initialized
    });
  });
});

// TODO: Add integration tests when component is used in parent contexts
// Future tests should cover:
// - Parent component data loading
// - Real-time revelation updates via WebSocket
// - Photo reveal flow
// - Haptic feedback integration
// - Animation timing and visual effects
// - Mobile responsive behavior
// - Accessibility keyboard navigation
