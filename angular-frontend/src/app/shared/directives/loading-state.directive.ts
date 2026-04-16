import {
  Directive,
  Input,
  OnInit,
  OnDestroy,
  TemplateRef,
  ViewContainerRef,
  ComponentRef,
  EmbeddedViewRef
} from '@angular/core';
import { Subscription } from 'rxjs';
import { LoadingStateService } from '../../core/services/loading-state.service';
import { SkeletonLoaderComponent } from '../components/skeleton-loader/skeleton-loader.component';

@Directive({
  selector: '[appLoadingState]',
  standalone: true
})
export class LoadingStateDirective implements OnInit, OnDestroy {
  @Input() appLoadingState!: string;
  @Input() appLoadingStateSkeleton: 'card' | 'text' | 'button' | 'avatar' | 'list-item' | 'soul-orb' | 'compatibility-radar' | 'profile-card' | 'message' = 'card';
  @Input() appLoadingStateSkeletonCount: number = 1;
  @Input() appLoadingStateSkeletonSize: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'md';
  @Input() appLoadingStateCustomMessage?: string;
  @Input() appLoadingStateShowMessage: boolean = true;

  private subscription?: Subscription;
  private contentViewRef?: EmbeddedViewRef<unknown>;
  private skeletonComponents: ComponentRef<SkeletonLoaderComponent>[] = [];
  private messageElement?: HTMLElement;

  constructor(
    private templateRef: TemplateRef<unknown>,
    private viewContainer: ViewContainerRef,
    private loadingStateService: LoadingStateService
  ) {}

  ngOnInit() {
    if (!this.appLoadingState) {
      console.warn('LoadingStateDirective: appLoadingState is required');
      return;
    }

    this.subscription = this.loadingStateService.getLoadingState$(this.appLoadingState)
      .subscribe(loadingState => {
        this.updateView(loadingState?.isLoading ?? false, loadingState?.message);
      });
  }

  ngOnDestroy() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
    this.clearView();
  }

  private updateView(isLoading: boolean, message?: string): void {
    if (isLoading) {
      this.showSkeletonView(message);
    } else {
      this.showContentView();
    }
  }

  private showSkeletonView(message?: string): void {
    this.clearView();

    // Create skeleton loaders
    for (let i = 0; i < this.appLoadingStateSkeletonCount; i++) {
      const skeletonComponentRef = this.viewContainer.createComponent(SkeletonLoaderComponent);
      skeletonComponentRef.instance.type = this.appLoadingStateSkeleton;
      skeletonComponentRef.instance.size = this.appLoadingStateSkeletonSize;
      skeletonComponentRef.instance.ariaLabel = `Loading ${this.appLoadingStateSkeleton} ${i + 1}`;

      this.skeletonComponents.push(skeletonComponentRef);

      // Add spacing between multiple skeletons
      if (i < this.appLoadingStateSkeletonCount - 1) {
        this.addSpacingElement();
      }
    }

    // Show loading message if enabled
    if (this.appLoadingStateShowMessage && (message || this.appLoadingStateCustomMessage)) {
      this.showLoadingMessage(message || this.appLoadingStateCustomMessage!);
    }
  }

  private showContentView(): void {
    this.clearView();
    this.contentViewRef = this.viewContainer.createEmbeddedView(this.templateRef);
  }

  private showLoadingMessage(message: string): void {
    this.messageElement = document.createElement('div');
    this.messageElement.className = 'loading-message';
    this.messageElement.textContent = message;
    this.messageElement.style.cssText = `
      text-align: center;
      padding: 1rem;
      color: var(--text-secondary, #6b7280);
      font-size: 0.9rem;
      font-style: italic;
      animation: message-fade 1.5s ease-in-out infinite alternate;
    `;

    // Add fade animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes message-fade {
        from { opacity: 0.6; }
        to { opacity: 1; }
      }
    `;
    document.head.appendChild(style);

    this.viewContainer.element.nativeElement.parentNode?.appendChild(this.messageElement);
  }

  private addSpacingElement(): void {
    const spacingElement = document.createElement('div');
    spacingElement.style.height = '0.5rem';
    this.viewContainer.element.nativeElement.parentNode?.appendChild(spacingElement);
  }

  private clearView(): void {
    // Clear content view
    if (this.contentViewRef) {
      this.contentViewRef.destroy();
      this.contentViewRef = undefined;
    }

    // Clear skeleton components
    this.skeletonComponents.forEach(componentRef => {
      componentRef.destroy();
    });
    this.skeletonComponents = [];

    // Clear message element
    if (this.messageElement) {
      this.messageElement.remove();
      this.messageElement = undefined;
    }

    // Clear view container
    this.viewContainer.clear();
  }
}
