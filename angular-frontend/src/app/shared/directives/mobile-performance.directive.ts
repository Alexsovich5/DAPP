import { 
  Directive, 
  ElementRef, 
  Input, 
  OnInit, 
  OnDestroy,
  ChangeDetectorRef,
  NgZone,
  AfterViewInit
} from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil, throttleTime, debounceTime } from 'rxjs/operators';
import { MobilePerformanceService, LazyLoadConfig, ImageOptimizationConfig } from '../services/mobile-performance.service';
import { MobileFeaturesService } from '../services/mobile-features.service';

@Directive({
  selector: '[appMobilePerformance]',
  standalone: true
})
export class MobilePerformanceDirective implements OnInit, OnDestroy, AfterViewInit {
  @Input() enableLazyLoading: boolean = true;
  @Input() enableImageOptimization: boolean = true;
  @Input() enableVirtualScrolling: boolean = false;
  @Input() optimizationLevel: 'low' | 'medium' | 'high' = 'medium';
  @Input() lazyLoadConfig?: Partial<LazyLoadConfig>;
  @Input() imageConfig?: Partial<ImageOptimizationConfig>;

  private destroy$ = new Subject<void>();
  private resizeObserver?: ResizeObserver;
  private mutationObserver?: MutationObserver;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private performanceService: MobilePerformanceService,
    private mobileFeatures: MobileFeaturesService,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    this.applyPerformanceOptimizations();
  }

  ngAfterViewInit(): void {
    this.setupOptimizations();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.cleanupObservers();
  }

  private applyPerformanceOptimizations(): void {
    const element = this.elementRef.nativeElement;
    const deviceInfo = this.mobileFeatures.getDeviceInfo();
    const config = this.performanceService.getMobileOptimizedConfig();

    // Apply CSS optimizations based on device capabilities
    if (deviceInfo.isLowEndDevice) {
      element.classList.add('low-end-device');
    }

    // Set animation intensity
    element.style.setProperty('--animation-intensity', config.animationIntensity);

    // Apply optimization level
    element.classList.add(`optimization-${this.optimizationLevel}`);

    // Enable hardware acceleration for better performance
    if (config.enableAdvancedFeatures) {
      element.style.transform = 'translateZ(0)';
      element.style.willChange = 'transform, opacity';
    }
  }

  private setupOptimizations(): void {
    this.ngZone.runOutsideAngular(() => {
      if (this.enableLazyLoading) {
        this.setupLazyLoading();
      }

      if (this.enableImageOptimization) {
        this.setupImageOptimization();
      }

      if (this.enableVirtualScrolling) {
        this.setupVirtualScrolling();
      }

      this.setupPerformanceMonitoring();
    });
  }

  private setupLazyLoading(): void {
    this.performanceService.enableLazyLoading(this.elementRef, this.lazyLoadConfig);

    // Watch for dynamically added images
    this.mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const element = node as Element;
            const lazyImages = element.querySelectorAll('img[data-src]');
            
            if (lazyImages.length > 0) {
              this.performanceService.enableLazyLoading(this.elementRef, this.lazyLoadConfig);
            }
          }
        });
      });
    });

    this.mutationObserver.observe(this.elementRef.nativeElement, {
      childList: true,
      subtree: true
    });
  }

  private setupImageOptimization(): void {
    const images = this.elementRef.nativeElement.querySelectorAll('img:not([data-src])');
    
    images.forEach(async (img) => {
      const imgElement = img as HTMLImageElement;
      
      if (imgElement.src && !imgElement.classList.contains('optimized')) {
        try {
          const optimizedSrc = await this.performanceService.optimizeImage(
            imgElement,
            this.imageConfig
          );
          
          if (optimizedSrc !== imgElement.src) {
            imgElement.src = optimizedSrc;
            imgElement.classList.add('optimized');
          }
        } catch (error) {
          console.warn('Failed to optimize image:', error);
        }
      }
    });
  }

  private setupVirtualScrolling(): void {
    // Implementation would depend on the specific scrolling library used
    // This is a placeholder for virtual scrolling setup
    const config = this.performanceService.optimizeComponentRendering();
    
    if (config.shouldVirtualize) {
      this.elementRef.nativeElement.classList.add('virtual-scroll-enabled');
      this.elementRef.nativeElement.style.setProperty('--batch-size', config.batchSize.toString());
    }
  }

  private setupPerformanceMonitoring(): void {
    // Monitor scroll performance
    const scrollContainer = this.findScrollContainer();
    
    if (scrollContainer) {
      this.monitorScrollPerformance(scrollContainer);
    }

    // Monitor rendering performance
    this.monitorRenderingPerformance();

    // Monitor memory usage
    this.performanceService.performance$
      .pipe(
        takeUntil(this.destroy$),
        throttleTime(5000)
      )
      .subscribe(metrics => {
        if (metrics.memoryUsage > 0.8) {
          this.applyMemoryOptimizations();
        }
        
        if (metrics.frameRate < 30) {
          this.applyFrameRateOptimizations();
        }
      });
  }

  private findScrollContainer(): Element | null {
    let parent = this.elementRef.nativeElement.parentElement;
    
    while (parent) {
      const style = window.getComputedStyle(parent);
      if (style.overflow === 'auto' || style.overflow === 'scroll' || 
          style.overflowY === 'auto' || style.overflowY === 'scroll') {
        return parent;
      }
      parent = parent.parentElement;
    }
    
    return window.document.documentElement;
  }

  private monitorScrollPerformance(scrollContainer: Element): void {
    let isScrolling = false;
    let scrollTimer: number;

    const handleScroll = () => {
      if (!isScrolling) {
        isScrolling = true;
        this.elementRef.nativeElement.classList.add('scrolling');
      }

      clearTimeout(scrollTimer);
      scrollTimer = window.setTimeout(() => {
        isScrolling = false;
        this.elementRef.nativeElement.classList.remove('scrolling');
      }, 150);
    };

    scrollContainer.addEventListener('scroll', handleScroll, { passive: true });

    // Cleanup
    this.destroy$.subscribe(() => {
      scrollContainer.removeEventListener('scroll', handleScroll);
      clearTimeout(scrollTimer);
    });
  }

  private monitorRenderingPerformance(): void {
    // Use ResizeObserver to monitor layout changes
    this.resizeObserver = new ResizeObserver((entries) => {
      entries.forEach((entry) => {
        // Optimize layout if element is getting too complex
        const element = entry.target as HTMLElement;
        const childCount = element.children.length;
        
        if (childCount > 100) {
          element.classList.add('complex-layout');
        }
      });
    });

    this.resizeObserver.observe(this.elementRef.nativeElement);
  }

  private applyMemoryOptimizations(): void {
    const element = this.elementRef.nativeElement;
    
    // Reduce image quality for existing images
    const images = element.querySelectorAll('img');
    images.forEach((img) => {
      if (!img.classList.contains('memory-optimized')) {
        img.style.imageRendering = 'auto';
        img.classList.add('memory-optimized');
      }
    });

    // Simplify animations
    element.classList.add('memory-constrained');

    // Trigger change detection to update component
    this.ngZone.run(() => {
      this.cdr.markForCheck();
    });
  }

  private applyFrameRateOptimizations(): void {
    const element = this.elementRef.nativeElement;
    
    // Disable non-essential animations
    element.classList.add('low-framerate');
    
    // Reduce animation complexity
    element.style.setProperty('--animation-complexity', 'simple');
    
    // Use transform instead of changing layout properties
    const animatedElements = element.querySelectorAll('.animated');
    animatedElements.forEach((el) => {
      (el as HTMLElement).style.willChange = 'transform';
    });

    this.ngZone.run(() => {
      this.cdr.markForCheck();
    });
  }

  private cleanupObservers(): void {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    
    if (this.mutationObserver) {
      this.mutationObserver.disconnect();
    }
  }
}

