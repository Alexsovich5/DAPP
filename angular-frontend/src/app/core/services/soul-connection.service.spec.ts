/**
 * Comprehensive tests for Soul Connection Service - Core Dating Platform Frontend
 * Tests the "Soul Before Skin" matching and connection management
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';

import { SoulConnectionService } from './soul-connection.service';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';

interface SoulConnection {
  id: number;
  user1_id: number;
  user2_id: number;
  connection_stage: string;
  compatibility_score: number;
  compatibility_breakdown: {
    interests: number;
    values: number;
    demographics: number;
    communication: number;
    personality: number;
  };
  reveal_day: number;
  mutual_reveal_consent: boolean | null;
  first_dinner_completed: boolean;
  created_at: string;
}

interface CompatibilityResult {
  total_compatibility: number;
  breakdown: {
    interests: number;
    values: number;
    demographics: number;
  };
  match_quality: string;
}

interface PotentialMatch {
  user_id: number;
  compatibility_score: number;
  compatibility_breakdown: CompatibilityResult['breakdown'];
  preview_profile: {
    life_philosophy: string;
    core_values: string[];
    interests: string[];
    emotional_depth_score: number;
  };
}

describe('SoulConnectionService', () => {
  let service: SoulConnectionService;
  let httpMock: HttpTestingController;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  const mockApiUrl = environment.apiUrl;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', ['getToken', 'getCurrentUser']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        SoulConnectionService,
        { provide: AuthService, useValue: authSpy }
      ]
    });

    service = TestBed.inject(SoulConnectionService);
    httpMock = TestBed.inject(HttpTestingController);
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;

    // Default auth setup
    authServiceSpy.getToken.and.returnValue('mock-jwt-token');
    authServiceSpy.getCurrentUser.and.returnValue(of({ id: 1, email: 'test@example.com' }));
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Soul Connection Discovery', () => {
    it('should discover potential soul connections', () => {
      const mockPotentialMatches: PotentialMatch[] = [
        {
          user_id: 2,
          compatibility_score: 85.5,
          compatibility_breakdown: {
            interests: 75,
            values: 90,
            demographics: 80
          },
          preview_profile: {
            life_philosophy: 'Connection before appearance, soul before skin',
            core_values: ['authenticity', 'growth', 'compassion'],
            interests: ['cooking', 'reading', 'hiking', 'photography'],
            emotional_depth_score: 8.5
          }
        },
        {
          user_id: 3,
          compatibility_score: 72.3,
          compatibility_breakdown: {
            interests: 60,
            values: 85,
            demographics: 75
          },
          preview_profile: {
            life_philosophy: 'Meaningful connections shape our souls',
            core_values: ['loyalty', 'adventure', 'authenticity'],
            interests: ['music', 'travel', 'cooking', 'art'],
            emotional_depth_score: 7.8
          }
        }
      ];

      service.discoverPotentialConnections().subscribe(matches => {
        expect(matches).toEqual(mockPotentialMatches);
        expect(matches.length).toBe(2);
        expect(matches[0].compatibility_score).toBeGreaterThan(matches[1].compatibility_score);
        expect(matches[0].preview_profile.core_values).toContain('authenticity');
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/discover`);
      expect(req.request.method).toBe('GET');
      expect(req.request.headers.get('Authorization')).toBe('Bearer mock-jwt-token');
      req.flush(mockPotentialMatches);
    });

    it('should handle empty discovery results', () => {
      service.discoverPotentialConnections().subscribe(matches => {
        expect(matches).toEqual([]);
        expect(matches.length).toBe(0);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/discover`);
      req.flush([]);
    });

    it('should handle discovery errors gracefully', () => {
      const errorMessage = 'Discovery service temporarily unavailable';
      
      service.discoverPotentialConnections().subscribe({
        next: () => fail('Should have failed with error'),
        error: (error) => {
          expect(error.message).toContain('Discovery failed');
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/discover`);
      req.flush({ error: errorMessage }, { status: 500, statusText: 'Server Error' });
    });

    it('should filter matches by minimum compatibility threshold', () => {
      const mockMatches: PotentialMatch[] = [
        { user_id: 1, compatibility_score: 85, compatibility_breakdown: { interests: 80, values: 85, demographics: 90 }, preview_profile: { life_philosophy: 'Test', core_values: [], interests: [], emotional_depth_score: 8 } },
        { user_id: 2, compatibility_score: 45, compatibility_breakdown: { interests: 40, values: 50, demographics: 45 }, preview_profile: { life_philosophy: 'Test', core_values: [], interests: [], emotional_depth_score: 5 } },
        { user_id: 3, compatibility_score: 92, compatibility_breakdown: { interests: 90, values: 95, demographics: 90 }, preview_profile: { life_philosophy: 'Test', core_values: [], interests: [], emotional_depth_score: 9 } }
      ];

      service.discoverPotentialConnections(50).subscribe(matches => {
        expect(matches.length).toBe(2);
        expect(matches.every(m => m.compatibility_score >= 50)).toBe(true);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/discover`);
      req.flush(mockMatches);
    });
  });

  describe('Soul Connection Initiation', () => {
    it('should initiate a new soul connection', () => {
      const connectionRequest = {
        target_user_id: 2,
        message: 'I felt a deep connection reading your profile. Would you like to start our soul journey together?'
      };

      const mockResponse: SoulConnection = {
        id: 1,
        user1_id: 1,
        user2_id: 2,
        connection_stage: 'soul_discovery',
        compatibility_score: 85.5,
        compatibility_breakdown: {
          interests: 75,
          values: 90,
          demographics: 80,
          communication: 85,
          personality: 88
        },
        reveal_day: 1,
        mutual_reveal_consent: null,
        first_dinner_completed: false,
        created_at: new Date().toISOString()
      };

      service.initiateConnection(connectionRequest.target_user_id, connectionRequest.message).subscribe(connection => {
        expect(connection).toEqual(mockResponse);
        expect(connection.connection_stage).toBe('soul_discovery');
        expect(connection.compatibility_score).toBe(85.5);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/initiate`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(connectionRequest);
      req.flush(mockResponse);
    });

    it('should handle duplicate connection prevention', () => {
      const connectionRequest = {
        target_user_id: 2,
        message: 'Second attempt at connection'
      };

      service.initiateConnection(connectionRequest.target_user_id, connectionRequest.message).subscribe({
        next: () => fail('Should have failed with duplicate error'),
        error: (error) => {
          expect(error.status).toBe(400);
          expect(error.error.detail).toContain('already exists');
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/initiate`);
      req.flush(
        { detail: 'Connection already exists between these users' },
        { status: 400, statusText: 'Bad Request' }
      );
    });

    it('should validate connection message requirements', () => {
      const shortMessage = 'Hi';
      
      service.initiateConnection(2, shortMessage).subscribe({
        next: () => fail('Should have failed with validation error'),
        error: (error) => {
          expect(error).toBeDefined();
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/initiate`);
      req.flush(
        { detail: 'Message must be at least 20 characters for meaningful connection' },
        { status: 422, statusText: 'Validation Error' }
      );
    });
  });

  describe('Active Connections Management', () => {
    it('should retrieve active soul connections', () => {
      const mockConnections: SoulConnection[] = [
        {
          id: 1,
          user1_id: 1,
          user2_id: 2,
          connection_stage: 'revelation_sharing',
          compatibility_score: 85.5,
          compatibility_breakdown: {
            interests: 75,
            values: 90,
            demographics: 80,
            communication: 85,
            personality: 88
          },
          reveal_day: 3,
          mutual_reveal_consent: null,
          first_dinner_completed: false,
          created_at: '2025-01-15T10:00:00Z'
        },
        {
          id: 2,
          user1_id: 1,
          user2_id: 3,
          connection_stage: 'deepening_bond',
          compatibility_score: 72.3,
          compatibility_breakdown: {
            interests: 65,
            values: 80,
            demographics: 70,
            communication: 75,
            personality: 72
          },
          reveal_day: 5,
          mutual_reveal_consent: false,
          first_dinner_completed: false,
          created_at: '2025-01-10T14:30:00Z'
        }
      ];

      service.getActiveConnections().subscribe(connections => {
        expect(connections).toEqual(mockConnections);
        expect(connections.length).toBe(2);
        expect(connections[0].connection_stage).toBe('revelation_sharing');
        expect(connections[1].connection_stage).toBe('deepening_bond');
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/active`);
      expect(req.request.method).toBe('GET');
      req.flush(mockConnections);
    });

    it('should handle no active connections', () => {
      service.getActiveConnections().subscribe(connections => {
        expect(connections).toEqual([]);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/active`);
      req.flush([]);
    });

    it('should get specific connection details', () => {
      const connectionId = 1;
      const mockConnection: SoulConnection = {
        id: connectionId,
        user1_id: 1,
        user2_id: 2,
        connection_stage: 'photo_reveal',
        compatibility_score: 88.7,
        compatibility_breakdown: {
          interests: 85,
          values: 95,
          demographics: 80,
          communication: 90,
          personality: 85
        },
        reveal_day: 7,
        mutual_reveal_consent: true,
        first_dinner_completed: false,
        created_at: '2025-01-08T09:15:00Z'
      };

      service.getConnection(connectionId).subscribe(connection => {
        expect(connection).toEqual(mockConnection);
        expect(connection.mutual_reveal_consent).toBe(true);
        expect(connection.reveal_day).toBe(7);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/${connectionId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockConnection);
    });
  });

  describe('Connection Stage Management', () => {
    it('should update connection stage progression', () => {
      const connectionId = 1;
      const stageUpdate = {
        connection_stage: 'revelation_sharing',
        progress_notes: 'Both users completed day 3 revelations'
      };

      const mockUpdatedConnection: SoulConnection = {
        id: connectionId,
        user1_id: 1,
        user2_id: 2,
        connection_stage: 'revelation_sharing',
        compatibility_score: 85.5,
        compatibility_breakdown: {
          interests: 75,
          values: 90,
          demographics: 80,
          communication: 85,
          personality: 88
        },
        reveal_day: 3,
        mutual_reveal_consent: null,
        first_dinner_completed: false,
        created_at: '2025-01-15T10:00:00Z'
      };

      service.updateConnectionStage(connectionId, stageUpdate.connection_stage, stageUpdate.progress_notes).subscribe(connection => {
        expect(connection.connection_stage).toBe('revelation_sharing');
        expect(connection.reveal_day).toBe(3);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/${connectionId}/stage`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(stageUpdate);
      req.flush(mockUpdatedConnection);
    });

    it('should validate connection stage progression rules', () => {
      const connectionId = 1;
      const invalidStageUpdate = {
        connection_stage: 'photo_reveal'  // Skipping revelation stages
      };

      service.updateConnectionStage(connectionId, invalidStageUpdate.connection_stage).subscribe({
        next: () => fail('Should have failed with validation error'),
        error: (error) => {
          expect(error.status).toBe(400);
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/${connectionId}/stage`);
      req.flush(
        { detail: 'Must complete revelation stages before photo reveal' },
        { status: 400, statusText: 'Bad Request' }
      );
    });
  });

  describe('Photo Reveal Consent Management', () => {
    it('should handle photo reveal consent', () => {
      const connectionId = 1;
      const consentData = {
        mutual_reveal_consent: true,
        consent_timestamp: new Date().toISOString()
      };

      service.updatePhotoRevealConsent(connectionId, true).subscribe(result => {
        expect(result.mutual_reveal_consent).toBe(true);
        expect(result.consent_timestamp).toBeDefined();
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/${connectionId}/photo-consent`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body.mutual_reveal_consent).toBe(true);
      req.flush(consentData);
    });

    it('should handle photo reveal consent withdrawal', () => {
      const connectionId = 1;
      
      service.updatePhotoRevealConsent(connectionId, false).subscribe(result => {
        expect(result.mutual_reveal_consent).toBe(false);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/${connectionId}/photo-consent`);
      expect(req.request.body.mutual_reveal_consent).toBe(false);
      req.flush({ mutual_reveal_consent: false });
    });
  });

  describe('Compatibility Analysis', () => {
    it('should analyze compatibility breakdown for insights', () => {
      const compatibility = {
        interests: 75,
        values: 90,
        demographics: 80,
        communication: 85,
        personality: 88
      };

      const analysis = service.analyzeCompatibility(compatibility);

      expect(analysis.strongest_area).toBe('values');
      expect(analysis.improvement_area).toBe('interests');
      expect(analysis.overall_rating).toBe('excellent');
      expect(analysis.recommendation).toContain('values alignment');
    });

    it('should provide meaningful compatibility insights', () => {
      const lowCompatibility = {
        interests: 45,
        values: 55,
        demographics: 40,
        communication: 50,
        personality: 48
      };

      const analysis = service.analyzeCompatibility(lowCompatibility);

      expect(analysis.overall_rating).toBe('moderate');
      expect(analysis.recommendation).toContain('explore shared interests');
    });

    it('should calculate weighted compatibility score', () => {
      const breakdown = {
        interests: 80,
        values: 90,
        demographics: 70,
        communication: 85,
        personality: 75
      };

      const weightedScore = service.calculateWeightedCompatibility(breakdown);

      // Values should have highest weight (30%), interests 25%, etc.
      expect(weightedScore).toBeGreaterThan(75);
      expect(weightedScore).toBeLessThan(85);
    });
  });

  describe('Connection Privacy and Safety', () => {
    it('should respect privacy controls', () => {
      service.getActiveConnections().subscribe(connections => {
        connections.forEach(connection => {
          // Should not expose sensitive personal data
          expect((connection as any).phone_number).toBeUndefined();
          expect((connection as any).full_address).toBeUndefined();
          expect((connection as any).private_notes).toBeUndefined();
        });
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/active`);
      req.flush([
        {
          id: 1,
          user1_id: 1,
          user2_id: 2,
          connection_stage: 'soul_discovery',
          compatibility_score: 85,
          compatibility_breakdown: { interests: 80, values: 90, demographics: 85, communication: 85, personality: 80 },
          reveal_day: 1,
          mutual_reveal_consent: null,
          first_dinner_completed: false,
          created_at: '2025-01-15T10:00:00Z'
        }
      ]);
    });

    it('should enforce authentication requirements', () => {
      authServiceSpy.getToken.and.returnValue(null);

      service.getActiveConnections().subscribe({
        next: () => fail('Should require authentication'),
        error: (error) => {
          expect(error.status).toBe(401);
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/active`);
      req.flush(
        { detail: 'Authentication required' },
        { status: 401, statusText: 'Unauthorized' }
      );
    });
  });

  describe('Error Handling and Resilience', () => {
    it('should handle network errors gracefully', () => {
      service.discoverPotentialConnections().subscribe({
        next: () => fail('Should have failed with network error'),
        error: (error) => {
          expect(error.message).toContain('Network error');
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/discover`);
      req.error(new ErrorEvent('Network error'));
    });

    it('should retry failed requests with exponential backoff', (done) => {
      let attempts = 0;
      
      service.discoverPotentialConnections().subscribe({
        next: (matches) => {
          expect(attempts).toBe(3); // Should retry 3 times
          expect(matches).toEqual([]);
          done();
        },
        error: () => fail('Should eventually succeed after retries')
      });

      // Mock multiple failed attempts followed by success
      const expectRequest = () => {
        const req = httpMock.expectOne(`${mockApiUrl}/connections/discover`);
        attempts++;
        
        if (attempts < 3) {
          req.error(new ErrorEvent('Temporary error'));
          // Schedule next expectation
          setTimeout(expectRequest, 10);
        } else {
          req.flush([]);
        }
      };
      
      expectRequest();
    });

    it('should validate service inputs', () => {
      expect(() => service.initiateConnection(-1, 'test')).toThrowError('Invalid user ID');
      expect(() => service.initiateConnection(2, '')).toThrowError('Message cannot be empty');
      expect(() => service.updateConnectionStage(0, 'invalid_stage')).toThrowError('Invalid connection ID');
    });
  });

  describe('Performance and Optimization', () => {
    it('should cache frequently accessed connections', () => {
      const mockConnections: SoulConnection[] = [
        {
          id: 1, user1_id: 1, user2_id: 2, connection_stage: 'active',
          compatibility_score: 85, compatibility_breakdown: { interests: 80, values: 90, demographics: 85, communication: 85, personality: 80 },
          reveal_day: 3, mutual_reveal_consent: null, first_dinner_completed: false, created_at: '2025-01-15T10:00:00Z'
        }
      ];

      // First request
      service.getActiveConnections().subscribe();
      let req = httpMock.expectOne(`${mockApiUrl}/connections/active`);
      req.flush(mockConnections);

      // Second request should use cache (no HTTP request)
      service.getActiveConnections().subscribe(connections => {
        expect(connections).toEqual(mockConnections);
      });

      // Should not make second HTTP request due to caching
      httpMock.expectNone(`${mockApiUrl}/connections/active`);
    });

    it('should debounce rapid connection discovery requests', (done) => {
      let requestCount = 0;

      // Make multiple rapid requests
      for (let i = 0; i < 5; i++) {
        service.discoverPotentialConnections().subscribe();
      }

      setTimeout(() => {
        // Should only make one request due to debouncing
        const req = httpMock.expectOne(`${mockApiUrl}/connections/discover`);
        req.flush([]);
        
        expect(requestCount).toBe(0); // Requests were debounced
        done();
      }, 600); // Wait for debounce period
    });
  });
});