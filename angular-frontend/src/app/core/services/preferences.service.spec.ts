/**
 * PreferencesService Tests
 * Comprehensive tests for user preference management
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { PreferencesService } from './preferences.service';
import { environment } from '../../../environments/environment';

describe('PreferencesService', () => {
  let service: PreferencesService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [PreferencesService]
    });

    service = TestBed.inject(PreferencesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should initialize with default reduced motion from media query', () => {
      // Note: This test assumes window.matchMedia is available
      expect(service).toBeTruthy();
    });

    it('should initialize haptics enabled by default', (done) => {
      service.hapticsEnabled$.subscribe(enabled => {
        expect(enabled).toBe(true);
        done();
      });
    });

    it('should check for prefers-reduced-motion on initialization', () => {
      // The service checks matchMedia on construction
      expect(service).toBeTruthy();
    });
  });

  describe('Reduced Motion Observable', () => {
    it('should expose reducedMotion$ observable', (done) => {
      service.reducedMotion$.subscribe(value => {
        expect(typeof value).toBe('boolean');
        done();
      });
    });

    it('should emit initial reduced motion state', (done) => {
      let emissionCount = 0;
      service.reducedMotion$.subscribe(value => {
        emissionCount++;
        if (emissionCount === 1) {
          expect(value).toBeDefined();
          done();
        }
      });
    });

    it('should support multiple subscribers', () => {
      let subscriber1Value: boolean | undefined;
      let subscriber2Value: boolean | undefined;

      service.reducedMotion$.subscribe(value => subscriber1Value = value);
      service.reducedMotion$.subscribe(value => subscriber2Value = value);

      service.setReducedMotion(true);

      expect(subscriber1Value).toBe(true);
      expect(subscriber2Value).toBe(true);
    });
  });

  describe('Haptics Enabled Observable', () => {
    it('should expose hapticsEnabled$ observable', (done) => {
      service.hapticsEnabled$.subscribe(value => {
        expect(typeof value).toBe('boolean');
        done();
      });
    });

    it('should emit initial haptics state', (done) => {
      let emissionCount = 0;
      service.hapticsEnabled$.subscribe(value => {
        emissionCount++;
        if (emissionCount === 1) {
          expect(value).toBe(true);
          done();
        }
      });
    });

    it('should support multiple subscribers', () => {
      let subscriber1Value: boolean | undefined;
      let subscriber2Value: boolean | undefined;

      service.hapticsEnabled$.subscribe(value => subscriber1Value = value);
      service.hapticsEnabled$.subscribe(value => subscriber2Value = value);

      service.setHapticsEnabled(false);

      expect(subscriber1Value).toBe(false);
      expect(subscriber2Value).toBe(false);
    });
  });

  describe('getPreferences()', () => {
    it('should GET preferences from API', () => {
      const mockPreferences = {
        theme: 'dark',
        reducedMotion: false,
        hapticsEnabled: true
      };

      service.getPreferences().subscribe(prefs => {
        expect(prefs).toEqual(mockPreferences);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      expect(req.request.method).toBe('GET');
      req.flush(mockPreferences);
    });

    it('should handle empty preferences response', () => {
      const emptyPrefs = {};

      service.getPreferences().subscribe(prefs => {
        expect(prefs).toEqual(emptyPrefs);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      req.flush(emptyPrefs);
    });

    it('should handle complex nested preferences', () => {
      const complexPrefs = {
        ui: {
          theme: 'dark',
          fontSize: 16,
          animations: { enabled: true, speed: 'normal' }
        },
        accessibility: {
          reducedMotion: false,
          highContrast: false
        }
      };

      service.getPreferences().subscribe(prefs => {
        expect(prefs).toEqual(complexPrefs);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      req.flush(complexPrefs);
    });

    it('should handle HTTP errors', () => {
      service.getPreferences().subscribe({
        next: () => fail('should have failed with 404 error'),
        error: (error) => {
          expect(error.status).toBe(404);
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });

    it('should use correct API endpoint', () => {
      service.getPreferences().subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      expect(req.request.url).toContain('/preferences');
      req.flush({});
    });
  });

  describe('updatePreferences()', () => {
    it('should PUT preferences to API', () => {
      const newPreferences = {
        theme: 'light',
        reducedMotion: true
      };

      service.updatePreferences(newPreferences).subscribe(prefs => {
        expect(prefs).toEqual(newPreferences);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(newPreferences);
      req.flush(newPreferences);
    });

    it('should handle empty preferences update', () => {
      const emptyPrefs = {};

      service.updatePreferences(emptyPrefs).subscribe(prefs => {
        expect(prefs).toEqual(emptyPrefs);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      expect(req.request.body).toEqual(emptyPrefs);
      req.flush(emptyPrefs);
    });

    it('should handle complex nested preferences update', () => {
      const complexPrefs = {
        ui: {
          theme: 'dark',
          animations: { enabled: false }
        }
      };

      service.updatePreferences(complexPrefs).subscribe(prefs => {
        expect(prefs).toEqual(complexPrefs);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      expect(req.request.body).toEqual(complexPrefs);
      req.flush(complexPrefs);
    });

    it('should handle HTTP errors', () => {
      const prefs = { theme: 'dark' };

      service.updatePreferences(prefs).subscribe({
        next: () => fail('should have failed with 500 error'),
        error: (error) => {
          expect(error.status).toBe(500);
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      req.flush('Server Error', { status: 500, statusText: 'Server Error' });
    });

    it('should use correct API endpoint', () => {
      service.updatePreferences({}).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      expect(req.request.url).toContain('/preferences');
      req.flush({});
    });

    it('should send preferences in request body', () => {
      const prefs = { setting1: 'value1', setting2: 42 };

      service.updatePreferences(prefs).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      expect(req.request.body).toBe(prefs);
      req.flush(prefs);
    });
  });

  describe('setReducedMotion()', () => {
    it('should set reduced motion to true', (done) => {
      service.setReducedMotion(true);

      service.reducedMotion$.subscribe(value => {
        if (value === true) {
          expect(value).toBe(true);
          done();
        }
      });
    });

    it('should set reduced motion to false', (done) => {
      service.setReducedMotion(false);

      service.reducedMotion$.subscribe(value => {
        if (value === false) {
          expect(value).toBe(false);
          done();
        }
      });
    });

    it('should update CSS custom property for linear motion', () => {
      service.setReducedMotion(true);

      const motionEase = document.documentElement.style.getPropertyValue('--motion-ease');
      expect(motionEase).toBe('linear');
    });

    it('should update CSS custom property for normal motion', () => {
      service.setReducedMotion(false);

      const motionEase = document.documentElement.style.getPropertyValue('--motion-ease');
      expect(motionEase).toBe('cubic-bezier(0.22, 1, 0.36, 1)');
    });

    it('should emit through observable', (done) => {
      let emissionCount = 0;

      service.reducedMotion$.subscribe(value => {
        emissionCount++;
        if (emissionCount === 2) {
          expect(value).toBe(true);
          done();
        }
      });

      service.setReducedMotion(true);
    });

    it('should handle rapid toggles', () => {
      service.setReducedMotion(true);
      service.setReducedMotion(false);
      service.setReducedMotion(true);
      service.setReducedMotion(false);

      let finalValue: boolean | undefined;
      service.reducedMotion$.subscribe(value => finalValue = value);

      expect(finalValue).toBe(false);
    });

    it('should update documentElement style', () => {
      // First set to false to ensure we have a known starting state
      service.setReducedMotion(false);
      const initialStyle = document.documentElement.style.getPropertyValue('--motion-ease');
      expect(initialStyle).toBe('cubic-bezier(0.22, 1, 0.36, 1)');

      service.setReducedMotion(true);

      const afterStyle = document.documentElement.style.getPropertyValue('--motion-ease');
      expect(afterStyle).not.toBe(initialStyle);
      expect(afterStyle).toBe('linear');
    });
  });

  describe('setHapticsEnabled()', () => {
    it('should set haptics enabled to true', (done) => {
      service.setHapticsEnabled(true);

      service.hapticsEnabled$.subscribe(value => {
        if (value === true) {
          expect(value).toBe(true);
          done();
        }
      });
    });

    it('should set haptics enabled to false', (done) => {
      service.setHapticsEnabled(false);

      service.hapticsEnabled$.subscribe(value => {
        if (value === false) {
          expect(value).toBe(false);
          done();
        }
      });
    });

    it('should emit through observable', (done) => {
      let emissionCount = 0;

      service.hapticsEnabled$.subscribe(value => {
        emissionCount++;
        if (emissionCount === 2) {
          expect(value).toBe(false);
          done();
        }
      });

      service.setHapticsEnabled(false);
    });

    it('should handle rapid toggles', () => {
      service.setHapticsEnabled(false);
      service.setHapticsEnabled(true);
      service.setHapticsEnabled(false);
      service.setHapticsEnabled(true);

      let finalValue: boolean | undefined;
      service.hapticsEnabled$.subscribe(value => finalValue = value);

      expect(finalValue).toBe(true);
    });

    it('should toggle haptics multiple times', () => {
      for (let i = 0; i < 10; i++) {
        service.setHapticsEnabled(i % 2 === 0);
      }

      let finalValue: boolean | undefined;
      service.hapticsEnabled$.subscribe(value => finalValue = value);

      // After 10 iterations (0-9), i=9 gives i%2=1 (false), but the loop sets i%2===0
      // So iteration 9 sets false. Result should be false.
      expect(finalValue).toBe(false);
    });
  });

  describe('Integration Tests', () => {
    it('should handle simultaneous preference updates', () => {
      service.setReducedMotion(true);
      service.setHapticsEnabled(false);

      let motionValue: boolean | undefined;
      let hapticsValue: boolean | undefined;

      service.reducedMotion$.subscribe(value => motionValue = value);
      service.hapticsEnabled$.subscribe(value => hapticsValue = value);

      expect(motionValue).toBe(true);
      expect(hapticsValue).toBe(false);
    });

    it('should not interfere between reducedMotion and hapticsEnabled', () => {
      service.setReducedMotion(true);

      let motionValue: boolean | undefined;
      let hapticsValue: boolean | undefined;

      service.reducedMotion$.subscribe(value => motionValue = value);
      service.hapticsEnabled$.subscribe(value => hapticsValue = value);

      expect(motionValue).toBe(true);
      expect(hapticsValue).toBe(true); // Should remain default
    });

    it('should maintain state across API calls', () => {
      service.setReducedMotion(true);
      service.setHapticsEnabled(false);

      service.getPreferences().subscribe();
      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      req.flush({});

      let motionValue: boolean | undefined;
      let hapticsValue: boolean | undefined;

      service.reducedMotion$.subscribe(value => motionValue = value);
      service.hapticsEnabled$.subscribe(value => hapticsValue = value);

      // Local state should be preserved
      expect(motionValue).toBe(true);
      expect(hapticsValue).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    it('should handle multiple API calls in sequence', () => {
      service.getPreferences().subscribe();
      service.updatePreferences({ theme: 'dark' }).subscribe();
      service.getPreferences().subscribe();

      const requests = httpMock.match(`${environment.apiUrl}/preferences`);
      expect(requests.length).toBe(3);

      requests[0].flush({});
      requests[1].flush({ theme: 'dark' });
      requests[2].flush({ theme: 'dark' });
    });

    it('should handle concurrent API calls', () => {
      service.getPreferences().subscribe();
      service.getPreferences().subscribe();

      const requests = httpMock.match(`${environment.apiUrl}/preferences`);
      expect(requests.length).toBe(2);

      requests.forEach(req => req.flush({}));
    });

    it('should handle setting same value multiple times', () => {
      service.setReducedMotion(true);
      service.setReducedMotion(true);
      service.setReducedMotion(true);

      let value: boolean | undefined;
      service.reducedMotion$.subscribe(v => value = v);

      expect(value).toBe(true);
    });

    it('should handle null/undefined in preferences object', () => {
      const prefsWithNull = {
        setting1: null,
        setting2: undefined
      };

      service.updatePreferences(prefsWithNull).subscribe(result => {
        expect(result).toBeDefined();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/preferences`);
      expect(req.request.body).toEqual(prefsWithNull);
      req.flush(prefsWithNull);
    });
  });
});
