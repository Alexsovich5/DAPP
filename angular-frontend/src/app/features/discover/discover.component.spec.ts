/**
 * Comprehensive tests for Discover Component - Core Soul Connection Discovery
 * Tests soul-based matching, compatibility display, and connection initiation
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { of, throwError } from 'rxjs';

import { DiscoverComponent } from './discover.component';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';

interface PotentialMatch {
  user_id: number;
  first_name: string;
  age: number;
  compatibility_score: number;
  compatibility_breakdown: {
    interests: number;
    values: number;
    demographics: number;
    communication: number;
    personality: number;
  };
  shared_interests: string[];
  values_alignment: string[];
  distance_km?: number;
  emotional_depth_score: number;
  soul_profile_preview: {
    life_philosophy: string;
    connection_style: string;
    relationship_values: string[];
  };
  discovery_insights: {
    why_compatible: string[];
    conversation_starters: string[];
    shared_values_summary: string;
  };
}

describe('DiscoverComponent', () => {
  let component: DiscoverComponent;
  let fixture: ComponentFixture<DiscoverComponent>;
  let soulConnectionService: jasmine.SpyObj<SoulConnectionService>;
  let authService: jasmine.SpyObj<AuthService>;
  let notificationService: jasmine.SpyObj<NotificationService>;

  const mockPotentialMatches: PotentialMatch[] = [
    {
      user_id: 2,
      first_name: 'Emma',
      age: 28,
      compatibility_score: 88.5,
      compatibility_breakdown: {
        interests: 85,
        values: 92,
        demographics: 78,
        communication: 90,
        personality: 83
      },
      shared_interests: ['photography', 'hiking', 'cooking', 'meditation'],
      values_alignment: ['authenticity', 'family_first', 'personal_growth'],
      distance_km: 12.5,
      emotional_depth_score: 9.2,
      soul_profile_preview: {
        life_philosophy: 'Life is about deep connections and meaningful experiences',
        connection_style: 'Quality time and heartfelt conversations',
        relationship_values: ['loyalty', 'growth', 'adventure']
      },
      discovery_insights: {
        why_compatible: [
          'Strong values alignment around authenticity and family',
          'Shared passion for outdoor activities and mindful living',
          'Similar communication style focused on deep conversations'
        ],
        conversation_starters: [
          'Your meditation practice sounds inspiring - how did you begin?',
          'I noticed we both value authentic connections...',
          'Your photography interests caught my eye...'
        ],
        shared_values_summary: 'Both value authentic relationships and personal growth'
      }
    },
    {
      user_id: 3,
      first_name: 'Sofia',
      age: 25,
      compatibility_score: 79.2,
      compatibility_breakdown: {
        interests: 75,
        values: 88,
        demographics: 70,
        communication: 85,
        personality: 77
      },
      shared_interests: ['travel', 'reading', 'volunteering'],
      values_alignment: ['compassion', 'adventure', 'learning'],
      distance_km: 8.3,
      emotional_depth_score: 8.7,
      soul_profile_preview: {
        life_philosophy: 'Growing through challenges and helping others along the way',
        connection_style: 'Shared adventures and meaningful support',
        relationship_values: ['support', 'exploration', 'empathy']
      },
      discovery_insights: {
        why_compatible: [
          'Both passionate about making a positive impact',
          'Love for exploration and new experiences',
          'High emotional intelligence and empathy'
        ],
        conversation_starters: [
          'Your volunteer work sounds meaningful...',
          'Which travel experience changed your perspective most?'
        ],
        shared_values_summary: 'Shared commitment to personal growth and helping others'
      }
    }
  ];

  beforeEach(async () => {
    const soulConnectionSpy = jasmine.createSpyObj('SoulConnectionService', [
      'discoverPotentialMatches',
      'initiateConnection',
      'getCompatibilityInsights'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser',
      'getToken'
    ]);

    const notificationSpy = jasmine.createSpyObj('NotificationService', [
      'showSuccess',
      'showError',
      'showWarning'
    ]);

    await TestBed.configureTestingModule({
      declarations: [DiscoverComponent],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NoopAnimationsModule,
        MatCardModule,
        MatButtonModule,
        MatProgressSpinnerModule,
        MatChipsModule,
        MatIconModule
      ],
      providers: [
        { provide: SoulConnectionService, useValue: soulConnectionSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notificationSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DiscoverComponent);
    component = fixture.componentInstance;

    soulConnectionService = TestBed.inject(SoulConnectionService) as jasmine.SpyObj<SoulConnectionService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;

    authService.getCurrentUser.and.returnValue(of({ id: 1, email: 'test@example.com', first_name: 'Alex' }));
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with loading state', () => {
      expect(component.isLoading).toBe(true);
      expect(component.potentialMatches).toEqual([]);
      expect(component.selectedMatchIndex).toBe(0);
    });

    it('should load potential matches on init', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));

      fixture.detectChanges();

      expect(soulConnectionService.discoverPotentialMatches).toHaveBeenCalled();
      expect(component.potentialMatches).toEqual(mockPotentialMatches);
      expect(component.isLoading).toBe(false);
    });

    it('should handle discovery errors gracefully', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(
        throwError({ error: { detail: 'No matches found' } })
      );

      fixture.detectChanges();

      expect(component.isLoading).toBe(false);
      expect(component.discoveryError).toBeTruthy();
      expect(notificationService.showWarning).toHaveBeenCalledWith(
        'No potential matches found. Try updating your profile or check back later!'
      );
    });
  });

  describe('Match Display', () => {
    beforeEach(() => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      fixture.detectChanges();
    });

    it('should display match cards with compatibility scores', () => {
      const matchCards = fixture.debugElement.queryAll(By.css('.match-card'));
      expect(matchCards.length).toBeGreaterThan(0);

      const firstCard = matchCards[0];
      expect(firstCard.nativeElement.textContent).toContain('Emma');
      expect(firstCard.nativeElement.textContent).toContain('88.5%');
    });

    it('should show compatibility breakdown visualization', () => {
      const compatibilityBars = fixture.debugElement.queryAll(By.css('.compatibility-bar'));
      expect(compatibilityBars.length).toBeGreaterThan(0);

      // Should show different metrics
      const compatibilityLabels = fixture.debugElement.queryAll(By.css('.compatibility-metric'));
      const labelTexts = compatibilityLabels.map(label => label.nativeElement.textContent);
      
      expect(labelTexts).toContain('Values');
      expect(labelTexts).toContain('Interests');
      expect(labelTexts).toContain('Communication');
    });

    it('should display shared interests as chips', () => {
      const interestChips = fixture.debugElement.queryAll(By.css('.interest-chip'));
      expect(interestChips.length).toBeGreaterThan(0);

      const chipTexts = interestChips.map(chip => chip.nativeElement.textContent.trim());
      expect(chipTexts).toContain('photography');
      expect(chipTexts).toContain('hiking');
    });

    it('should show soul profile preview', () => {
      const profilePreview = fixture.debugElement.query(By.css('.soul-profile-preview'));
      expect(profilePreview).toBeTruthy();
      expect(profilePreview.nativeElement.textContent).toContain('deep connections');
    });

    it('should display compatibility insights', () => {
      const insights = fixture.debugElement.queryAll(By.css('.compatibility-insight'));
      expect(insights.length).toBeGreaterThan(0);
      expect(insights[0].nativeElement.textContent).toContain('values alignment');
    });

    it('should show distance information when available', () => {
      const distanceInfo = fixture.debugElement.query(By.css('.distance-info'));
      expect(distanceInfo).toBeTruthy();
      expect(distanceInfo.nativeElement.textContent).toContain('12.5 km');
    });
  });

  describe('Navigation Between Matches', () => {
    beforeEach(() => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      fixture.detectChanges();
    });

    it('should navigate to next match', () => {
      expect(component.selectedMatchIndex).toBe(0);

      component.nextMatch();

      expect(component.selectedMatchIndex).toBe(1);
    });

    it('should navigate to previous match', () => {
      component.selectedMatchIndex = 1;

      component.previousMatch();

      expect(component.selectedMatchIndex).toBe(0);
    });

    it('should wrap to first match when reaching end', () => {
      component.selectedMatchIndex = mockPotentialMatches.length - 1;

      component.nextMatch();

      expect(component.selectedMatchIndex).toBe(0);
    });

    it('should wrap to last match when going before first', () => {
      component.selectedMatchIndex = 0;

      component.previousMatch();

      expect(component.selectedMatchIndex).toBe(mockPotentialMatches.length - 1);
    });

    it('should show navigation controls when multiple matches exist', () => {
      const navButtons = fixture.debugElement.queryAll(By.css('.nav-button'));
      expect(navButtons.length).toBe(2); // Previous and Next buttons
    });
  });

  describe('Connection Initiation', () => {
    beforeEach(() => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      fixture.detectChanges();
    });

    it('should initiate connection with custom message', () => {
      const testMessage = 'Your perspective on authentic connections really resonates with me.';
      soulConnectionService.initiateConnection.and.returnValue(of({
        id: 1,
        status: 'pending',
        compatibility_score: 88.5
      }));

      component.initiateConnection(mockPotentialMatches[0], testMessage);

      expect(soulConnectionService.initiateConnection).toHaveBeenCalledWith(
        mockPotentialMatches[0].user_id,
        testMessage
      );
      expect(notificationService.showSuccess).toHaveBeenCalledWith(
        'Connection request sent to Emma! 💫'
      );
    });

    it('should use conversation starter as default message', () => {
      soulConnectionService.initiateConnection.and.returnValue(of({ id: 1, status: 'pending' }));

      component.useConversationStarter(mockPotentialMatches[0], 0);

      const expectedMessage = mockPotentialMatches[0].discovery_insights.conversation_starters[0];
      expect(soulConnectionService.initiateConnection).toHaveBeenCalledWith(
        mockPotentialMatches[0].user_id,
        expectedMessage
      );
    });

    it('should handle connection initiation errors', () => {
      soulConnectionService.initiateConnection.and.returnValue(
        throwError({ error: { detail: 'Connection limit reached' } })
      );

      component.initiateConnection(mockPotentialMatches[0], 'Test message');

      expect(notificationService.showError).toHaveBeenCalledWith(
        'Unable to send connection request: Connection limit reached'
      );
    });

    it('should disable connection button during request', () => {
      soulConnectionService.initiateConnection.and.returnValue(of({ id: 1, status: 'pending' }));

      component.initiateConnection(mockPotentialMatches[0], 'Test');

      expect(component.isConnecting).toBe(true);
      // Should complete and reset after response
      expect(component.isConnecting).toBe(false);
    });

    it('should show custom message input when clicked', () => {
      component.showMessageInput(mockPotentialMatches[0]);

      expect(component.showingMessageInput).toBe(true);
      expect(component.customMessage).toBe('');

      fixture.detectChanges();
      
      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      expect(messageInput).toBeTruthy();
    });

    it('should validate message length', () => {
      const shortMessage = 'Hi';
      const longMessage = 'a'.repeat(501); // Over 500 character limit

      expect(component.isMessageValid(shortMessage)).toBe(false);
      expect(component.isMessageValid(longMessage)).toBe(false);
      expect(component.isMessageValid('This is a meaningful message about our compatibility.')).toBe(true);
    });
  });

  describe('Compatibility Analysis', () => {
    beforeEach(() => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      fixture.detectChanges();
    });

    it('should calculate overall compatibility color', () => {
      expect(component.getCompatibilityColor(88.5)).toContain('green'); // High compatibility
      expect(component.getCompatibilityColor(65.0)).toContain('orange'); // Medium compatibility
      expect(component.getCompatibilityColor(45.0)).toContain('red'); // Lower compatibility
    });

    it('should format compatibility percentage', () => {
      expect(component.formatCompatibilityScore(88.5)).toBe('88.5%');
      expect(component.formatCompatibilityScore(92)).toBe('92.0%');
    });

    it('should get compatibility level description', () => {
      expect(component.getCompatibilityLevel(90)).toBe('Exceptional Match');
      expect(component.getCompatibilityLevel(75)).toBe('Strong Compatibility');
      expect(component.getCompatibilityLevel(60)).toBe('Good Potential');
      expect(component.getCompatibilityLevel(45)).toBe('Some Compatibility');
    });

    it('should highlight strongest compatibility areas', () => {
      const match = mockPotentialMatches[0];
      const strongestAreas = component.getStrongestCompatibilityAreas(match);

      expect(strongestAreas).toContain('Values'); // 92%
      expect(strongestAreas).toContain('Communication'); // 90%
      expect(strongestAreas.length).toBeLessThanOrEqual(3); // Top 3 areas
    });
  });

  describe('Filtering and Preferences', () => {
    it('should apply distance filter when set', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      
      component.maxDistance = 10; // 10km limit
      fixture.detectChanges();

      expect(soulConnectionService.discoverPotentialMatches).toHaveBeenCalledWith(
        jasmine.objectContaining({ maxDistance: 10 })
      );
    });

    it('should apply minimum compatibility filter', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      
      component.minCompatibility = 80;
      fixture.detectChanges();

      expect(soulConnectionService.discoverPotentialMatches).toHaveBeenCalledWith(
        jasmine.objectContaining({ minCompatibilityScore: 80 })
      );
    });

    it('should refresh matches when filters change', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      fixture.detectChanges();

      soulConnectionService.discoverPotentialMatches.calls.reset();

      component.refreshMatches();

      expect(soulConnectionService.discoverPotentialMatches).toHaveBeenCalled();
    });
  });

  describe('Responsive Behavior', () => {
    it('should adapt layout for mobile', () => {
      // Simulate mobile viewport
      spyOnProperty(window, 'innerWidth').and.returnValue(375);
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      
      fixture.detectChanges();

      expect(component.isMobile).toBe(true);
      
      const mobileLayout = fixture.debugElement.query(By.css('.mobile-layout'));
      expect(mobileLayout).toBeTruthy();
    });

    it('should use swipe gestures on mobile', () => {
      component.isMobile = true;
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      fixture.detectChanges();

      // Simulate swipe left
      component.onSwipeLeft();
      expect(component.selectedMatchIndex).toBe(1);

      // Simulate swipe right  
      component.onSwipeRight();
      expect(component.selectedMatchIndex).toBe(0);
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      fixture.detectChanges();
    });

    it('should have proper ARIA labels', () => {
      const matchCard = fixture.debugElement.query(By.css('.match-card'));
      expect(matchCard.nativeElement.getAttribute('role')).toBe('article');
      expect(matchCard.nativeElement.getAttribute('aria-label')).toContain('Emma');
    });

    it('should support keyboard navigation', () => {
      const nextButton = fixture.debugElement.query(By.css('.nav-button[aria-label="Next match"]'));
      expect(nextButton).toBeTruthy();

      // Simulate keyboard navigation
      nextButton.triggerEventHandler('keydown.enter', {});
      expect(component.selectedMatchIndex).toBe(1);
    });

    it('should announce compatibility scores to screen readers', () => {
      const compatibilityScore = fixture.debugElement.query(By.css('.compatibility-score'));
      expect(compatibilityScore.nativeElement.getAttribute('aria-label')).toContain('88.5 percent compatible');
    });
  });

  describe('Performance Optimization', () => {
    it('should track matches by user_id for ngFor performance', () => {
      expect(component.trackByUserId).toBeDefined();
      expect(component.trackByUserId(0, mockPotentialMatches[0])).toBe(mockPotentialMatches[0].user_id);
    });

    it('should lazy load match details', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      soulConnectionService.getCompatibilityInsights.and.returnValue(of({
        detailed_breakdown: {},
        compatibility_factors: []
      }));

      fixture.detectChanges();

      // Should not load detailed insights until requested
      expect(soulConnectionService.getCompatibilityInsights).not.toHaveBeenCalled();

      component.loadDetailedInsights(mockPotentialMatches[0]);

      expect(soulConnectionService.getCompatibilityInsights).toHaveBeenCalledWith(
        mockPotentialMatches[0].user_id
      );
    });
  });

  describe('Error Scenarios', () => {
    it('should handle empty matches gracefully', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(of([]));

      fixture.detectChanges();

      expect(component.potentialMatches).toEqual([]);
      expect(component.isLoading).toBe(false);

      const emptyState = fixture.debugElement.query(By.css('.empty-state'));
      expect(emptyState).toBeTruthy();
      expect(emptyState.nativeElement.textContent).toContain('No matches found');
    });

    it('should handle network connectivity issues', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(
        throwError({ name: 'NetworkError', message: 'Failed to fetch' })
      );

      fixture.detectChanges();

      expect(notificationService.showError).toHaveBeenCalledWith(
        'Connection issue. Please check your internet and try again.'
      );
    });

    it('should provide retry functionality after errors', () => {
      soulConnectionService.discoverPotentialMatches.and.returnValue(
        throwError({ error: { detail: 'Server error' } })
      );

      fixture.detectChanges();

      const retryButton = fixture.debugElement.query(By.css('.retry-button'));
      expect(retryButton).toBeTruthy();

      soulConnectionService.discoverPotentialMatches.and.returnValue(of(mockPotentialMatches));
      retryButton.triggerEventHandler('click', {});

      expect(soulConnectionService.discoverPotentialMatches).toHaveBeenCalledTimes(2);
    });
  });
});