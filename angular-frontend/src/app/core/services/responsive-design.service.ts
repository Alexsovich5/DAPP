/**
 * Responsive Design Service - Phase 3 Mobile-First Implementation
 * Provides responsive breakpoints and device detection for optimal UX
 */
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent } from 'rxjs';
import { map, throttleTime, distinctUntilChanged, startWith } from 'rxjs/operators';

export interface ViewportInfo {
  width: number;
  height: number;
  breakpoint: Breakpoint;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLandscape: boolean;
  devicePixelRatio: number;
  supportsTouchscreen: boolean;
  supportsHover: boolean;
}

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';

export interface BreakpointConfig {
  xs: number;  // Extra small devices (phones)
  sm: number;  // Small devices (large phones)
  md: number;  // Medium devices (tablets)
  lg: number;  // Large devices (desktops)
  xl: number;  // Extra large devices
  xxl: number; // Extra extra large devices
}

export interface ResponsiveConfig {
  // Grid system
  maxColumns: number;
  gutterSize: string;
  containerMaxWidth: string;
  
  // Typography
  baseFontSize: string;
  lineHeight: number;
  
  // Spacing
  baseSpacing: string;
  componentPadding: string;
  
  // Touch targets
  minTouchTarget: string;
  touchPadding: string;
  
  // Animations
  reducedMotion: boolean;
  animationDuration: string;
}

@Injectable({
  providedIn: 'root'
})
export class ResponsiveDesignService {
  private readonly breakpoints: BreakpointConfig = {
    xs: 0,     // 0px and up
    sm: 576,   // 576px and up
    md: 768,   // 768px and up
    lg: 992,   // 992px and up
    xl: 1200,  // 1200px and up
    xxl: 1400  // 1400px and up
  };

  private viewportInfo$ = new BehaviorSubject<ViewportInfo>(this.getInitialViewportInfo());
  private currentConfig$ = new BehaviorSubject<ResponsiveConfig>(this.getConfigForBreakpoint('md'));

  public viewport$ = this.viewportInfo$.asObservable();
  public config$ = this.currentConfig$.asObservable();

  constructor() {
    this.initializeViewportTracking();
    this.detectDeviceCapabilities();
  }

  private initializeViewportTracking(): void {
    fromEvent(window, 'resize').pipe(
      throttleTime(100),
      map(() => this.getCurrentViewportInfo()),
      distinctUntilChanged((prev, curr) => 
        prev.width === curr.width && 
        prev.height === curr.height && 
        prev.breakpoint === curr.breakpoint
      ),
      startWith(this.getCurrentViewportInfo())
    ).subscribe(viewportInfo => {
      this.viewportInfo$.next(viewportInfo);
      this.currentConfig$.next(this.getConfigForBreakpoint(viewportInfo.breakpoint));
      this.updateCSSCustomProperties(viewportInfo);
    });

    // Listen for orientation changes
    fromEvent(window, 'orientationchange').pipe(
      // Delay to ensure dimensions are updated
      throttleTime(200)
    ).subscribe(() => {
      setTimeout(() => {
        const viewportInfo = this.getCurrentViewportInfo();
        this.viewportInfo$.next(viewportInfo);
      }, 100);
    });
  }

  private getInitialViewportInfo(): ViewportInfo {
    return this.getCurrentViewportInfo();
  }

  private getCurrentViewportInfo(): ViewportInfo {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const breakpoint = this.getBreakpointForWidth(width);

    return {
      width,
      height,
      breakpoint,
      isMobile: breakpoint === 'xs' || breakpoint === 'sm',
      isTablet: breakpoint === 'md',
      isDesktop: breakpoint === 'lg' || breakpoint === 'xl' || breakpoint === 'xxl',
      isLandscape: width > height,
      devicePixelRatio: window.devicePixelRatio || 1,
      supportsTouchscreen: this.supportsTouchscreen(),
      supportsHover: this.supportsHover()
    };
  }

