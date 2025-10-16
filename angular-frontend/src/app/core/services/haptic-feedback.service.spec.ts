/**
 * HapticFeedbackService Tests
 * Comprehensive tests for tactile feedback system
 */

import { TestBed } from '@angular/core/testing';
import { HapticFeedbackService } from './haptic-feedback.service';

describe('HapticFeedbackService', () => {
  let service: HapticFeedbackService;
  let navigatorSpy: jasmine.SpyObj<Navigator>;
  let originalNavigator: Navigator;
  let originalWindow: Window;

  beforeEach(() => {
    // Store original navigator and window for restoration
    originalNavigator = navigator;
    originalWindow = window;

    // Create spy for navigator.vibrate
    navigatorSpy = jasmine.createSpyObj('Navigator', ['vibrate']);
    navigatorSpy.vibrate.and.returnValue(true);

    // Mock navigator with vibrate support
    Object.defineProperty(window, 'navigator', {
      value: {
        ...originalNavigator,
        vibrate: navigatorSpy.vibrate,
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
      },
      configurable: true,
      writable: true
    });

    TestBed.configureTestingModule({
      providers: [HapticFeedbackService]
    });

    service = TestBed.inject(HapticFeedbackService);
  });

  afterEach(() => {
    // Restore original navigator and window
    Object.defineProperty(window, 'navigator', {
      value: originalNavigator,
      configurable: true,
      writable: true
    });
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should detect haptic support on initialization', () => {
      const status = service.getHapticStatus();
      expect(status.supported).toBe(true);
    });

    it('should detect mobile device on initialization', () => {
      const status = service.getHapticStatus();
      expect(status.mobile).toBe(true);
    });

    it('should have haptics enabled by default', () => {
      expect(service.getHapticsEnabled()).toBe(true);
    });
  });

  describe('Haptic Support Detection', () => {
    it('should return haptic status correctly', () => {
      const status = service.getHapticStatus();
      expect(status).toEqual({
        supported: true,
        mobile: true
      });
    });

    it('should announce haptic status for enabled devices', () => {
      const announcement = service.announceHapticStatus();
      expect(announcement).toContain('Haptic feedback enabled');
    });

    it('should detect desktop devices correctly', () => {
      // Create new service with desktop user agent
      Object.defineProperty(window, 'navigator', {
        value: {
          ...originalNavigator,
          vibrate: navigatorSpy.vibrate,
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        configurable: true,
        writable: true
      });

      const desktopService = new HapticFeedbackService();
      const status = desktopService.getHapticStatus();
      expect(status.mobile).toBe(false);
    });
  });

  describe('Basic Haptic Feedback Methods', () => {
    it('should trigger hover feedback with gentle vibration', () => {
      service.triggerHoverFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([20]);
    });

    it('should trigger connection success with pattern', () => {
      service.triggerConnectionSuccess();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50, 50, 150, 50, 50]);
    });

    it('should trigger pass feedback', () => {
      service.triggerPassFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([100]);
    });

    it('should trigger high compatibility feedback', () => {
      service.triggerHighCompatibilityFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([80, 100, 120, 100, 80]);
    });

    it('should trigger filter change feedback', () => {
      service.triggerFilterChangeFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([15]);
    });

    it('should trigger error feedback', () => {
      service.triggerErrorFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([100, 50, 100, 50, 100]);
    });

    it('should trigger loading feedback', () => {
      service.triggerLoadingFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([30]);
    });

    it('should trigger revelation feedback', () => {
      service.triggerRevelationFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50, 30, 80, 30, 120, 30, 80, 30, 50]);
    });

    it('should trigger focus feedback', () => {
      service.triggerFocusFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([10]);
    });

    it('should trigger welcome feedback', () => {
      service.triggerWelcomeFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([100, 50, 100, 50, 200]);
    });

    it('should trigger selection feedback', () => {
      service.triggerSelectionFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50]);
    });

    it('should trigger success feedback', () => {
      service.triggerSuccessFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([100, 50, 100, 50, 150]);
    });
  });

  describe('Compatibility-Based Feedback', () => {
    it('should trigger soulmate pattern for 95%+ compatibility', () => {
      service.triggerCompatibilityFeedback(95);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50, 30, 100, 30, 150, 30, 100, 30, 50]);
    });

    it('should trigger high compatibility pattern for 80-89% compatibility', () => {
      service.triggerCompatibilityFeedback(85);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([80, 100, 120, 100, 80]);
    });

    it('should trigger medium compatibility pattern for 60-79% compatibility', () => {
      service.triggerCompatibilityFeedback(70);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([60, 40, 80]);
    });

    it('should trigger low compatibility pattern for <60% compatibility', () => {
      service.triggerCompatibilityFeedback(50);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([40]);
    });
  });

  describe('Advanced Haptic Patterns', () => {
    it('should trigger breathing feedback', () => {
      service.triggerBreathingFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([80, 100, 120, 100, 80]);
    });

    it('should trigger celebration burst', () => {
      service.triggerCelebrationBurst();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50, 20, 70, 20, 90, 20, 110, 20, 90, 20, 70, 20, 50]);
    });

    it('should trigger light impact feedback', () => {
      service.triggerImpactFeedback('light');
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([15]);
    });

    it('should trigger medium impact feedback', () => {
      service.triggerImpactFeedback('medium');
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([30]);
    });

    it('should trigger heavy impact feedback', () => {
      service.triggerImpactFeedback('heavy');
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50]);
    });

    it('should trigger custom pattern', () => {
      const customPattern = [10, 20, 30, 40, 50];
      service.triggerCustomPattern(customPattern);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith(customPattern);
    });
  });

  describe('Match Celebration Patterns', () => {
    it('should trigger soulmate celebration for 95%+ matches', (done) => {
      navigatorSpy.vibrate.calls.reset();
      service.triggerMatchCelebration(96);

      // Wait for all setTimeout callbacks
      setTimeout(() => {
        expect(navigatorSpy.vibrate).toHaveBeenCalledTimes(4);
        done();
      }, 1300);
    });

    it('should trigger exceptional match celebration for 85-94% matches', (done) => {
      service.triggerMatchCelebration(90);

      setTimeout(() => {
        expect(navigatorSpy.vibrate).toHaveBeenCalledTimes(3);
        done();
      }, 900);
    });

    it('should trigger good match celebration for 70-84% matches', (done) => {
      service.triggerMatchCelebration(75);

      setTimeout(() => {
        expect(navigatorSpy.vibrate).toHaveBeenCalledTimes(2);
        done();
      }, 400);
    });

    it('should trigger standard match celebration for <70% matches', () => {
      service.triggerMatchCelebration(65);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([60, 30, 80, 30, 100]);
    });
  });

  describe('Special Event Celebrations', () => {
    it('should trigger photo reveal celebration', (done) => {
      service.triggerPhotoRevealCelebration();

      setTimeout(() => {
        expect(navigatorSpy.vibrate).toHaveBeenCalledTimes(3);
        done();
      }, 600);
    });

    it('should trigger first message celebration', () => {
      service.triggerFirstMessageCelebration();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([80, 40, 100, 40, 120, 40, 100, 40, 80]);
    });

    it('should trigger mutual interest celebration', () => {
      service.triggerMutualInterestCelebration();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([60, 20, 80, 20, 100, 20, 120, 20, 100, 20, 80]);
    });

    it('should trigger revelation step celebration for day 1', () => {
      service.triggerRevelationStepCelebration(1);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50, 25]);
    });

    it('should trigger revelation step celebration for day 7', () => {
      service.triggerRevelationStepCelebration(7);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50, 25, 60, 25, 70, 25, 80, 25, 90, 25, 100, 25, 110, 25]);
    });

    it('should trigger anniversary celebration', (done) => {
      service.triggerAnniversaryCelebration();

      setTimeout(() => {
        expect(navigatorSpy.vibrate).toHaveBeenCalledTimes(3);
        done();
      }, 700);
    });
  });

  describe('Interactive Feedback', () => {
    it('should trigger elastic tension feedback with 0 tension', () => {
      service.triggerElasticTensionFeedback(0);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([10]);
    });

    it('should trigger elastic tension feedback with 0.5 tension', () => {
      service.triggerElasticTensionFeedback(0.5);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([30]);
    });

    it('should trigger elastic tension feedback with 1.0 tension', () => {
      service.triggerElasticTensionFeedback(1.0);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50]);
    });

    it('should trigger low soul energy feedback', () => {
      service.triggerSoulEnergyFeedback('low');
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([30, 50, 30]);
    });

    it('should trigger medium soul energy feedback', () => {
      service.triggerSoulEnergyFeedback('medium');
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([40, 30, 60, 30, 40]);
    });

    it('should trigger high soul energy feedback', () => {
      service.triggerSoulEnergyFeedback('high');
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50, 20, 80, 20, 100, 20, 80, 20, 50]);
    });

    it('should trigger soulmate energy feedback', () => {
      service.triggerSoulEnergyFeedback('soulmate');
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([60, 20, 100, 20, 140, 20, 100, 20, 80, 20, 60, 20, 40]);
    });

    it('should trigger progressive feedback with 0% progress', () => {
      service.triggerProgressiveFeedback(0);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([20]);
    });

    it('should trigger progressive feedback with 50% progress', () => {
      service.triggerProgressiveFeedback(0.5);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([50]);
    });

    it('should trigger progressive feedback with 100% progress', () => {
      service.triggerProgressiveFeedback(1.0);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([80]);
    });
  });

  describe('Settings Management', () => {
    it('should allow disabling haptics', () => {
      service.setHapticsEnabled(false);
      expect(service.getHapticsEnabled()).toBe(false);
    });

    it('should allow enabling haptics', () => {
      service.setHapticsEnabled(false);
      service.setHapticsEnabled(true);
      expect(service.getHapticsEnabled()).toBe(true);
    });

    it('should not trigger haptics when disabled', () => {
      service.setHapticsEnabled(false);
      service.triggerHoverFeedback();
      expect(navigatorSpy.vibrate).not.toHaveBeenCalled();
    });

    it('should resume triggering haptics when re-enabled', () => {
      service.setHapticsEnabled(false);
      service.setHapticsEnabled(true);
      service.triggerHoverFeedback();
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([20]);
    });
  });

  describe('iOS Haptic Permission', () => {
    it('should request haptic permission on iOS', async () => {
      const mockRequestPermission = jasmine.createSpy('requestPermission').and.returnValue(Promise.resolve('granted'));

      Object.defineProperty(window, 'DeviceMotionEvent', {
        value: {
          requestPermission: mockRequestPermission
        },
        configurable: true,
        writable: true
      });

      const result = await service.requestHapticPermission();
      expect(result).toBe(true);
    });

    it('should handle permission denial on iOS', async () => {
      const mockRequestPermission = jasmine.createSpy('requestPermission').and.returnValue(Promise.resolve('denied'));

      Object.defineProperty(window, 'DeviceMotionEvent', {
        value: {
          requestPermission: mockRequestPermission
        },
        configurable: true,
        writable: true
      });

      const result = await service.requestHapticPermission();
      expect(result).toBe(false);
    });

    it('should return true when no permission needed (Android/Desktop)', async () => {
      Object.defineProperty(window, 'DeviceMotionEvent', {
        value: undefined,
        configurable: true,
        writable: true
      });

      const result = await service.requestHapticPermission();
      expect(result).toBe(true);
    });

    it('should handle permission request errors gracefully', async () => {
      const mockRequestPermission = jasmine.createSpy('requestPermission').and.returnValue(Promise.reject(new Error('Permission error')));

      Object.defineProperty(window, 'DeviceMotionEvent', {
        value: {
          requestPermission: mockRequestPermission
        },
        configurable: true,
        writable: true
      });

      const result = await service.requestHapticPermission();
      expect(result).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle vibration errors gracefully', () => {
      navigatorSpy.vibrate.and.throwError('Vibration API error');

      expect(() => service.triggerHoverFeedback()).not.toThrow();
    });

    it('should not trigger haptics on unsupported devices', () => {
      // Create service with no vibrate support
      Object.defineProperty(window, 'navigator', {
        value: {
          ...originalNavigator,
          userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        },
        configurable: true,
        writable: true
      });

      const unsupportedService = new HapticFeedbackService();
      unsupportedService.triggerHoverFeedback();

      // Should not crash, just not call vibrate
      expect(true).toBe(true);
    });

    it('should not trigger haptics on desktop devices', () => {
      Object.defineProperty(window, 'navigator', {
        value: {
          ...originalNavigator,
          vibrate: navigatorSpy.vibrate,
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        configurable: true,
        writable: true
      });

      const desktopService = new HapticFeedbackService();
      desktopService.triggerHoverFeedback();

      expect(navigatorSpy.vibrate).not.toHaveBeenCalled();
    });
  });

  describe('Haptic Status Announcements', () => {
    it('should announce haptic availability for mobile with support', () => {
      const announcement = service.announceHapticStatus();
      expect(announcement).toBe('Haptic feedback enabled for emotional connection moments');
    });

    it('should announce unavailability on mobile without support', () => {
      // Create a new service with mobile device but no vibrate support
      const tempNavigator = window.navigator;
      Object.defineProperty(window, 'navigator', {
        value: {
          userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
          // No vibrate property
        },
        configurable: true,
        writable: true
      });

      const noSupportService = new HapticFeedbackService();
      const announcement = noSupportService.announceHapticStatus();

      // Restore navigator
      Object.defineProperty(window, 'navigator', {
        value: tempNavigator,
        configurable: true,
        writable: true
      });

      expect(announcement).toBe('Haptic feedback not available on this device');
    });

    it('should announce mobile-only availability on desktop', () => {
      Object.defineProperty(window, 'navigator', {
        value: {
          ...originalNavigator,
          vibrate: navigatorSpy.vibrate,
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        configurable: true,
        writable: true
      });

      const desktopService = new HapticFeedbackService();
      const announcement = desktopService.announceHapticStatus();
      expect(announcement).toBe('Haptic feedback available on mobile devices');
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero-length pattern arrays', () => {
      service.triggerCustomPattern([]);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([]);
    });

    it('should handle negative tension values', () => {
      service.triggerElasticTensionFeedback(-0.5);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([-10]);
    });

    it('should handle tension values greater than 1', () => {
      service.triggerElasticTensionFeedback(2.0);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([90]);
    });

    it('should handle negative progress values', () => {
      service.triggerProgressiveFeedback(-0.5);
      expect(navigatorSpy.vibrate).toHaveBeenCalled();
    });

    it('should handle progress values greater than 1', () => {
      service.triggerProgressiveFeedback(2.0);
      expect(navigatorSpy.vibrate).toHaveBeenCalled();
    });

    it('should handle revelation step for day 0', () => {
      service.triggerRevelationStepCelebration(0);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([]);
    });

    it('should handle negative compatibility scores', () => {
      service.triggerCompatibilityFeedback(-10);
      expect(navigatorSpy.vibrate).toHaveBeenCalledWith([40]);
    });

    it('should handle compatibility scores over 100', () => {
      service.triggerCompatibilityFeedback(150);
      expect(navigatorSpy.vibrate).toHaveBeenCalled();
    });
  });
});
