/**
 * Comprehensive tests for Revelation Service - Core "Soul Before Skin" Feature
 * Tests the 7-day revelation cycle and emotional connection building
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { of } from 'rxjs';

import { RevelationService } from './revelation.service';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';

interface DailyRevelation {
  id: number;
  connection_id: number;
  sender_id: number;
  day_number: number;
  revelation_type: string;
  content: string;
  created_at: string;
  reaction_count?: number;
  user_reaction?: string;
}

interface RevelationTimeline {
  day_number: number;
  revelation_type: string;
  user1_revelation?: DailyRevelation;
  user2_revelation?: DailyRevelation;
  both_completed: boolean;
  unlock_date: string;
}

interface RevelationPrompt {
  day: number;
  type: string;
  title: string;
  prompt: string;
  examples: string[];
  character_guidance: {
    min_length: number;
    suggested_length: number;
    tone: string;
  };
}

describe('RevelationService', () => {
  let service: RevelationService;
  let httpMock: HttpTestingController;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  const mockApiUrl = environment.apiUrl;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', ['getToken', 'getCurrentUser']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        RevelationService,
        { provide: AuthService, useValue: authSpy }
      ]
    });

    service = TestBed.inject(RevelationService);
    httpMock = TestBed.inject(HttpTestingController);
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;

    authServiceSpy.getToken.and.returnValue('mock-jwt-token');
    authServiceSpy.getCurrentUser.and.returnValue(of({ id: 1, email: 'test@example.com' }));
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Revelation Creation', () => {
    it('should create a new daily revelation', () => {
      const revelationData = {
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
        created_at: new Date().toISOString()
      };

      service.createRevelation(
        revelationData.connection_id,
        revelationData.day_number,
        revelationData.revelation_type,
        revelationData.content
      ).subscribe(revelation => {
        expect(revelation).toEqual(mockResponse);
        expect(revelation.day_number).toBe(1);
        expect(revelation.revelation_type).toBe('personal_value');
        expect(revelation.content).toContain('authenticity');
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/create`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(revelationData);
      expect(req.request.headers.get('Authorization')).toBe('Bearer mock-jwt-token');
      req.flush(mockResponse);
    });

    it('should validate revelation content length', () => {
      const shortContent = 'Too short';
      
      expect(() => {
        service.validateRevelationContent(shortContent);
      }).toThrowError('Revelation content must be at least 50 characters for meaningful sharing');

      const appropriateContent = 'This is a meaningful revelation that shares something deep and personal about my values and experiences in life.';
      expect(() => {
        service.validateRevelationContent(appropriateContent);
      }).not.toThrow();
    });

    it('should prevent duplicate revelations for same day', () => {
      const duplicateRevelation = {
        connection_id: 1,
        day_number: 1,
        revelation_type: 'personal_value',
        content: 'Attempting duplicate revelation for the same day'
      };

      service.createRevelation(
        duplicateRevelation.connection_id,
        duplicateRevelation.day_number,
        duplicateRevelation.revelation_type,
        duplicateRevelation.content
      ).subscribe({
        next: () => fail('Should have failed with duplicate error'),
        error: (error) => {
          expect(error.status).toBe(400);
          expect(error.error.detail).toContain('already submitted');
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/create`);
      req.flush(
        { detail: 'You have already submitted a revelation for day 1' },
        { status: 400, statusText: 'Bad Request' }
      );
    });

    it('should enforce day progression rules', () => {
      const skipAheadRevelation = {
        connection_id: 1,
        day_number: 5,
        revelation_type: 'challenge_overcome',
        content: 'Trying to skip ahead to day 5 without completing previous days'
      };

      service.createRevelation(
        skipAheadRevelation.connection_id,
        skipAheadRevelation.day_number,
        skipAheadRevelation.revelation_type,
        skipAheadRevelation.content
      ).subscribe({
        next: () => fail('Should enforce progression rules'),
        error: (error) => {
          expect(error.status).toBe(400);
          expect(error.error.detail).toContain('must complete previous days');
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/create`);
      req.flush(
        { detail: 'You must complete previous days before revealing day 5' },
        { status: 400, statusText: 'Bad Request' }
      );
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
            reaction_count: 2
          },
          user2_revelation: {
            id: 2,
            connection_id: 1,
            sender_id: 2,
            day_number: 1,
            revelation_type: 'personal_value',
            content: 'Authenticity and growth are my core values',
            created_at: '2025-01-15T14:30:00Z',
            reaction_count: 1
          },
          both_completed: true,
          unlock_date: '2025-01-15T00:00:00Z'
        },
        {
          day_number: 2,
          revelation_type: 'meaningful_experience',
          user1_revelation: {
            id: 3,
            connection_id: 1,
            sender_id: 1,
            day_number: 2,
            revelation_type: 'meaningful_experience',
            content: 'Volunteering at the shelter taught me about compassion',
            created_at: '2025-01-16T09:15:00Z'
          },
          user2_revelation: undefined,
          both_completed: false,
          unlock_date: '2025-01-16T00:00:00Z'
        }
      ];

      service.getRevelationTimeline(connectionId).subscribe(timeline => {
        expect(timeline).toEqual(mockTimeline);
        expect(timeline.length).toBe(2);
        expect(timeline[0].both_completed).toBe(true);
        expect(timeline[1].both_completed).toBe(false);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/timeline/${connectionId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockTimeline);
    });

    it('should handle empty timeline for new connections', () => {
      const connectionId = 999;

      service.getRevelationTimeline(connectionId).subscribe(timeline => {
        expect(timeline).toEqual([]);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/timeline/${connectionId}`);
      req.flush([]);
    });

    it('should calculate revelation progress percentage', () => {
      const timeline: RevelationTimeline[] = [
        { day_number: 1, revelation_type: 'personal_value', both_completed: true, unlock_date: '' },
        { day_number: 2, revelation_type: 'meaningful_experience', both_completed: true, unlock_date: '' },
        { day_number: 3, revelation_type: 'hope_or_dream', both_completed: false, unlock_date: '' }
      ];

      const progress = service.calculateRevelationProgress(timeline);
      expect(progress.completed_days).toBe(2);
      expect(progress.total_days).toBe(7);
      expect(progress.percentage).toBe(Math.round((2 / 7) * 100));
      expect(progress.current_day).toBe(3);
    });
  });

  describe('Revelation Prompts and Guidance', () => {
    it('should provide revelation prompts for each day', () => {
      const day1Prompt = service.getRevelationPrompt(1);
      
      expect(day1Prompt.day).toBe(1);
      expect(day1Prompt.type).toBe('personal_value');
      expect(day1Prompt.title).toContain('Personal Value');
      expect(day1Prompt.prompt).toContain('value most');
      expect(day1Prompt.examples).toBeInstanceOf(Array);
      expect(day1Prompt.examples.length).toBeGreaterThan(0);
      expect(day1Prompt.character_guidance.min_length).toBeGreaterThan(30);
    });

    it('should provide all 7 days of revelation prompts', () => {
      const expectedTypes = [
        'personal_value',
        'meaningful_experience',
        'hope_or_dream',
        'humor_source',
        'challenge_overcome',
        'ideal_connection',
        'photo_reveal'
      ];

      for (let day = 1; day <= 7; day++) {
        const prompt = service.getRevelationPrompt(day);
        expect(prompt.day).toBe(day);
        expect(expectedTypes).toContain(prompt.type);
        expect(prompt.prompt.length).toBeGreaterThan(20);
        expect(prompt.examples.length).toBeGreaterThanOrEqual(2);
      }
    });

    it('should provide contextual writing guidance', () => {
      const guidance = service.getRevelationWritingGuidance('personal_value');
      
      expect(guidance.tone_suggestions).toContain('authentic');
      expect(guidance.content_tips).toBeInstanceOf(Array);
      expect(guidance.avoid_warnings).toContain('generic statements');
      expect(guidance.example_starters.length).toBeGreaterThan(2);
    });

    it('should validate revelation type for day', () => {
      expect(() => {
        service.validateRevelationTypeForDay(1, 'photo_reveal');
      }).toThrowError('Invalid revelation type for day 1');

      expect(() => {
        service.validateRevelationTypeForDay(7, 'photo_reveal');
      }).not.toThrow();

      expect(() => {
        service.validateRevelationTypeForDay(3, 'hope_or_dream');
      }).not.toThrow();
    });
  });

  describe('Revelation Reactions', () => {
    it('should react to a revelation', () => {
      const revelationId = 1;
      const reactionData = {
        reaction_type: 'heart',
        message: 'This really resonates with my own values'
      };

      const mockResponse = {
        revelation_id: revelationId,
        reaction_type: 'heart',
        message: reactionData.message,
        created_at: new Date().toISOString()
      };

      service.reactToRevelation(revelationId, reactionData.reaction_type, reactionData.message).subscribe(response => {
        expect(response.reaction_type).toBe('heart');
        expect(response.message).toBe(reactionData.message);
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/${revelationId}/react`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(reactionData);
      req.flush(mockResponse);
    });

    it('should get available reaction types', () => {
      const reactionTypes = service.getAvailableReactionTypes();
      
      expect(reactionTypes).toContain({ type: 'heart', label: 'Heart', emoji: '❤️' });
      expect(reactionTypes).toContain({ type: 'thoughtful', label: 'Thoughtful', emoji: '🤔' });
      expect(reactionTypes).toContain({ type: 'inspiring', label: 'Inspiring', emoji: '✨' });
      expect(reactionTypes.length).toBeGreaterThanOrEqual(5);
    });

    it('should limit reaction message length', () => {
      const longMessage = 'a'.repeat(501); // Over 500 character limit
      
      expect(() => {
        service.validateReactionMessage(longMessage);
      }).toThrowError('Reaction message must be under 500 characters');

      const appropriateMessage = 'This deeply resonates with my own experiences and values.';
      expect(() => {
        service.validateReactionMessage(appropriateMessage);
      }).not.toThrow();
    });
  });

  describe('Revelation Scheduling and Timing', () => {
    it('should check if day is unlocked based on connection start date', () => {
      const connectionStartDate = new Date('2025-01-15T10:00:00Z');
      const currentDate = new Date('2025-01-17T15:30:00Z'); // 2 days later
      
      expect(service.isDayUnlocked(1, connectionStartDate, currentDate)).toBe(true);
      expect(service.isDayUnlocked(2, connectionStartDate, currentDate)).toBe(true);
      expect(service.isDayUnlocked(3, connectionStartDate, currentDate)).toBe(true);
      expect(service.isDayUnlocked(4, connectionStartDate, currentDate)).toBe(false);
    });

    it('should calculate time until next day unlock', () => {
      const connectionStartDate = new Date('2025-01-15T10:00:00Z');
      const currentDate = new Date('2025-01-16T08:00:00Z'); // Day 2, but early
      
      const timeUntilUnlock = service.getTimeUntilDayUnlock(3, connectionStartDate, currentDate);
      
      expect(timeUntilUnlock.hours).toBeGreaterThan(0);
      expect(timeUntilUnlock.totalMinutes).toBeGreaterThan(0);
      expect(timeUntilUnlock.isUnlocked).toBe(false);
    });

    it('should handle timezone considerations for day unlock', () => {
      // User timezone considerations for fair revelation scheduling
      const connectionStart = new Date('2025-01-15T10:00:00Z');
      const userTimezone = 'America/New_York';
      
      const dayStatus = service.getDayStatusWithTimezone(2, connectionStart, userTimezone);
      
      expect(dayStatus.day).toBe(2);
      expect(dayStatus.isUnlocked).toBeDefined();
      expect(dayStatus.unlockTime).toBeDefined();
      expect(dayStatus.userLocalTime).toBeDefined();
    });
  });

  describe('Content Moderation and Safety', () => {
    it('should flag inappropriate content for moderation', () => {
      const inappropriateContent = [
        'Here is my phone number: 555-123-4567',
        'Let\'s meet up tonight at my place',
        'Check out my OnlyFans for more content'
      ];

      inappropriateContent.forEach(content => {
        const moderationResult = service.moderateContent(content);
        expect(moderationResult.needsReview).toBe(true);
        expect(moderationResult.flags.length).toBeGreaterThan(0);
      });
    });

    it('should allow appropriate emotional content', () => {
      const appropriateContent = [
        'Family has always been my anchor through life\'s storms. I believe in showing up for the people you love.',
        'The moment I realized I wanted to help others led me to volunteer work that changed my perspective.',
        'I dream of building a life where I can balance personal growth with meaningful partnerships.'
      ];

      appropriateContent.forEach(content => {
        const moderationResult = service.moderateContent(content);
        expect(moderationResult.needsReview).toBe(false);
        expect(moderationResult.isAppropriate).toBe(true);
      });
    });

    it('should provide content improvement suggestions', () => {
      const genericContent = 'I like movies and food';
      const suggestions = service.getContentImprovementSuggestions(genericContent);
      
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions[0]).toContain('specific');
      expect(suggestions.some(s => s.includes('personal'))).toBe(true);
    });
  });

  describe('Revelation Analytics and Insights', () => {
    it('should analyze revelation emotional depth', () => {
      const deepRevelation = 'Losing my father taught me that every moment matters. I learned to cherish vulnerability and authentic connection because life is too precious to waste on surface-level interactions.';
      
      const analysis = service.analyzeEmotionalDepth(deepRevelation);
      
      expect(analysis.depth_score).toBeGreaterThan(7);
      expect(analysis.authenticity_indicators).toContain('personal experience');
      expect(analysis.emotional_themes).toContain('loss');
      expect(analysis.connection_potential).toBe('high');
    });

    it('should provide revelation quality feedback', () => {
      const revelation = 'I believe in honesty and treating people with respect.';
      const feedback = service.getRevelationQualityFeedback(revelation);
      
      expect(feedback.score).toBeLessThan(8); // Generic statement should score lower
      expect(feedback.suggestions).toContain('Add a personal story');
      expect(feedback.strengths.length).toBeGreaterThan(0);
      expect(feedback.improvements.length).toBeGreaterThan(0);
    });

    it('should track revelation engagement metrics', () => {
      const revelationId = 1;
      
      service.getRevelationEngagement(revelationId).subscribe(engagement => {
        expect(engagement.revelation_id).toBe(revelationId);
        expect(engagement.view_count).toBeDefined();
        expect(engagement.reaction_count).toBeDefined();
        expect(engagement.response_time_hours).toBeDefined();
        expect(engagement.engagement_score).toBeDefined();
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/${revelationId}/engagement`);
      req.flush({
        revelation_id: revelationId,
        view_count: 5,
        reaction_count: 2,
        response_time_hours: 3.5,
        engagement_score: 8.2
      });
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle network errors gracefully', () => {
      service.getRevelationTimeline(1).subscribe({
        next: () => fail('Should have failed with network error'),
        error: (error) => {
          expect(error.message).toContain('network error');
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/timeline/1`);
      req.error(new ErrorEvent('Network error'));
    });

    it('should validate input parameters', () => {
      expect(() => service.createRevelation(-1, 1, 'personal_value', 'content')).toThrowError('Invalid connection ID');
      expect(() => service.createRevelation(1, 0, 'personal_value', 'content')).toThrowError('Invalid day number');
      expect(() => service.createRevelation(1, 8, 'personal_value', 'content')).toThrowError('Day must be between 1 and 7');
      expect(() => service.createRevelation(1, 1, '', 'content')).toThrowError('Revelation type is required');
    });

    it('should handle unauthorized access', () => {
      authServiceSpy.getToken.and.returnValue(null);

      service.getRevelationTimeline(1).subscribe({
        next: () => fail('Should require authentication'),
        error: (error) => {
          expect(error.status).toBe(401);
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/timeline/1`);
      req.flush(
        { detail: 'Authentication required' },
        { status: 401, statusText: 'Unauthorized' }
      );
    });

    it('should handle connection not found errors', () => {
      service.getRevelationTimeline(999).subscribe({
        next: () => fail('Should handle connection not found'),
        error: (error) => {
          expect(error.status).toBe(404);
        }
      });

      const req = httpMock.expectOne(`${mockApiUrl}/revelations/timeline/999`);
      req.flush(
        { detail: 'Connection not found' },
        { status: 404, statusText: 'Not Found' }
      );
    });
  });

  describe('Performance and Caching', () => {
    it('should cache revelation prompts for performance', () => {
      // First call
      const prompt1 = service.getRevelationPrompt(1);
      // Second call should return cached version
      const prompt2 = service.getRevelationPrompt(1);
      
      expect(prompt1).toBe(prompt2); // Should be same object reference (cached)
    });

    it('should debounce content moderation calls', (done) => {
      const content = 'Test content for moderation';
      
      // Make multiple rapid calls
      service.moderateContent(content);
      service.moderateContent(content);
      service.moderateContent(content);
      
      setTimeout(() => {
        // Should only process once due to debouncing
        expect(service['moderationCallCount']).toBe(1);
        done();
      }, 300);
    });
  });
});