import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { AccessibilityService } from './accessibility.service';

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  targetSelector?: string;
  position: 'top' | 'bottom' | 'left' | 'right' | 'center';
  highlightElement?: boolean;
  showOverlay?: boolean;
  customComponent?: string;
  actions: OnboardingAction[];
  prerequisites?: string[];
  optional?: boolean;
  emotionalTheme?: 'discovery' | 'connection' | 'growth' | 'celebration';
}

export interface OnboardingAction {
  type: 'next' | 'skip' | 'complete' | 'custom';
  label: string;
  primary?: boolean;
  action?: () => void;
}

export interface OnboardingTour {
  id: string;
  name: string;
  description: string;
  steps: OnboardingStep[];
  category: 'first-time' | 'feature' | 'advanced';
  triggerCondition?: string;
  emotionalJourney?: string[];
}

export interface OnboardingState {
  currentTour: string | null;
  currentStep: number;
  completedTours: string[];
  skippedSteps: string[];
  userPreferences: {
    showTutorials: boolean;
    animationSpeed: 'slow' | 'normal' | 'fast';
    skipIntroductions: boolean;
    autoAdvance: boolean;
  };
}

@Injectable({
  providedIn: 'root'
})
export class OnboardingService {
  private readonly STORAGE_KEY = 'soul-onboarding-state';
  
  private stateSubject = new BehaviorSubject<OnboardingState>(this.getInitialState());
  private activeStepSubject = new BehaviorSubject<OnboardingStep | null>(null);
  
  public state$ = this.stateSubject.asObservable();
  public activeStep$ = this.activeStepSubject.asObservable();
  
  private tours: Map<string, OnboardingTour> = new Map();
  private currentTourSteps: OnboardingStep[] = [];

  constructor(private accessibilityService: AccessibilityService) {
    this.initializeDefaultTours();
    this.loadState();
  }

  /**
   * Initialize default onboarding tours
   */
  private initializeDefaultTours(): void {
    // First-time user journey
    this.registerTour({
      id: 'soul-first-experience',
      name: 'Welcome to Soul Before Skin',
      description: 'Discover how emotional connections work in our unique dating experience',
      category: 'first-time',
      emotionalJourney: ['curiosity', 'understanding', 'excitement', 'confidence'],
      steps: [
        {
          id: 'welcome',
          title: '✨ Welcome to Dinner First',
          description: 'Where souls connect before eyes meet. Let us show you how meaningful connections begin with emotional compatibility.',
          position: 'center',
          showOverlay: true,
          emotionalTheme: 'discovery',
          actions: [
            { type: 'next', label: 'Begin Journey', primary: true },
            { type: 'skip', label: 'Skip Tutorial' }
          ]
        },
        {
          id: 'soul-profile',
          title: '💖 Your Soul Profile',
          description: 'Share your values, dreams, and what makes you truly you. This creates the foundation for authentic connections.',
          targetSelector: '.profile-section',
          position: 'right',
          highlightElement: true,
          emotionalTheme: 'growth',
          actions: [
            { type: 'next', label: 'Continue', primary: true },
            { type: 'skip', label: 'Skip' }
          ]
        },
        {
          id: 'compatibility-magic',
          title: '🌟 Compatibility Magic',
          description: 'Our algorithm analyzes emotional compatibility, shared values, and communication styles to find your perfect matches.',
          targetSelector: '.compatibility-score',
          position: 'top',
          highlightElement: true,
          emotionalTheme: 'discovery',
          actions: [
            { type: 'next', label: 'Amazing!', primary: true },
            { type: 'skip', label: 'Skip' }
          ]
        },
        {
          id: 'soul-connections',
          title: '💫 Soul Connections',
          description: 'Discover people who align with your values and dreams. Photos are revealed after you connect emotionally.',
          targetSelector: '.soul-card',
          position: 'bottom',
          highlightElement: true,
          emotionalTheme: 'connection',
          actions: [
            { type: 'next', label: 'I love this!', primary: true },
            { type: 'skip', label: 'Skip' }
          ]
        },
        {
          id: 'meaningful-conversations',
          title: '💬 Meaningful Conversations',
          description: 'Start conversations about what truly matters. Share your thoughts, dreams, and build genuine connections.',
          targetSelector: '.message-area',
          position: 'left',
          highlightElement: true,
          emotionalTheme: 'connection',
          actions: [
            { type: 'complete', label: 'Start Connecting!', primary: true }
          ]
        }
      ]
    });

    // Discovery feature tour
    this.registerTour({
      id: 'discovery-tour',
      name: 'Soul Discovery Guide',
      description: 'Learn how to navigate and interact with potential soul connections',
      category: 'feature',
      emotionalJourney: ['exploration', 'understanding', 'confidence'],
      steps: [
        {
          id: 'discovery-filters',
          title: '🎛️ Discovery Filters',
          description: 'Customize your search by compatibility threshold, age range, and photo preferences.',
          targetSelector: '.discovery-filters',
          position: 'bottom',
          highlightElement: true,
          emotionalTheme: 'discovery',
          actions: [
            { type: 'next', label: 'Show me more', primary: true },
            { type: 'skip', label: 'Skip' }
          ]
        },
        {
          id: 'soul-orb-guide',
          title: '🔮 Soul Orb Energy',
          description: 'The soul orb shows emotional energy and compatibility. Watch it pulse and glow for high-compatibility matches!',
          targetSelector: '.soul-orb',
          position: 'right',
          highlightElement: true,
          emotionalTheme: 'discovery',
          actions: [
            { type: 'next', label: 'Fascinating!', primary: true },
            { type: 'skip', label: 'Skip' }
          ]
        },
        {
          id: 'compatibility-breakdown',
          title: '📊 Compatibility Insights',
          description: 'See detailed compatibility in values, interests, and communication style. High scores unlock special animations!',
          targetSelector: '.compatibility-score',
          position: 'top',
          highlightElement: true,
          emotionalTheme: 'discovery',
          actions: [
            { type: 'next', label: 'Incredible!', primary: true },
            { type: 'skip', label: 'Skip' }
          ]
        },
        {
          id: 'keyboard-navigation',
          title: '⌨️ Keyboard Magic',
          description: 'Use arrow keys to navigate cards, Enter to connect, and discover keyboard shortcuts for efficient browsing.',
          targetSelector: '.keyboard-help',
          position: 'top',
          highlightElement: true,
          emotionalTheme: 'growth',
          actions: [
            { type: 'complete', label: 'Ready to explore!', primary: true }
          ]
        }
      ]
    });

    // Conversation feature tour
    this.registerTour({
      id: 'conversation-tour',
      name: 'Meaningful Conversations',
      description: 'Master the art of soul-deep communication',
      category: 'feature',
      emotionalJourney: ['connection', 'intimacy', 'understanding'],
      steps: [
        {
          id: 'conversation-starters',
          title: '💭 Soul Conversation Starters',
          description: 'Use our curated conversation starters to dive deep into meaningful topics that reveal true compatibility.',
          targetSelector: '.conversation-starters',
          position: 'right',
          highlightElement: true,
          emotionalTheme: 'connection',
          actions: [
            { type: 'next', label: 'Love these!', primary: true },
            { type: 'skip', label: 'Skip' }
          ]
        },
        {
          id: 'emotional-reactions',
          title: '💫 Emotional Reactions',
          description: 'React with emotional depth using our soul-centered emoji system. Express how messages truly make you feel.',
          targetSelector: '.message-reactions',
          position: 'top',
          highlightElement: true,
          emotionalTheme: 'connection',
          actions: [
            { type: 'next', label: 'So thoughtful!', primary: true },
            { type: 'skip', label: 'Skip' }
          ]
        },
        {
          id: 'revelation-sharing',
          title: '🌅 Daily Revelations',
          description: 'Share personal insights and growth moments. This deeper sharing builds authentic emotional bonds.',
          targetSelector: '.revelation-area',
          position: 'bottom',
          highlightElement: true,
          emotionalTheme: 'growth',
          actions: [
            { type: 'complete', label: 'Ready to connect deeply!', primary: true }
          ]
        }
      ]
    });
  }

