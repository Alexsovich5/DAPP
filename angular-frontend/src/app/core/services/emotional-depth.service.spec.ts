import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import {
  EmotionalDepthService,
  EmotionalDepthAnalysis,
  DepthCompatibility,
  EmotionalDepthSummary
} from './emotional-depth.service';
import { environment } from '@environments/environment';

describe('EmotionalDepthService', () => {
  let service: EmotionalDepthService;
  let httpMock: HttpTestingController;
  const baseUrl = `${environment.apiUrl}/emotional-depth`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [EmotionalDepthService]
    });

    service = TestBed.inject(EmotionalDepthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('State Management', () => {
    it('should initialize with null current user depth', (done) => {
      service.currentUserDepth$.subscribe(depth => {
        expect(depth).toBeNull();
        done();
      });
    });

    it('should initialize with loading false', (done) => {
      service.analysisLoading$.subscribe(loading => {
        expect(loading).toBe(false);
        done();
      });
    });
  });

  describe('analyzeUserEmotionalDepth()', () => {
    it('should analyze emotional depth for a user', (done) => {
      const userId = 123;
      const mockAnalysis: EmotionalDepthAnalysis = {
        user_id: userId,
        emotional_depth: {
          overall_depth: 75.5,
          depth_level: 'deep',
          emotional_vocabulary_count: 120,
          vulnerability_score: 80,
          authenticity_score: 85,
          empathy_indicators: 15,
          growth_mindset: 90,
          emotional_availability: 75,
          attachment_security: 70,
          communication_depth: 80,
          confidence: 85,
          text_quality: 'high',
          response_richness: 88
        },
        insights: {
          vulnerability_types: ['emotional openness', 'past experiences'],
          depth_indicators: ['reflective language', 'emotional awareness'],
          maturity_signals: ['emotional regulation', 'empathy'],
          authenticity_markers: ['genuine expression', 'consistency']
        },
        analysis_metadata: {
          timestamp: '2025-10-18T00:00:00Z',
          algorithm_version: '2.0.1',
          confidence_level: 85
        }
      };

      service.analyzeUserEmotionalDepth(userId).subscribe(analysis => {
        expect(analysis).toEqual(mockAnalysis);
        expect(analysis.user_id).toBe(userId);
        expect(analysis.emotional_depth.overall_depth).toBe(75.5);
        done();
      });

      const req = httpMock.expectOne(`${baseUrl}/analyze/${userId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockAnalysis);
    });

    it('should set loading state during analysis', () => {
      const userId = 123;
      let loadingStates: boolean[] = [];

      service.analysisLoading$.subscribe(loading => {
        loadingStates.push(loading);
      });

      service.analyzeUserEmotionalDepth(userId).subscribe();

      expect(loadingStates).toContain(true);

      const req = httpMock.expectOne(`${baseUrl}/analyze/${userId}`);
      req.flush({} as EmotionalDepthAnalysis);

      expect(loadingStates[loadingStates.length - 1]).toBe(false);
    });

    it('should reset loading state on error', (done) => {
      const userId = 123;

      service.analyzeUserEmotionalDepth(userId).subscribe({
        error: () => {
          service.analysisLoading$.subscribe(loading => {
            expect(loading).toBe(false);
            done();
          });
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/analyze/${userId}`);
      req.error(new ErrorEvent('Network error'));
    });
  });

  describe('analyzeDepthCompatibility()', () => {
    it('should analyze compatibility between two users', (done) => {
      const user1Id = 123;
      const user2Id = 456;
      const mockCompatibility: DepthCompatibility = {
        user1_id: user1Id,
        user2_id: user2Id,
        depth_compatibility: {
          overall_compatibility: 85,
          depth_harmony: 88,
          vulnerability_match: 82,
          growth_alignment: 90
        },
        individual_depths: {
          user1: { overall_depth: 75, depth_level: 'deep' },
          user2: { overall_depth: 80, depth_level: 'deep' }
        },
        relationship_insights: {
          connection_potential: 'Strong potential for deep connection',
          recommended_approach: 'Open and vulnerable communication',
          depth_growth_timeline: '3-6 months to deep bond'
        },
        analysis_metadata: {
          timestamp: '2025-10-18T00:00:00Z',
          algorithm_version: '2.0.1'
        }
      };

      service.analyzeDepthCompatibility(user1Id, user2Id).subscribe(compatibility => {
        expect(compatibility).toEqual(mockCompatibility);
        expect(compatibility.depth_compatibility.overall_compatibility).toBe(85);
        done();
      });

      const req = httpMock.expectOne(`${baseUrl}/compatibility/${user1Id}/${user2Id}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockCompatibility);
    });

    it('should set loading state during compatibility analysis', () => {
      let loadingStates: boolean[] = [];

      service.analysisLoading$.subscribe(loading => {
        loadingStates.push(loading);
      });

      service.analyzeDepthCompatibility(1, 2).subscribe();

      expect(loadingStates).toContain(true);

      const req = httpMock.expectOne(`${baseUrl}/compatibility/1/2`);
      req.flush({} as DepthCompatibility);

      expect(loadingStates[loadingStates.length - 1]).toBe(false);
    });

    it('should reset loading state on compatibility error', (done) => {
      service.analyzeDepthCompatibility(1, 2).subscribe({
        error: () => {
          service.analysisLoading$.subscribe(loading => {
            expect(loading).toBe(false);
            done();
          });
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/compatibility/1/2`);
      req.error(new ErrorEvent('Network error'));
    });
  });

  describe('getMyEmotionalDepthSummary()', () => {
    it('should get current user emotional depth summary', (done) => {
      const mockSummary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 78,
          depth_level: 'deep',
          depth_level_description: 'High emotional sophistication',
          key_strengths: ['Emotional awareness', 'Empathy'],
          growth_areas: ['Vulnerability expression'],
          emotional_vocabulary_richness: 'well-developed',
          vulnerability_comfort: 'moderately comfortable',
          authenticity_level: 'high'
        },
        personal_insights: [
          'You show strong emotional intelligence',
          'Your self-awareness is well-developed'
        ],
        recommendations: [
          'Continue practicing vulnerability',
          'Explore deeper emotional expression'
        ],
        profile_completeness: {
          confidence: 85,
          text_quality: 'high',
          suggestions: ['Share more personal experiences']
        }
      };

      service.getMyEmotionalDepthSummary().subscribe(summary => {
        expect(summary).toEqual(mockSummary);
        expect(summary.emotional_depth_summary.overall_depth).toBe(78);
        done();
      });

      const req = httpMock.expectOne(`${baseUrl}/summary/me`);
      expect(req.request.method).toBe('GET');
      req.flush(mockSummary);
    });

    it('should update currentUserDepth subject on success', (done) => {
      const mockSummary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 78,
          depth_level: 'deep',
          depth_level_description: 'High emotional sophistication',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'well-developed',
          vulnerability_comfort: 'moderately comfortable',
          authenticity_level: 'high'
        },
        personal_insights: [],
        recommendations: [],
        profile_completeness: {
          confidence: 85,
          text_quality: 'high',
          suggestions: []
        }
      };

      service.getMyEmotionalDepthSummary().subscribe(() => {
        service.currentUserDepth$.subscribe(depth => {
          expect(depth).toEqual(mockSummary);
          done();
        });
      });

      const req = httpMock.expectOne(`${baseUrl}/summary/me`);
      req.flush(mockSummary);
    });

    it('should set loading state during summary fetch', () => {
      let loadingStates: boolean[] = [];

      service.analysisLoading$.subscribe(loading => {
        loadingStates.push(loading);
      });

      service.getMyEmotionalDepthSummary().subscribe();

      expect(loadingStates).toContain(true);

      const req = httpMock.expectOne(`${baseUrl}/summary/me`);
      req.flush({} as EmotionalDepthSummary);

      expect(loadingStates[loadingStates.length - 1]).toBe(false);
    });
  });

  describe('getDepthLevelColor()', () => {
    it('should return correct color for surface level', () => {
      expect(service.getDepthLevelColor('surface')).toBe('#94a3b8');
    });

    it('should return correct color for emerging level', () => {
      expect(service.getDepthLevelColor('emerging')).toBe('#60a5fa');
    });

    it('should return correct color for moderate level', () => {
      expect(service.getDepthLevelColor('moderate')).toBe('#34d399');
    });

    it('should return correct color for deep level', () => {
      expect(service.getDepthLevelColor('deep')).toBe('#a78bfa');
    });

    it('should return correct color for profound level', () => {
      expect(service.getDepthLevelColor('profound')).toBe('#f59e0b');
    });

    it('should handle case-insensitive input', () => {
      expect(service.getDepthLevelColor('DEEP')).toBe('#a78bfa');
      expect(service.getDepthLevelColor('DeEp')).toBe('#a78bfa');
    });

    it('should return default color for unknown level', () => {
      expect(service.getDepthLevelColor('unknown')).toBe('#34d399');
    });
  });

  describe('getDepthLevelDescription()', () => {
    it('should return correct description for surface level', () => {
      expect(service.getDepthLevelDescription('surface')).toBe('Developing emotional awareness');
    });

    it('should return correct description for emerging level', () => {
      expect(service.getDepthLevelDescription('emerging')).toBe('Growing emotional intelligence');
    });

    it('should return correct description for moderate level', () => {
      expect(service.getDepthLevelDescription('moderate')).toBe('Good emotional depth');
    });

    it('should return correct description for deep level', () => {
      expect(service.getDepthLevelDescription('deep')).toBe('High emotional sophistication');
    });

    it('should return correct description for profound level', () => {
      expect(service.getDepthLevelDescription('profound')).toBe('Exceptional emotional wisdom');
    });

    it('should handle case-insensitive input', () => {
      expect(service.getDepthLevelDescription('PROFOUND')).toBe('Exceptional emotional wisdom');
    });

    it('should return default description for unknown level', () => {
      expect(service.getDepthLevelDescription('unknown')).toBe('Good emotional depth');
    });
  });

  describe('getCompatibilityDescription()', () => {
    it('should return exceptional for score >= 90', () => {
      expect(service.getCompatibilityDescription(95)).toBe('Exceptional emotional compatibility');
      expect(service.getCompatibilityDescription(90)).toBe('Exceptional emotional compatibility');
    });

    it('should return strong for score >= 80', () => {
      expect(service.getCompatibilityDescription(85)).toBe('Strong emotional connection potential');
      expect(service.getCompatibilityDescription(80)).toBe('Strong emotional connection potential');
    });

    it('should return good for score >= 70', () => {
      expect(service.getCompatibilityDescription(75)).toBe('Good emotional compatibility');
      expect(service.getCompatibilityDescription(70)).toBe('Good emotional compatibility');
    });

    it('should return moderate for score >= 60', () => {
      expect(service.getCompatibilityDescription(65)).toBe('Moderate emotional alignment');
      expect(service.getCompatibilityDescription(60)).toBe('Moderate emotional alignment');
    });

    it('should return limited for score < 60', () => {
      expect(service.getCompatibilityDescription(55)).toBe('Limited emotional compatibility');
      expect(service.getCompatibilityDescription(30)).toBe('Limited emotional compatibility');
    });
  });

  describe('getCompatibilityColor()', () => {
    it('should return emerald for score >= 90', () => {
      expect(service.getCompatibilityColor(95)).toBe('#10b981');
      expect(service.getCompatibilityColor(90)).toBe('#10b981');
    });

    it('should return blue for score >= 80', () => {
      expect(service.getCompatibilityColor(85)).toBe('#3b82f6');
      expect(service.getCompatibilityColor(80)).toBe('#3b82f6');
    });

    it('should return violet for score >= 70', () => {
      expect(service.getCompatibilityColor(75)).toBe('#8b5cf6');
      expect(service.getCompatibilityColor(70)).toBe('#8b5cf6');
    });

    it('should return amber for score >= 60', () => {
      expect(service.getCompatibilityColor(65)).toBe('#f59e0b');
      expect(service.getCompatibilityColor(60)).toBe('#f59e0b');
    });

    it('should return red for score < 60', () => {
      expect(service.getCompatibilityColor(55)).toBe('#ef4444');
      expect(service.getCompatibilityColor(30)).toBe('#ef4444');
    });
  });

  describe('formatScore()', () => {
    it('should format score as percentage', () => {
      expect(service.formatScore(85)).toBe('85%');
      expect(service.formatScore(70.5)).toBe('71%');
      expect(service.formatScore(90.2)).toBe('90%');
    });

    it('should round decimal scores', () => {
      expect(service.formatScore(75.4)).toBe('75%');
      expect(service.formatScore(75.6)).toBe('76%');
    });

    it('should handle edge cases', () => {
      expect(service.formatScore(0)).toBe('0%');
      expect(service.formatScore(100)).toBe('100%');
    });
  });

  describe('getVocabularyIcon()', () => {
    it('should return correct icon for limited vocabulary', () => {
      expect(service.getVocabularyIcon('limited')).toBe('sentiment_dissatisfied');
    });

    it('should return correct icon for developing vocabulary', () => {
      expect(service.getVocabularyIcon('developing')).toBe('sentiment_neutral');
    });

    it('should return correct icon for well-developed vocabulary', () => {
      expect(service.getVocabularyIcon('well-developed')).toBe('sentiment_satisfied');
    });

    it('should return correct icon for rich and sophisticated vocabulary', () => {
      expect(service.getVocabularyIcon('rich and sophisticated')).toBe('sentiment_very_satisfied');
    });

    it('should handle case-insensitive input', () => {
      expect(service.getVocabularyIcon('LIMITED')).toBe('sentiment_dissatisfied');
    });

    it('should return default icon for unknown richness', () => {
      expect(service.getVocabularyIcon('unknown')).toBe('sentiment_neutral');
    });
  });

  describe('getVulnerabilityIcon()', () => {
    it('should return favorite for very comfortable', () => {
      expect(service.getVulnerabilityIcon('very comfortable')).toBe('favorite');
      expect(service.getVulnerabilityIcon('very comfortable with vulnerability')).toBe('favorite');
    });

    it('should return thumb_up for moderately comfortable', () => {
      expect(service.getVulnerabilityIcon('moderately comfortable')).toBe('thumb_up');
      expect(service.getVulnerabilityIcon('moderately comfortable sharing')).toBe('thumb_up');
    });

    it('should return hourglass_empty for developing', () => {
      expect(service.getVulnerabilityIcon('developing comfort')).toBe('hourglass_empty');
      expect(service.getVulnerabilityIcon('still developing')).toBe('hourglass_empty');
    });

    it('should return lock for other values', () => {
      expect(service.getVulnerabilityIcon('uncomfortable')).toBe('lock');
      expect(service.getVulnerabilityIcon('unknown')).toBe('lock');
    });
  });

  describe('refreshCurrentUserDepth()', () => {
    it('should refresh current user depth data', () => {
      spyOn(console, 'log');

      const mockSummary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 75,
          depth_level: 'deep',
          depth_level_description: 'High emotional sophistication',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'well-developed',
          vulnerability_comfort: 'moderately comfortable',
          authenticity_level: 'high'
        },
        personal_insights: [],
        recommendations: [],
        profile_completeness: {
          confidence: 80,
          text_quality: 'high',
          suggestions: []
        }
      };

      service.refreshCurrentUserDepth();

      const req = httpMock.expectOne(`${baseUrl}/summary/me`);
      req.flush(mockSummary);

      expect(console.log).toHaveBeenCalledWith('Emotional depth summary refreshed:', mockSummary);
    });

    it('should log error on refresh failure', () => {
      spyOn(console, 'error');

      service.refreshCurrentUserDepth();

      const req = httpMock.expectOne(`${baseUrl}/summary/me`);
      const errorEvent = new ErrorEvent('Network error');
      req.error(errorEvent);

      expect(console.error).toHaveBeenCalledWith('Error refreshing emotional depth:', jasmine.any(Object));
    });
  });

  describe('clearCurrentUserDepth()', () => {
    it('should clear current user depth data', (done) => {
      service.clearCurrentUserDepth();

      service.currentUserDepth$.subscribe(depth => {
        expect(depth).toBeNull();
        done();
      });
    });
  });

  describe('hasSufficientDepthData()', () => {
    it('should return true when confidence >= 50 and quality is sufficient', () => {
      const summary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 70,
          depth_level: 'moderate',
          depth_level_description: 'Good emotional depth',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'well-developed',
          vulnerability_comfort: 'moderately comfortable',
          authenticity_level: 'medium'
        },
        personal_insights: [],
        recommendations: [],
        profile_completeness: {
          confidence: 50,
          text_quality: 'high',
          suggestions: []
        }
      };

      expect(service.hasSufficientDepthData(summary)).toBe(true);
    });

    it('should return false when confidence < 50', () => {
      const summary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 70,
          depth_level: 'moderate',
          depth_level_description: 'Good emotional depth',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'well-developed',
          vulnerability_comfort: 'moderately comfortable',
          authenticity_level: 'medium'
        },
        personal_insights: [],
        recommendations: [],
        profile_completeness: {
          confidence: 49,
          text_quality: 'high',
          suggestions: []
        }
      };

      expect(service.hasSufficientDepthData(summary)).toBe(false);
    });

    it('should return false when text quality is insufficient', () => {
      const summary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 70,
          depth_level: 'moderate',
          depth_level_description: 'Good emotional depth',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'limited',
          vulnerability_comfort: 'developing',
          authenticity_level: 'low'
        },
        personal_insights: [],
        recommendations: [],
        profile_completeness: {
          confidence: 60,
          text_quality: 'insufficient',
          suggestions: []
        }
      };

      expect(service.hasSufficientDepthData(summary)).toBe(false);
    });
  });

  describe('getImprovementRecommendations()', () => {
    it('should include recommendation for low confidence', () => {
      const summary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 50,
          depth_level: 'emerging',
          depth_level_description: 'Growing emotional intelligence',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'well-developed',
          vulnerability_comfort: 'moderately comfortable',
          authenticity_level: 'medium'
        },
        personal_insights: [],
        recommendations: ['Existing recommendation'],
        profile_completeness: {
          confidence: 55,
          text_quality: 'medium',
          suggestions: []
        }
      };

      const recommendations = service.getImprovementRecommendations(summary);
      expect(recommendations).toContain('Complete more detailed profile responses to improve analysis accuracy');
    });

    it('should include recommendation for limited text quality', () => {
      const summary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 60,
          depth_level: 'moderate',
          depth_level_description: 'Good emotional depth',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'well-developed',
          vulnerability_comfort: 'moderately comfortable',
          authenticity_level: 'medium'
        },
        personal_insights: [],
        recommendations: [],
        profile_completeness: {
          confidence: 70,
          text_quality: 'limited',
          suggestions: []
        }
      };

      const recommendations = service.getImprovementRecommendations(summary);
      expect(recommendations).toContain('Share more personal experiences and feelings in your responses');
    });

    it('should include recommendation for limited vocabulary', () => {
      const summary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 60,
          depth_level: 'moderate',
          depth_level_description: 'Good emotional depth',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'limited',
          vulnerability_comfort: 'moderately comfortable',
          authenticity_level: 'medium'
        },
        personal_insights: [],
        recommendations: [],
        profile_completeness: {
          confidence: 70,
          text_quality: 'high',
          suggestions: []
        }
      };

      const recommendations = service.getImprovementRecommendations(summary);
      expect(recommendations).toContain('Explore and use more diverse emotional words to express your feelings');
    });

    it('should include all existing recommendations', () => {
      const summary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 80,
          depth_level: 'deep',
          depth_level_description: 'High emotional sophistication',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'well-developed',
          vulnerability_comfort: 'very comfortable',
          authenticity_level: 'high'
        },
        personal_insights: [],
        recommendations: ['Recommendation 1', 'Recommendation 2'],
        profile_completeness: {
          confidence: 85,
          text_quality: 'high',
          suggestions: []
        }
      };

      const recommendations = service.getImprovementRecommendations(summary);
      expect(recommendations).toContain('Recommendation 1');
      expect(recommendations).toContain('Recommendation 2');
    });

    it('should combine generated and existing recommendations', () => {
      const summary: EmotionalDepthSummary = {
        emotional_depth_summary: {
          overall_depth: 50,
          depth_level: 'emerging',
          depth_level_description: 'Growing emotional intelligence',
          key_strengths: [],
          growth_areas: [],
          emotional_vocabulary_richness: 'limited',
          vulnerability_comfort: 'developing',
          authenticity_level: 'medium'
        },
        personal_insights: [],
        recommendations: ['Existing recommendation'],
        profile_completeness: {
          confidence: 55,
          text_quality: 'limited',
          suggestions: []
        }
      };

      const recommendations = service.getImprovementRecommendations(summary);
      expect(recommendations.length).toBeGreaterThan(1);
      expect(recommendations).toContain('Existing recommendation');
      expect(recommendations).toContain('Complete more detailed profile responses to improve analysis accuracy');
      expect(recommendations).toContain('Share more personal experiences and feelings in your responses');
      expect(recommendations).toContain('Explore and use more diverse emotional words to express your feelings');
    });
  });

  describe('Edge cases', () => {
    it('should handle very high scores', () => {
      expect(service.formatScore(100)).toBe('100%');
      expect(service.getCompatibilityDescription(100)).toBe('Exceptional emotional compatibility');
      expect(service.getCompatibilityColor(100)).toBe('#10b981');
    });

    it('should handle very low scores', () => {
      expect(service.formatScore(0)).toBe('0%');
      expect(service.getCompatibilityDescription(0)).toBe('Limited emotional compatibility');
      expect(service.getCompatibilityColor(0)).toBe('#ef4444');
    });

    it('should handle empty strings in icon methods', () => {
      expect(service.getVocabularyIcon('')).toBe('sentiment_neutral');
      expect(service.getVulnerabilityIcon('')).toBe('lock');
    });
  });
});
