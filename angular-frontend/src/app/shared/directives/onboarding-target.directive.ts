import { Directive, ElementRef, Input, OnInit, OnDestroy } from '@angular/core';
import { OnboardingService } from '@core/services/onboarding.service';
import { Subscription } from 'rxjs';

@Directive({
  selector: '[appOnboardingTarget]',
  standalone: true
})
export class OnboardingTargetDirective implements OnInit, OnDestroy {
  @Input('appOnboardingTarget') targetId?: string;
  @Input() onboardingTour?: string;
  @Input() onboardingStep?: string;
  @Input() onboardingHighlight: boolean = true;
  @Input() onboardingAutoTrigger: boolean = false;

  private subscription = new Subscription();
  private isHighlighted = false;

  constructor(
    private elementRef: ElementRef,
    private onboardingService: OnboardingService
  ) {}

  ngOnInit(): void {
    // Add data attribute for easier targeting
    if (this.targetId) {
      this.elementRef.nativeElement.setAttribute('data-onboarding-target', this.targetId);
    }

    // Subscribe to active step changes
    this.subscription.add(
      this.onboardingService.activeStep$.subscribe(step => {
        this.handleStepChange(step);
      })
    );

    // Auto-trigger tour if specified
    if (this.onboardingAutoTrigger && this.onboardingTour) {
      // Check if element is visible and trigger tour
      this.checkVisibilityAndTrigger();
    }
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
    this.removeHighlight();
  }

  /**
   * Handle active step changes
   */
  private handleStepChange(step: any): void {
    if (!step || !this.targetId) return;

    // Check if this element is the target for the current step
    const isTargetElement = step.targetSelector?.includes(this.targetId) ||
                           step.targetSelector?.includes(`[data-onboarding-target="${this.targetId}"]`);

    if (isTargetElement && this.onboardingHighlight) {
      this.addHighlight();
    } else {
      this.removeHighlight();
    }
  }

  /**
   * Add highlight styling to element
   */
  private addHighlight(): void {
    if (this.isHighlighted) return;

    const element = this.elementRef.nativeElement;
    element.classList.add('onboarding-highlight');
    
    // Add custom styling
    element.style.position = 'relative';
    element.style.zIndex = '9990';
    element.style.outline = '3px solid var(--primary-color)';
    element.style.outlineOffset = '4px';
    element.style.borderRadius = '8px';
    element.style.transition = 'all 0.3s ease';
    element.style.boxShadow = '0 0 20px rgba(255, 107, 157, 0.4)';

    this.isHighlighted = true;

    // Scroll element into view if needed
    this.scrollIntoViewIfNeeded();
  }

  /**
   * Remove highlight styling from element
   */
  private removeHighlight(): void {
    if (!this.isHighlighted) return;

    const element = this.elementRef.nativeElement;
    element.classList.remove('onboarding-highlight');
    
    // Remove custom styling
    element.style.outline = '';
    element.style.outlineOffset = '';
    element.style.borderRadius = '';
    element.style.transition = '';
    element.style.boxShadow = '';
    element.style.zIndex = '';

    this.isHighlighted = false;
  }

  /**
   * Scroll element into view if needed
   */
  private scrollIntoViewIfNeeded(): void {
    const element = this.elementRef.nativeElement;
    const rect = element.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    // Check if element is outside viewport
    const isOutsideViewport = rect.bottom < 0 || 
                             rect.top > viewportHeight || 
                             rect.right < 0 || 
                             rect.left > viewportWidth;

    if (isOutsideViewport) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'center'
      });
    }
  }

  /**
   * Check if element is visible and trigger tour
   */
  private checkVisibilityAndTrigger(): void {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && this.onboardingTour) {
          // Element is visible, check if tour should be triggered
          if (!this.onboardingService.isTourCompleted(this.onboardingTour)) {
            setTimeout(() => {
              this.onboardingService.startTour(this.onboardingTour!);
            }, 1000); // Delay to ensure user has time to see the page
          }
          observer.disconnect();
        }
      });
    }, {
      threshold: 0.5 // Element must be at least 50% visible
    });

    observer.observe(this.elementRef.nativeElement);
  }

  /**
   * Manually trigger tour for this element
   */
  triggerTour(): void {
    if (this.onboardingTour) {
      this.onboardingService.startTour(this.onboardingTour);
    }
  }

  /**
   * Check if this element is currently highlighted
   */
  isCurrentlyHighlighted(): boolean {
    return this.isHighlighted;
  }
}