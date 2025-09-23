import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface ScreenReaderMessage {
  id: string;
  message: string;
  priority: 'polite' | 'assertive';
  type: 'announcement' | 'status' | 'alert' | 'progress';
  timestamp: number;
  context?: string;
}

export interface ScreenReaderConfig {
  enableAnnouncements: boolean;
  enableProgressUpdates: boolean;
  enableNavigationHelp: boolean;
  enableContextualHelp: boolean;
  verbosityLevel: 'minimal' | 'standard' | 'verbose';
  announcementDelay: number;
}

@Injectable({
  providedIn: 'root'
})
export class ScreenReaderService {
  private config: ScreenReaderConfig = {
    enableAnnouncements: true,
    enableProgressUpdates: true,
    enableNavigationHelp: true,
    enableContextualHelp: true,
    verbosityLevel: 'standard',
    announcementDelay: 100
  };

  private messageQueue: ScreenReaderMessage[] = [];
  private isProcessingQueue = false;
  private currentMessage$ = new BehaviorSubject<ScreenReaderMessage | null>(null);

  get currentMessage(): Observable<ScreenReaderMessage | null> {
    return this.currentMessage$.asObservable();
  }

  /**
   * Update screen reader configuration
   */
  updateConfig(newConfig: Partial<ScreenReaderConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current configuration
   */
  getConfig(): ScreenReaderConfig {
    return { ...this.config };
  }

  /**
   * Announce a message to screen readers
   */
  announce(
    message: string,
    priority: 'polite' | 'assertive' = 'polite',
    context?: string
  ): void {
    if (!this.config.enableAnnouncements) return;

    const announcement: ScreenReaderMessage = {
      id: this.generateId(),
      message: this.formatMessage(message),
      priority,
      type: 'announcement',
      timestamp: Date.now(),
      context
    };

    this.queueMessage(announcement);
  }

  /**
   * Announce status updates (like loading states)
   */
  announceStatus(
    message: string,
    context?: string
  ): void {
    if (!this.config.enableProgressUpdates) return;

    const statusUpdate: ScreenReaderMessage = {
      id: this.generateId(),
      message: this.formatMessage(message),
      priority: 'polite',
      type: 'status',
      timestamp: Date.now(),
      context
    };

    this.queueMessage(statusUpdate);
  }

  /**
   * Announce alerts (urgent messages)
   */
  announceAlert(
    message: string,
    context?: string
  ): void {
    const alert: ScreenReaderMessage = {
      id: this.generateId(),
      message: this.formatMessage(message),
      priority: 'assertive',
      type: 'alert',
      timestamp: Date.now(),
      context
    };

    this.queueMessage(alert);
  }

  /**
   * Announce progress updates
   */
  announceProgress(
    current: number,
    total: number,
    description?: string,
    context?: string
  ): void {
    if (!this.config.enableProgressUpdates) return;

    const percentage = Math.round((current / total) * 100);
    const progressMessage = description
      ? `${description}: ${current} of ${total} (${percentage}%)`
      : `Progress: ${current} of ${total} (${percentage}%)`;

    const progress: ScreenReaderMessage = {
      id: this.generateId(),
      message: progressMessage,
      priority: 'polite',
      type: 'progress',
      timestamp: Date.now(),
      context
    };

    this.queueMessage(progress);
  }

  /**
   * Announce navigation help
   */
  announceNavigationHelp(helpText: string, context?: string): void {
    if (!this.config.enableNavigationHelp) return;

    this.announce(`Navigation help: ${helpText}`, 'polite', context);
  }

  /**
   * Announce contextual help
   */
  announceContextualHelp(helpText: string, context?: string): void {
    if (!this.config.enableContextualHelp) return;

    this.announce(`Help: ${helpText}`, 'polite', context);
  }

  /**
   * Soul-specific announcements
   */
  announceSoulDiscovery(discoveryCount: number): void {
    const message = discoveryCount === 0
      ? 'No soul connections found. Try adjusting your filters for better matches.'
      : `Found ${discoveryCount} soul connection${discoveryCount === 1 ? '' : 's'}. Use arrow keys to navigate between profiles.`;

    this.announce(message, 'polite', 'soul-discovery');
  }

  announceCompatibilityScore(score: number, breakdown?: any): void {
    let message = `Soul compatibility: ${score}%`;

    if (breakdown && this.config.verbosityLevel !== 'minimal') {
      const details = [];
      if (breakdown.values) details.push(`Values: ${breakdown.values}%`);
      if (breakdown.interests) details.push(`Interests: ${breakdown.interests}%`);
      if (breakdown.communication) details.push(`Communication: ${breakdown.communication}%`);

      if (details.length > 0) {
        message += `. Breakdown: ${details.join(', ')}`;
      }
    }

    this.announce(message, 'polite', 'compatibility');
  }

  announceRevelationStep(day: number, totalDays: number = 7): void {
    const message = `Day ${day} of ${totalDays} revelation journey. ${this.getRevelationStepDescription(day)}`;
    this.announce(message, 'polite', 'revelation-step');
  }

  announceConnectionStage(stage: string): void {
    const stageDescriptions = {
      'soul_discovery': 'Soul discovery phase - getting to know each other through questions and interests',
      'revelation_phase': 'Revelation phase - sharing deeper insights through daily revelations',
      'photo_reveal': 'Photo revelation phase - preparing to see each other',
      'dinner_planning': 'Dinner planning phase - arranging your first meeting',
      'completed': 'Connection completed - enjoy your ongoing relationship'
    };

    const description = stageDescriptions[stage as keyof typeof stageDescriptions] || stage;
    this.announce(`Connection stage: ${description}`, 'polite', 'connection-stage');
  }

  announceMessageReceived(senderName: string, messagePreview: string): void {
    const preview = messagePreview.length > 50
      ? messagePreview.substring(0, 50) + '...'
      : messagePreview;

    this.announce(
      `New message from ${senderName}: ${preview}`,
      'assertive',
      'new-message'
    );
  }

  /**
   * Clear all pending announcements
   */
  clearQueue(): void {
    this.messageQueue = [];
  }

  /**
   * Get message history for debugging
   */
  getMessageHistory(limit: number = 10): ScreenReaderMessage[] {
    return this.messageQueue.slice(-limit);
  }

  private queueMessage(message: ScreenReaderMessage): void {
    // Remove duplicate messages within a short time frame
    const recentDuplicate = this.messageQueue.find(
      msg => msg.message === message.message &&
             (message.timestamp - msg.timestamp) < 2000
    );

    if (recentDuplicate) return;

    this.messageQueue.push(message);
    this.processQueue();
  }

  private async processQueue(): Promise<void> {
    if (this.isProcessingQueue || this.messageQueue.length === 0) return;

    this.isProcessingQueue = true;

    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()!;
      await this.announceToScreenReader(message);

      // Update current message observable
      this.currentMessage$.next(message);

      // Delay between announcements
      if (this.messageQueue.length > 0) {
        await this.delay(this.config.announcementDelay);
      }
    }

    this.isProcessingQueue = false;
    this.currentMessage$.next(null);
  }

