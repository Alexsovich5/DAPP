import { Injectable, ElementRef, NgZone } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent, merge, timer } from 'rxjs';
import { map, debounceTime, throttleTime, distinctUntilChanged, filter } from 'rxjs/operators';
import { MobileFeaturesService } from './mobile-features.service';

export interface PerformanceMetrics {
  memoryUsage: number;
  loadTime: number;
  renderTime: number;
  networkSpeed: 'slow' | 'medium' | 'fast';
  batteryLevel?: number;
  isLowEndDevice: boolean;
  frameRate: number;
  domNodes: number;
}

export interface ImageOptimizationConfig {
  quality: number;
  maxWidth: number;
  maxHeight: number;
  format: 'webp' | 'jpeg' | 'png';
  lazy: boolean;
  placeholder: boolean;
}

export interface LazyLoadConfig {
  rootMargin: string;
  threshold: number;
  imageQuality: number;
  enablePlaceholder: boolean;
}

export interface MemoryManagementConfig {
  maxCacheSize: number;
  cleanupInterval: number;
  criticalMemoryThreshold: number;
  profileImageCacheLimit: number;
}

@Injectable({
  providedIn: 'root'
})
export class MobilePerformanceService {
  private performanceMetrics$ = new BehaviorSubject<PerformanceMetrics>({
    memoryUsage: 0,
    loadTime: 0,
    renderTime: 0,
    networkSpeed: 'medium',
    isLowEndDevice: false,
    frameRate: 60,
    domNodes: 0
  });

  private imageCache = new Map<string, HTMLImageElement>();
  private intersectionObserver?: IntersectionObserver;
  private performanceObserver?: PerformanceObserver;
  private animationFrameId?: number;
  private memoryCleanupTimer?: number;

  private readonly defaultImageConfig: ImageOptimizationConfig = {
    quality: 0.8,
    maxWidth: 800,
    maxHeight: 600,
    format: 'webp',
    lazy: true,
    placeholder: true
  };

  private readonly defaultLazyConfig: LazyLoadConfig = {
    rootMargin: '50px',
    threshold: 0.1,
    imageQuality: 0.8,
    enablePlaceholder: true
  };

  private readonly defaultMemoryConfig: MemoryManagementConfig = {
    maxCacheSize: 50 * 1024 * 1024, // 50MB
    cleanupInterval: 5 * 60 * 1000, // 5 minutes
    criticalMemoryThreshold: 0.85,
    profileImageCacheLimit: 100
  };

  public performance$ = this.performanceMetrics$.asObservable();

  constructor(
    private ngZone: NgZone,
    private mobileFeatures: MobileFeaturesService
  ) {
    this.initializePerformanceMonitoring();
    this.setupMemoryManagement();
    this.detectNetworkSpeed();
    this.detectDeviceCapabilities();
  }