  private getBreakpointForWidth(width: number): Breakpoint {
    if (width >= this.breakpoints.xxl) return 'xxl';
    if (width >= this.breakpoints.xl) return 'xl';
    if (width >= this.breakpoints.lg) return 'lg';
    if (width >= this.breakpoints.md) return 'md';
    if (width >= this.breakpoints.sm) return 'sm';
    return 'xs';
  }

  private getConfigForBreakpoint(breakpoint: Breakpoint): ResponsiveConfig {
    const configs: Record<Breakpoint, ResponsiveConfig> = {
      xs: {
        maxColumns: 1,
        gutterSize: '1rem',
        containerMaxWidth: '100%',
        baseFontSize: '14px',
        lineHeight: 1.5,
        baseSpacing: '1rem',
        componentPadding: '0.75rem',
        minTouchTarget: '44px',
        touchPadding: '0.5rem',
        reducedMotion: this.prefersReducedMotion(),
        animationDuration: '200ms'
      },
      sm: {
        maxColumns: 2,
        gutterSize: '1.25rem',
        containerMaxWidth: '540px',
        baseFontSize: '15px',
        lineHeight: 1.5,
        baseSpacing: '1.25rem',
        componentPadding: '1rem',
        minTouchTarget: '44px',
        touchPadding: '0.5rem',
        reducedMotion: this.prefersReducedMotion(),
        animationDuration: '250ms'
      },
      md: {
        maxColumns: 3,
        gutterSize: '1.5rem',
        containerMaxWidth: '720px',
        baseFontSize: '16px',
        lineHeight: 1.6,
        baseSpacing: '1.5rem',
        componentPadding: '1.25rem',
        minTouchTarget: '40px',
        touchPadding: '0.5rem',
        reducedMotion: this.prefersReducedMotion(),
        animationDuration: '300ms'
      },
      lg: {
        maxColumns: 4,
        gutterSize: '2rem',
        containerMaxWidth: '960px',
        baseFontSize: '16px',
        lineHeight: 1.6,
        baseSpacing: '2rem',
        componentPadding: '1.5rem',
        minTouchTarget: '32px',
        touchPadding: '0.25rem',
        reducedMotion: this.prefersReducedMotion(),
        animationDuration: '350ms'
      },
      xl: {
        maxColumns: 5,
        gutterSize: '2.5rem',
        containerMaxWidth: '1140px',
        baseFontSize: '17px',
        lineHeight: 1.7,
        baseSpacing: '2.5rem',
        componentPadding: '2rem',
        minTouchTarget: '32px',
        touchPadding: '0.25rem',
        reducedMotion: this.prefersReducedMotion(),
        animationDuration: '400ms'
      },
      xxl: {
        maxColumns: 6,
        gutterSize: '3rem',
        containerMaxWidth: '1320px',
        baseFontSize: '18px',
        lineHeight: 1.8,
        baseSpacing: '3rem',
        componentPadding: '2.5rem',
        minTouchTarget: '32px',
        touchPadding: '0.25rem',
        reducedMotion: this.prefersReducedMotion(),
        animationDuration: '450ms'
      }
    };

    return configs[breakpoint];
  }

