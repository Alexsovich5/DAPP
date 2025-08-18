import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { AuthService } from './auth.service';

// === A/B TESTING INTERFACES ===

export interface ABTestConfig {
  id: string;
  name: string;
  description: string;
  variants: ABTestVariant[];
  allocation: Record<string, number>; // Percentage allocation per variant
  startDate: Date;
  endDate?: Date;
  isActive: boolean;
  targetAudience?: ABTestAudience;
  primaryMetric: string;
  secondaryMetrics?: string[];
}

export interface ABTestVariant {
  id: string;
  name: string;
  description: string;
  config: Record<string, any>;
  isControl: boolean;
}

export interface ABTestAudience {
  newUsers?: boolean;
  existingUsers?: boolean;
  ageRange?: { min: number; max: number };
  genderFilter?: string[];
  platforms?: ('web' | 'mobile')[];
}

export interface ABTestAssignment {
  userId: string;
  testId: string;
  variantId: string;
  assignedAt: Date;
  sessionId?: string;
}

export interface ABTestEvent {
  userId: string;
  testId: string;
  variantId: string;
  eventType: string;
  eventData?: Record<string, any>;
  timestamp: Date;
  sessionId?: string;
}

// === PREDEFINED TEST CONFIGURATIONS ===

export const AB_TEST_CONFIGS: Record<string, ABTestConfig> = {
  // Discovery Card Layout Test
  discovery_card_layout: {
    id: 'discovery_card_layout',
    name: 'Discovery Card Layout Optimization',
    description: 'Test different layouts for discovery cards to improve engagement',
    variants: [
      {
        id: 'control',
        name: 'Current Layout',
        description: 'Existing discovery card design',
        config: {
          layout: 'vertical',
          showCompatibilityFirst: false,
          cardAnimation: 'default',
          buttonStyle: 'standard'
        },
        isControl: true
      },
      {
        id: 'horizontal_compact',
        name: 'Horizontal Compact',
        description: 'Compact horizontal layout with emphasis on compatibility',
        config: {
          layout: 'horizontal',
          showCompatibilityFirst: true,
          cardAnimation: 'slide',
          buttonStyle: 'minimal'
        },
        isControl: false
      },
      {
        id: 'compatibility_focus',
        name: 'Compatibility Focus',
        description: 'Vertical layout with large compatibility score display',
        config: {
          layout: 'vertical',
          showCompatibilityFirst: true,
          cardAnimation: 'bounce',
          buttonStyle: 'highlighted'
        },
        isControl: false
      }
    ],
    allocation: {
      control: 40,
      horizontal_compact: 30,
      compatibility_focus: 30
    },
    startDate: new Date('2025-01-01'),
    isActive: true,
    primaryMetric: 'connection_rate',
    secondaryMetrics: ['time_on_discovery', 'cards_viewed_per_session']
  },

  // Onboarding Flow Test
  onboarding_flow: {
    id: 'onboarding_flow',
    name: 'Onboarding Flow Optimization',
    description: 'Test different onboarding approaches to improve completion rates',
    variants: [
      {
        id: 'control',
        name: 'Current Flow',
        description: 'Existing step-by-step onboarding',
        config: {
          flowType: 'stepped',
          questionsPerStep: 3,
          showProgress: true,
          allowSkip: true
        },
        isControl: true
      },
      {
        id: 'single_page',
        name: 'Single Page Flow',
        description: 'All questions on one scrollable page',
        config: {
          flowType: 'single_page',
          questionsPerStep: 0,
          showProgress: false,
          allowSkip: false
        },
        isControl: false
      },
      {
        id: 'progressive_disclosure',
        name: 'Progressive Disclosure',
        description: 'Questions revealed based on previous answers',
        config: {
          flowType: 'progressive',
          questionsPerStep: 1,
          showProgress: true,
          allowSkip: false
        },
        isControl: false
      }
    ],
    allocation: {
      control: 34,
      single_page: 33,
      progressive_disclosure: 33
    },
    startDate: new Date('2025-01-01'),
    isActive: true,
    targetAudience: {
      newUsers: true,
      existingUsers: false
    },
    primaryMetric: 'onboarding_completion_rate',
    secondaryMetrics: ['time_to_complete', 'form_abandonment_rate']
  },

  // Message List Design Test
  message_list_design: {
    id: 'message_list_design',
    name: 'Message List Design Optimization',
    description: 'Test different message list designs for better engagement',
    variants: [
      {
        id: 'control',
        name: 'Current Design',
        description: 'Existing message list layout',
        config: {
          avatarSize: 'medium',
          showPreview: true,
          revealationBadge: 'corner',
          swipeActions: 'standard'
        },
        isControl: true
      },
      {
        id: 'large_avatars',
        name: 'Large Avatars',
        description: 'Emphasis on larger profile avatars',
        config: {
          avatarSize: 'large',
          showPreview: true,
          revealationBadge: 'overlay',
          swipeActions: 'enhanced'
        },
        isControl: false
      }
    ],
    allocation: {
      control: 50,
      large_avatars: 50
    },
    startDate: new Date('2025-01-01'),
    isActive: true,
    primaryMetric: 'message_open_rate',
    secondaryMetrics: ['conversation_length', 'response_rate']
  }
};