  private initializePerformanceMonitoring(): void {
    this.ngZone.runOutsideAngular(() => {
      // Monitor performance metrics
      if ('performance' in window && 'PerformanceObserver' in window) {
        this.performanceObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          this.processPerformanceEntries(entries);
        });

        try {
          this.performanceObserver.observe({ entryTypes: ['navigation', 'paint', 'measure'] });
        } catch (error) {
          console.warn('Performance Observer not fully supported:', error);
        }
      }

      // Monitor frame rate
      this.monitorFrameRate();

      // Monitor memory usage
      this.monitorMemoryUsage();

      // Monitor DOM size
      this.monitorDOMSize();
    });
  }

  private monitorFrameRate(): void {
    let lastTime = performance.now();
    let frameCount = 0;
    const targetFPS = 60;
    const measureInterval = 1000; // 1 second

    const measureFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime - lastTime >= measureInterval) {
        const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
        
        this.updateMetrics({ frameRate: fps });
        
        frameCount = 0;
        lastTime = currentTime;
      }
      
      this.animationFrameId = requestAnimationFrame(measureFPS);
    };

    this.animationFrameId = requestAnimationFrame(measureFPS);
  }

  private monitorMemoryUsage(): void {
    if ('memory' in performance) {
      timer(0, 30000).subscribe(() => { // Check every 30 seconds
        const memory = (performance as any).memory;
        if (memory) {
          const usedMemory = memory.usedJSHeapSize;
          const totalMemory = memory.totalJSHeapSize;
          const memoryUsage = usedMemory / totalMemory;
          
          this.updateMetrics({ memoryUsage });
          
          // Trigger cleanup if memory usage is high
          if (memoryUsage > this.defaultMemoryConfig.criticalMemoryThreshold) {
            this.performEmergencyCleanup();
          }
        }
      });
    }
  }

  private monitorDOMSize(): void {
    const resizeObserver = new ResizeObserver(() => {
      const domNodes = document.querySelectorAll('*').length;
      this.updateMetrics({ domNodes });
    });

    resizeObserver.observe(document.body);
  }

  private setupMemoryManagement(): void {
    // Regular memory cleanup
    this.memoryCleanupTimer = window.setInterval(() => {
      this.performMemoryCleanup();
    }, this.defaultMemoryConfig.cleanupInterval);

    // Cleanup on page visibility change
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.performMemoryCleanup();
      }
    });

    // Cleanup on low memory warning
    if ('navigator' in window && 'connection' in navigator) {
      const connection = (navigator as any).connection;
      if (connection) {
        connection.addEventListener('change', () => {
          if (connection.saveData) {
            this.performEmergencyCleanup();
          }
        });
      }
    }
  }

  /**
   * Optimize images for mobile devices
   */
  async optimizeImage(
    imageElement: HTMLImageElement | string,
    config: Partial<ImageOptimizationConfig> = {}
  ): Promise<string> {
    const finalConfig = { ...this.defaultImageConfig, ...config };
    
    try {
      let img: HTMLImageElement;
      
      if (typeof imageElement === 'string') {
        img = new Image();
        img.src = imageElement;
        await new Promise((resolve, reject) => {
          img.onload = resolve;
          img.onerror = reject;
        });
      } else {
        img = imageElement;
      }

      // Check if image needs optimization
      if (img.naturalWidth <= finalConfig.maxWidth && 
          img.naturalHeight <= finalConfig.maxHeight) {
        return img.src;
      }

      return this.resizeAndCompressImage(img, finalConfig);
    } catch (error) {
      console.error('Image optimization failed:', error);
      return typeof imageElement === 'string' ? imageElement : imageElement.src;
    }
  }

  private async resizeAndCompressImage(
    img: HTMLImageElement,
    config: ImageOptimizationConfig
  ): Promise<string> {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Canvas context not available');
    }

    // Calculate new dimensions maintaining aspect ratio
    const aspectRatio = img.naturalWidth / img.naturalHeight;
    let { maxWidth, maxHeight } = config;

    if (img.naturalWidth > maxWidth || img.naturalHeight > maxHeight) {
      if (aspectRatio > 1) {
        maxHeight = maxWidth / aspectRatio;
      } else {
        maxWidth = maxHeight * aspectRatio;
      }
    } else {
      maxWidth = img.naturalWidth;
      maxHeight = img.naturalHeight;
    }

    canvas.width = maxWidth;
    canvas.height = maxHeight;

    // Apply image smoothing for better quality
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';

    // Draw and compress
    ctx.drawImage(img, 0, 0, maxWidth, maxHeight);

    // Return optimized image as data URL
    const mimeType = config.format === 'webp' ? 'image/webp' : 
                    config.format === 'png' ? 'image/png' : 'image/jpeg';
    
    return canvas.toDataURL(mimeType, config.quality);
  }

  /**
   * Enable lazy loading for images
   */
  enableLazyLoading(
    container: ElementRef<HTMLElement> | HTMLElement,
    config: Partial<LazyLoadConfig> = {}
  ): void {
    const finalConfig = { ...this.defaultLazyConfig, ...config };
    const element = container instanceof ElementRef ? container.nativeElement : container;

    if (!this.intersectionObserver) {
      this.intersectionObserver = new IntersectionObserver(
        (entries) => this.handleIntersectionEntries(entries, finalConfig),
        {
          root: null,
          rootMargin: finalConfig.rootMargin,
          threshold: finalConfig.threshold
        }
      );
    }

    // Find all images with data-src attribute
    const lazyImages = element.querySelectorAll('img[data-src]');
    lazyImages.forEach(img => {
      if (finalConfig.enablePlaceholder) {
        this.addImagePlaceholder(img as HTMLImageElement);
      }
      this.intersectionObserver!.observe(img);
    });
  }

  private handleIntersectionEntries(entries: IntersectionObserverEntry[], config: LazyLoadConfig): void {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        this.loadLazyImage(img, config);
        this.intersectionObserver!.unobserve(img);
      }
    });
  }

  private async loadLazyImage(img: HTMLImageElement, config: LazyLoadConfig): Promise<void> {
    const src = img.dataset.src;
    if (!src) return;

    try {
      // Check cache first
      const cachedImg = this.imageCache.get(src);
      if (cachedImg) {
        img.src = cachedImg.src;
        img.classList.add('loaded');
        return;
      }

      // Load and potentially optimize
      const optimizedSrc = await this.optimizeImage(src, {
        quality: config.imageQuality,
        maxWidth: this.getOptimalImageWidth(),
        maxHeight: this.getOptimalImageHeight(),
        format: this.supportsWebP() ? 'webp' : 'jpeg',
        lazy: false,
        placeholder: false
      });

      img.src = optimizedSrc;
      img.classList.add('loaded');

      // Cache the optimized image
      const cacheImg = new Image();
      cacheImg.src = optimizedSrc;
      this.imageCache.set(src, cacheImg);

      // Limit cache size
      this.limitImageCache();

    } catch (error) {
      console.error('Failed to load lazy image:', error);
      img.src = src; // Fallback to original
    }
  }

  private addImagePlaceholder(img: HTMLImageElement): void {
    // Create a low-quality placeholder
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;

    canvas.width = 40;
    canvas.height = 30;
    
    // Create a simple gradient placeholder
    const gradient = ctx.createLinearGradient(0, 0, 40, 30);
    gradient.addColorStop(0, '#f0f0f0');
    gradient.addColorStop(1, '#e0e0e0');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 40, 30);
    
    img.src = canvas.toDataURL();
    img.classList.add('placeholder');
  }

  /**
   * Preload critical images for dating app
   */
  async preloadCriticalImages(imageUrls: string[]): Promise<void> {
    const deviceInfo = this.mobileFeatures.getDeviceInfo();
    
    // Reduce preload count for low-end devices
    const maxPreload = deviceInfo.isLowEndDevice ? 3 : 8;
    const urlsToPreload = imageUrls.slice(0, maxPreload);

    const preloadPromises = urlsToPreload.map(async (url) => {
      try {
        const optimizedUrl = await this.optimizeImage(url, {
          quality: 0.7,
          maxWidth: this.getOptimalImageWidth(),
          maxHeight: this.getOptimalImageHeight(),
          format: this.supportsWebP() ? 'webp' : 'jpeg',
          lazy: false,
          placeholder: false
        });

        const img = new Image();
        img.src = optimizedUrl;
        
        return new Promise<void>((resolve) => {
          img.onload = () => {
            this.imageCache.set(url, img);
            resolve();
          };
          img.onerror = () => resolve(); // Don't fail the whole batch
        });
      } catch (error) {
        console.warn('Failed to preload image:', url, error);
      }
    });

    await Promise.allSettled(preloadPromises);
  }

  /**
   * Optimize component rendering for mobile
   */
  optimizeComponentRendering(): {
    shouldVirtualize: boolean;
    batchSize: number;
    debounceTime: number;
  } {
    const metrics = this.performanceMetrics$.value;
    const deviceInfo = this.mobileFeatures.getDeviceInfo();

    return {
      shouldVirtualize: deviceInfo.isLowEndDevice || metrics.memoryUsage > 0.7,
      batchSize: deviceInfo.isLowEndDevice ? 10 : 20,
      debounceTime: deviceInfo.isLowEndDevice ? 300 : 150
    };
  }

  /**
   * Get optimal configuration for mobile device
   */
  getMobileOptimizedConfig(): {
    maxProfiles: number;
    imageQuality: number;
    animationIntensity: 'low' | 'medium' | 'high';
    enableAdvancedFeatures: boolean;
  } {
    const metrics = this.performanceMetrics$.value;
    const deviceInfo = this.mobileFeatures.getDeviceInfo();

    if (deviceInfo.isLowEndDevice || metrics.memoryUsage > 0.8) {
      return {
        maxProfiles: 5,
        imageQuality: 0.6,
        animationIntensity: 'low',
        enableAdvancedFeatures: false
      };
    } else if (metrics.networkSpeed === 'slow' || metrics.frameRate < 45) {
      return {
        maxProfiles: 10,
        imageQuality: 0.7,
        animationIntensity: 'medium',
        enableAdvancedFeatures: true
      };
    } else {
      return {
        maxProfiles: 20,
        imageQuality: 0.8,
        animationIntensity: 'high',
        enableAdvancedFeatures: true
      };
    }
  }

  /**
   * Perform memory cleanup
   */
  private performMemoryCleanup(): void {
    // Clear old cached images
    this.limitImageCache();

    // Clear unused DOM references
    this.clearDOMReferences();

    // Force garbage collection if available
    if ('gc' in window) {
      (window as any).gc();
    }
  }

  private performEmergencyCleanup(): void {
    // Clear most of the image cache
    const currentSize = this.imageCache.size;
    const keepCount = Math.floor(currentSize * 0.3);
    
    const entries = Array.from(this.imageCache.entries());
    entries.slice(0, currentSize - keepCount).forEach(([key]) => {
      this.imageCache.delete(key);
    });

    // Clear any large cached data
    this.clearLargeCachedData();
  }

  private limitImageCache(): void {
    const maxCacheItems = this.defaultMemoryConfig.profileImageCacheLimit;
    
    if (this.imageCache.size > maxCacheItems) {
      const entries = Array.from(this.imageCache.entries());
      const removeCount = this.imageCache.size - maxCacheItems;
      
      // Remove oldest entries (FIFO)
      entries.slice(0, removeCount).forEach(([key]) => {
        this.imageCache.delete(key);
      });
    }
  }

  private clearDOMReferences(): void {
    // Remove any stale event listeners
    // This would be implemented based on specific app needs
  }

  private clearLargeCachedData(): void {
    // Clear localStorage items larger than 1MB
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        const value = localStorage.getItem(key);
        if (value && value.length > 1024 * 1024) { // 1MB
          localStorage.removeItem(key);
        }
      }
    }
  }

  private detectNetworkSpeed(): void {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      
      if (connection) {
        const updateNetworkSpeed = () => {
          let speed: 'slow' | 'medium' | 'fast' = 'medium';
          
          if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
            speed = 'slow';
          } else if (connection.effectiveType === '3g') {
            speed = 'medium';
          } else {
            speed = 'fast';
          }
          
          this.updateMetrics({ networkSpeed: speed });
        };

        updateNetworkSpeed();
        connection.addEventListener('change', updateNetworkSpeed);
      }
    }
  }

  private detectDeviceCapabilities(): void {
    const deviceInfo = this.mobileFeatures.getDeviceInfo();
    
    // Detect low-end device based on various factors
    const isLowEndDevice = 
      deviceInfo.screenSize.width < 400 ||
      navigator.hardwareConcurrency <= 2 ||
      (navigator as any).deviceMemory <= 2;

    this.updateMetrics({ isLowEndDevice });
  }

  private processPerformanceEntries(entries: PerformanceEntry[]): void {
    entries.forEach(entry => {
      if (entry.entryType === 'navigation') {
        const navEntry = entry as PerformanceNavigationTiming;
        this.updateMetrics({
          loadTime: navEntry.loadEventEnd - navEntry.loadEventStart,
          renderTime: navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart
        });
      }
    });
  }

  private updateMetrics(updates: Partial<PerformanceMetrics>): void {
    const current = this.performanceMetrics$.value;
    this.performanceMetrics$.next({ ...current, ...updates });
  }

  private getOptimalImageWidth(): number {
    const deviceInfo = this.mobileFeatures.getDeviceInfo();
    return Math.min(deviceInfo.screenSize.width * window.devicePixelRatio, 800);
  }

  private getOptimalImageHeight(): number {
    const deviceInfo = this.mobileFeatures.getDeviceInfo();
    return Math.min(deviceInfo.screenSize.height * window.devicePixelRatio, 600);
  }

  private supportsWebP(): boolean {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    
    if (this.memoryCleanupTimer) {
      clearInterval(this.memoryCleanupTimer);
    }
    
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
    }
    
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }
    
    this.imageCache.clear();
  }
}