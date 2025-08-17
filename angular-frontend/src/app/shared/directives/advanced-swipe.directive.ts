/**
 * Advanced Swipe Directive - Phase 3 Mobile UX Enhancement
 * Provides elastic swipe gestures with soul-themed haptic feedback
 */
import { Directive, ElementRef, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { AdvancedSwipeService, SwipeAction, AdvancedSwipeConfig, ElasticSwipeEvent } from '../../core/services/advanced-swipe.service';

@Directive({
  selector: '[appAdvancedSwipe]',
  standalone: true
})
export class AdvancedSwipeDirective implements OnInit, OnDestroy {
  @Input() swipeConfig: Partial<AdvancedSwipeConfig> = {};
  @Input() swipeActions: SwipeAction[] = [];
  @Input() connectionEnergy: 'low' | 'medium' | 'high' | 'soulmate' = 'medium';
  @Input() soulTheme: 'discovery' | 'revelation' | 'connection' | 'energy' = 'discovery';
  @Input() compatibilityScore?: number;
  @Input() swipeEnabled = true;

  @Output() swipeStart = new EventEmitter<ElasticSwipeEvent>();
  @Output() swipeMove = new EventEmitter<ElasticSwipeEvent>();
  @Output() swipeEnd = new EventEmitter<ElasticSwipeEvent>();
  @Output() actionTriggered = new EventEmitter<{ action: SwipeAction; event: ElasticSwipeEvent }>();

  private swipeZoneId: string;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private advancedSwipeService: AdvancedSwipeService
  ) {
    this.swipeZoneId = `advanced-swipe-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }

  ngOnInit(): void {
    this.setupAdvancedSwipe();
  }

  ngOnDestroy(): void {
    this.advancedSwipeService.unregisterAdvancedSwipeZone(this.swipeZoneId);
  }

  private setupAdvancedSwipe(): void {
    if (!this.swipeEnabled) return;

    // Merge configuration with directive inputs
    const config: Partial<AdvancedSwipeConfig> = {
      ...this.swipeConfig,
      connectionEnergy: this.connectionEnergy,
      soulTheme: this.soulTheme,
      compatibilityScore: this.compatibilityScore
    };

    // Process actions and add event handlers
    const processedActions = this.swipeActions.map(action => ({
      ...action,
      onActivate: (event: ElasticSwipeEvent) => {
        this.actionTriggered.emit({ action, event });
        action.onActivate(event);
      }
    }));

    // Register with advanced swipe service
    this.advancedSwipeService.registerAdvancedSwipeZone(
      this.swipeZoneId,
      this.elementRef.nativeElement,
      processedActions,
      config
    );

    // Subscribe to swipe events for directive outputs
    this.subscribeToSwipeEvents();
  }

  private subscribeToSwipeEvents(): void {
    // Listen to current swipe data from the service
    this.advancedSwipeService.currentSwipe$.subscribe(swipeEvent => {
      if (!swipeEvent) return;

      switch (swipeEvent.phase) {
        case 'start':
          this.swipeStart.emit(swipeEvent);
          break;
        case 'move':
          this.swipeMove.emit(swipeEvent);
          break;
        case 'end':
          this.swipeEnd.emit(swipeEvent);
          break;
      }
    });
  }

  /**
   * Update connection energy dynamically
   */
  updateConnectionEnergy(energy: 'low' | 'medium' | 'high' | 'soulmate'): void {
    this.connectionEnergy = energy;
    this.advancedSwipeService.setConnectionEnergy(this.swipeZoneId, energy);
  }

  /**
   * Update available actions dynamically
   */
  updateActions(actions: SwipeAction[]): void {
    this.swipeActions = actions;
    const processedActions = actions.map(action => ({
      ...action,
      onActivate: (event: ElasticSwipeEvent) => {
        this.actionTriggered.emit({ action, event });
        action.onActivate(event);
      }
    }));
    
    this.advancedSwipeService.updateSwipeActions(this.swipeZoneId, processedActions);
  }

  /**
   * Enable or disable swipe functionality
   */
  setSwipeEnabled(enabled: boolean): void {
    this.swipeEnabled = enabled;
    
    if (enabled) {
      this.setupAdvancedSwipe();
    } else {
      this.advancedSwipeService.unregisterAdvancedSwipeZone(this.swipeZoneId);
    }
  }
}