// Specialized directive for profile cards optimization
@Directive({
  selector: '[appProfileCardPerformance]',
  standalone: true
})
export class ProfileCardPerformanceDirective implements OnInit, OnDestroy, AfterViewInit {
  @Input() profileData: any;
  @Input() isVisible: boolean = true;

  private destroy$ = new Subject<void>();

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private performanceService: MobilePerformanceService,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    this.optimizeForProfileCard();
  }

  ngAfterViewInit(): void {
    this.setupProfileOptimizations();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private optimizeForProfileCard(): void {
    const element = this.elementRef.nativeElement;
    const config = this.performanceService.getMobileOptimizedConfig();

    // Apply profile-specific optimizations
    element.classList.add('profile-card-optimized');

    // Preload only essential images
    if (this.profileData?.photos && config.enableAdvancedFeatures) {
      this.preloadCriticalPhotos();
    }

    // Enable GPU acceleration for card interactions
    element.style.transform = 'translate3d(0, 0, 0)';
    element.style.willChange = 'transform, opacity';
  }

  private setupProfileOptimizations(): void {
    this.ngZone.runOutsideAngular(() => {
      // Optimize images for profile display
      this.optimizeProfileImages();

      // Setup performance-aware gesture handling
      this.setupPerformanceAwareGestures();

      // Monitor visibility for performance adjustments
      this.monitorVisibility();
    });
  }

  private async preloadCriticalPhotos(): Promise<void> {
    if (!this.profileData?.photos) return;

    const primaryPhoto = this.profileData.photos[0];
    if (primaryPhoto) {
      try {
        await this.performanceService.optimizeImage(primaryPhoto.url, {
          quality: 0.8,
          maxWidth: 400,
          maxHeight: 600,
          format: 'webp',
          lazy: false,
          placeholder: false
        });
      } catch (error) {
        console.warn('Failed to preload primary photo:', error);
      }
    }
  }

  private optimizeProfileImages(): void {
    const images = this.elementRef.nativeElement.querySelectorAll('img');
    const config = this.performanceService.getMobileOptimizedConfig();

    images.forEach(async (img) => {
      try {
        const optimizedSrc = await this.performanceService.optimizeImage(img, {
          quality: config.imageQuality,
          maxWidth: 400,
          maxHeight: 600,
          format: 'webp',
          lazy: !this.isVisible,
          placeholder: true
        });

        if (optimizedSrc !== img.src) {
          img.src = optimizedSrc;
        }
      } catch (error) {
        console.warn('Failed to optimize profile image:', error);
      }
    });
  }

  private setupPerformanceAwareGestures(): void {
    const element = this.elementRef.nativeElement;

    // Throttle gesture events to improve performance
    let gestureTimeout: number;
    
    const handleTouchStart = () => {
      element.classList.add('gesture-active');
    };

    const handleTouchEnd = () => {
      clearTimeout(gestureTimeout);
      gestureTimeout = window.setTimeout(() => {
        element.classList.remove('gesture-active');
      }, 100);
    };

    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });

    this.destroy$.subscribe(() => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchend', handleTouchEnd);
      clearTimeout(gestureTimeout);
    });
  }

  private monitorVisibility(): void {
    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const element = entry.target as HTMLElement;
          
          if (entry.isIntersecting) {
            element.classList.add('visible');
            element.classList.remove('hidden');
          } else {
            element.classList.add('hidden');
            element.classList.remove('visible');
            
            // Pause non-critical animations when not visible
            element.style.animationPlayState = 'paused';
          }
        });
      },
      { threshold: 0.1 }
    );

    intersectionObserver.observe(this.elementRef.nativeElement);

    this.destroy$.subscribe(() => {
      intersectionObserver.disconnect();
    });
  }
}