  private updateCSSCustomProperties(viewportInfo: ViewportInfo): void {
    const config = this.getConfigForBreakpoint(viewportInfo.breakpoint);
    const root = document.documentElement;

    // Update CSS custom properties
    root.style.setProperty('--viewport-width', `${viewportInfo.width}px`);
    root.style.setProperty('--viewport-height', `${viewportInfo.height}px`);
    root.style.setProperty('--breakpoint', viewportInfo.breakpoint);
    root.style.setProperty('--is-mobile', viewportInfo.isMobile ? '1' : '0');
    root.style.setProperty('--is-tablet', viewportInfo.isTablet ? '1' : '0');
    root.style.setProperty('--is-desktop', viewportInfo.isDesktop ? '1' : '0');
    root.style.setProperty('--device-pixel-ratio', viewportInfo.devicePixelRatio.toString());

    // Update responsive config properties
    root.style.setProperty('--max-columns', config.maxColumns.toString());
    root.style.setProperty('--gutter-size', config.gutterSize);
    root.style.setProperty('--container-max-width', config.containerMaxWidth);
    root.style.setProperty('--base-font-size', config.baseFontSize);
    root.style.setProperty('--line-height', config.lineHeight.toString());
    root.style.setProperty('--base-spacing', config.baseSpacing);
    root.style.setProperty('--component-padding', config.componentPadding);
    root.style.setProperty('--min-touch-target', config.minTouchTarget);
    root.style.setProperty('--touch-padding', config.touchPadding);
    root.style.setProperty('--animation-duration', config.animationDuration);

    // Update body classes for styling hooks
    document.body.className = document.body.className.replace(/\b(xs|sm|md|lg|xl|xxl)\b/g, '');
    document.body.classList.add(viewportInfo.breakpoint);
    
    if (viewportInfo.isMobile) document.body.classList.add('mobile');
    else document.body.classList.remove('mobile');
    
    if (viewportInfo.isTablet) document.body.classList.add('tablet');
    else document.body.classList.remove('tablet');
    
    if (viewportInfo.isDesktop) document.body.classList.add('desktop');
    else document.body.classList.remove('desktop');

    if (viewportInfo.supportsTouchscreen) document.body.classList.add('touch');
    else document.body.classList.remove('touch');

    if (viewportInfo.supportsHover) document.body.classList.add('hover');
    else document.body.classList.remove('hover');
  }

  private detectDeviceCapabilities(): void {
    // Detect and apply initial device capabilities
    const viewportInfo = this.getCurrentViewportInfo();
    this.updateCSSCustomProperties(viewportInfo);
  }

  private supportsTouchscreen(): boolean {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }

  private supportsHover(): boolean {
    return window.matchMedia('(hover: hover)').matches;
  }