  private async announceToScreenReader(message: ScreenReaderMessage): Promise<void> {
    return new Promise((resolve) => {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', message.priority);
      announcement.setAttribute('aria-atomic', 'true');
      announcement.setAttribute('role', this.getARIARole(message.type));
      announcement.className = 'sr-only';
      announcement.id = `sr-announcement-${message.id}`;

      // Add context as aria-label if available
      if (message.context) {
        announcement.setAttribute('aria-label', `${message.context}: ${message.message}`);
      }

      announcement.textContent = message.message;

      document.body.appendChild(announcement);

      // Remove after announcement
      setTimeout(() => {
        if (announcement.parentNode) {
          document.body.removeChild(announcement);
        }
        resolve();
      }, Math.max(1000, message.message.length * 50)); // Dynamic timing based on message length
    });
  }

  private formatMessage(message: string): string {
    // Clean up message formatting for better screen reader experience
    return message
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/[^\w\s.,!?;:-]/g, '') // Remove special characters that might confuse screen readers
      .trim();
  }

  private getARIARole(type: ScreenReaderMessage['type']): string {
    switch (type) {
      case 'alert': return 'alert';
      case 'status': return 'status';
      case 'progress': return 'progressbar';
      default: return 'status';
    }
  }

  private getRevelationStepDescription(day: number): string {
    const descriptions = {
      1: 'Share a personal value that guides your life decisions',
      2: 'Describe a meaningful experience that shaped who you are',
      3: 'Share a hope or dream for your future',
      4: 'Describe what makes you laugh and brings you joy',
      5: 'Share a challenge you\'ve overcome and what you learned',
      6: 'Describe your ideal deep connection with someone',
      7: 'Photo revelation day - time to see each other'
    };

    return descriptions[day as keyof typeof descriptions] || 'Continue your revelation journey';
  }

  private generateId(): string {
    return Math.random().toString(36).substr(2, 9);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Detect if screen reader is likely active
   */
  isScreenReaderActive(): boolean {
    // Check for common screen reader indicators
    const hasScreenReaderCSS = document.querySelector('.sr-only') !== null;
    const hasAriaLive = document.querySelector('[aria-live]') !== null;
    const hasHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
    const hasReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    return hasScreenReaderCSS || hasAriaLive || hasHighContrast || hasReducedMotion;
  }

  /**
   * Get recommended verbosity level based on user preferences
   */
  getRecommendedVerbosity(): 'minimal' | 'standard' | 'verbose' {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return 'minimal';
    }

    if (this.isScreenReaderActive()) {
      return 'verbose';
    }

    return 'standard';
  }

  /**
   * Auto-configure based on user preferences
   */
  autoConfigureForAccessibility(): void {
    const recommendedVerbosity = this.getRecommendedVerbosity();
    const isScreenReaderLikelyActive = this.isScreenReaderActive();

    this.updateConfig({
      verbosityLevel: recommendedVerbosity,
      enableAnnouncements: true,
      enableProgressUpdates: isScreenReaderLikelyActive,
      enableNavigationHelp: isScreenReaderLikelyActive,
      enableContextualHelp: isScreenReaderLikelyActive,
      announcementDelay: isScreenReaderLikelyActive ? 200 : 100
    });
  }
}
