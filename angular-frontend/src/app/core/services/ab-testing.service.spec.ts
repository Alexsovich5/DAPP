/**
 * ABTestingService Tests
 * Comprehensive tests for A/B testing and variant assignment
 */

import { TestBed } from '@angular/core/testing';
import { ABTestingService, AB_TEST_CONFIGS, ABTestConfig, ABTestVariant, ABTestAssignment } from './ab-testing.service';
import { AuthService } from './auth.service';

describe('ABTestingService', () => {
  let service: ABTestingService;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();

    const spy = jasmine.createSpyObj('AuthService', ['getCurrentUser']);

    TestBed.configureTestingModule({
      providers: [
        ABTestingService,
        { provide: AuthService, useValue: spy }
      ]
    });

    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    service = TestBed.inject(ABTestingService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should generate a session ID', () => {
      expect((service as any).sessionId).toBeDefined();
      expect((service as any).sessionId).toContain('session_');
    });

    it('should initialize with empty assignments', (done) => {
      service.assignments$.subscribe(assignments => {
        expect(assignments.size).toBe(0);
        done();
      });
    });

    it('should load assignments from localStorage if available', () => {
      const testAssignment: ABTestAssignment = {
        userId: 'user-123',
        testId: 'discovery_card_layout',
        variantId: 'control',
        assignedAt: new Date().toISOString() as unknown as Date
      };

      localStorage.setItem('ab_test_assignments', JSON.stringify([testAssignment]));

      // Manually call the private loadAssignments method
      (service as any).loadAssignments();

      const assignments = service.getUserAssignments();
      expect(assignments.length).toBe(1);
      expect(assignments[0].testId).toBe('discovery_card_layout');
    });
  });

  describe('Variant Assignment', () => {
    it('should assign user to a variant for active test', () => {
      const variant = service.getVariant('discovery_card_layout');

      expect(variant).toBeTruthy();
      expect(variant?.id).toBeDefined();
    });

    it('should return null for inactive test', () => {
      const inactiveTestId = 'non_existent_test';
      const variant = service.getVariant(inactiveTestId);

      expect(variant).toBeNull();
    });

    it('should return same variant on subsequent calls', () => {
      const variant1 = service.getVariant('discovery_card_layout');
      const variant2 = service.getVariant('discovery_card_layout');

      expect(variant1?.id).toBe(variant2?.id);
    });

    it('should assign variant from control', () => {
      const variant = service.getVariant('discovery_card_layout');

      const testConfig = AB_TEST_CONFIGS['discovery_card_layout'];
      const validVariantIds = testConfig.variants.map(v => v.id);

      expect(variant).toBeTruthy();
      if (variant) {
        expect(validVariantIds).toContain(variant.id);
      }
    });

    it('should save assignment to localStorage', () => {
      service.getVariant('discovery_card_layout');

      const stored = localStorage.getItem('ab_test_assignments');
      expect(stored).toBeTruthy();

      const assignments = JSON.parse(stored!);
      expect(assignments.length).toBe(1);
      expect(assignments[0].testId).toBe('discovery_card_layout');
    });

    it('should handle multiple test assignments', () => {
      service.getVariant('discovery_card_layout');
      service.getVariant('onboarding_flow');

      const assignments = service.getUserAssignments();
      expect(assignments.length).toBe(2);
    });
  });

  describe('Variant Configuration', () => {
    it('should get full variant config', () => {
      const config = service.getVariantConfig('discovery_card_layout');

      expect(config).toBeTruthy();
      expect(typeof config).toBe('object');
    });

    it('should get specific config key', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      const layout = service.getVariantConfig('discovery_card_layout', 'layout');
      expect(layout).toBe('vertical');
    });

    it('should return null for non-existent config key', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      const nonExistent = service.getVariantConfig('discovery_card_layout', 'nonExistentKey');
      expect(nonExistent).toBeNull();
    });

    it('should return null for inactive test config', () => {
      const config = service.getVariantConfig('non_existent_test');
      expect(config).toBeNull();
    });
  });

  describe('Variant Checking', () => {
    it('should correctly identify if user is in specific variant', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      const isInControl = service.isInVariant('discovery_card_layout', 'control');
      expect(isInControl).toBe(true);
    });

    it('should return false for different variant', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      const isInOther = service.isInVariant('discovery_card_layout', 'horizontal_compact');
      expect(isInOther).toBe(false);
    });

    it('should return false for non-existent test', () => {
      const isIn = service.isInVariant('non_existent', 'any_variant');
      expect(isIn).toBe(false);
    });
  });

  describe('Event Tracking', () => {
    it('should track event for assigned variant', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      spyOn(console, 'log');
      service.trackEvent('discovery_card_layout', 'card_view');

      expect(console.log).toHaveBeenCalledWith('A/B Test Event:', jasmine.any(Object));
    });

    it('should include event data in tracked event', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      const eventData = { cardId: '123', duration: 5000 };
      service.trackEvent('discovery_card_layout', 'card_view', eventData);

      const stored = localStorage.getItem('ab_test_events');
      const events = JSON.parse(stored!);

      expect(events[0].eventData).toEqual(eventData);
    });

    it('should not track event for non-assigned test', () => {
      spyOn(console, 'log');
      service.trackEvent('non_existent_test', 'some_event');

      expect(console.log).not.toHaveBeenCalled();
    });

    it('should include timestamp in event', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      const beforeTime = new Date();
      service.trackEvent('discovery_card_layout', 'test_event');
      const afterTime = new Date();

      const stored = localStorage.getItem('ab_test_events');
      const events = JSON.parse(stored!);
      const eventTime = new Date(events[0].timestamp);

      expect(eventTime.getTime()).toBeGreaterThanOrEqual(beforeTime.getTime());
      expect(eventTime.getTime()).toBeLessThanOrEqual(afterTime.getTime());
    });

    it('should limit stored events to 1000', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      // Create 1100 events
      for (let i = 0; i < 1100; i++) {
        service.trackEvent('discovery_card_layout', `event_${i}`);
      }

      const stored = localStorage.getItem('ab_test_events');
      const events = JSON.parse(stored!);

      expect(events.length).toBe(1000);
    });
  });

  describe('Active Tests Retrieval', () => {
    it('should return all active tests', () => {
      const activeTests = service.getActiveTests();

      expect(activeTests.length).toBeGreaterThan(0);
      activeTests.forEach(test => {
        expect(test.isActive).toBe(true);
      });
    });

    it('should filter out tests with future start dates', () => {
      // All predefined tests start at 2025-01-01, which is in the past
      // so this test just verifies the filtering logic works
      const activeTests = service.getActiveTests();

      activeTests.forEach(test => {
        expect(test.startDate.getTime()).toBeLessThanOrEqual(new Date().getTime());
      });
    });

    it('should include tests without end dates', () => {
      const activeTests = service.getActiveTests();

      const testsWithoutEndDate = activeTests.filter(t => !t.endDate);
      expect(testsWithoutEndDate.length).toBeGreaterThan(0);
    });
  });

  describe('Force Assignment', () => {
    it('should force user into specific variant', () => {
      const success = service.forceAssignment('discovery_card_layout', 'horizontal_compact');

      expect(success).toBe(true);

      const variant = service.getVariant('discovery_card_layout');
      expect(variant?.id).toBe('horizontal_compact');
    });

    it('should return false for non-existent variant', () => {
      const success = service.forceAssignment('discovery_card_layout', 'non_existent_variant');

      expect(success).toBe(false);
    });

    it('should return false for non-existent test', () => {
      const success = service.forceAssignment('non_existent_test', 'any_variant');

      expect(success).toBe(false);
    });

    it('should override previous assignment', () => {
      service.forceAssignment('discovery_card_layout', 'control');
      service.forceAssignment('discovery_card_layout', 'horizontal_compact');

      const variant = service.getVariant('discovery_card_layout');
      expect(variant?.id).toBe('horizontal_compact');
    });
  });

  describe('Assignment Reset', () => {
    it('should clear all assignments', () => {
      service.forceAssignment('discovery_card_layout', 'control');
      service.forceAssignment('onboarding_flow', 'control');

      service.resetAssignments();

      const assignments = service.getUserAssignments();
      expect(assignments.length).toBe(0);
    });

    it('should clear localStorage', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      service.resetAssignments();

      const stored = localStorage.getItem('ab_test_assignments');
      const assignments = stored ? JSON.parse(stored) : [];
      expect(assignments.length).toBe(0);
    });

    it('should allow new assignments after reset', () => {
      service.forceAssignment('discovery_card_layout', 'control');
      service.resetAssignments();

      const variant = service.getVariant('discovery_card_layout');
      expect(variant).toBeTruthy();
    });
  });

  describe('User Assignment History', () => {
    it('should return empty array initially', () => {
      const assignments = service.getUserAssignments();
      expect(assignments).toEqual([]);
    });

    it('should return all user assignments', () => {
      service.forceAssignment('discovery_card_layout', 'control');
      service.forceAssignment('onboarding_flow', 'control');

      const assignments = service.getUserAssignments();
      expect(assignments.length).toBe(2);
    });

    it('should include assignment metadata', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      const assignments = service.getUserAssignments();
      const assignment = assignments[0];

      expect(assignment.userId).toBeDefined();
      expect(assignment.testId).toBe('discovery_card_layout');
      expect(assignment.variantId).toBe('control');
      expect(assignment.assignedAt).toBeInstanceOf(Date);
    });
  });

  describe('Hash Function', () => {
    it('should produce consistent hash for same input', () => {
      const hash1 = (service as any).hashUserId('test-user-123');
      const hash2 = (service as any).hashUserId('test-user-123');

      expect(hash1).toBe(hash2);
    });

    it('should produce different hashes for different inputs', () => {
      const hash1 = (service as any).hashUserId('user-1');
      const hash2 = (service as any).hashUserId('user-2');

      expect(hash1).not.toBe(hash2);
    });

    it('should always return positive numbers', () => {
      const hash = (service as any).hashUserId('any-user-id');
      expect(hash).toBeGreaterThanOrEqual(0);
    });

    it('should handle empty string', () => {
      const hash = (service as any).hashUserId('');
      expect(hash).toBe(0);
    });
  });

  describe('Deterministic Assignment', () => {
    it('should assign same variant for same user ID', () => {
      const variant1 = service.getVariant('discovery_card_layout');
      const variant2 = service.getVariant('discovery_card_layout');

      expect(variant1?.id).toBe(variant2?.id);
    });

    it('should respect allocation percentages over many assignments', () => {
      const testConfig = AB_TEST_CONFIGS['discovery_card_layout'];
      const variantCounts: Record<string, number> = {};

      // Simulate 1000 different users
      for (let i = 0; i < 1000; i++) {
        const userId = `user-${i}`;
        const hash = (service as any).hashUserId(userId + testConfig.id);
        const randomValue = (hash % 100) + 1;

        let cumulativeAllocation = 0;
        for (const variant of testConfig.variants) {
          cumulativeAllocation += testConfig.allocation[variant.id] || 0;
          if (randomValue <= cumulativeAllocation) {
            variantCounts[variant.id] = (variantCounts[variant.id] || 0) + 1;
            break;
          }
        }
      }

      // Verify each variant got roughly its allocated percentage (within 10% margin)
      Object.entries(testConfig.allocation).forEach(([variantId, expectedPercent]) => {
        const actualCount = variantCounts[variantId] || 0;
        const actualPercent = (actualCount / 1000) * 100;
        expect(Math.abs(actualPercent - expectedPercent)).toBeLessThan(10);
      });
    });
  });

  describe('Test Configuration Constants', () => {
    it('should have discovery_card_layout test', () => {
      expect(AB_TEST_CONFIGS['discovery_card_layout']).toBeDefined();
    });

    it('should have onboarding_flow test', () => {
      expect(AB_TEST_CONFIGS['onboarding_flow']).toBeDefined();
    });

    it('should have message_list_design test', () => {
      expect(AB_TEST_CONFIGS['message_list_design']).toBeDefined();
    });

    it('should have valid variant configurations', () => {
      Object.values(AB_TEST_CONFIGS).forEach(test => {
        expect(test.variants.length).toBeGreaterThan(0);
        expect(test.variants.some(v => v.isControl)).toBe(true);
      });
    });

    it('should have allocation that sums to 100', () => {
      Object.values(AB_TEST_CONFIGS).forEach(test => {
        const total = Object.values(test.allocation).reduce((sum, val) => sum + val, 0);
        expect(total).toBe(100);
      });
    });
  });

  describe('LocalStorage Error Handling', () => {
    it('should handle localStorage save errors gracefully', () => {
      spyOn(localStorage, 'setItem').and.throwError('Storage full');
      spyOn(console, 'warn');

      service.forceAssignment('discovery_card_layout', 'control');

      expect(console.warn).toHaveBeenCalledWith('Failed to save A/B test assignments:', jasmine.any(Error));
    });

    it('should handle localStorage load errors gracefully', () => {
      spyOn(localStorage, 'getItem').and.throwError('Storage error');
      spyOn(console, 'warn');

      // Manually call loadAssignments to trigger the error
      (service as any).loadAssignments();

      expect(console.warn).toHaveBeenCalledWith('Failed to load A/B test assignments:', jasmine.any(Error));
    });

    it('should handle event persist errors gracefully', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      spyOn(localStorage, 'setItem').and.throwError('Storage full');
      spyOn(console, 'warn');

      service.trackEvent('discovery_card_layout', 'test_event');

      expect(console.warn).toHaveBeenCalledWith('Failed to persist A/B test event:', jasmine.any(Error));
    });

    it('should handle malformed JSON in localStorage', () => {
      localStorage.setItem('ab_test_assignments', 'invalid json');
      spyOn(console, 'warn');

      // Manually call loadAssignments to trigger the error
      (service as any).loadAssignments();

      expect(console.warn).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle test with single variant', () => {
      const singleVariantTest: ABTestConfig = {
        id: 'single_variant_test',
        name: 'Single Variant',
        description: 'Test with only one variant',
        variants: [{
          id: 'only',
          name: 'Only Variant',
          description: 'The only option',
          config: {},
          isControl: true
        }],
        allocation: { only: 100 },
        startDate: new Date('2020-01-01'),
        isActive: true,
        primaryMetric: 'test_metric'
      };

      (AB_TEST_CONFIGS as any)['single_variant_test'] = singleVariantTest;

      const variant = service.getVariant('single_variant_test');
      expect(variant?.id).toBe('only');

      delete (AB_TEST_CONFIGS as any)['single_variant_test'];
    });

    it('should handle variant with empty config', () => {
      service.forceAssignment('discovery_card_layout', 'control');

      // Even if config is present, test that we can handle edge cases
      const config = service.getVariantConfig('discovery_card_layout');
      expect(config).toBeTruthy();
    });

    it('should handle rapid successive assignments', () => {
      for (let i = 0; i < 100; i++) {
        service.getVariant('discovery_card_layout');
      }

      const assignments = service.getUserAssignments();
      expect(assignments.length).toBe(1); // Should still only have one assignment
    });

    it('should handle session ID generation uniqueness', () => {
      const sessionIds = new Set();
      for (let i = 0; i < 100; i++) {
        const id = (service as any).generateSessionId();
        sessionIds.add(id);
      }

      expect(sessionIds.size).toBe(100); // All should be unique
    });
  });

  describe('Audience Targeting', () => {
    it('should handle test with new user targeting', () => {
      const variant = service.getVariant('onboarding_flow');

      expect(variant).toBeTruthy();
      // Currently always returns true, but test structure is ready for implementation
    });

    it('should handle test without audience targeting', () => {
      const variant = service.getVariant('discovery_card_layout');

      expect(variant).toBeTruthy();
    });
  });

  describe('Date Validation', () => {
    it('should validate test start date correctly', () => {
      const testConfig = AB_TEST_CONFIGS['discovery_card_layout'];
      const isValid = (service as any).isTestDateValid(testConfig);

      // Test started in 2025-01-01 which is in the past
      expect(isValid).toBe(true);
    });

    it('should handle test without end date', () => {
      const testConfig = AB_TEST_CONFIGS['discovery_card_layout'];
      const isValid = (service as any).isTestDateValid(testConfig);

      expect(isValid).toBe(true);
    });

    it('should reject test with future start date', () => {
      const futureTest: ABTestConfig = {
        ...AB_TEST_CONFIGS['discovery_card_layout'],
        startDate: new Date('2099-01-01'),
        id: 'future_test'
      };

      const isValid = (service as any).isTestDateValid(futureTest);
      expect(isValid).toBe(false);
    });

    it('should reject test with past end date', () => {
      const pastTest: ABTestConfig = {
        ...AB_TEST_CONFIGS['discovery_card_layout'],
        startDate: new Date('2020-01-01'),
        endDate: new Date('2020-12-31'),
        id: 'past_test'
      };

      const isValid = (service as any).isTestDateValid(pastTest);
      expect(isValid).toBe(false);
    });
  });
});
