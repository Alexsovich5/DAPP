import { Injectable } from '@angular/core';

/**
 * Haptic Feedback Service for Mobile Emotional Connection Moments
 * Provides tactile feedback for soul connection interactions
 */
@Injectable({
  providedIn: 'root'
})
export class HapticFeedbackService {
  private isHapticSupported = false;
  private isMobileDevice = false;

  constructor() {
    this.detectHapticSupport();
    this.detectMobileDevice();
  }

  /**
   * Detect if haptic feedback is supported
   */
  private detectHapticSupport(): void {
    // Check for Vibration API support
    this.isHapticSupported = 'vibrate' in navigator;
    
    // Additional check for iOS Haptic Feedback
    if ((window as any).DeviceMotionEvent && typeof (window as any).DeviceMotionEvent.requestPermission === 'function') {
      this.isHapticSupported = true;
    }
  }

  /**
   * Detect if running on mobile device
   */
  private detectMobileDevice(): void {
    this.isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  /**
   * Provide gentle feedback for hovering over high compatibility profiles
   */
  triggerHoverFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Gentle single tap
    this.vibrate([20]);
  }

  /**
   * Provide success feedback for soul connections
   */
  triggerConnectionSuccess(): void {
    if (!this.canProvideHaptics()) return;
    
    // Success pattern: short-long-short
    this.vibrate([50, 50, 150, 50, 50]);
  }

  /**
   * Provide feedback for passing on a profile
   */
  triggerPassFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Gentle dismissal: single longer vibration
    this.vibrate([100]);
  }

  /**
   * Provide feedback for high compatibility matches
   */
  triggerHighCompatibilityFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Heartbeat pattern for high compatibility
    this.vibrate([80, 100, 120, 100, 80]);
  }

  /**
   * Provide feedback for filter changes
   */
  triggerFilterChangeFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Subtle tick for filter adjustments
    this.vibrate([15]);
  }

  /**
   * Provide error feedback
   */
  triggerErrorFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Error pattern: three short bursts
    this.vibrate([100, 50, 100, 50, 100]);
  }

  /**
   * Provide loading feedback
   */
  triggerLoadingFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Gentle pulse for loading states
    this.vibrate([30]);
  }

  /**
   * Provide revelation moment feedback
   */
  triggerRevelationFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Special pattern for emotional revelations
    this.vibrate([50, 30, 80, 30, 120, 30, 80, 30, 50]);
  }

  /**
   * Provide focus feedback for keyboard navigation
   */
  triggerFocusFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Minimal feedback for focus changes
    this.vibrate([10]);
  }

  /**
   * Welcome haptic feedback for new users
   */
  triggerWelcomeFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Warm, welcoming pattern
    this.vibrate([100, 50, 100, 50, 200]);
  }

  /**
   * Selection feedback for UI interactions
   */
  triggerSelectionFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Quick, crisp selection feedback
    this.vibrate([50]);
  }

  /**
   * Success feedback for completed actions
   */
  triggerSuccessFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Celebratory success pattern
    this.vibrate([100, 50, 100, 50, 150]);
  }

  /**
   * Check if haptic feedback can be provided
   */
  private canProvideHaptics(): boolean {
    return this.isHapticSupported && this.isMobileDevice;
  }

  /**
   * Execute vibration pattern
   * @param pattern - Array of vibration durations in milliseconds
   */
  private vibrate(pattern: number[]): void {
    try {
      if ('vibrate' in navigator) {
        navigator.vibrate(pattern);
      }
    } catch (error) {
      console.debug('Haptic feedback not available:', error);
    }
  }

  /**
   * Request haptic permissions for iOS devices
   */
  async requestHapticPermission(): Promise<boolean> {
    try {
      if ((window as any).DeviceMotionEvent && typeof (window as any).DeviceMotionEvent.requestPermission === 'function') {
        const permission = await (window as any).DeviceMotionEvent.requestPermission();
        return permission === 'granted';
      }
      return true;
    } catch (error) {
      console.debug('Haptic permission request failed:', error);
      return false;
    }
  }

  /**
   * Get haptic support status
   */
  getHapticStatus(): { supported: boolean; mobile: boolean } {
    return {
      supported: this.isHapticSupported,
      mobile: this.isMobileDevice
    };
  }

  /**
   * Announce haptic capabilities to screen readers
   */
  announceHapticStatus(): string {
    if (this.canProvideHaptics()) {
      return 'Haptic feedback enabled for emotional connection moments';
    } else if (this.isMobileDevice) {
      return 'Haptic feedback not available on this device';
    } else {
      return 'Haptic feedback available on mobile devices';
    }
  }

  /**
   * Create emotional haptic sequence based on compatibility score
   */
  triggerCompatibilityFeedback(compatibilityScore: number): void {
    if (!this.canProvideHaptics()) return;
    
    if (compatibilityScore >= 90) {
      // Soul mate level - magical pattern
      this.vibrate([50, 30, 100, 30, 150, 30, 100, 30, 50]);
    } else if (compatibilityScore >= 80) {
      // High compatibility - heartbeat pattern
      this.triggerHighCompatibilityFeedback();
    } else if (compatibilityScore >= 60) {
      // Medium compatibility - gentle pulse
      this.vibrate([60, 40, 80]);
    } else {
      // Low compatibility - subtle feedback
      this.vibrate([40]);
    }
  }

  /**
   * Create breathing pattern haptic for soul orb interactions
   */
  triggerBreathingFeedback(): void {
    if (!this.canProvideHaptics()) return;
    
    // Breathing pattern: inhale, hold, exhale
    this.vibrate([80, 100, 120, 100, 80]);
  }

  /**
   * Create celebratory haptic burst for successful matches
   */
  triggerCelebrationBurst(): void {
    if (!this.canProvideHaptics()) return;
    
    // Celebration burst pattern
    this.vibrate([50, 20, 70, 20, 90, 20, 110, 20, 90, 20, 70, 20, 50]);
  }
}