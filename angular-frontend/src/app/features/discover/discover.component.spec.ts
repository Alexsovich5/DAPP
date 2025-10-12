/**
 * Discover Component Tests
 * Tests for soul connection discovery functionality
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';

import { DiscoverComponent } from './discover.component';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { AuthService } from '../../core/services/auth.service';
import { ErrorLoggingService } from '../../core/services/error-logging.service';
import { HapticFeedbackService } from '../../core/services/haptic-feedback.service';
import { LoadingStateService } from '../../core/services/loading-state.service';
import { SoulConnectionRealtimeService } from '../../core/services/soul-connection-realtime.service';
import { WebSocketPoolService } from '../../core/services/websocket-pool.service';
import { ABTestingService } from '../../core/services/ab-testing.service';
import { DiscoveryResponse } from '../../core/interfaces/soul-connection.interfaces';

describe('DiscoverComponent', () => {
  let component: DiscoverComponent;
  let fixture: ComponentFixture<DiscoverComponent>;
  let soulConnectionService: jasmine.SpyObj<SoulConnectionService>;
  let authService: jasmine.SpyObj<AuthService>;

  const mockUser = {
    id: 1,
    email: 'test@example.com',
    username: 'testuser',
    first_name: 'Test',
    is_profile_complete: true,
    is_active: true,
    emotional_onboarding_completed: true
  };

  const mockDiscoveries: DiscoveryResponse[] = [
    {
      user_id: 2,
      profile_preview: {
        first_name: 'Emma',
        age: 28,
        location: 'San Francisco',
        bio: 'Love hiking and photography',
        interests: ['photography', 'hiking', 'cooking'],
        emotional_depth_score: 92
      },
      compatibility: {
        total_compatibility: 88.5,
        match_quality: 'high',
        breakdown: {
          interests: 85,
          values: 92,
          demographics: 78,
          communication: 90,
          personality: 83
        },
        explanation: 'Strong values alignment and shared interests'
      },
      is_photo_hidden: true
    }
  ];

  beforeEach(async () => {
    const soulConnectionSpy = jasmine.createSpyObj('SoulConnectionService', [
      'discoverSoulConnections',
      'initiateSoulConnection',
      'needsEmotionalOnboarding',
      'getMatchQualityColor'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser$: of(mockUser)
    });

    const errorLoggingSpy = jasmine.createSpyObj('ErrorLoggingService', ['logError']);
    const hapticSpy = jasmine.createSpyObj('HapticFeedbackService', [
      'triggerLoadingFeedback',
      'triggerPassFeedback',
      'triggerSuccessFeedback',
      'triggerCompatibilityFeedback',
      'triggerMatchCelebration',
      'triggerMutualInterestCelebration',
      'triggerHighCompatibilityFeedback',
      'triggerHoverFeedback',
      'triggerErrorFeedback'
    ]);
    const loadingStateSpy = jasmine.createSpyObj('LoadingStateService', [
      'startLoading',
      'stopLoading',
      'updateProgress',
      'setError'
    ]);
    const realtimeSpy = jasmine.createSpyObj('SoulConnectionRealtimeService', [
      'subscribeToCompatibilityUpdates',
      'subscribeToPresenceUpdates',
      'subscribeToConnectionStateChanges',
      'getConnectionHealth',
      'getConnectionStatus',
      'getConnectionCount',
      'getActiveConnections',
      'getUserPresence',
      'sendEnergyPulse'
    ]);
    const wsPoolSpy = jasmine.createSpyObj('WebSocketPoolService', ['getConnection', 'getConnectionCount']);
    const abTestSpy = jasmine.createSpyObj('ABTestingService', [
      'getVariantConfig',
      'isInVariant',
      'trackEvent'
    ]);

    // Setup default return values
    realtimeSpy.subscribeToCompatibilityUpdates.and.returnValue(of({}));
    realtimeSpy.subscribeToPresenceUpdates.and.returnValue(of({}));
    realtimeSpy.subscribeToConnectionStateChanges.and.returnValue(of({}));
    realtimeSpy.getConnectionHealth.and.returnValue(of('connected'));
    realtimeSpy.getConnectionStatus.and.returnValue(of(true));
    realtimeSpy.getConnectionCount.and.returnValue(of(1));
    realtimeSpy.getActiveConnections.and.returnValue(of([]));
    realtimeSpy.getUserPresence.and.returnValue(of(new Map()));
    wsPoolSpy.getConnectionCount.and.returnValue(of(1));

    await TestBed.configureTestingModule({
      imports: [
        DiscoverComponent,
        RouterTestingModule,
        BrowserAnimationsModule
      ],
      providers: [
        { provide: SoulConnectionService, useValue: soulConnectionSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: ErrorLoggingService, useValue: errorLoggingSpy },
        { provide: HapticFeedbackService, useValue: hapticSpy },
        { provide: LoadingStateService, useValue: loadingStateSpy },
        { provide: SoulConnectionRealtimeService, useValue: realtimeSpy },
        { provide: WebSocketPoolService, useValue: wsPoolSpy },
        { provide: ABTestingService, useValue: abTestSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DiscoverComponent);
    component = fixture.componentInstance;
    soulConnectionService = TestBed.inject(SoulConnectionService) as jasmine.SpyObj<SoulConnectionService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have discoveries array', () => {
    expect(component.discoveries).toEqual([]);
  });

  it('should have discoveryFilters with defaults', () => {
    expect(component.discoveryFilters).toEqual({
      max_results: 10,
      min_compatibility: 50,
      hide_photos: true,
      age_range_min: 21,
      age_range_max: 35
    });
  });

  it('should initialize on ngOnInit', () => {
    soulConnectionService.needsEmotionalOnboarding.and.returnValue(false);
    soulConnectionService.discoverSoulConnections.and.returnValue(of(mockDiscoveries));

    component.ngOnInit();

    expect(component.currentUser).toEqual(mockUser);
  });

  it('should check onboarding status', () => {
    soulConnectionService.needsEmotionalOnboarding.and.returnValue(true);

    component.ngOnInit();
    fixture.detectChanges();

    expect(component.needsOnboarding).toBe(true);
  });

  it('should load discoveries when not needing onboarding', (done) => {
    soulConnectionService.needsEmotionalOnboarding.and.returnValue(false);
    soulConnectionService.discoverSoulConnections.and.returnValue(of(mockDiscoveries));

    component.ngOnInit();

    // Wait for async currentUser$ subscription and loadDiscoveriesWithProgress intervals
    setTimeout(() => {
      expect(soulConnectionService.discoverSoulConnections).toHaveBeenCalled();
      done();
    }, 2000);
  });

  it('should handle discovery errors', (done) => {
    const errorMessage = 'Failed to load discoveries';
    soulConnectionService.needsEmotionalOnboarding.and.returnValue(false);
    soulConnectionService.discoverSoulConnections.and.returnValue(
      throwError(() => new Error(errorMessage))
    );

    component.ngOnInit();

    // Wait for async currentUser$ subscription and error handling
    setTimeout(() => {
      expect(component.error).toBeTruthy();
      done();
    }, 2000);
  });

  it('should toggle filters', () => {
    expect(component.showFilters).toBe(false);
    component.toggleFilters();
    expect(component.showFilters).toBe(true);
    component.toggleFilters();
    expect(component.showFilters).toBe(false);
  });

  it('should reset filters to defaults', () => {
    component.discoveryFilters.max_results = 20;
    component.discoveryFilters.min_compatibility = 80;

    soulConnectionService.discoverSoulConnections.and.returnValue(of([]));
    component.resetFilters();

    expect(component.discoveryFilters.max_results).toBe(10);
    expect(component.discoveryFilters.min_compatibility).toBe(50);
  });

  it('should navigate to onboarding', () => {
    const router = TestBed.inject(RouterTestingModule);
    spyOn(component['router'], 'navigate');

    component.goToOnboarding();

    expect(component['router'].navigate).toHaveBeenCalledWith(['/onboarding']);
  });

  it('should navigate to profile', () => {
    spyOn(component['router'], 'navigate');

    component.goToProfile();

    expect(component['router'].navigate).toHaveBeenCalledWith(['/profile']);
  });

  it('should handle pass action', () => {
    component.discoveries = [...mockDiscoveries];
    const initialLength = component.discoveries.length;

    component.onPass(mockDiscoveries[0].user_id);

    setTimeout(() => {
      expect(component.discoveries.length).toBeLessThan(initialLength);
    }, 400);
  });

  it('should handle connect action', () => {
    soulConnectionService.initiateSoulConnection.and.returnValue(of({
      id: 1,
      user1_id: 1,
      user2_id: 2,
      initiated_by: 1,
      connection_stage: 'soul_discovery',
      reveal_day: 1,
      mutual_reveal_consent: false,
      first_dinner_completed: false,
      status: 'active',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    }));
    component.discoveries = [...mockDiscoveries];

    component.onConnect(mockDiscoveries[0]);

    expect(soulConnectionService.initiateSoulConnection).toHaveBeenCalledWith({
      user2_id: mockDiscoveries[0].user_id
    });
  });

  it('should get compatibility color', () => {
    soulConnectionService.getMatchQualityColor.and.returnValue('#4CAF50');

    const color = component.getCompatibilityColor(85);

    expect(soulConnectionService.getMatchQualityColor).toHaveBeenCalledWith(85);
    expect(color).toBe('#4CAF50');
  });

  it('should get compatibility breakdown', () => {
    const breakdown = {
      interests: 85,
      values: 92,
      demographics: 78,
      communication: 90,
      personality: 83
    };

    const result = component.getCompatibilityBreakdown(breakdown);

    expect(result.length).toBe(5);
    expect(result[0].label).toBe('Interests');
    expect(result[0].score).toBe(85);
  });

  it('should track by userId', () => {
    const discovery = mockDiscoveries[0];
    const result = component.trackByUserId(0, discovery);

    expect(result).toBe(discovery.user_id);
  });

  it('should cleanup on destroy', () => {
    component.lastAction = {
      type: 'pass',
      item: mockDiscoveries[0],
      index: 0,
      message: 'Passed',
      timeoutId: setTimeout(() => {}, 1000)
    };

    component.ngOnDestroy();

    // Should clear timeout
    expect(component.lastAction).toBeTruthy();
  });
});

// TODO: Add comprehensive tests when full integration is complete
// Future tests should cover:
// - Swipe gesture handling (left, right, up)
// - Keyboard navigation for accessibility
// - Real-time compatibility updates via WebSocket
// - A/B testing variant configurations
// - Haptic feedback for different actions
// - Card animations and transitions
// - Filter changes and debouncing
// - Undo functionality for actions
// - Super like functionality
// - Energy pulse sending
// - Presence updates
// - Match celebration animations
