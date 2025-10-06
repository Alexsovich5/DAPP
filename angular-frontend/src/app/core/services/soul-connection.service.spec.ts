/**
 * Comprehensive tests for Soul Connection Service - Core Dating Platform Frontend
 * Tests the "Soul Before Skin" matching and connection management
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { of } from 'rxjs';

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

interface DiscoveryResponse {
  user_id: number;
  compatibility_score: number;
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

  const mockApiUrl = environment.apiUrl;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', ['getToken']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        SoulConnectionService,
        { provide: AuthService, useValue: authSpy }
      ]
    });

    service = TestBed.inject(SoulConnectionService);
    httpMock = TestBed.inject(HttpTestingController);

    const authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    authService.getToken.and.returnValue('mock-jwt-token');
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Soul Connection Discovery', () => {
    it('should discover potential soul connections', () => {
      const mockMatches: DiscoveryResponse[] = [
        {
          user_id: 2,
          compatibility_score: 85.5,
          preview_profile: {
            life_philosophy: 'Connection before appearance',
            core_values: ['authenticity', 'growth'],
            interests: ['reading', 'hiking'],
            emotional_depth_score: 8.5
          }
        }
      ];

      service.discoverSoulConnections().subscribe(matches => {
        expect(matches.length).toBe(1);
        expect(matches[0].compatibility_score).toBe(85.5);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/discover`);
      expect(req.request.method).toBe('GET');
      req.flush(mockMatches);
    });
  });

  describe('Soul Connection Initiation', () => {
    it('should initiate a new soul connection', () => {
      const connectionData = {
        target_user_id: 2,
        message: 'I felt a deep connection reading your profile'
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

      service.initiateSoulConnection(connectionData).subscribe(connection => {
        expect(connection.connection_stage).toBe('soul_discovery');
        expect(connection.compatibility_score).toBe(85.5);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/initiate`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(connectionData);
      req.flush(mockResponse);
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
          mutual_reveal_consent: false,
          first_dinner_completed: false,
          created_at: '2025-01-15T10:00:00Z'
        }
      ];

      service.getActiveConnections().subscribe(connections => {
        expect(connections.length).toBe(1);
        expect(connections[0].connection_stage).toBe('revelation_sharing');
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/active`);
      expect(req.request.method).toBe('GET');
      req.flush(mockConnections);
    });

    it('should get a specific soul connection', () => {
      const connectionId = 1;
      const mockConnection: SoulConnection = {
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
        mutual_reveal_consent: false,
        first_dinner_completed: false,
        created_at: '2025-01-15T10:00:00Z'
      };

      service.getSoulConnection(connectionId).subscribe(connection => {
        expect(connection.id).toBe(connectionId);
        expect(connection.connection_stage).toBe('revelation_sharing');
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/${connectionId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockConnection);
    });
  });

  describe('Connection Stage Progression', () => {
    it('should progress connection stage', () => {
      const connectionId = 1;
      const newStage = 'photo_reveal';

      const mockResponse: SoulConnection = {
        id: 1,
        user1_id: 1,
        user2_id: 2,
        connection_stage: 'photo_reveal',
        compatibility_score: 85.5,
        compatibility_breakdown: {
          interests: 75,
          values: 90,
          demographics: 80,
          communication: 85,
          personality: 88
        },
        reveal_day: 7,
        mutual_reveal_consent: true,
        first_dinner_completed: false,
        created_at: '2025-01-15T10:00:00Z'
      };

      service.progressConnectionStage(connectionId, newStage).subscribe(connection => {
        expect(connection.connection_stage).toBe('photo_reveal');
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/${connectionId}/progress`);
      expect(req.request.method).toBe('PUT');
      req.flush(mockResponse);
    });
  });

  describe('Photo Reveal Consent', () => {
    it('should give reveal consent', () => {
      const connectionId = 1;

      const mockResponse: SoulConnection = {
        id: 1,
        user1_id: 1,
        user2_id: 2,
        connection_stage: 'photo_reveal',
        compatibility_score: 85.5,
        compatibility_breakdown: {
          interests: 75,
          values: 90,
          demographics: 80,
          communication: 85,
          personality: 88
        },
        reveal_day: 7,
        mutual_reveal_consent: true,
        first_dinner_completed: false,
        created_at: '2025-01-15T10:00:00Z'
      };

      service.giveRevealConsent(connectionId).subscribe(connection => {
        expect(connection.mutual_reveal_consent).toBe(true);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/connections/${connectionId}/reveal-consent`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });
});
