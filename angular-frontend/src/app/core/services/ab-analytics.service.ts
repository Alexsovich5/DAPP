import { Injectable } from '@angular/core';
import { ABTestingService, ABTestEvent, ABTestConfig, AB_TEST_CONFIGS } from './ab-testing.service';

// === ANALYTICS INTERFACES ===

export interface ABTestMetrics {
  testId: string;
  testName: string;
  totalParticipants: number;
  variantMetrics: VariantMetrics[];
  primaryMetric: MetricResult;
  secondaryMetrics: MetricResult[];
  statisticalSignificance: number;
  recommendedAction: 'continue' | 'conclude_winner' | 'conclude_no_winner' | 'extend_test';
  confidenceLevel: number;
}

export interface VariantMetrics {
  variantId: string;
  variantName: string;
  participants: number;
  conversionRate: number;
  averageValue: number;
  events: EventSummary[];
}

export interface MetricResult {
  name: string;
  variants: VariantMetric[];
  winner?: string;
  improvement?: number; // Percentage improvement over control
  confidenceInterval: [number, number];
}

export interface VariantMetric {
  variantId: string;
  value: number;
  sampleSize: number;
  standardError: number;
}

export interface EventSummary {
  eventType: string;
  count: number;
  rate: number; // Events per participant
  averageValue?: number;
}

// === PREDEFINED METRIC CALCULATIONS ===

export const METRIC_DEFINITIONS: Record<string, MetricCalculation> = {
  connection_rate: {
    name: 'Connection Rate',
    description: 'Percentage of users who create a connection',
    numeratorEvents: ['connection_created', 'super_like_sent'],
    denominatorEvents: ['discovery_viewed'],
    isPercentage: true
  },
  onboarding_completion_rate: {
    name: 'Onboarding Completion Rate',
    description: 'Percentage of users who complete onboarding',
    numeratorEvents: ['onboarding_completed'],
    denominatorEvents: ['onboarding_started'],
    isPercentage: true
  },
  message_open_rate: {
    name: 'Message Open Rate',
    description: 'Percentage of message notifications that result in opens',
    numeratorEvents: ['message_opened'],
    denominatorEvents: ['message_received'],
    isPercentage: true
  },
  time_on_discovery: {
    name: 'Time on Discovery',
    description: 'Average time spent on discovery page',
    valueEvents: ['discovery_time_spent'],
    isPercentage: false
  },
  cards_viewed_per_session: {
    name: 'Cards Viewed per Session',
    description: 'Average number of discovery cards viewed per session',
    numeratorEvents: ['discovery_card_viewed'],
    denominatorEvents: ['session_started'],
    isPercentage: false
  }
};