// Directive for message list performance optimization
@Directive({
  selector: '[appMessageListPerformance]',
  standalone: true
})
export class MessageListPerformanceDirective implements OnInit, OnDestroy {
  @Input() messageCount: number = 0;

  private destroy$ = new Subject<void>();
  private virtualScrollEnabled = false;

  constructor(
    private elementRef: ElementRef<HTMLElement>,
    private performanceService: MobilePerformanceService,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    this.optimizeMessageList();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private optimizeMessageList(): void {
    const config = this.performanceService.optimizeComponentRendering();
    
    // Enable virtual scrolling for large message lists
    if (this.messageCount > 50 || config.shouldVirtualize) {
      this.enableVirtualScrolling();
    }

    // Optimize message rendering
    this.optimizeMessageRendering(config);
  }

  private enableVirtualScrolling(): void {
    const element = this.elementRef.nativeElement;
    element.classList.add('virtual-scroll');
    this.virtualScrollEnabled = true;

    // Setup intersection observer for visible messages
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const messageElement = entry.target as HTMLElement;
          
          if (entry.isIntersecting) {
            messageElement.classList.add('visible');
          } else {
            messageElement.classList.remove('visible');
          }
        });
      },
      { threshold: 0 }
    );

    // Observe message elements
    this.ngZone.runOutsideAngular(() => {
      const messages = element.querySelectorAll('.message-item');
      messages.forEach(message => observer.observe(message));
    });

    this.destroy$.subscribe(() => {
      observer.disconnect();
    });
  }

  private optimizeMessageRendering(config: any): void {
    const element = this.elementRef.nativeElement;
    
    // Apply batching for message updates
    element.style.setProperty('--batch-size', config.batchSize.toString());
    
    // Use transform for message animations instead of layout changes
    element.classList.add('optimized-animations');
    
    // Debounce scroll events
    let scrollTimeout: number;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = window.setTimeout(() => {
        // Process scroll end
      }, config.debounceTime);
    };

    element.addEventListener('scroll', handleScroll, { passive: true });
    
    this.destroy$.subscribe(() => {
      element.removeEventListener('scroll', handleScroll);
      clearTimeout(scrollTimeout);
    });
  }
}