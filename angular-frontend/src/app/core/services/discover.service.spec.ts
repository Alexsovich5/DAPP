/**
 * DiscoverService Tests
 * Comprehensive tests for profile discovery and matching
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { DiscoverService, PotentialMatch, MatchPercentageResponse } from './discover.service';
import { NotificationService } from './notification.service';
import { ErrorLoggingService } from './error-logging.service';
import { environment } from '../../../environments/environment';

describe('DiscoverService', () => {
  let service: DiscoverService;
  let httpMock: HttpTestingController;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let errorLoggingService: jasmine.SpyObj<ErrorLoggingService>;

  beforeEach(() => {
    const notificationSpy = jasmine.createSpyObj('NotificationService', ['showSuccess', 'showError']);
    const errorLoggingSpy = jasmine.createSpyObj('ErrorLoggingService', ['logApiError']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        DiscoverService,
        { provide: NotificationService, useValue: notificationSpy },
        { provide: ErrorLoggingService, useValue: errorLoggingSpy }
      ]
    });

    service = TestBed.inject(DiscoverService);
    httpMock = TestBed.inject(HttpTestingController);
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;
    errorLoggingService = TestBed.inject(ErrorLoggingService) as jasmine.SpyObj<ErrorLoggingService>;
  });

  afterEach(() => {
    httpMock.verify();
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
      expect(service['apiUrl']).toBe(`${environment.apiUrl}/users`);
    });
  });

  describe('getProfiles()', () => {
    it('should GET potential matches', () => {
      const mockProfiles: PotentialMatch[] = [
        {
          id: 1,
          first_name: 'John',
          last_name: 'Doe',
          date_of_birth: '1990-01-01',
          bio: 'Test bio',
          profile_picture: 'url1',
          interests: ['reading', 'hiking'],
          dietary_preferences: ['vegetarian'],
          location: 'New York',
          matchPercentage: 85
        },
        {
          id: 2,
          first_name: 'Jane',
          last_name: 'Smith',
          date_of_birth: '1992-05-15',
          bio: 'Another bio',
          profile_picture: 'url2',
          interests: ['music', 'art'],
          dietary_preferences: ['vegan'],
          location: 'Los Angeles',
          matchPercentage: 75
        }
      ];

      service.getProfiles().subscribe(profiles => {
        expect(profiles.length).toBe(2);
        expect(profiles[0].id).toBe(mockProfiles[0].id);
        expect(profiles[0].first_name).toBe(mockProfiles[0].first_name);
        expect(profiles[1].id).toBe(mockProfiles[1].id);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/potential-matches`);
      expect(req.request.method).toBe('GET');
      req.flush(mockProfiles);
    });

    it('should return empty array when no profiles exist', () => {
      service.getProfiles().subscribe(profiles => {
        expect(profiles).toEqual([]);
        expect(profiles.length).toBe(0);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/potential-matches`);
      req.flush([]);
    });

    it('should transform lastActive string to Date', () => {
      const mockProfiles: PotentialMatch[] = [{
        id: 1,
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        bio: 'Test',
        profile_picture: 'url',
        interests: ['reading'],
        dietary_preferences: ['none'],
        location: 'NYC',
        lastActive: new Date('2025-10-17T00:00:00Z') as any
      }];

      service.getProfiles().subscribe(profiles => {
        expect(profiles[0].lastActive).toBeInstanceOf(Date);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/potential-matches`);
      req.flush(mockProfiles);
    });

    it('should handle profiles without lastActive', () => {
      const mockProfiles: PotentialMatch[] = [{
        id: 1,
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        bio: 'Test',
        profile_picture: 'url',
        interests: ['reading'],
        dietary_preferences: ['none'],
        location: 'NYC'
      }];

      service.getProfiles().subscribe(profiles => {
        expect(profiles[0].lastActive).toBeUndefined();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/potential-matches`);
      req.flush(mockProfiles);
    });

    it('should handle profiles with multiple interests', () => {
      const mockProfiles: PotentialMatch[] = [{
        id: 1,
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        bio: 'Test',
        profile_picture: 'url',
        interests: ['reading', 'hiking', 'cooking', 'travel', 'music'],
        dietary_preferences: ['vegetarian', 'gluten-free'],
        location: 'NYC'
      }];

      service.getProfiles().subscribe(profiles => {
        expect(profiles[0].interests.length).toBe(5);
        expect(profiles[0].dietary_preferences.length).toBe(2);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/potential-matches`);
      req.flush(mockProfiles);
    });

    it('should handle HTTP errors and return empty array', () => {
      spyOn(console, 'error');

      service.getProfiles().subscribe(profiles => {
        expect(profiles).toEqual([]);
        expect(notificationService.showError).toHaveBeenCalled();
        expect(errorLoggingService.logApiError).toHaveBeenCalled();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/potential-matches`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });

    it('should use correct endpoint URL', () => {
      service.getProfiles().subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/potential-matches`);
      expect(req.request.url).toBe(`${environment.apiUrl}/users/potential-matches`);
      req.flush([]);
    });
  });

  describe('likeProfile()', () => {
    it('should POST to create a match', () => {
      const profileId = '123';

      service.likeProfile(profileId).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/matches`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        receiver_id: 123,
        restaurant_preference: '',
        proposed_date: null
      });
      req.flush({});
    });

    it('should show success notification on successful like', () => {
      const profileId = '456';

      service.likeProfile(profileId).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/matches`);
      req.flush({});

      expect(notificationService.showSuccess).toHaveBeenCalledWith('Profile liked successfully!');
    });

    it('should convert string profileId to integer', () => {
      const profileId = '789';

      service.likeProfile(profileId).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/matches`);
      expect(req.request.body.receiver_id).toBe(789);
      expect(typeof req.request.body.receiver_id).toBe('number');
      req.flush({});
    });

    it('should handle HTTP errors', () => {
      const profileId = '999';
      spyOn(console, 'error');

      service.likeProfile(profileId).subscribe(result => {
        expect(result).toBeUndefined();
        expect(notificationService.showError).toHaveBeenCalled();
        expect(errorLoggingService.logApiError).toHaveBeenCalled();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/matches`);
      req.flush('Conflict', { status: 409, statusText: 'Conflict' });
    });

    it('should send empty restaurant_preference', () => {
      service.likeProfile('100').subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/matches`);
      expect(req.request.body.restaurant_preference).toBe('');
      req.flush({});
    });

    it('should send null proposed_date', () => {
      service.likeProfile('200').subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/matches`);
      expect(req.request.body.proposed_date).toBeNull();
      req.flush({});
    });
  });

  describe('dislikeProfile()', () => {
    it('should return success without making HTTP call', () => {
      service.dislikeProfile('123').subscribe(result => {
        expect(result).toBeUndefined();
      });

      httpMock.expectNone(`${environment.apiUrl}/matches`);
    });

    it('should complete immediately', (done) => {
      service.dislikeProfile('456').subscribe(result => {
        expect(result).toBeUndefined();
        done();
      });
    });

    it('should handle any profileId without error', () => {
      let count = 0;

      service.dislikeProfile('').subscribe(() => count++);
      service.dislikeProfile('0').subscribe(() => count++);
      service.dislikeProfile('999999').subscribe(() => count++);

      expect(count).toBe(3);
      httpMock.expectNone(() => true);
    });
  });

  describe('getMatches()', () => {
    it('should GET sent matches', () => {
      const mockMatches: PotentialMatch[] = [
        {
          id: 1,
          first_name: 'Match1',
          last_name: 'User',
          date_of_birth: '1990-01-01',
          bio: 'Matched user',
          profile_picture: 'url',
          interests: ['reading'],
          dietary_preferences: ['none'],
          location: 'NYC'
        }
      ];

      service.getMatches().subscribe(matches => {
        expect(matches).toEqual(mockMatches);
        expect(matches.length).toBe(1);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/matches/sent`);
      expect(req.request.method).toBe('GET');
      req.flush(mockMatches);
    });

    it('should return empty array when no matches exist', () => {
      service.getMatches().subscribe(matches => {
        expect(matches).toEqual([]);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/matches/sent`);
      req.flush([]);
    });

    it('should handle HTTP errors', () => {
      service.getMatches().subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error).toBeDefined();
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/matches/sent`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });
  });

  describe('getMutualInterests()', () => {
    it('should GET mutual interests for a profile', () => {
      const profileId = '123';
      const mockInterests = ['reading', 'hiking', 'cooking'];

      service.getMutualInterests(profileId).subscribe(interests => {
        expect(interests).toEqual(mockInterests);
        expect(interests.length).toBe(3);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/mutual-interests/${profileId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockInterests);
    });

    it('should return empty array when no mutual interests', () => {
      const profileId = '456';

      service.getMutualInterests(profileId).subscribe(interests => {
        expect(interests).toEqual([]);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/mutual-interests/${profileId}`);
      req.flush([]);
    });

    it('should handle HTTP errors and return empty array', () => {
      const profileId = '789';
      spyOn(console, 'error');

      service.getMutualInterests(profileId).subscribe(interests => {
        expect(interests).toEqual([]);
        expect(notificationService.showError).toHaveBeenCalled();
        expect(errorLoggingService.logApiError).toHaveBeenCalled();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/mutual-interests/${profileId}`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });

    it('should use correct endpoint URL', () => {
      const profileId = '999';

      service.getMutualInterests(profileId).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/mutual-interests/${profileId}`);
      expect(req.request.url).toBe(`${environment.apiUrl}/users/mutual-interests/${profileId}`);
      req.flush([]);
    });
  });

  describe('getMatchPercentage()', () => {
    it('should GET match percentage and transform response', () => {
      const profileId = '123';
      const mockResponse = {
        match_percentage: 85,
        breakdown: { interests: 90, values: 80 },
        compatibility_rating: 'Excellent',
        mutual_interests_count: 5
      };

      service.getMatchPercentage(profileId).subscribe(response => {
        expect(response.percentage).toBe(85);
        expect(response.breakdown).toEqual({ interests: 90, values: 80 });
        expect(response.rating).toBe('Excellent');
        expect(response.mutualInterestsCount).toBe(5);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/match-percentage/${profileId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should map response fields correctly', () => {
      const profileId = '456';
      const mockResponse = {
        match_percentage: 75,
        breakdown: { test: 'value' },
        compatibility_rating: 'Good',
        mutual_interests_count: 3
      };

      service.getMatchPercentage(profileId).subscribe(response => {
        // Check that old field names are mapped to new ones
        expect(response.percentage).toBe(mockResponse.match_percentage);
        expect(response.rating).toBe(mockResponse.compatibility_rating);
        expect(response.mutualInterestsCount).toBe(mockResponse.mutual_interests_count);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/match-percentage/${profileId}`);
      req.flush(mockResponse);
    });

    it('should handle HTTP errors and return default values', () => {
      const profileId = '789';
      spyOn(console, 'error');

      service.getMatchPercentage(profileId).subscribe(response => {
        expect(response.percentage).toBe(0);
        expect(response.breakdown).toEqual({});
        expect(response.rating).toBe('Unknown');
        expect(response.mutualInterestsCount).toBe(0);
        expect(notificationService.showError).toHaveBeenCalled();
        expect(errorLoggingService.logApiError).toHaveBeenCalled();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/match-percentage/${profileId}`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });

    it('should handle zero match percentage', () => {
      const profileId = '100';
      const mockResponse = {
        match_percentage: 0,
        breakdown: {},
        compatibility_rating: 'Low',
        mutual_interests_count: 0
      };

      service.getMatchPercentage(profileId).subscribe(response => {
        expect(response.percentage).toBe(0);
        expect(response.mutualInterestsCount).toBe(0);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/match-percentage/${profileId}`);
      req.flush(mockResponse);
    });

    it('should handle high match percentage', () => {
      const profileId = '200';
      const mockResponse = {
        match_percentage: 100,
        breakdown: { perfect: 100 },
        compatibility_rating: 'Perfect',
        mutual_interests_count: 20
      };

      service.getMatchPercentage(profileId).subscribe(response => {
        expect(response.percentage).toBe(100);
        expect(response.rating).toBe('Perfect');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/match-percentage/${profileId}`);
      req.flush(mockResponse);
    });

    it('should use correct endpoint URL', () => {
      const profileId = '999';

      service.getMatchPercentage(profileId).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/match-percentage/${profileId}`);
      expect(req.request.url).toBe(`${environment.apiUrl}/users/match-percentage/${profileId}`);
      req.flush({
        match_percentage: 50,
        breakdown: {},
        compatibility_rating: 'Medium',
        mutual_interests_count: 2
      });
    });
  });

  describe('Integration Tests', () => {
    it('should handle multiple concurrent requests', () => {
      service.getProfiles().subscribe();
      service.getMatches().subscribe();
      service.getMutualInterests('123').subscribe();

      const requests = httpMock.match(req => req.url.includes(environment.apiUrl));
      expect(requests.length).toBe(3);

      requests[0].flush([]);
      requests[1].flush([]);
      requests[2].flush([]);
    });

    it('should handle sequential profile discovery workflow', () => {
      // Get profiles
      service.getProfiles().subscribe(profiles => {
        expect(profiles).toBeDefined();
      });
      const getReq = httpMock.expectOne(`${environment.apiUrl}/users/potential-matches`);
      getReq.flush([{ id: 1, first_name: 'John', last_name: 'Doe', date_of_birth: '1990-01-01', bio: 'Test', profile_picture: 'url', interests: [], dietary_preferences: [], location: 'NYC' }]);

      // Get mutual interests for first profile
      service.getMutualInterests('1').subscribe(interests => {
        expect(interests).toBeDefined();
      });
      const interestsReq = httpMock.expectOne(`${environment.apiUrl}/users/mutual-interests/1`);
      interestsReq.flush(['reading']);

      // Get match percentage
      service.getMatchPercentage('1').subscribe(match => {
        expect(match.percentage).toBeDefined();
      });
      const matchReq = httpMock.expectOne(`${environment.apiUrl}/users/match-percentage/1`);
      matchReq.flush({ match_percentage: 80, breakdown: {}, compatibility_rating: 'Good', mutual_interests_count: 1 });

      // Like profile
      service.likeProfile('1').subscribe();
      const likeReq = httpMock.expectOne(`${environment.apiUrl}/matches`);
      likeReq.flush({});
    });
  });
});
