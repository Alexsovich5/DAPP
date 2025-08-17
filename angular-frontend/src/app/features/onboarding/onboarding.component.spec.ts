/**
 * Comprehensive tests for Onboarding Component - Soul Before Skin Emotional Journey
 * Tests emotional onboarding flow, profile creation, and soul mapping questions
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { By } from '@angular/platform-browser';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatStepperModule } from '@angular/material/stepper';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatCardModule } from '@angular/material/card';
import { of, throwError } from 'rxjs';

import { OnboardingComponent } from './onboarding.component';
import { OnboardingService } from '../../core/services/onboarding.service';
import { AuthService } from '../../core/services/auth.service';
import { ProfileService } from '../../core/services/profile.service';
import { NotificationService } from '../../core/services/notification.service';

interface OnboardingStep {
  stepNumber: number;
  title: string;
  description: string;
  isCompleted: boolean;
  isActive: boolean;
}

interface SoulMappingQuestion {
  id: string;
  question: string;
  type: 'text' | 'select' | 'multiselect' | 'slider';
  category: 'values' | 'connection' | 'lifestyle' | 'goals';
  options?: string[];
  placeholder?: string;
  minLength?: number;
  required: boolean;
  helpText?: string;
}

describe('OnboardingComponent', () => {
  let component: OnboardingComponent;
  let fixture: ComponentFixture<OnboardingComponent>;
  let onboardingService: jasmine.SpyObj<OnboardingService>;
  let authService: jasmine.SpyObj<AuthService>;
  let profileService: jasmine.SpyObj<ProfileService>;
  let notificationService: jasmine.SpyObj<NotificationService>;

  const mockSoulMappingQuestions: SoulMappingQuestion[] = [
    {
      id: 'relationship_values',
      question: 'What do you value most in a relationship?',
      type: 'text',
      category: 'values',
      placeholder: 'Share what authentic connection means to you...',
      minLength: 50,
      required: true,
      helpText: 'Be authentic - this helps us find your soul connections'
    },
    {
      id: 'ideal_evening',
      question: 'Describe your ideal evening with someone special',
      type: 'text',
      category: 'connection',
      placeholder: 'Paint a picture of meaningful time together...',
      minLength: 40,
      required: true
    },
    {
      id: 'understanding_moments',
      question: 'What makes you feel truly understood?',
      type: 'text',
      category: 'connection',
      placeholder: 'Describe moments when you feel deeply seen...',
      minLength: 30,
      required: true
    },
    {
      id: 'communication_style',
      question: 'How do you prefer to connect with others?',
      type: 'multiselect',
      category: 'connection',
      options: [
        'Deep conversations',
        'Shared activities',
        'Quality time together',
        'Words of affirmation',
        'Acts of service',
        'Physical touch'
      ],
      required: true
    },
    {
      id: 'life_priorities',
      question: 'What are your top life priorities right now?',
      type: 'multiselect',
      category: 'goals',
      options: [
        'Career growth',
        'Personal relationships',
        'Health & wellness',
        'Travel & adventure',
        'Creative pursuits',
        'Learning & education',
        'Family & home',
        'Community involvement'
      ],
      required: true
    }
  ];

  beforeEach(async () => {
    const onboardingSpy = jasmine.createSpyObj('OnboardingService', [
      'getSoulMappingQuestions',
      'submitOnboardingResponses',
      'getOnboardingProgress',
      'validateResponse'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser',
      'updateUser'
    ]);

    const profileSpy = jasmine.createSpyObj('ProfileService', [
      'createProfile',
      'updateProfile'
    ]);

    const notificationSpy = jasmine.createSpyObj('NotificationService', [
      'showSuccess',
      'showError',
      'showWarning'
    ]);

    await TestBed.configureTestingModule({
      declarations: [OnboardingComponent],
      imports: [
        ReactiveFormsModule,
        HttpClientTestingModule,
        RouterTestingModule,
        NoopAnimationsModule,
        MatStepperModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatProgressBarModule,
        MatChipsModule,
        MatCardModule
      ],
      providers: [
        FormBuilder,
        { provide: OnboardingService, useValue: onboardingSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: ProfileService, useValue: profileSpy },
        { provide: NotificationService, useValue: notificationSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(OnboardingComponent);
    component = fixture.componentInstance;

    onboardingService = TestBed.inject(OnboardingService) as jasmine.SpyObj<OnboardingService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    profileService = TestBed.inject(ProfileService) as jasmine.SpyObj<ProfileService>;
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;

    authService.getCurrentUser.and.returnValue(of({
      id: 1,
      email: 'test@example.com',
      first_name: 'Alex',
      emotional_onboarding_completed: false
    }));
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with welcome step', () => {
      expect(component.currentStepIndex).toBe(0);
      expect(component.onboardingProgress).toBe(0);
      expect(component.isCompleting).toBe(false);
    });

    it('should load soul mapping questions on init', () => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));

      fixture.detectChanges();

      expect(onboardingService.getSoulMappingQuestions).toHaveBeenCalled();
      expect(component.soulMappingQuestions).toEqual(mockSoulMappingQuestions);
    });

    it('should create reactive forms for all questions', () => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));

      fixture.detectChanges();

      expect(component.soulMappingForm).toBeTruthy();
      expect(component.soulMappingForm.get('relationship_values')).toBeTruthy();
      expect(component.soulMappingForm.get('communication_style')).toBeTruthy();
    });

    it('should set up form validation based on question requirements', () => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));

      fixture.detectChanges();

      const relationshipValuesControl = component.soulMappingForm.get('relationship_values');
      expect(relationshipValuesControl?.hasError('required')).toBe(true);
      expect(relationshipValuesControl?.hasError('minlength')).toBe(true);
    });
  });

  describe('Onboarding Steps Navigation', () => {
    beforeEach(() => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));
      fixture.detectChanges();
    });

    it('should navigate to next step when current step is complete', () => {
      component.currentStepIndex = 0;

      component.nextStep();

      expect(component.currentStepIndex).toBe(1);
      expect(component.onboardingProgress).toBeGreaterThan(0);
    });

    it('should navigate to previous step', () => {
      component.currentStepIndex = 2;

      component.previousStep();

      expect(component.currentStepIndex).toBe(1);
    });

    it('should prevent navigation to next step if current step is invalid', () => {
      component.currentStepIndex = 1; // Soul mapping step
      // Form is invalid by default
      
      const canProceed = component.canProceedToNextStep();

      expect(canProceed).toBe(false);
    });

    it('should calculate progress percentage correctly', () => {
      component.currentStepIndex = 2;
      component.totalSteps = 4;

      const progress = component.calculateProgress();

      expect(progress).toBe(50); // 2/4 = 50%
    });

    it('should show step indicators with correct states', () => {
      component.currentStepIndex = 1;
      fixture.detectChanges();

      const stepIndicators = fixture.debugElement.queryAll(By.css('.step-indicator'));
      expect(stepIndicators.length).toBeGreaterThan(0);

      // First step should be completed, second active, rest pending
      expect(stepIndicators[0].nativeElement.classList).toContain('completed');
      expect(stepIndicators[1].nativeElement.classList).toContain('active');
    });
  });

  describe('Soul Mapping Questions', () => {
    beforeEach(() => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));
      fixture.detectChanges();
    });

    it('should display all soul mapping questions', () => {
      const questionElements = fixture.debugElement.queryAll(By.css('.soul-question'));
      expect(questionElements.length).toBe(mockSoulMappingQuestions.length);
    });

    it('should validate text responses for minimum length', () => {
      const shortResponse = 'Too short';
      const validResponse = 'This is a meaningful response about my values and what authentic connection means to me in relationships';

      const relationshipValuesControl = component.soulMappingForm.get('relationship_values');
      
      relationshipValuesControl?.setValue(shortResponse);
      expect(relationshipValuesControl?.hasError('minlength')).toBe(true);

      relationshipValuesControl?.setValue(validResponse);
      expect(relationshipValuesControl?.hasError('minlength')).toBe(false);
    });

    it('should handle multiselect questions correctly', () => {
      const communicationControl = component.soulMappingForm.get('communication_style');
      const selectedValues = ['Deep conversations', 'Quality time together'];

      communicationControl?.setValue(selectedValues);

      expect(communicationControl?.value).toEqual(selectedValues);
      expect(communicationControl?.valid).toBe(true);
    });

    it('should provide helpful guidance for each question', () => {
      const questionWithHelp = fixture.debugElement.query(By.css('.soul-question[data-question-id="relationship_values"]'));
      const helpText = questionWithHelp.query(By.css('.help-text'));

      expect(helpText).toBeTruthy();
      expect(helpText.nativeElement.textContent).toContain('authentic');
    });

    it('should show character count for text responses', () => {
      const relationshipValuesControl = component.soulMappingForm.get('relationship_values');
      const testResponse = 'Family and authenticity are the foundations of meaningful relationships';

      relationshipValuesControl?.setValue(testResponse);
      fixture.detectChanges();

      const characterCount = fixture.debugElement.query(By.css('.character-count'));
      expect(characterCount).toBeTruthy();
      expect(characterCount.nativeElement.textContent).toContain(testResponse.length.toString());
    });

    it('should validate responses in real-time', () => {
      onboardingService.validateResponse.and.returnValue(of({
        isValid: true,
        feedback: 'Great response! This shows authentic self-reflection.',
        emotionalDepthScore: 8.5
      }));

      const relationshipValuesControl = component.soulMappingForm.get('relationship_values');
      relationshipValuesControl?.setValue('Authenticity and deep emotional connection are what I value most');

      // Trigger validation
      component.validateResponse('relationship_values');

      expect(onboardingService.validateResponse).toHaveBeenCalled();
    });
  });

  describe('Profile Creation', () => {
    beforeEach(() => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));
      fixture.detectChanges();
    });

    it('should collect basic profile information', () => {
      // Fill out basic profile form
      const basicProfileData = {
        first_name: 'Alex',
        last_name: 'Johnson',
        date_of_birth: '1995-03-15',
        gender: 'non-binary',
        location: 'San Francisco, CA'
      };

      Object.keys(basicProfileData).forEach(key => {
        const control = component.basicProfileForm?.get(key);
        control?.setValue(basicProfileData[key as keyof typeof basicProfileData]);
      });

      expect(component.basicProfileForm?.valid).toBe(true);
    });

    it('should validate age requirements', () => {
      const underageDate = new Date();
      underageDate.setFullYear(underageDate.getFullYear() - 17); // 17 years old

      const dobControl = component.basicProfileForm?.get('date_of_birth');
      dobControl?.setValue(underageDate.toISOString().split('T')[0]);

      expect(dobControl?.hasError('ageRequirement')).toBe(true);
    });

    it('should validate required profile fields', () => {
      const requiredFields = ['first_name', 'date_of_birth', 'gender'];

      requiredFields.forEach(field => {
        const control = component.basicProfileForm?.get(field);
        expect(control?.hasError('required')).toBe(true);
      });
    });
  });

  describe('Interest Selection', () => {
    beforeEach(() => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));
      fixture.detectChanges();
    });

    it('should display interest categories', () => {
      const interestCategories = fixture.debugElement.queryAll(By.css('.interest-category'));
      expect(interestCategories.length).toBeGreaterThan(0);

      const categoryTitles = interestCategories.map(cat => 
        cat.query(By.css('.category-title')).nativeElement.textContent
      );
      expect(categoryTitles).toContain('Creative & Arts');
      expect(categoryTitles).toContain('Outdoor & Adventure');
    });

    it('should allow selecting multiple interests', () => {
      const selectedInterests = ['photography', 'hiking', 'cooking', 'meditation'];
      
      selectedInterests.forEach(interest => {
        component.toggleInterest(interest);
      });

      expect(component.selectedInterests).toEqual(selectedInterests);
    });

    it('should enforce minimum interest selection', () => {
      component.selectedInterests = ['photography']; // Only 1 interest

      const canProceed = component.canProceedFromInterests();

      expect(canProceed).toBe(false);
      expect(component.interestSelectionError).toBeTruthy();
    });

    it('should categorize interests properly', () => {
      const creativeInterests = component.getInterestsByCategory('creative');
      const outdoorInterests = component.getInterestsByCategory('outdoor');

      expect(creativeInterests).toContain('photography');
      expect(creativeInterests).toContain('writing');
      expect(outdoorInterests).toContain('hiking');
      expect(outdoorInterests).toContain('camping');
    });
  });

  describe('Onboarding Completion', () => {
    beforeEach(() => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));
      fixture.detectChanges();
      
      // Set up valid form data
      component.soulMappingForm.patchValue({
        relationship_values: 'Authenticity and deep emotional connection are what I value most in relationships',
        ideal_evening: 'Cooking together while sharing stories about our dreams and experiences',
        understanding_moments: 'When someone truly listens and sees my authentic self',
        communication_style: ['Deep conversations', 'Quality time together'],
        life_priorities: ['Personal relationships', 'Health & wellness', 'Creative pursuits']
      });
    });

    it('should submit complete onboarding data', () => {
      onboardingService.submitOnboardingResponses.and.returnValue(of({
        success: true,
        profile_id: 123,
        emotional_depth_score: 8.7
      }));

      component.completeOnboarding();

      expect(onboardingService.submitOnboardingResponses).toHaveBeenCalled();
      expect(component.isCompleting).toBe(true);
    });

    it('should handle onboarding submission errors', () => {
      onboardingService.submitOnboardingResponses.and.returnValue(
        throwError({ error: { detail: 'Profile creation failed' } })
      );

      component.completeOnboarding();

      expect(notificationService.showError).toHaveBeenCalledWith(
        'Unable to complete onboarding: Profile creation failed'
      );
      expect(component.isCompleting).toBe(false);
    });

    it('should show completion success message', () => {
      onboardingService.submitOnboardingResponses.and.returnValue(of({
        success: true,
        profile_id: 123,
        emotional_depth_score: 8.7
      }));

      component.completeOnboarding();

      expect(notificationService.showSuccess).toHaveBeenCalledWith(
        '🎉 Welcome to your soul connection journey!'
      );
    });

    it('should update user onboarding status', () => {
      authService.updateUser.and.returnValue(of({
        id: 1,
        emotional_onboarding_completed: true
      }));

      onboardingService.submitOnboardingResponses.and.returnValue(of({
        success: true,
        profile_id: 123
      }));

      component.completeOnboarding();

      expect(authService.updateUser).toHaveBeenCalledWith({
        emotional_onboarding_completed: true
      });
    });

    it('should redirect to discovery after completion', () => {
      const routerSpy = spyOn(component['router'], 'navigate');
      
      onboardingService.submitOnboardingResponses.and.returnValue(of({
        success: true,
        profile_id: 123
      }));

      component.completeOnboarding();

      expect(routerSpy).toHaveBeenCalledWith(['/discover']);
    });
  });

  describe('Progress Tracking', () => {
    it('should track onboarding progress', () => {
      onboardingService.getOnboardingProgress.and.returnValue(of({
        currentStep: 2,
        totalSteps: 4,
        completedSteps: ['welcome', 'basic_profile'],
        nextStep: 'soul_mapping'
      }));

      component.loadOnboardingProgress();

      expect(component.currentStepIndex).toBe(2);
      expect(component.onboardingProgress).toBe(50); // 2/4 steps
    });

    it('should save progress periodically', () => {
      spyOn(component, 'saveProgress');
      
      // Simulate form changes
      component.soulMappingForm.get('relationship_values')?.setValue('Test response');

      fixture.detectChanges();

      // Should auto-save after form changes
      expect(component.saveProgress).toHaveBeenCalled();
    });
  });

  describe('UI/UX Features', () => {
    beforeEach(() => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));
      fixture.detectChanges();
    });

    it('should show encouraging messages throughout onboarding', () => {
      const encouragementMessages = fixture.debugElement.queryAll(By.css('.encouragement-message'));
      expect(encouragementMessages.length).toBeGreaterThan(0);
      
      const messageText = encouragementMessages[0].nativeElement.textContent;
      expect(messageText).toContain('authentic');
    });

    it('should display progress visually', () => {
      const progressBar = fixture.debugElement.query(By.css('.progress-bar'));
      expect(progressBar).toBeTruthy();
      
      const progressValue = progressBar.nativeElement.getAttribute('value');
      expect(progressValue).toBeDefined();
    });

    it('should provide examples for better responses', () => {
      const exampleButtons = fixture.debugElement.queryAll(By.css('.example-trigger'));
      expect(exampleButtons.length).toBeGreaterThan(0);

      // Click to show examples
      exampleButtons[0].triggerEventHandler('click', {});
      fixture.detectChanges();

      const examples = fixture.debugElement.queryAll(By.css('.response-example'));
      expect(examples.length).toBeGreaterThan(0);
    });

    it('should show typing indicators for character count', () => {
      const textInput = fixture.debugElement.query(By.css('textarea[formControlName="relationship_values"]'));
      const testText = 'This is a test response about my relationship values';

      textInput.triggerEventHandler('input', { target: { value: testText } });
      fixture.detectChanges();

      const characterCount = fixture.debugElement.query(By.css('.character-count'));
      expect(characterCount.nativeElement.textContent).toContain(testText.length.toString());
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      onboardingService.getSoulMappingQuestions.and.returnValue(of(mockSoulMappingQuestions));
      fixture.detectChanges();
    });

    it('should have proper ARIA labels for form fields', () => {
      const formFields = fixture.debugElement.queryAll(By.css('input, textarea, select'));
      
      formFields.forEach(field => {
        const ariaLabel = field.nativeElement.getAttribute('aria-label');
        const ariaDescribedBy = field.nativeElement.getAttribute('aria-describedby');
        
        expect(ariaLabel || ariaDescribedBy).toBeTruthy();
      });
    });

    it('should announce progress changes to screen readers', () => {
      const progressAnnouncement = fixture.debugElement.query(By.css('[aria-live="polite"]'));
      expect(progressAnnouncement).toBeTruthy();
    });

    it('should support keyboard navigation between steps', () => {
      const nextButton = fixture.debugElement.query(By.css('.next-step-button'));
      
      nextButton.triggerEventHandler('keydown.enter', {});
      
      expect(component.currentStepIndex).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle service errors gracefully', () => {
      onboardingService.getSoulMappingQuestions.and.returnValue(
        throwError({ error: { detail: 'Questions unavailable' } })
      );

      fixture.detectChanges();

      expect(component.loadingError).toBeTruthy();
      expect(notificationService.showError).toHaveBeenCalledWith(
        'Unable to load onboarding questions. Please refresh and try again.'
      );
    });

    it('should validate all required steps before completion', () => {
      // Don't fill out required forms
      component.currentStepIndex = component.totalSteps - 1;

      const canComplete = component.canCompleteOnboarding();

      expect(canComplete).toBe(false);
    });

    it('should prevent double submission', () => {
      onboardingService.submitOnboardingResponses.and.returnValue(of({ success: true }));
      
      component.completeOnboarding();
      component.completeOnboarding(); // Try to submit again

      expect(onboardingService.submitOnboardingResponses).toHaveBeenCalledTimes(1);
    });
  });

  describe('Mobile Responsiveness', () => {
    it('should adapt layout for mobile screens', () => {
      // Simulate mobile viewport
      spyOnProperty(window, 'innerWidth').and.returnValue(375);
      
      fixture.detectChanges();

      expect(component.isMobile).toBe(true);

      const mobileLayout = fixture.debugElement.query(By.css('.mobile-onboarding'));
      expect(mobileLayout).toBeTruthy();
    });

    it('should adjust step navigation for mobile', () => {
      component.isMobile = true;
      fixture.detectChanges();

      const mobileNavigation = fixture.debugElement.query(By.css('.mobile-step-navigation'));
      expect(mobileNavigation).toBeTruthy();
    });
  });
});