interface MetricCalculation {
  name: string;
  description: string;
  numeratorEvents?: string[];
  denominatorEvents?: string[];
  valueEvents?: string[];
  isPercentage: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ABAnalyticsService {
  constructor(private abTestingService: ABTestingService) {}

  /**
   * Get comprehensive analytics for a specific A/B test
   */
  getTestAnalytics(testId: string): ABTestMetrics | null {
    const testConfig = AB_TEST_CONFIGS[testId];
    if (!testConfig) {
      return null;
    }

    const events = this.getTestEvents(testId);
    const variantMetrics = this.calculateVariantMetrics(testConfig, events);
    const primaryMetric = this.calculateMetric(testConfig.primaryMetric, variantMetrics);
    const secondaryMetrics = (testConfig.secondaryMetrics || [])
      .map(metric => this.calculateMetric(metric, variantMetrics))
      .filter(metric => metric !== null) as MetricResult[];

    const totalParticipants = variantMetrics.reduce((sum, v) => sum + v.participants, 0);
    const statisticalSignificance = this.calculateStatisticalSignificance(primaryMetric);
    const recommendedAction = this.getRecommendedAction(primaryMetric, statisticalSignificance);

    return {
      testId,
      testName: testConfig.name,
      totalParticipants,
      variantMetrics,
      primaryMetric,
      secondaryMetrics,
      statisticalSignificance,
      recommendedAction,
      confidenceLevel: 95 // Standard confidence level
    };
  }

  /**
   * Get analytics for all active tests
   */
  getAllTestAnalytics(): ABTestMetrics[] {
    const activeTests = this.abTestingService.getActiveTests();
    return activeTests
      .map(test => this.getTestAnalytics(test.id))
      .filter(analytics => analytics !== null) as ABTestMetrics[];
  }

  /**
   * Export test data for external analysis
   */
  exportTestData(testId: string): string {
    const analytics = this.getTestAnalytics(testId);
    if (!analytics) {
      return '';
    }

    const csvData = this.convertToCSV(analytics);
    return csvData;
  }

  /**
   * Get funnel analysis for a test
   */
  getFunnelAnalysis(testId: string, funnelSteps: string[]): Record<string, any[]> {
    const events = this.getTestEvents(testId);
    const variants = new Set(events.map(e => e.variantId));
    
    const funnelData: Record<string, any[]> = {};
    
    variants.forEach(variantId => {
      const variantEvents = events.filter(e => e.variantId === variantId);
      const userSessions = this.groupEventsByUser(variantEvents);
      
      funnelData[variantId] = this.calculateFunnel(userSessions, funnelSteps);
    });

    return funnelData;
  }

  // === PRIVATE METHODS ===

  private getTestEvents(testId: string): ABTestEvent[] {
    try {
      const storedEvents = localStorage.getItem('ab_test_events');
      if (!storedEvents) {
        return [];
      }

      const allEvents: ABTestEvent[] = JSON.parse(storedEvents);
      return allEvents
        .filter(event => event.testId === testId)
        .map(event => ({
          ...event,
          timestamp: new Date(event.timestamp)
        }));
    } catch (error) {
      console.warn('Failed to load A/B test events:', error);
      return [];
    }
  }

  private calculateVariantMetrics(testConfig: ABTestConfig, events: ABTestEvent[]): VariantMetrics[] {
    return testConfig.variants.map(variant => {
      const variantEvents = events.filter(e => e.variantId === variant.id);
      const participants = new Set(variantEvents.map(e => e.userId)).size;
      
      // Calculate event summaries
      const eventSummaries = this.calculateEventSummaries(variantEvents, participants);
      
      // Calculate conversion rate (primary metric events / participants)
      const primaryMetricDef = METRIC_DEFINITIONS[testConfig.primaryMetric];
      let conversionRate = 0;
      
      if (primaryMetricDef && primaryMetricDef.numeratorEvents) {
        const conversions = variantEvents.filter(e => 
          primaryMetricDef.numeratorEvents!.includes(e.eventType)
        ).length;
        conversionRate = participants > 0 ? (conversions / participants) * 100 : 0;
      }

      return {
        variantId: variant.id,
        variantName: variant.name,
        participants,
        conversionRate,
        averageValue: this.calculateAverageValue(variantEvents),
        events: eventSummaries
      };
    });
  }

  private calculateEventSummaries(events: ABTestEvent[], participants: number): EventSummary[] {
    const eventGroups = events.reduce((groups, event) => {
      if (!groups[event.eventType]) {
        groups[event.eventType] = [];
      }
      groups[event.eventType].push(event);
      return groups;
    }, {} as Record<string, ABTestEvent[]>);

    return Object.entries(eventGroups).map(([eventType, eventList]) => ({
      eventType,
      count: eventList.length,
      rate: participants > 0 ? eventList.length / participants : 0,
      averageValue: this.calculateEventAverageValue(eventList)
    }));
  }

  private calculateEventAverageValue(events: ABTestEvent[]): number {
    const values = events
      .map(e => e.eventData?.value)
      .filter(v => typeof v === 'number') as number[];
    
    if (values.length === 0) {
      return 0;
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
  }

  private calculateAverageValue(events: ABTestEvent[]): number {
    return this.calculateEventAverageValue(events);
  }

  private calculateMetric(metricName: string, variantMetrics: VariantMetrics[]): MetricResult {
    const metricDef = METRIC_DEFINITIONS[metricName];
    if (!metricDef) {
      return {
        name: metricName,
        variants: [],
        confidenceInterval: [0, 0]
      };
    }

    const variants: VariantMetric[] = variantMetrics.map(variant => {
      let value = 0;
      let sampleSize = variant.participants;

      if (metricDef.numeratorEvents && metricDef.denominatorEvents) {
        // Rate calculation
        const numerator = this.getEventCount(variant.events, metricDef.numeratorEvents);
        const denominator = this.getEventCount(variant.events, metricDef.denominatorEvents);
        value = denominator > 0 ? (numerator / denominator) : 0;
        if (metricDef.isPercentage) {
          value *= 100;
        }
      } else if (metricDef.valueEvents) {
        // Average value calculation
        const eventSummary = variant.events.find(e => 
          metricDef.valueEvents!.includes(e.eventType)
        );
        value = eventSummary?.averageValue || 0;
      }

      return {
        variantId: variant.variantId,
        value,
        sampleSize,
        standardError: this.calculateStandardError(value, sampleSize, metricDef.isPercentage)
      };
    });

    // Find winner and calculate improvement
    const controlVariant = variants.find(v => 
      variantMetrics.find(vm => vm.variantId === v.variantId)?.variantName.includes('Control') ||
      v.variantId === 'control'
    );
    
    const winner = this.findWinner(variants);
    const improvement = controlVariant && winner && winner.variantId !== controlVariant.variantId
      ? ((winner.value - controlVariant.value) / controlVariant.value) * 100
      : undefined;

    return {
      name: metricDef.name,
      variants,
      winner: winner?.variantId,
      improvement,
      confidenceInterval: this.calculateConfidenceInterval(variants)
    };
  }

  private getEventCount(events: EventSummary[], eventTypes: string[]): number {
    return events
      .filter(e => eventTypes.includes(e.eventType))
      .reduce((sum, e) => sum + e.count, 0);
  }

  private calculateStandardError(value: number, sampleSize: number, isPercentage: boolean): number {
    if (sampleSize === 0) {
      return 0;
    }

    if (isPercentage) {
      // Standard error for proportion
      const p = value / 100;
      return Math.sqrt((p * (1 - p)) / sampleSize) * 100;
    } else {
      // Simplified standard error for means (would need actual variance in real implementation)
      return value / Math.sqrt(sampleSize);
    }
  }

  private findWinner(variants: VariantMetric[]): VariantMetric | undefined {
    if (variants.length === 0) {
      return undefined;
    }

    return variants.reduce((best, current) => 
      current.value > best.value ? current : best
    );
  }

  private calculateConfidenceInterval(variants: VariantMetric[]): [number, number] {
    if (variants.length === 0) {
      return [0, 0];
    }

    const bestVariant = this.findWinner(variants);
    if (!bestVariant) {
      return [0, 0];
    }

    // 95% confidence interval (z-score = 1.96)
    const margin = 1.96 * bestVariant.standardError;
    return [
      Math.max(0, bestVariant.value - margin),
      bestVariant.value + margin
    ];
  }

  private calculateStatisticalSignificance(metric: MetricResult): number {
    // Simplified calculation - in reality, you'd need proper statistical tests
    if (metric.variants.length < 2) {
      return 0;
    }

    const controlVariant = metric.variants[0];
    const testVariant = metric.variants[1];
    
    if (!controlVariant || !testVariant) {
      return 0;
    }

    // Calculate z-score for difference in proportions
    const diff = Math.abs(testVariant.value - controlVariant.value);
    const pooledSE = Math.sqrt(
      controlVariant.standardError ** 2 + testVariant.standardError ** 2
    );

    if (pooledSE === 0) {
      return 0;
    }

    const zScore = diff / pooledSE;
    
    // Convert z-score to confidence level (simplified)
    if (zScore >= 1.96) return 95; // 95% confidence
    if (zScore >= 1.645) return 90; // 90% confidence
    if (zScore >= 1.282) return 80; // 80% confidence
    
    return Math.min(80, zScore * 40); // Rough approximation
  }

  private getRecommendedAction(
    metric: MetricResult, 
    significance: number
  ): 'continue' | 'conclude_winner' | 'conclude_no_winner' | 'extend_test' {
    if (significance >= 95 && metric.improvement && metric.improvement > 5) {
      return 'conclude_winner';
    }
    
    if (significance >= 95 && (!metric.improvement || Math.abs(metric.improvement) < 2)) {
      return 'conclude_no_winner';
    }
    
    if (significance < 80) {
      return 'extend_test';
    }
    
    return 'continue';
  }

  private groupEventsByUser(events: ABTestEvent[]): Record<string, ABTestEvent[]> {
    return events.reduce((groups, event) => {
      if (!groups[event.userId]) {
        groups[event.userId] = [];
      }
      groups[event.userId].push(event);
      return groups;
    }, {} as Record<string, ABTestEvent[]>);
  }

  private calculateFunnel(userSessions: Record<string, ABTestEvent[]>, steps: string[]): any[] {
    const userCount = Object.keys(userSessions).length;
    
    return steps.map((step, index) => {
      const usersAtStep = Object.values(userSessions).filter(events =>
        events.some(event => event.eventType === step)
      ).length;

      return {
        step,
        users: usersAtStep,
        conversionRate: userCount > 0 ? (usersAtStep / userCount) * 100 : 0,
        dropoffRate: index > 0 ? 
          ((steps[index - 1] ? userCount - usersAtStep : 0) / userCount) * 100 : 0
      };
    });
  }

  private convertToCSV(analytics: ABTestMetrics): string {
    const headers = [
      'Variant ID',
      'Variant Name', 
      'Participants',
      'Conversion Rate (%)',
      'Primary Metric Value'
    ];

    const rows = analytics.variantMetrics.map(variant => [
      variant.variantId,
      variant.variantName,
      variant.participants.toString(),
      variant.conversionRate.toFixed(2),
      analytics.primaryMetric.variants
        .find(v => v.variantId === variant.variantId)?.value.toFixed(2) || '0'
    ]);

    return [headers, ...rows]
      .map(row => row.join(','))
      .join('\n');
  }
}