@Injectable({
  providedIn: 'root'
})
export class ABTestingService {
  private assignments = new BehaviorSubject<Map<string, ABTestAssignment>>(new Map());
  private events: ABTestEvent[] = [];
  private sessionId: string;

  public assignments$ = this.assignments.asObservable();

  constructor(private authService: AuthService) {
    this.sessionId = this.generateSessionId();
    this.loadAssignments();
  }

  /**
   * Get the variant assignment for a specific test
   */
  getVariant(testId: string): ABTestVariant | null {
    const testConfig = AB_TEST_CONFIGS[testId];
    if (!testConfig || !testConfig.isActive) {
      return null;
    }

    // Check if user has existing assignment
    const currentAssignments = this.assignments.value;
    const existingAssignment = currentAssignments.get(testId);
    
    if (existingAssignment) {
      const variant = testConfig.variants.find(v => v.id === existingAssignment.variantId);
      return variant || null;
    }

    // Create new assignment
    const assignedVariant = this.assignUserToVariant(testConfig);
    if (assignedVariant) {
      this.saveAssignment(testId, assignedVariant.id);
    }

    return assignedVariant;
  }

  /**
   * Get configuration for a specific variant
   */
  getVariantConfig(testId: string, configKey?: string): any {
    const variant = this.getVariant(testId);
    if (!variant) {
      return null;
    }

    if (configKey) {
      return variant.config[configKey] || null;
    }

    return variant.config;
  }

  /**
   * Check if user is in a specific variant
   */
  isInVariant(testId: string, variantId: string): boolean {
    const variant = this.getVariant(testId);
    return variant?.id === variantId;
  }

  /**
   * Track an A/B test event
   */
  trackEvent(testId: string, eventType: string, eventData?: Record<string, any>): void {
    const variant = this.getVariant(testId);
    if (!variant) {
      return;
    }

    const userId = this.getCurrentUserId();
    const event: ABTestEvent = {
      userId,
      testId,
      variantId: variant.id,
      eventType,
      eventData,
      timestamp: new Date(),
      sessionId: this.sessionId
    };

    this.events.push(event);
    this.persistEvent(event);

    // Log for debugging
    console.log('A/B Test Event:', event);
  }

  /**
   * Get all active tests
   */
  getActiveTests(): ABTestConfig[] {
    return Object.values(AB_TEST_CONFIGS).filter(test => 
      test.isActive && this.isTestDateValid(test)
    );
  }

  /**
   * Get assignment history for current user
   */
  getUserAssignments(): ABTestAssignment[] {
    return Array.from(this.assignments.value.values());
  }

