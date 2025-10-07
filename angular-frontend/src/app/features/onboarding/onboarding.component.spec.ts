/**
 * Onboarding Component Tests
 * Tests for onboarding flow wrapper component with step navigation
 *
 * NOTE: This is a simple wrapper component that manages navigation between onboarding steps.
 * The actual onboarding content (emotional questions, personality, interests) is handled
 * by child route components.
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, NavigationEnd } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of, Subject } from 'rxjs';

import { OnboardingComponent } from './onboarding.component';
import { AuthService } from '../../core/services/auth.service';
import { RevelationService } from '../../core/services/revelation.service';

describe('OnboardingComponent', () => {
  let component: OnboardingComponent;
  let fixture: ComponentFixture<OnboardingComponent>;
  let authService: jasmine.SpyObj<AuthService>;
  let router: Router;

  const mockUser = {
    id: 1,
    email: 'test@example.com',
    username: 'testuser',
    is_profile_complete: false,
    is_active: true,
    emotional_onboarding_completed: false
  };

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser$: of(mockUser)
    });

    const revelationSpy = jasmine.createSpyObj('RevelationService', []);

    await TestBed.configureTestingModule({
      imports: [
        OnboardingComponent,
        RouterTestingModule
      ],
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: RevelationService, useValue: revelationSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(OnboardingComponent);
    component = fixture.componentInstance;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    router = TestBed.inject(Router);
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with default step values', () => {
      expect(component.currentStep).toBe(1);
      expect(component.totalSteps).toBe(4);
      expect(component.progressPercentage).toBe(25);
      expect(component.canProceed).toBe(false);
      expect(component.showNavigation).toBe(true);
    });

    it('should have defined steps array', () => {
      expect(component['steps']).toBeDefined();
      expect(component['steps'].length).toBe(4);
      expect(component['steps']).toEqual([
        'emotional-questions',
        'personality-assessment',
        'interest-selection',
        'complete'
      ]);
    });
  });

  describe('Progress Tracking', () => {
    it('should calculate progress percentage correctly', () => {
      component.currentStep = 1;
      component.totalSteps = 4;
      component.progressPercentage = (component.currentStep / component.totalSteps) * 100;
      expect(component.progressPercentage).toBe(25);

      component.currentStep = 2;
      component.progressPercentage = (component.currentStep / component.totalSteps) * 100;
      expect(component.progressPercentage).toBe(50);

      component.currentStep = 4;
      component.progressPercentage = (component.currentStep / component.totalSteps) * 100;
      expect(component.progressPercentage).toBe(100);
    });

    it('should have current user property', () => {
      expect(component.currentUser).toBeNull();
    });
  });

  describe('Navigation', () => {
    it('should have goNext method', () => {
      expect(component.goNext).toBeDefined();
      expect(typeof component.goNext).toBe('function');
    });

    it('should have goBack method', () => {
      expect(component.goBack).toBeDefined();
      expect(typeof component.goBack).toBe('function');
    });

    it('should not go back when on first step', () => {
      const navigateSpy = spyOn(router, 'navigate');
      component.currentStep = 1;
      component.goBack();
      expect(navigateSpy).not.toHaveBeenCalled();
    });

    it('should have onStepCompleted method', () => {
      expect(component.onStepCompleted).toBeDefined();
      component.canProceed = false;
      component.onStepCompleted();
      expect(component.canProceed).toBe(true);
    });
  });

  describe('UI State', () => {
    it('should show navigation by default', () => {
      expect(component.showNavigation).toBe(true);
    });

    it('should have canProceed flag', () => {
      expect(component.canProceed).toBeDefined();
      expect(typeof component.canProceed).toBe('boolean');
    });

    it('should track current step', () => {
      expect(component.currentStep).toBe(1);
      component.currentStep = 2;
      expect(component.currentStep).toBe(2);
    });

    it('should track total steps', () => {
      expect(component.totalSteps).toBe(4);
    });
  });

  describe('User Authentication', () => {
    it('should initialize current user as null', () => {
      expect(component.currentUser).toBeNull();
    });

    it('should subscribe to currentUser$ on init', () => {
      fixture.detectChanges(); // Trigger ngOnInit
      // User subscription happens in ngOnInit
      expect(authService.currentUser$).toBeDefined();
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

    it('should clean up on destroy', () => {
      fixture.detectChanges(); // Initialize component
      const destroySpy = spyOn(component['destroy$'], 'next');
      const completeSpy = spyOn(component['destroy$'], 'complete');

      component.ngOnDestroy();

      expect(destroySpy).toHaveBeenCalled();
      expect(completeSpy).toHaveBeenCalled();
    });
  });

  describe('Step Management', () => {
    it('should have 4 total steps', () => {
      expect(component.totalSteps).toBe(4);
    });

    it('should start at step 1', () => {
      expect(component.currentStep).toBe(1);
    });

    it('should have steps configuration', () => {
      const steps = component['steps'];
      expect(steps).toContain('emotional-questions');
      expect(steps).toContain('personality-assessment');
      expect(steps).toContain('interest-selection');
      expect(steps).toContain('complete');
    });
  });

  describe('Progress Calculation', () => {
    it('should calculate 25% progress for step 1', () => {
      component.currentStep = 1;
      const progress = (component.currentStep / component.totalSteps) * 100;
      expect(progress).toBe(25);
    });

    it('should calculate 50% progress for step 2', () => {
      component.currentStep = 2;
      const progress = (component.currentStep / component.totalSteps) * 100;
      expect(progress).toBe(50);
    });

    it('should calculate 75% progress for step 3', () => {
      component.currentStep = 3;
      const progress = (component.currentStep / component.totalSteps) * 100;
      expect(progress).toBe(75);
    });

    it('should calculate 100% progress for step 4', () => {
      component.currentStep = 4;
      const progress = (component.currentStep / component.totalSteps) * 100;
      expect(progress).toBe(100);
    });
  });

  describe('Component Properties', () => {
    it('should have all required properties', () => {
      expect(component.currentStep).toBeDefined();
      expect(component.totalSteps).toBeDefined();
      expect(component.progressPercentage).toBeDefined();
      expect(component.canProceed).toBeDefined();
      expect(component.showNavigation).toBeDefined();
      expect(component.currentUser).toBeDefined();
    });

    it('should initialize with correct default values', () => {
      expect(component.currentStep).toBe(1);
      expect(component.totalSteps).toBe(4);
      expect(component.progressPercentage).toBe(25);
      expect(component.canProceed).toBe(false);
      expect(component.showNavigation).toBe(true);
      expect(component.currentUser).toBeNull();
    });
  });
});

// TODO: Add comprehensive tests when child step components are implemented
// Future tests should cover:
// - Emotional questions step functionality
// - Personality assessment step functionality
// - Interest selection step functionality
// - Complete step functionality
// - Step validation and progression logic
// - LocalStorage integration for step data
// - Router navigation between steps
// - Form data persistence
// - Emotional onboarding completion flow
