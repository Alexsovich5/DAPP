/**
 * Comprehensive tests for Revelation Service - Core "Soul Before Skin" Feature
 * Tests the 7-day revelation cycle and emotional connection building
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { RevelationService } from './revelation.service';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';

import { DailyRevelation, DailyRevelationCreate, RevelationType } from '../interfaces/revelation.interfaces';

interface RevelationTimeline {
  day_number: number;
  revelation_type: RevelationType;
  user1_revelation?: DailyRevelation;
  user2_revelation?: DailyRevelation;
  both_completed: boolean;
  unlock_date: string;
}

describe('RevelationService', () => {
  let service: RevelationService;
  let httpMock: HttpTestingController;

  const mockApiUrl = environment.apiUrl;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', ['getToken']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        RevelationService,
        { provide: AuthService, useValue: authSpy }
      ]
    });

    service = TestBed.inject(RevelationService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Revelation Creation', () => {
    it('should create a new daily revelation', () => {
      const revelationData: DailyRevelationCreate = {
        connection_id: 1,
        day_number: 1,
        revelation_type: 'personal_value',
        content: 'Family and authenticity are the foundations of my life. I believe in being true to yourself and cherishing the people who matter most.'
      };

      const mockResponse: DailyRevelation = {
        id: 1,
        connection_id: 1,
        sender_id: 1,
        day_number: 1,
        revelation_type: 'personal_value',
        content: revelationData.content,
        created_at: new Date().toISOString(),
        is_read: false
      };

      const mockTimeline = {
        revelations: [mockResponse],
        current_day: 1,
        is_cycle_complete: false
      };

      service.createRevelation(revelationData).subscribe(revelation => {
        expect(revelation.day_number).toBe(1);
        expect(revelation.revelation_type).toBe('personal_value');
        expect(revelation.content).toContain('authenticity');
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/create`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(revelationData);
      req.flush(mockResponse);

      // Expect the timeline refresh call
      const timelineReq = httpMock.expectOne(`${mockApiUrl}/revelations/timeline/${revelationData.connection_id}`);
      expect(timelineReq.request.method).toBe('GET');
      timelineReq.flush(mockTimeline);
    });

    it('should validate revelation content length', () => {
      const shortContent = 'Too short';
      const result = service.validateRevelationContent(shortContent);
      expect(result.valid).toBe(false);
      expect(result.message).toContain('10 characters');

      const appropriateContent = 'This is a meaningful revelation that shares something deep and personal about my values and experiences in life.';
      const validResult = service.validateRevelationContent(appropriateContent);
      expect(validResult.valid).toBe(true);
    });
  });

  describe('Revelation Timeline', () => {
    it('should retrieve complete revelation timeline for connection', () => {
      const connectionId = 1;
      const mockTimeline: RevelationTimeline[] = [
        {
          day_number: 1,
          revelation_type: 'personal_value',
          user1_revelation: {
            id: 1,
            connection_id: 1,
            sender_id: 1,
            day_number: 1,
            revelation_type: 'personal_value',
            content: 'Family and loyalty guide all my decisions',
            created_at: '2025-01-15T10:00:00Z',
            is_read: true
          },
          user2_revelation: {
            id: 2,
            connection_id: 1,
            sender_id: 2,
            day_number: 1,
            revelation_type: 'personal_value',
            content: 'Authenticity and growth are my core values',
            created_at: '2025-01-15T14:30:00Z',
            is_read: true
          },
          both_completed: true,
          unlock_date: '2025-01-15T00:00:00Z'
        }
      ];

      service.getRevelationTimeline(connectionId).subscribe(timeline => {
        const timelineData = timeline as unknown as RevelationTimeline[];
        expect(timelineData).toEqual(mockTimeline);
        expect(timelineData.length).toBe(1);
        expect(timelineData[0].both_completed).toBe(true);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/timeline/${connectionId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockTimeline);
    });
  });

  describe('Revelation Reactions', () => {
    it('should react to a revelation', () => {
      const revelationId = 1;
      const emoji = 'heart';

      const mockResponse = {
        revelation_id: revelationId,
        emoji: emoji,
        created_at: new Date().toISOString()
      };

      service.reactToRevelation(revelationId, emoji).subscribe(response => {
        expect(response['emoji']).toBe('heart');
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/${revelationId}/react`);
      expect(req.request.method).toBe('PUT');
      req.flush(mockResponse);
    });
  });
});
