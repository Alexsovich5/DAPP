import { 
  Directive, 
  ElementRef, 
  EventEmitter, 
  Input, 
  OnDestroy, 
  OnInit, 
  Output 
} from '@angular/core';
import { SwipeGestureService, SwipeEvent, SwipeConfig } from '../../core/services/swipe-gesture.service';

@Directive({
  selector: '[appSwipe]',
  standalone: true
})
export class SwipeDirective implements OnInit, OnDestroy {
  @Input() swipeConfig: Partial<SwipeConfig> = {};
  @Input() swipeEnabled = true;
  @Input() swipeZoneId?: string;

  @Output() swipe = new EventEmitter<SwipeEvent>();
  @Output() swipeLeft = new EventEmitter<SwipeEvent>();
  @Output() swipeRight = new EventEmitter<SwipeEvent>();
  @Output() swipeUp = new EventEmitter<SwipeEvent>();
  @Output() swipeDown = new EventEmitter<SwipeEvent>();

  private zoneId: string;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private swipeGestureService: SwipeGestureService
  ) {
    this.zoneId = this.swipeZoneId || `swipe-directive-${Date.now()}-${Math.random()}`;
  }

  ngOnInit(): void {
    this.setupSwipeZone();
  }

  ngOnDestroy(): void {
    this.swipeGestureService.unregisterSwipeZone(this.zoneId);
  }

  private setupSwipeZone(): void {
    const element = this.elementRef.nativeElement;
    
    // Add swipe styling
    element.style.touchAction = 'none';
    element.style.userSelect = 'none';
    element.classList.add('swipe-enabled');

    this.swipeGestureService.registerSwipeZone(
      this.zoneId,
      element,
      (event: SwipeEvent) => this.handleSwipe(event),
      this.swipeConfig
    );
  }

  private handleSwipe(event: SwipeEvent): void {
    if (!this.swipeEnabled) return;

    // Emit general swipe event
    this.swipe.emit(event);

    // Emit direction-specific events
    switch (event.direction) {
      case 'left':
        this.swipeLeft.emit(event);
        break;
      case 'right':
        this.swipeRight.emit(event);
        break;
      case 'up':
        this.swipeUp.emit(event);
        break;
      case 'down':
        this.swipeDown.emit(event);
        break;
    }
  }

  /**
   * Enable or disable swipe detection
   */
  setSwipeEnabled(enabled: boolean): void {
    this.swipeEnabled = enabled;
    this.swipeGestureService.toggleSwipeZone(this.zoneId, enabled);
  }

  /**
   * Update swipe configuration
   */
  updateConfig(config: Partial<SwipeConfig>): void {
    this.swipeConfig = { ...this.swipeConfig, ...config };
    this.swipeGestureService.updateSwipeZoneConfig(this.zoneId, this.swipeConfig);
  }
}