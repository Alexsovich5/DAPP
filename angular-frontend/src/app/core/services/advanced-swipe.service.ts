/**
 * Advanced Swipe Service - Enhanced version with elastic physics and soul-themed interactions
 * Phase 3 implementation for mobile-first UX
 */
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent, merge, animationFrameScheduler } from 'rxjs';
import { filter, map, switchMap, takeUntil, tap, throttleTime } from 'rxjs/operators';
import { HapticFeedbackService } from './haptic-feedback.service';

export interface ElasticSwipeEvent extends SwipeEvent {
  elasticProgress: number; // 0-1, how far into elastic zone
  resistance: number; // Current resistance factor
  shouldTriggerAction: boolean; // If swipe meets action threshold
  snapBackVelocity: number; // Velocity for snap-back animation
  energyLevel: 'low' | 'medium' | 'high' | 'soulmate'; // Based on swipe intensity
}

export interface SwipeEvent {
  direction: 'left' | 'right' | 'up' | 'down';
  distance: number;
  velocity: number;
  startPosition: { x: number; y: number };
  endPosition: { x: number; y: number };
  duration: number;
  element: HTMLElement;
  originalEvent: TouchEvent | MouseEvent;
  deltaX: number;
  deltaY: number;
  phase: 'start' | 'move' | 'end';
}

export interface AdvancedSwipeConfig {
  // Basic thresholds
  threshold: number;
  velocityThreshold: number;
  timeThreshold: number;
  
  // Elastic physics
  elasticZone: number; // Distance where elastic behavior starts
  maxElasticDistance: number; // Maximum elastic stretch
  elasticResistance: number; // Resistance factor (0-1)
  snapBackDuration: number; // Snap-back animation duration
  
  // Haptic feedback
  hapticFeedback: boolean;
  hapticIntensity: 'light' | 'medium' | 'heavy';
  progressiveHaptics: boolean; // Haptics get stronger with distance
  
  // Visual feedback
  visualFeedback: boolean;
  showProgress: boolean;
  ghostElement: boolean; // Show preview of action
  
  // Soul-themed enhancements
  soulTheme: 'discovery' | 'revelation' | 'connection' | 'energy';
  connectionEnergy: 'low' | 'medium' | 'high' | 'soulmate';
  compatibilityScore?: number; // Affects swipe sensitivity
  
  // Advanced options
  enabledDirections: ('left' | 'right' | 'up' | 'down')[];
  preventDefaultEvents: boolean;
  multitouch: boolean;
  deadZone: number; // Minimum movement to start tracking
}