  /**
   * Register a new onboarding tour
   */
  registerTour(tour: OnboardingTour): void {
    this.tours.set(tour.id, tour);
  }

  /**
   * Start a specific onboarding tour
   */
  startTour(tourId: string): void {
    const tour = this.tours.get(tourId);
    if (!tour) {
      console.warn(`Tour ${tourId} not found`);
      return;
    }

    const currentState = this.stateSubject.value;
    
    // Check if tour was already completed and user preferences
    if (currentState.completedTours.includes(tourId) && 
        currentState.userPreferences.skipIntroductions) {
      return;
    }

    this.currentTourSteps = tour.steps;
    
    const newState: OnboardingState = {
      ...currentState,
      currentTour: tourId,
      currentStep: 0
    };

    this.stateSubject.next(newState);
    this.showStep(0);
    this.saveState();

    // Announce to screen readers
    this.accessibilityService.announce(
      `Starting ${tour.name} tutorial. ${tour.description}`,
      'polite'
    );
  }

  /**
   * Show a specific step in the current tour
   */
  private showStep(stepIndex: number): void {
    if (stepIndex < 0 || stepIndex >= this.currentTourSteps.length) {
      this.completeTour();
      return;
    }

    const step = this.currentTourSteps[stepIndex];
    this.activeStepSubject.next(step);

    // Wait for element to be available if targetSelector is specified
    if (step.targetSelector) {
      this.waitForElement(step.targetSelector).then(() => {
        this.highlightElement(step);
      });
    }

    // Announce step to screen readers
    this.accessibilityService.announce(
      `${step.title}. ${step.description}`,
      'polite'
    );
  }

  /**
   * Move to the next step
   */
  nextStep(): void {
    const currentState = this.stateSubject.value;
    const nextStepIndex = currentState.currentStep + 1;

    const newState: OnboardingState = {
      ...currentState,
      currentStep: nextStepIndex
    };

    this.stateSubject.next(newState);
    this.showStep(nextStepIndex);
    this.saveState();
  }

