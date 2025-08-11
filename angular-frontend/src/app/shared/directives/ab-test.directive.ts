import { 
  Directive, 
  Input, 
  TemplateRef, 
  ViewContainerRef, 
  OnInit, 
  OnDestroy 
} from '@angular/core';
import { ABTestingService } from '../../core/services/ab-testing.service';

/**
 * A/B Test Directive for conditional rendering based on test variants
 * 
 * Usage examples:
 * 
 * <!-- Show content only for specific variant -->
 * <div *abTest="'discovery_card_layout'; variant: 'horizontal_compact'">
 *   Horizontal layout content
 * </div>
 * 
 * <!-- Show content for multiple variants -->
 * <div *abTest="'discovery_card_layout'; variants: ['horizontal_compact', 'compatibility_focus']">
 *   Enhanced layout content
 * </div>
 * 
 * <!-- Show content when NOT in specific variant (control) -->
 * <div *abTest="'discovery_card_layout'; exclude: 'control'">
 *   Non-control content
 * </div>
 * 
 * <!-- Track events when content is shown -->
 * <button *abTest="'discovery_card_layout'; variant: 'horizontal_compact'; trackView: 'button_shown'"
 *         (click)="onButtonClick()">
 *   Enhanced Button
 * </button>
 */
@Directive({
  selector: '[abTest]',
  standalone: true
})
export class ABTestDirective implements OnInit, OnDestroy {
  @Input() abTest!: string; // Test ID
  @Input() abTestVariant?: string; // Single variant to show for
  @Input() abTestVariants?: string[]; // Multiple variants to show for
  @Input() abTestExclude?: string | string[]; // Variants to exclude
  @Input() abTestTrackView?: string; // Event to track when content is shown

  private hasView = false;

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private abTestingService: ABTestingService
  ) {}

  ngOnInit(): void {
    this.updateView();
  }

  ngOnDestroy(): void {
    this.clearView();
  }

  private updateView(): void {
    const shouldShow = this.shouldShowContent();

    if (shouldShow && !this.hasView) {
      this.showContent();
    } else if (!shouldShow && this.hasView) {
      this.clearView();
    }
  }

  private shouldShowContent(): boolean {
    const currentVariant = this.abTestingService.getVariant(this.abTest);
    
    if (!currentVariant) {
      // If no test is active or user not assigned, show control content only
      return this.isControlContent();
    }

    // Check specific variant
    if (this.abTestVariant) {
      return currentVariant.id === this.abTestVariant;
    }

    // Check multiple variants
    if (this.abTestVariants && this.abTestVariants.length > 0) {
      return this.abTestVariants.includes(currentVariant.id);
    }

    // Check exclusions
    if (this.abTestExclude) {
      const excludeList = Array.isArray(this.abTestExclude) 
        ? this.abTestExclude 
        : [this.abTestExclude];
      return !excludeList.includes(currentVariant.id);
    }

    // Default: show for all variants
    return true;
  }

  private isControlContent(): boolean {
    // Show content if it's marked for control variant
    return this.abTestVariant === 'control' || 
           (this.abTestVariants?.includes('control') ?? false);
  }

  private showContent(): void {
    this.viewContainer.createEmbeddedView(this.templateRef);
    this.hasView = true;

    // Track view event if specified
    if (this.abTestTrackView) {
      this.abTestingService.trackEvent(this.abTest, this.abTestTrackView);
    }
  }

  private clearView(): void {
    this.viewContainer.clear();
    this.hasView = false;
  }
}

/**
 * A/B Test Configuration Directive for applying CSS classes or styles
 * 
 * Usage examples:
 * 
 * <!-- Apply CSS classes based on variant -->
 * <div [abTestClass]="'discovery_card_layout'" 
 *      [classMap]="{
 *        'horizontal-layout': 'horizontal_compact',
 *        'compatibility-first': 'compatibility_focus'
 *      }">
 *   Discovery Card
 * </div>
 * 
 * <!-- Apply inline styles based on variant -->
 * <div [abTestStyle]="'discovery_card_layout'"
 *      [styleMap]="{
 *        'horizontal_compact': { 'flex-direction': 'row' },
 *        'compatibility_focus': { 'font-size': '1.2rem' }
 *      }">
 *   Content
 * </div>
 */
@Directive({
  selector: '[abTestClass]',
  standalone: true
})
export class ABTestClassDirective implements OnInit {
  @Input() abTestClass!: string; // Test ID
  @Input() classMap!: Record<string, string>; // Map of CSS class to variant ID

  constructor(
    private abTestingService: ABTestingService
  ) {}

  ngOnInit(): void {
    this.applyClasses();
  }

  private applyClasses(): void {
    const currentVariant = this.abTestingService.getVariant(this.abTestClass);
    
    if (!currentVariant || !this.classMap) {
      return;
    }

    // Find matching class for current variant
    const cssClass = this.classMap[currentVariant.id];
    if (cssClass) {
      // Note: In a real implementation, you'd apply the class to the host element
      // This is a simplified version for demonstration
      console.log(`Apply CSS class "${cssClass}" for variant "${currentVariant.id}"`);
    }
  }
}

/**
 * A/B Test Configuration Pipe for getting variant configurations in templates
 * 
 * Usage examples:
 * 
 * <!-- Get specific config value -->
 * <div [style.flex-direction]="'discovery_card_layout' | abTestConfig:'layout'">
 *   Content
 * </div>
 * 
 * <!-- Get entire config object -->
 * <ng-container *ngLet="'discovery_card_layout' | abTestConfig as config">
 *   <div [class.horizontal]="config?.layout === 'horizontal'">
 *     Content
 *   </div>
 * </ng-container>
 */
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'abTestConfig',
  standalone: true
})
export class ABTestConfigPipe implements PipeTransform {
  constructor(private abTestingService: ABTestingService) {}

  transform(testId: string, configKey?: string): any {
    return this.abTestingService.getVariantConfig(testId, configKey);
  }
}