export interface SwipeAction {
  id: string;
  direction: 'left' | 'right' | 'up' | 'down';
  threshold: number;
  icon: string;
  label: string;
  color: string;
  hapticPattern?: number[];
  onActivate: (event: ElasticSwipeEvent) => void;
  onPreview?: (progress: number) => void;
  canExecute?: () => boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AdvancedSwipeService {
  private defaultConfig: AdvancedSwipeConfig = {
    threshold: 80,
    velocityThreshold: 0.3,
    timeThreshold: 800,
    elasticZone: 60,
    maxElasticDistance: 150,
    elasticResistance: 0.4,
    snapBackDuration: 300,
    hapticFeedback: true,
    hapticIntensity: 'medium',
    progressiveHaptics: true,
    visualFeedback: true,
    showProgress: true,
    ghostElement: true,
    soulTheme: 'discovery',
    connectionEnergy: 'medium',
    enabledDirections: ['left', 'right'],
    preventDefaultEvents: true,
    multitouch: false,
    deadZone: 10
  };

  private swipeZones = new Map<string, AdvancedSwipeZone>();
  private isSwipeInProgress = new BehaviorSubject<boolean>(false);
  private currentSwipeData = new BehaviorSubject<ElasticSwipeEvent | null>(null);
  
  public swipeInProgress$ = this.isSwipeInProgress.asObservable();
  public currentSwipe$ = this.currentSwipeData.asObservable();

  constructor(private hapticService: HapticFeedbackService) {
    this.initializePhysicsEngine();
  }

  /**
   * Register an advanced swipe zone with elastic physics and soul theming
   */
  registerAdvancedSwipeZone(
    id: string,
    element: HTMLElement,
    actions: SwipeAction[],
    config: Partial<AdvancedSwipeConfig> = {}
  ): void {
    const mergedConfig = { ...this.defaultConfig, ...config };
    
    const zone: AdvancedSwipeZone = {
      id,
      element,
      config: mergedConfig,
      actions: new Map(actions.map(action => [action.direction, action])),
      isActive: true,
      currentTransform: { x: 0, y: 0 },
      isAnimating: false
    };

    this.swipeZones.set(id, zone);
    this.attachAdvancedSwipeListeners(zone);
    this.setupVisualFeedback(zone);
  }

  /**
   * Update swipe zone with new actions (for dynamic UI)
   */
  updateSwipeActions(id: string, actions: SwipeAction[]): void {
    const zone = this.swipeZones.get(id);
    if (zone) {
      zone.actions = new Map(actions.map(action => [action.direction, action]));
    }
  }

  /**
   * Set connection energy level (affects swipe sensitivity and theming)
   */
  setConnectionEnergy(id: string, energy: 'low' | 'medium' | 'high' | 'soulmate'): void {
    const zone = this.swipeZones.get(id);
    if (zone) {
      zone.config.connectionEnergy = energy;
      this.updateSwipePhysics(zone);
    }
  }

  private attachAdvancedSwipeListeners(zone: AdvancedSwipeZone): void {
    const element = zone.element;
    let startPosition: { x: number; y: number } | null = null;
    let startTime: number = 0;
    let isSwipeActive = false;
    let lastHapticDistance = 0;

    // Enhanced event detection
    const startEvents$ = this.getStartEvents(element);
    const moveEvents$ = this.getMoveEvents();
    const endEvents$ = this.getEndEvents();

    // Handle swipe start
    startEvents$.subscribe((event) => {
      if (!zone.isActive || zone.isAnimating) return;

      const position = this.getEventPosition(event);
      startPosition = position;
      startTime = Date.now();
      isSwipeActive = true;
      lastHapticDistance = 0;
      
      this.isSwipeInProgress.next(true);
      
      // Add soul-themed visual feedback
      element.classList.add('soul-swipe-active', `theme-${zone.config.soulTheme}`);
      
      if (zone.config.preventDefaultEvents) {
        event.preventDefault();
      }

      // Initial haptic feedback
      if (zone.config.hapticFeedback) {
        this.hapticService.triggerImpactFeedback('light');
      }
    });

    // Handle swipe move with elastic physics
    moveEvents$.pipe(
      filter(() => isSwipeActive && startPosition !== null && zone.isActive),
      throttleTime(16, animationFrameScheduler), // 60fps updates
      tap((event) => {
        if (zone.config.preventDefaultEvents) {
          event.preventDefault();
        }
      })
    ).subscribe((event) => {
      const currentPosition = this.getEventPosition(event);
      const rawDelta = this.calculateDelta(startPosition!, currentPosition);
      const direction = this.getSwipeDirection(rawDelta);
      
      // Apply dead zone
      if (Math.abs(rawDelta.x) < zone.config.deadZone && Math.abs(rawDelta.y) < zone.config.deadZone) {
        return;
      }

      // Calculate elastic physics
      const elasticData = this.calculateElasticPhysics(rawDelta, zone.config, direction);
      const distance = Math.abs(elasticData.distance);

      // Create enhanced swipe event
      const swipeEvent: ElasticSwipeEvent = {
        direction,
        distance,
        velocity: distance / (Date.now() - startTime),
        startPosition: startPosition!,
        endPosition: currentPosition,
        duration: Date.now() - startTime,
        element,
        originalEvent: event as any,
        deltaX: rawDelta.x,
        deltaY: rawDelta.y,
        phase: 'move',
        elasticProgress: elasticData.elasticProgress,
        resistance: elasticData.resistance,
        shouldTriggerAction: elasticData.shouldTrigger,
        snapBackVelocity: 0,
        energyLevel: this.calculateEnergyLevel(distance, zone.config)
      };

      // Update current swipe data
      this.currentSwipeData.next(swipeEvent);

      // Apply visual transform with elastic physics
      this.applyElasticTransform(element, elasticData, zone);

      // Progressive haptic feedback
      if (zone.config.progressiveHaptics && distance > lastHapticDistance + 20) {
        this.triggerProgressiveHaptic(elasticData.elasticProgress, zone.config);
        lastHapticDistance = distance;
      }

      // Update action previews
      this.updateActionPreviews(zone, swipeEvent);
    });

    // Handle swipe end with snap-back animation
    endEvents$.pipe(
      filter(() => isSwipeActive && startPosition !== null && zone.isActive)
    ).subscribe((event) => {
      if (!startPosition) return;

      const endPosition = this.getEventPosition(event);
      const duration = Date.now() - startTime;
      const rawDelta = this.calculateDelta(startPosition, endPosition);
      const direction = this.getSwipeDirection(rawDelta);
      const elasticData = this.calculateElasticPhysics(rawDelta, zone.config, direction);

      const finalEvent: ElasticSwipeEvent = {
        direction,
        distance: elasticData.distance,
        velocity: elasticData.distance / duration,
        startPosition,
        endPosition,
        duration,
        element,
        originalEvent: event as any,
        deltaX: rawDelta.x,
        deltaY: rawDelta.y,
        phase: 'end',
        elasticProgress: elasticData.elasticProgress,
        resistance: elasticData.resistance,
        shouldTriggerAction: elasticData.shouldTrigger,
        snapBackVelocity: this.calculateSnapBackVelocity(elasticData),
        energyLevel: this.calculateEnergyLevel(elasticData.distance, zone.config)
      };

      // Execute action if threshold met
      if (elasticData.shouldTrigger) {
        const action = zone.actions.get(direction);
        if (action && (!action.canExecute || action.canExecute())) {
          this.executeSwipeAction(action, finalEvent, zone);
        }
      }

      // Animate snap-back
      this.animateSnapBack(zone, finalEvent);

      // Reset state
      this.resetSwipeState(zone, startPosition, isSwipeActive);
      startPosition = null;
      isSwipeActive = false;
      this.isSwipeInProgress.next(false);
      this.currentSwipeData.next(null);
    });
  }

  private calculateElasticPhysics(
    delta: { x: number; y: number }, 
    config: AdvancedSwipeConfig,
    direction: 'left' | 'right' | 'up' | 'down'
  ): ElasticPhysicsData {
    const primaryAxis = ['left', 'right'].includes(direction) ? Math.abs(delta.x) : Math.abs(delta.y);
    const rawDistance = primaryAxis;
    
    let adjustedDistance = rawDistance;
    let elasticProgress = 0;
    let resistance = 1;
    let shouldTrigger = false;

    if (rawDistance > config.elasticZone) {
      // Calculate elastic behavior
      const elasticDistance = rawDistance - config.elasticZone;
      const maxElastic = config.maxElasticDistance - config.elasticZone;
      
      elasticProgress = Math.min(elasticDistance / maxElastic, 1);
      resistance = 1 - (config.elasticResistance * elasticProgress);
      
      // Apply elastic damping
      const dampedElasticDistance = elasticDistance * resistance;
      adjustedDistance = config.elasticZone + dampedElasticDistance;
      
      // Check if should trigger action
      shouldTrigger = rawDistance > config.threshold;
    }

    return {
      distance: adjustedDistance,
      elasticProgress,
      resistance,
      shouldTrigger
    };
  }

  private applyElasticTransform(
    element: HTMLElement, 
    elasticData: ElasticPhysicsData, 
    zone: AdvancedSwipeZone
  ): void {
    const { distance, elasticProgress } = elasticData;
    
    // Calculate transform values
    const scale = 1 - (elasticProgress * 0.02); // Subtle scale effect
    const opacity = 1 - (elasticProgress * 0.1); // Slight fade in elastic zone
    const blur = elasticProgress * 1; // Subtle blur effect

    // Apply transform
    element.style.transform = `translateX(${distance}px) scale(${scale})`;
    element.style.opacity = opacity.toString();
    element.style.filter = `blur(${blur}px)`;
    element.style.transition = 'none';

    // Update zone state
    zone.currentTransform = { 
      x: distance, 
      y: 0 
    };

    // Add visual feedback classes
    if (elasticProgress > 0.5) {
      element.classList.add('elastic-high-tension');
    } else {
      element.classList.remove('elastic-high-tension');
    }
  }

  private animateSnapBack(zone: AdvancedSwipeZone, event: ElasticSwipeEvent): void {
    const element = zone.element;
    zone.isAnimating = true;

    // Calculate spring animation
    const springConfig = this.getSpringConfigForEnergy(zone.config.connectionEnergy);
    
    element.style.transition = `
      transform ${zone.config.snapBackDuration}ms ${springConfig},
      opacity ${zone.config.snapBackDuration}ms ease-out,
      filter ${zone.config.snapBackDuration}ms ease-out
    `;
    
    // Animate back to origin
    element.style.transform = 'translateX(0) scale(1)';
    element.style.opacity = '1';
    element.style.filter = 'blur(0px)';

    // Clean up after animation
    setTimeout(() => {
      element.classList.remove('soul-swipe-active', 'elastic-high-tension', `theme-${zone.config.soulTheme}`);
      element.style.transition = '';
      zone.isAnimating = false;
      zone.currentTransform = { x: 0, y: 0 };
    }, zone.config.snapBackDuration);
  }

  private executeSwipeAction(
    action: SwipeAction, 
    event: ElasticSwipeEvent, 
    zone: AdvancedSwipeZone
  ): void {
    // Trigger action haptic pattern
    if (action.hapticPattern && zone.config.hapticFeedback) {
      this.hapticService.triggerCustomPattern(action.hapticPattern);
    } else {
      this.hapticService.triggerSuccessFeedback();
    }

    // Add success visual feedback
    zone.element.classList.add('swipe-action-success', `action-${action.id}`);
    
    setTimeout(() => {
      zone.element.classList.remove('swipe-action-success', `action-${action.id}`);
    }, 300);

    // Execute action callback
    action.onActivate(event);
  }

  private getSpringConfigForEnergy(energy: string): string {
    switch (energy) {
      case 'soulmate': return 'cubic-bezier(0.34, 1.56, 0.64, 1)';
      case 'high': return 'cubic-bezier(0.25, 0.46, 0.45, 0.94)';
      case 'medium': return 'cubic-bezier(0.25, 0.46, 0.45, 0.94)';
      case 'low': return 'ease-out';
      default: return 'ease-out';
    }
  }

  private calculateEnergyLevel(
    distance: number, 
    config: AdvancedSwipeConfig
  ): 'low' | 'medium' | 'high' | 'soulmate' {
    const ratio = distance / config.threshold;
    
    if (ratio < 0.5) return 'low';
    if (ratio < 1.2) return 'medium';
    if (ratio < 2.0) return 'high';
    return 'soulmate';
  }

  private triggerProgressiveHaptic(
    elasticProgress: number, 
    config: AdvancedSwipeConfig
  ): void {
    const intensity = elasticProgress > 0.7 ? 'heavy' : elasticProgress > 0.4 ? 'medium' : 'light';
    this.hapticService.triggerImpactFeedback(intensity);
  }

  private updateActionPreviews(zone: AdvancedSwipeZone, event: ElasticSwipeEvent): void {
    zone.actions.forEach((action, direction) => {
      if (direction === event.direction && action.onPreview) {
        const progress = Math.min(event.distance / action.threshold, 1);
        action.onPreview(progress);
      }
    });
  }

  private setupVisualFeedback(zone: AdvancedSwipeZone): void {
    const element = zone.element;
    
    // Add CSS classes for styling
    element.classList.add('advanced-swipe-zone', `energy-${zone.config.connectionEnergy}`);
    
    // Create action indicators if enabled
    if (zone.config.showProgress) {
      this.createActionIndicators(zone);
    }
  }

  private createActionIndicators(zone: AdvancedSwipeZone): void {
    // Create indicator elements for each action
    zone.actions.forEach((action, direction) => {
      const indicator = document.createElement('div');
      indicator.className = `swipe-action-indicator ${direction} ${action.id}`;
      indicator.innerHTML = `
        <div class="icon">${action.icon}</div>
        <div class="label">${action.label}</div>
        <div class="progress-ring">
          <svg width="40" height="40">
            <circle cx="20" cy="20" r="18" stroke="${action.color}" stroke-width="2" fill="none" opacity="0.3"/>
            <circle cx="20" cy="20" r="18" stroke="${action.color}" stroke-width="3" fill="none" 
                    stroke-dasharray="113" stroke-dashoffset="113" class="progress"/>
          </svg>
        </div>
      `;
      
      zone.element.appendChild(indicator);
    });
  }

  // Helper methods
  private getStartEvents(element: HTMLElement): Observable<TouchEvent | MouseEvent> {
    const touchStart$ = fromEvent<TouchEvent>(element, 'touchstart');
    const mouseDown$ = fromEvent<MouseEvent>(element, 'mousedown');
    return merge(touchStart$, mouseDown$);
  }

  private getMoveEvents(): Observable<TouchEvent | MouseEvent> {
    const touchMove$ = fromEvent<TouchEvent>(document, 'touchmove');
    const mouseMove$ = fromEvent<MouseEvent>(document, 'mousemove');
    return merge(touchMove$, mouseMove$);
  }

  private getEndEvents(): Observable<TouchEvent | MouseEvent> {
    const touchEnd$ = fromEvent<TouchEvent>(document, 'touchend');
    const mouseUp$ = fromEvent<MouseEvent>(document, 'mouseup');
    return merge(touchEnd$, mouseUp$);
  }

  private getEventPosition(event: TouchEvent | MouseEvent): { x: number; y: number } {
    if ('touches' in event && event.touches.length > 0) {
      return { x: event.touches[0].clientX, y: event.touches[0].clientY };
    } else if ('clientX' in event) {
      return { x: event.clientX, y: event.clientY };
    }
    return { x: 0, y: 0 };
  }

  private calculateDelta(start: { x: number; y: number }, end: { x: number; y: number }): { x: number; y: number } {
    return {
      x: end.x - start.x,
      y: end.y - start.y
    };
  }

  private getSwipeDirection(delta: { x: number; y: number }): 'left' | 'right' | 'up' | 'down' {
    if (Math.abs(delta.x) > Math.abs(delta.y)) {
      return delta.x > 0 ? 'right' : 'left';
    } else {
      return delta.y > 0 ? 'down' : 'up';
    }
  }

  private calculateSnapBackVelocity(elasticData: ElasticPhysicsData): number {
    return elasticData.elasticProgress * 0.8; // Higher elastic = faster snap back
  }

  private resetSwipeState(
    zone: AdvancedSwipeZone, 
    startPosition: { x: number; y: number } | null, 
    isSwipeActive: boolean
  ): void {
    // Reset internal state variables in the calling context
  }

  private initializePhysicsEngine(): void {
    // Initialize any physics-related systems
    // This could include setting up RAF-based physics updates if needed
  }

  /**
   * Clean up swipe zone
   */
  unregisterAdvancedSwipeZone(id: string): void {
    const zone = this.swipeZones.get(id);
    if (zone) {
      // Clean up visual elements
      zone.element.classList.remove(
        'advanced-swipe-zone', 
        'soul-swipe-active',
        `energy-${zone.config.connectionEnergy}`,
        `theme-${zone.config.soulTheme}`
      );
      
      // Remove action indicators
      zone.element.querySelectorAll('.swipe-action-indicator').forEach(indicator => {
        indicator.remove();
      });
      
      this.swipeZones.delete(id);
    }
  }

  /**
   * Get current swipe zones (for debugging/monitoring)
   */
  getActiveZones(): AdvancedSwipeZone[] {
    return Array.from(this.swipeZones.values()).filter(zone => zone.isActive);
  }
}

// Supporting interfaces
interface AdvancedSwipeZone {
  id: string;
  element: HTMLElement;
  config: AdvancedSwipeConfig;
  actions: Map<string, SwipeAction>;
  isActive: boolean;
  currentTransform: { x: number; y: number };
  isAnimating: boolean;
}

interface ElasticPhysicsData {
  distance: number;
  elasticProgress: number;
  resistance: number;
  shouldTrigger: boolean;
}