  /**
   * Skip the current step
   */
  skipStep(): void {
    const currentState = this.stateSubject.value;
    const currentStep = this.currentTourSteps[currentState.currentStep];
    
    if (currentStep) {
      const newState: OnboardingState = {
        ...currentState,
        skippedSteps: [...currentState.skippedSteps, currentStep.id]
      };
      this.stateSubject.next(newState);
    }

    this.nextStep();
  }

  /**
   * Complete the current tour
   */
  completeTour(): void {
    const currentState = this.stateSubject.value;
    
    if (currentState.currentTour) {
      const newState: OnboardingState = {
        ...currentState,
        currentTour: null,
        currentStep: 0,
        completedTours: [...currentState.completedTours, currentState.currentTour]
      };

      this.stateSubject.next(newState);
      this.activeStepSubject.next(null);
      this.saveState();

      // Clear any highlights
      this.clearHighlights();

      // Announce completion
      this.accessibilityService.announce(
        'Tutorial completed! You\'re ready to start your soul connection journey.',
        'polite'
      );
    }
  }

  /**
   * Skip the entire tour
   */
  skipTour(): void {
    this.completeTour();
  }

  /**
   * Check if a tour should be triggered
   */
  checkTourTrigger(condition: string): void {
    const currentState = this.stateSubject.value;
    
    // Don't show tours if user has disabled them
    if (!currentState.userPreferences.showTutorials) {
      return;
    }

    // Check if any tours should be triggered by this condition
    for (const [tourId, tour] of this.tours) {
      if (tour.triggerCondition === condition && 
          !currentState.completedTours.includes(tourId) &&
          !currentState.currentTour) {
        this.startTour(tourId);
        break;
      }
    }
  }

  /**
   * Update user preferences
   */
  updatePreferences(preferences: Partial<OnboardingState['userPreferences']>): void {
    const currentState = this.stateSubject.value;
    const newState: OnboardingState = {
      ...currentState,
      userPreferences: { ...currentState.userPreferences, ...preferences }
    };

    this.stateSubject.next(newState);
    this.saveState();
  }

  /**
   * Reset all onboarding progress
   */
  resetOnboarding(): void {
    const initialState = this.getInitialState();
    this.stateSubject.next(initialState);
    this.activeStepSubject.next(null);
    this.clearHighlights();
    this.saveState();
  }

  /**
   * Wait for an element to be available in the DOM
   */
  private waitForElement(selector: string, timeout = 5000): Promise<Element> {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);
      if (element) {
        resolve(element);
        return;
      }

      const observer = new MutationObserver(() => {
        const element = document.querySelector(selector);
        if (element) {
          observer.disconnect();
          resolve(element);
        }
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`Element ${selector} not found within timeout`));
      }, timeout);
    });
  }

  /**
   * Highlight target element
   */
  private highlightElement(step: OnboardingStep): void {
    if (!step.targetSelector || !step.highlightElement) return;

    const element = document.querySelector(step.targetSelector) as HTMLElement;
    if (!element) return;

    // Add highlight class
    element.classList.add('onboarding-highlight');
    
    // Add focus ring for accessibility
    element.style.outline = '3px solid var(--primary-color)';
    element.style.outlineOffset = '4px';
    element.style.borderRadius = '8px';
    element.style.transition = 'all 0.3s ease';
  }

  /**
   * Clear all element highlights
   */
  private clearHighlights(): void {
    const highlightedElements = document.querySelectorAll('.onboarding-highlight');
    highlightedElements.forEach((element: Element) => {
      const el = element as HTMLElement;
      el.classList.remove('onboarding-highlight');
      el.style.outline = '';
      el.style.outlineOffset = '';
      el.style.borderRadius = '';
      el.style.transition = '';
    });
  }

  /**
   * Get initial onboarding state
   */
  private getInitialState(): OnboardingState {
    return {
      currentTour: null,
      currentStep: 0,
      completedTours: [],
      skippedSteps: [],
      userPreferences: {
        showTutorials: true,
        animationSpeed: 'normal',
        skipIntroductions: false,
        autoAdvance: false
      }
    };
  }

  /**
   * Load state from localStorage
   */
  private loadState(): void {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (saved) {
        const state = JSON.parse(saved);
        this.stateSubject.next({ ...this.getInitialState(), ...state });
      }
    } catch (error) {
      console.warn('Failed to load onboarding state:', error);
    }
  }

  /**
   * Save state to localStorage
   */
  private saveState(): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.stateSubject.value));
    } catch (error) {
      console.warn('Failed to save onboarding state:', error);
    }
  }

  /**
   * Get available tours
   */
  getAvailableTours(): OnboardingTour[] {
    return Array.from(this.tours.values());
  }

  /**
   * Check if user is new (no completed tours)
   */
  isNewUser(): boolean {
    return this.stateSubject.value.completedTours.length === 0;
  }

  /**
   * Check if tour is completed
   */
  isTourCompleted(tourId: string): boolean {
    return this.stateSubject.value.completedTours.includes(tourId);
  }
}