  /**
   * Force assign user to specific variant (for testing)
   */
  forceAssignment(testId: string, variantId: string): boolean {
    const testConfig = AB_TEST_CONFIGS[testId];
    const variant = testConfig?.variants.find(v => v.id === variantId);
    
    if (!variant) {
      return false;
    }

    this.saveAssignment(testId, variantId);
    return true;
  }

  /**
   * Reset all assignments (for testing)
   */
  resetAssignments(): void {
    this.assignments.next(new Map());
    this.saveAssignments();
  }

  // === PRIVATE METHODS ===

  private assignUserToVariant(testConfig: ABTestConfig): ABTestVariant | null {
    // Check audience targeting
    if (!this.isUserInTargetAudience(testConfig.targetAudience)) {
      return null;
    }

    // Use deterministic assignment based on user ID hash
    const userId = this.getCurrentUserId();
    const hash = this.hashUserId(userId + testConfig.id);
    const randomValue = (hash % 100) + 1; // 1-100

    let cumulativeAllocation = 0;
    for (const variant of testConfig.variants) {
      cumulativeAllocation += testConfig.allocation[variant.id] || 0;
      if (randomValue <= cumulativeAllocation) {
        return variant;
      }
    }

    // Fallback to control
    return testConfig.variants.find(v => v.isControl) || testConfig.variants[0];
  }

  private isUserInTargetAudience(audience?: ABTestAudience): boolean {
    if (!audience) {
      return true; // No targeting means everyone is eligible
    }

    // TODO: Implement real audience targeting based on user profile
    // For now, return true for all users
    return true;
  }

  private isTestDateValid(test: ABTestConfig): boolean {
    const now = new Date();
    const isAfterStart = now >= test.startDate;
    const isBeforeEnd = !test.endDate || now <= test.endDate;
    return isAfterStart && isBeforeEnd;
  }

  private hashUserId(input: string): number {
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  private getCurrentUserId(): string {
    // TODO: Get from AuthService when available
    return this.sessionId; // Fallback to session ID for anonymous users
  }

  private generateSessionId(): string {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  private saveAssignment(testId: string, variantId: string): void {
    const userId = this.getCurrentUserId();
    const assignment: ABTestAssignment = {
      userId,
      testId,
      variantId,
      assignedAt: new Date(),
      sessionId: this.sessionId
    };

    const currentAssignments = this.assignments.value;
    currentAssignments.set(testId, assignment);
    this.assignments.next(currentAssignments);
    this.saveAssignments();
  }

  private loadAssignments(): void {
    try {
      const stored = localStorage.getItem('ab_test_assignments');
      if (stored) {
        const assignments = JSON.parse(stored);
        const assignmentMap = new Map<string, ABTestAssignment>();
        
        assignments.forEach((assignment: ABTestAssignment) => {
          // Convert date strings back to Date objects
          assignment.assignedAt = new Date(assignment.assignedAt);
          assignmentMap.set(assignment.testId, assignment);
        });
        
        this.assignments.next(assignmentMap);
      }
    } catch (error) {
      console.warn('Failed to load A/B test assignments:', error);
    }
  }

  private saveAssignments(): void {
    try {
      const assignments = Array.from(this.assignments.value.values());
      localStorage.setItem('ab_test_assignments', JSON.stringify(assignments));
    } catch (error) {
      console.warn('Failed to save A/B test assignments:', error);
    }
  }

  private persistEvent(event: ABTestEvent): void {
    try {
      // Save to localStorage for now - in production, send to analytics service
      const storedEvents = localStorage.getItem('ab_test_events');
      const events = storedEvents ? JSON.parse(storedEvents) : [];
      events.push(event);
      
      // Keep only last 1000 events to prevent storage bloat
      if (events.length > 1000) {
        events.splice(0, events.length - 1000);
      }
      
      localStorage.setItem('ab_test_events', JSON.stringify(events));
    } catch (error) {
      console.warn('Failed to persist A/B test event:', error);
    }
  }
}