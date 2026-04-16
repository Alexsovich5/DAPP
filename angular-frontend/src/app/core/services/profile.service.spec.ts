/**
 * ProfileService Tests
 * Comprehensive tests for user profile management
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ProfileService, UserProfileData, ProfileUpdateData, ProfilePictureResponse } from './profile.service';
import { AuthService } from './auth.service';
import { NotificationService } from './notification.service';
import { ErrorLoggingService } from './error-logging.service';
import { environment } from '../../../environments/environment';
import { User } from '../interfaces/auth.interfaces';

describe('ProfileService', () => {
  let service: ProfileService;
  let httpMock: HttpTestingController;
  let authService: jasmine.SpyObj<AuthService>;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let errorLoggingService: jasmine.SpyObj<ErrorLoggingService>;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', ['updateCurrentUser']);
    const notificationSpy = jasmine.createSpyObj('NotificationService', ['showSuccess', 'showError']);
    const errorLoggingSpy = jasmine.createSpyObj('ErrorLoggingService', ['logApiError']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        ProfileService,
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notificationSpy },
        { provide: ErrorLoggingService, useValue: errorLoggingSpy }
      ]
    });

    service = TestBed.inject(ProfileService);
    httpMock = TestBed.inject(HttpTestingController);
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
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
      expect(service['apiUrl']).toBe(environment.apiUrl);
    });
  });

  describe('getProfile()', () => {
    it('should GET user profile data', () => {
      const mockUser: User = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        gender: 'male',
        is_profile_complete: true
      } as User;

      service.getProfile().subscribe(profile => {
        expect(profile.id).toBe(1);
        expect(profile.email).toBe('test@example.com');
        expect(profile.username).toBe('testuser');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      expect(req.request.method).toBe('GET');
      req.flush(mockUser);
    });

    it('should handle profile with Soul Before Skin fields', () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        emotional_onboarding_completed: true,
        emotional_depth_score: 85,
        core_values: { honesty: true, empathy: true },
        soul_profile_visibility: 'discovery',
        is_profile_complete: true
      } as unknown as User;

      service.getProfile().subscribe(profile => {
        expect(profile.emotional_onboarding_completed).toBe(true);
        expect(profile.emotional_depth_score).toBe(85);
        expect(profile.core_values).toEqual({ honesty: true, empathy: true });
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      req.flush(mockUser);
    });

    it('should handle incomplete profile', () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        is_profile_complete: false
      } as User;

      service.getProfile().subscribe(profile => {
        expect(profile.is_profile_complete).toBe(false);
        expect(profile.first_name).toBeUndefined();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      req.flush(mockUser);
    });

    it('should handle HTTP errors via BaseService', () => {
      spyOn(console, 'error');

      service.getProfile().subscribe({
        next: () => {
          expect(notificationService.showError).toHaveBeenCalled();
          expect(errorLoggingService.logApiError).toHaveBeenCalled();
        },
        error: () => fail('Should not error - BaseService handles errors')
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });
  });

  describe('updateProfile()', () => {
    it('should PUT profile updates', () => {
      const updateData: ProfileUpdateData = {
        first_name: 'Jane',
        last_name: 'Smith',
        bio: 'Updated bio',
        location: 'New York'
      };

      const mockUpdatedUser = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Jane',
        last_name: 'Smith',
        bio: 'Updated bio',
        location: 'New York',
        is_profile_complete: true
      } as User;

      service.updateProfile(updateData).subscribe(profile => {
        expect(profile.first_name).toBe('Jane');
        expect(profile.last_name).toBe('Smith');
        expect(profile.bio).toBe('Updated bio');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(updateData);
      req.flush(mockUpdatedUser);
    });

    it('should update AuthService current user', () => {
      const updateData: ProfileUpdateData = {
        first_name: 'Jane'
      };

      const mockUpdatedUser = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Jane',
        is_profile_complete: true
      } as User;

      service.updateProfile(updateData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      req.flush(mockUpdatedUser);

      expect(authService.updateCurrentUser).toHaveBeenCalledWith(mockUpdatedUser);
    });

    it('should show success notification', () => {
      const updateData: ProfileUpdateData = {
        bio: 'New bio'
      };

      service.updateProfile(updateData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      req.flush({ id: 1, email: 'test@example.com', username: 'test', is_profile_complete: true } as User);

      expect(notificationService.showSuccess).toHaveBeenCalled();
    });

    it('should update Soul Before Skin fields', () => {
      const updateData: ProfileUpdateData = {
        core_values: { honesty: true, empathy: true },
        soul_profile_visibility: 'connections_only',
        photo_sharing_consent: true
      };

      service.updateProfile(updateData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      expect(req.request.body.core_values).toEqual({ honesty: true, empathy: true });
      expect(req.request.body.soul_profile_visibility).toBe('connections_only');
      req.flush({ id: 1, email: 'test@example.com', username: 'test', is_profile_complete: true } as User);
    });

    it('should update interests and dietary preferences', () => {
      const updateData: ProfileUpdateData = {
        interests: ['reading', 'hiking', 'cooking'],
        dietary_preferences: ['vegetarian', 'gluten-free']
      };

      service.updateProfile(updateData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      expect(req.request.body.interests).toEqual(['reading', 'hiking', 'cooking']);
      expect(req.request.body.dietary_preferences).toEqual(['vegetarian', 'gluten-free']);
      req.flush({ id: 1, email: 'test@example.com', username: 'test', is_profile_complete: true } as User);
    });

    it('should update emotional responses', () => {
      const updateData: ProfileUpdateData = {
        emotional_responses: {
          relationship_values: 'Trust and honesty',
          ideal_evening: 'Deep conversation',
          feeling_understood: 'Active listening'
        }
      };

      service.updateProfile(updateData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      expect(req.request.body.emotional_responses).toEqual(updateData.emotional_responses);
      req.flush({ id: 1, email: 'test@example.com', username: 'test', is_profile_complete: true } as User);
    });

    it('should handle partial updates', () => {
      const updateData: ProfileUpdateData = {
        bio: 'Only updating bio'
      };

      service.updateProfile(updateData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      expect(req.request.body).toEqual({ bio: 'Only updating bio' });
      req.flush({ id: 1, email: 'test@example.com', username: 'test', is_profile_complete: true } as User);
    });

    it('should handle HTTP errors via BaseService', () => {
      spyOn(console, 'error');

      service.updateProfile({ bio: 'Test' }).subscribe({
        next: () => {
          expect(notificationService.showError).toHaveBeenCalled();
          expect(errorLoggingService.logApiError).toHaveBeenCalled();
        },
        error: () => fail('Should not error - BaseService handles errors')
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });
  });

  describe('uploadProfilePicture()', () => {
    it('should POST profile picture file', () => {
      const mockFile = new File(['test'], 'profile.jpg', { type: 'image/jpeg' });
      const mockResponse: ProfilePictureResponse = {
        message: 'Profile picture uploaded successfully',
        profile_picture_url: 'https://example.com/profile.jpg'
      };

      service.uploadProfilePicture(mockFile).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.profile_picture_url).toContain('profile.jpg');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me/profile-picture`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body instanceof FormData).toBe(true);
      req.flush(mockResponse);
    });

    it('should show success notification', () => {
      const mockFile = new File(['test'], 'profile.jpg', { type: 'image/jpeg' });

      service.uploadProfilePicture(mockFile).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me/profile-picture`);
      req.flush({ message: 'Success', profile_picture_url: 'url' });

      expect(notificationService.showSuccess).toHaveBeenCalled();
    });

    it('should handle different image formats', () => {
      const pngFile = new File(['test'], 'profile.png', { type: 'image/png' });

      service.uploadProfilePicture(pngFile).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me/profile-picture`);
      const formData = req.request.body as FormData;
      expect(formData.has('file')).toBe(true);
      req.flush({ message: 'Success', profile_picture_url: 'url.png' });
    });

    it('should handle HTTP errors via BaseService', () => {
      const mockFile = new File(['test'], 'profile.jpg', { type: 'image/jpeg' });
      spyOn(console, 'error');

      service.uploadProfilePicture(mockFile).subscribe({
        next: () => {
          expect(notificationService.showError).toHaveBeenCalled();
          expect(errorLoggingService.logApiError).toHaveBeenCalled();
        },
        error: () => fail('Should not error - BaseService handles errors')
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me/profile-picture`);
      req.flush('File too large', { status: 413, statusText: 'Payload Too Large' });
    });
  });

  describe('calculateProfileCompletion()', () => {
    it('should return 100% for complete profile', () => {
      const completeProfile: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        gender: 'male',
        location: 'New York',
        bio: 'Test bio',
        interests: ['reading', 'hiking'],
        dietary_preferences: ['vegetarian'],
        profile_picture: 'url',
        is_profile_complete: true
      };

      const completion = service.calculateProfileCompletion(completeProfile);
      expect(completion).toBe(100);
    });

    it('should return 70% for only required fields', () => {
      const profileWithRequiredOnly: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        gender: 'male',
        location: 'New York',
        bio: 'Test bio',
        is_profile_complete: false
      };

      const completion = service.calculateProfileCompletion(profileWithRequiredOnly);
      expect(completion).toBe(70);
    });

    it('should return 0% for empty profile', () => {
      const emptyProfile: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        is_profile_complete: false
      };

      const completion = service.calculateProfileCompletion(emptyProfile);
      expect(completion).toBe(0);
    });

    it('should handle partial completion', () => {
      const partialProfile: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        is_profile_complete: false
      };

      const completion = service.calculateProfileCompletion(partialProfile);
      // 3/6 required fields = 35%, 0/3 optional = 0%, total = 35%
      expect(completion).toBe(35);
    });

    it('should ignore empty strings', () => {
      const profileWithEmptyStrings: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: '   ',  // Only whitespace
        last_name: '',      // Empty
        date_of_birth: '1990-01-01',
        is_profile_complete: false
      };

      const completion = service.calculateProfileCompletion(profileWithEmptyStrings);
      // Only date_of_birth counts: 1/6 required = ~12%
      expect(completion).toBe(12);
    });

    it('should ignore empty arrays', () => {
      const profileWithEmptyArrays: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        gender: 'male',
        location: 'New York',
        bio: 'Bio',
        interests: [],              // Empty array
        dietary_preferences: [],    // Empty array
        is_profile_complete: false
      };

      const completion = service.calculateProfileCompletion(profileWithEmptyArrays);
      // All required (6/6 = 70%), no optional (0/3 = 0%)
      expect(completion).toBe(70);
    });

    it('should count non-empty arrays', () => {
      const profileWithArrays: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        gender: 'male',
        location: 'New York',
        bio: 'Bio',
        interests: ['reading'],
        dietary_preferences: ['vegetarian'],
        is_profile_complete: false
      };

      const completion = service.calculateProfileCompletion(profileWithArrays);
      // All required (70%) + 2/3 optional (20%)
      expect(completion).toBe(90);
    });

    it('should handle profile picture', () => {
      const profileWithPicture: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        gender: 'male',
        location: 'New York',
        bio: 'Bio',
        profile_picture: 'https://example.com/pic.jpg',
        is_profile_complete: false
      };

      const completion = service.calculateProfileCompletion(profileWithPicture);
      // All required (70%) + 1/3 optional (10%)
      expect(completion).toBe(80);
    });

    it('should calculate 50% completion correctly', () => {
      const halfProfile: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        interests: ['reading'],
        is_profile_complete: false
      };

      const completion = service.calculateProfileCompletion(halfProfile);
      // 3/6 required (35%) + 1/3 optional (10%)
      expect(completion).toBe(45);
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete profile workflow', () => {
      // Get profile
      service.getProfile().subscribe(profile => {
        expect(profile.is_profile_complete).toBe(false);
      });
      const getReq = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      getReq.flush({ id: 1, email: 'test@example.com', username: 'test', is_profile_complete: false } as User);

      // Update profile
      service.updateProfile({ first_name: 'John', last_name: 'Doe' }).subscribe();
      const updateReq = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      updateReq.flush({ id: 1, email: 'test@example.com', username: 'test', first_name: 'John', last_name: 'Doe', is_profile_complete: true } as User);

      // Upload picture
      const file = new File(['test'], 'profile.jpg', { type: 'image/jpeg' });
      service.uploadProfilePicture(file).subscribe();
      const uploadReq = httpMock.expectOne(`${environment.apiUrl}/users/me/profile-picture`);
      uploadReq.flush({ message: 'Success', profile_picture_url: 'url' });
    });

    it('should calculate completion after updates', () => {
      const initialProfile: UserProfileData = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        is_profile_complete: false
      };

      let completion = service.calculateProfileCompletion(initialProfile);
      expect(completion).toBe(0);

      const updatedProfile: UserProfileData = {
        ...initialProfile,
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        gender: 'male',
        location: 'New York',
        bio: 'Bio'
      };

      completion = service.calculateProfileCompletion(updatedProfile);
      expect(completion).toBe(70);
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long bio text', () => {
      const longBio = 'a'.repeat(5000);
      const updateData: ProfileUpdateData = {
        bio: longBio
      };

      service.updateProfile(updateData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      expect(req.request.body.bio.length).toBe(5000);
      req.flush({ id: 1, email: 'test@example.com', username: 'test', is_profile_complete: true } as User);
    });

    it('should handle special characters in profile fields', () => {
      const updateData: ProfileUpdateData = {
        first_name: 'José',
        last_name: "O'Brien",
        bio: 'Test with émojis 🎉 and "quotes"'
      };

      service.updateProfile(updateData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me`);
      expect(req.request.body.first_name).toBe('José');
      expect(req.request.body.last_name).toBe("O'Brien");
      req.flush({ id: 1, email: 'test@example.com', username: 'test', is_profile_complete: true } as User);
    });

    it('should handle large file upload', () => {
      const largeFile = new File([new ArrayBuffer(5000000)], 'large.jpg', { type: 'image/jpeg' });

      service.uploadProfilePicture(largeFile).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/users/me/profile-picture`);
      expect(req.request.body instanceof FormData).toBe(true);
      req.flush({ message: 'Success', profile_picture_url: 'url' });
    });
  });
});