  private prefersReducedMotion(): boolean {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // Public API methods

  /**
   * Get current viewport information
   */
  getCurrentViewport(): ViewportInfo {
    return this.viewportInfo$.value;
  }

  /**
   * Get current responsive configuration
   */
  getCurrentConfig(): ResponsiveConfig {
    return this.currentConfig$.value;
  }

  /**
   * Check if current viewport matches breakpoint
   */
  isBreakpoint(breakpoint: Breakpoint): boolean {
    return this.getCurrentViewport().breakpoint === breakpoint;
  }

  /**
   * Check if current viewport is at least the specified breakpoint
   */
  isBreakpointUp(breakpoint: Breakpoint): boolean {
    const current = this.getCurrentViewport().width;
    return current >= this.breakpoints[breakpoint];
  }

  /**
   * Check if current viewport is below the specified breakpoint
   */
  isBreakpointDown(breakpoint: Breakpoint): boolean {
    const current = this.getCurrentViewport().width;
    return current < this.breakpoints[breakpoint];
  }

  /**
   * Get optimal column count for current viewport
   */
  getOptimalColumns(maxColumns?: number): number {
    const config = this.getCurrentConfig();
    const optimal = config.maxColumns;
    return maxColumns ? Math.min(optimal, maxColumns) : optimal;
  }

  /**
   * Get optimal grid layout for current viewport
   */
  getGridLayout(itemCount: number, preferredColumns?: number): { columns: number; rows: number } {
    const maxColumns = this.getOptimalColumns(preferredColumns);
    const columns = Math.min(itemCount, maxColumns);
    const rows = Math.ceil(itemCount / columns);
    
    return { columns, rows };
  }

  /**
   * Calculate responsive font size based on viewport
   */
  getResponsiveFontSize(baseSize: number): string {
    const viewport = this.getCurrentViewport();
    const scaleFactor = this.getFontScaleFactor(viewport.breakpoint);
    return `${baseSize * scaleFactor}px`;
  }

  private getFontScaleFactor(breakpoint: Breakpoint): number {
    const factors = {
      xs: 0.875,   // 14px base
      sm: 0.9375,  // 15px base
      md: 1,       // 16px base
      lg: 1,       // 16px base
      xl: 1.0625,  // 17px base
      xxl: 1.125   // 18px base
    };
    
    return factors[breakpoint];
  }

  /**
   * Get optimal spacing for current viewport
   */
  getResponsiveSpacing(multiplier: number = 1): string {
    const config = this.getCurrentConfig();
    const baseValue = parseFloat(config.baseSpacing);
    return `${baseValue * multiplier}rem`;
  }

  /**
   * Check if device supports advanced animations
   */
  supportsAdvancedAnimations(): boolean {
    const viewport = this.getCurrentViewport();
    return !viewport.isMobile && !this.prefersReducedMotion() && viewport.devicePixelRatio <= 2;
  }

  /**
   * Get optimal animation duration for current context
   */
  getAnimationDuration(base: number = 300): number {
    const config = this.getCurrentConfig();
    const baseDuration = parseInt(config.animationDuration);
    
    if (this.prefersReducedMotion()) return 0;
    if (this.getCurrentViewport().isMobile) return baseDuration * 0.8;
    
    return baseDuration;
  }

  /**
   * Create responsive observable for component updates
   */
  createResponsiveObservable<T>(
    transform: (viewport: ViewportInfo, config: ResponsiveConfig) => T
  ): Observable<T> {
    return this.viewport$.pipe(
      map(viewport => {
        const config = this.getCurrentConfig();
        return transform(viewport, config);
      }),
      distinctUntilChanged()
    );
  }

  /**
   * Get safe area insets (for devices with notches/safe areas)
   */
  getSafeAreaInsets(): { top: string; right: string; bottom: string; left: string } {
    const computedStyle = getComputedStyle(document.documentElement);
    
    return {
      top: computedStyle.getPropertyValue('env(safe-area-inset-top)') || '0px',
      right: computedStyle.getPropertyValue('env(safe-area-inset-right)') || '0px',
      bottom: computedStyle.getPropertyValue('env(safe-area-inset-bottom)') || '0px',
      left: computedStyle.getPropertyValue('env(safe-area-inset-left)') || '0px'
    };
  }

  /**
   * Apply responsive classes to element
   */
  applyResponsiveClasses(element: HTMLElement, classes: Partial<Record<Breakpoint, string>>): void {
    const currentBreakpoint = this.getCurrentViewport().breakpoint;
    
    // Remove all breakpoint classes
    Object.values(classes).forEach(className => {
      if (className) element.classList.remove(className);
    });
    
    // Apply current breakpoint class
    const currentClass = classes[currentBreakpoint];
    if (currentClass) {
      element.classList.add(currentClass);
    }
  }

  /**
   * Initialize responsive behavior for component
   */
  initializeResponsiveComponent(element: HTMLElement): () => void {
    const viewport = this.getCurrentViewport();
    
    // Apply initial classes
    element.setAttribute('data-breakpoint', viewport.breakpoint);
    element.setAttribute('data-is-mobile', viewport.isMobile.toString());
    element.setAttribute('data-supports-touch', viewport.supportsTouchscreen.toString());
    
    // Subscribe to viewport changes
    const subscription = this.viewport$.subscribe(newViewport => {
      element.setAttribute('data-breakpoint', newViewport.breakpoint);
      element.setAttribute('data-is-mobile', newViewport.isMobile.toString());
      element.setAttribute('data-supports-touch', newViewport.supportsTouchscreen.toString());
    });
    
    // Return cleanup function
    return () => {
      subscription.unsubscribe();
    };
  }
}