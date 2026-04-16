/**
 * OnboardingApiService Tests
 * Comprehensive tests for emotional onboarding API operations
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { OnboardingApiService, OnboardingData, OnboardingStatus } from './onboarding-api.service';
import { NotificationService } from './notification.service';
import { ErrorLoggingService } from './error-logging.service';
import { environment } from '../../../environments/environment';

describe('OnboardingApiService', () => {
  let service: OnboardingApiService;
  let httpMock: HttpTestingController;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let errorLoggingService: jasmine.SpyObj<ErrorLoggingService>;

  beforeEach(() => {
    const notificationSpy = jasmine.createSpyObj('NotificationService', ['showSuccess', 'showError']);
    const errorLoggingSpy = jasmine.createSpyObj('ErrorLoggingService', ['logApiError']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        OnboardingApiService,
        { provide: NotificationService, useValue: notificationSpy },
        { provide: ErrorLoggingService, useValue: errorLoggingSpy }
      ]
    });

    service = TestBed.inject(OnboardingApiService);
    httpMock = TestBed.inject(HttpTestingController);
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;
    errorLoggingService = TestBed.inject(ErrorLoggingService) as jasmine.SpyObj<ErrorLoggingService>;

    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should extend BaseService', () => {
      expect(service['notificationService']).toBeDefined();
      expect(service['errorLoggingService']).toBeDefined();
    });

    it('should have apiUrl configured', () => {
      expect(service['apiUrl']).toBe(environment.apiUrl);
    });
  });

  describe('completeOnboarding()', () => {
    it('should POST onboarding data to API', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Trust and communication',
        ideal_evening: 'Deep conversation over dinner',
        feeling_understood: 'When someone listens actively',
        core_values: { honesty: true, empathy: true },
        personality_traits: { introverted: false, creative: true },
        communication_style: { preferred: 'direct', frequency: 'regular' },
        interests: ['reading', 'hiking', 'cooking']
      };

      const mockResponse = { success: true, message: 'Onboarding completed' };
      spyOn(console, 'log');

      service.completeOnboarding(mockData).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.success).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(mockData);
      req.flush(mockResponse);

      expect(console.log).toHaveBeenCalledWith('Completing onboarding API call to:', jasmine.any(String), 'with data:', mockData);
      expect(console.log).toHaveBeenCalledWith('Onboarding API response:', mockResponse);
    });

    it('should store onboarding_completed in localStorage on success', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      req.flush({ success: true });

      expect(localStorage.getItem('onboarding_completed')).toBe('true');
    });

    it('should handle response without message field', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.message).toBeUndefined();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      req.flush({ success: true });
    });

    it('should handle complex core_values object', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {
          honesty: { importance: 10, description: 'Very important' },
          empathy: { importance: 9, description: 'Critical' }
        },
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      expect(req.request.body.core_values).toEqual(mockData.core_values);
      req.flush({ success: true });
    });

    it('should handle multiple interests', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: ['reading', 'hiking', 'cooking', 'music', 'art', 'travel']
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      expect(req.request.body.interests.length).toBe(6);
      req.flush({ success: true });
    });

    it('should handle empty interests array', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      expect(req.request.body.interests).toEqual([]);
      req.flush({ success: true });
    });

    it('should handle HTTP errors via BaseService', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };
      spyOn(console, 'error');

      service.completeOnboarding(mockData).subscribe({
        next: (response) => {
          // BaseService handleError returns the default result value
          expect(notificationService.showError).toHaveBeenCalled();
          expect(errorLoggingService.logApiError).toHaveBeenCalled();
        },
        error: () => fail('Should not error - BaseService handles errors')
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      expect(console.error).toHaveBeenCalledWith('Onboarding API error:', jasmine.any(Object));
    });

    it('should handle validation errors (422)', () => {
      const mockData: OnboardingData = {
        relationship_values: '',  // Invalid: empty
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };
      spyOn(console, 'error');

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      req.flush({ detail: 'Validation error' }, { status: 422, statusText: 'Unprocessable Entity' });

      expect(notificationService.showError).toHaveBeenCalled();
    });

    it('should use correct endpoint URL', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      expect(req.request.url).toBe(`${environment.apiUrl}/onboarding/complete`);
      req.flush({ success: true });
    });

    it('should log API call details', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };
      spyOn(console, 'log');

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      req.flush({ success: true });

      expect(console.log).toHaveBeenCalledTimes(2); // Call + response
    });
  });

  describe('getOnboardingStatus()', () => {
    it('should GET onboarding status from API', () => {
      const mockStatus: OnboardingStatus = {
        completed: true,
        has_interests: true,
        profile_complete: true
      };
      spyOn(console, 'log');

      service.getOnboardingStatus().subscribe(status => {
        expect(status).toEqual(mockStatus);
        expect(status.completed).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/status`);
      expect(req.request.method).toBe('GET');
      req.flush(mockStatus);

      expect(console.log).toHaveBeenCalledWith('Onboarding status:', mockStatus);
    });

    it('should return incomplete status', () => {
      const mockStatus: OnboardingStatus = {
        completed: false,
        has_interests: false,
        profile_complete: false
      };

      service.getOnboardingStatus().subscribe(status => {
        expect(status.completed).toBe(false);
        expect(status.has_interests).toBe(false);
        expect(status.profile_complete).toBe(false);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/status`);
      req.flush(mockStatus);
    });

    it('should return partially complete status', () => {
      const mockStatus: OnboardingStatus = {
        completed: true,
        has_interests: true,
        profile_complete: false
      };

      service.getOnboardingStatus().subscribe(status => {
        expect(status.completed).toBe(true);
        expect(status.profile_complete).toBe(false);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/status`);
      req.flush(mockStatus);
    });

    it('should handle HTTP errors via BaseService', () => {
      spyOn(console, 'error');

      service.getOnboardingStatus().subscribe({
        next: (status) => {
          // BaseService handleError returns the default result value
          expect(notificationService.showError).toHaveBeenCalled();
          expect(errorLoggingService.logApiError).toHaveBeenCalled();
        },
        error: () => fail('Should not error - BaseService handles errors')
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/status`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });

    it('should use correct endpoint URL', () => {
      service.getOnboardingStatus().subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/status`);
      expect(req.request.url).toBe(`${environment.apiUrl}/onboarding/status`);
      req.flush({ completed: false, has_interests: false, profile_complete: false });
    });

    it('should log status response', () => {
      const mockStatus: OnboardingStatus = {
        completed: true,
        has_interests: true,
        profile_complete: true
      };
      spyOn(console, 'log');

      service.getOnboardingStatus().subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/status`);
      req.flush(mockStatus);

      expect(console.log).toHaveBeenCalledWith('Onboarding status:', mockStatus);
    });
  });

  describe('LocalStorage Integration', () => {
    it('should not set localStorage if onboarding fails', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      req.flush('Error', { status: 500, statusText: 'Server Error' });

      expect(localStorage.getItem('onboarding_completed')).toBeNull();
    });

    it('should set localStorage even if response has success: false', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      req.flush({ success: false, message: 'Failed' });

      // localStorage is set in tap() before error handling, so it gets set
      expect(localStorage.getItem('onboarding_completed')).toBe('true');
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete onboarding workflow', () => {
      // First, check status
      service.getOnboardingStatus().subscribe(status => {
        expect(status.completed).toBe(false);
      });
      const statusReq = httpMock.expectOne(`${environment.apiUrl}/onboarding/status`);
      statusReq.flush({ completed: false, has_interests: false, profile_complete: false });

      // Complete onboarding
      const mockData: OnboardingData = {
        relationship_values: 'Trust',
        ideal_evening: 'Conversation',
        feeling_understood: 'Listening',
        core_values: { honesty: true },
        personality_traits: { creative: true },
        communication_style: { direct: true },
        interests: ['reading']
      };

      service.completeOnboarding(mockData).subscribe(response => {
        expect(response.success).toBe(true);
      });
      const completeReq = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      completeReq.flush({ success: true });

      // Check status again
      service.getOnboardingStatus().subscribe(status => {
        expect(status.completed).toBe(true);
      });
      const statusReq2 = httpMock.expectOne(`${environment.apiUrl}/onboarding/status`);
      statusReq2.flush({ completed: true, has_interests: true, profile_complete: true });
    });

    it('should handle multiple concurrent requests', () => {
      service.getOnboardingStatus().subscribe();
      service.getOnboardingStatus().subscribe();

      const requests = httpMock.match(`${environment.apiUrl}/onboarding/status`);
      expect(requests.length).toBe(2);

      requests.forEach(req => req.flush({ completed: false, has_interests: false, profile_complete: false }));
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long text responses', () => {
      const longText = 'a'.repeat(5000);
      const mockData: OnboardingData = {
        relationship_values: longText,
        ideal_evening: longText,
        feeling_understood: longText,
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      expect(req.request.body.relationship_values.length).toBe(5000);
      req.flush({ success: true });
    });

    it('should handle special characters in responses', () => {
      const specialText = 'Test with "quotes", \'apostrophes\', \n newlines, and special chars';
      const mockData: OnboardingData = {
        relationship_values: specialText,
        ideal_evening: specialText,
        feeling_understood: specialText,
        core_values: {},
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      expect(req.request.body.relationship_values).toBe(specialText);
      req.flush({ success: true });
    });

    it('should handle deeply nested objects in core_values', () => {
      const mockData: OnboardingData = {
        relationship_values: 'Test',
        ideal_evening: 'Test',
        feeling_understood: 'Test',
        core_values: {
          level1: {
            level2: {
              level3: {
                value: 'deeply nested'
              }
            }
          }
        },
        personality_traits: {},
        communication_style: {},
        interests: []
      };

      service.completeOnboarding(mockData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/onboarding/complete`);
      expect(req.request.body.core_values).toEqual(mockData.core_values);
      req.flush({ success: true });
    });
  });
});
