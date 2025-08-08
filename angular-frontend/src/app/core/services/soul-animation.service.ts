/**
 * Soul Animation Service - Phase 3 Advanced Animation System
 * Provides soul-themed animations with performance optimization and accessibility
 */
import { Injectable, ElementRef } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent, animationFrameScheduler, EMPTY } from 'rxjs';
import { map, takeUntil, startWith, distinctUntilChanged } from 'rxjs/operators';
import { ResponsiveDesignService } from './responsive-design.service';

export interface SoulAnimationConfig {
  duration: number;
  easing: string;
  delay: number;
  iterations: number | 'infinite';
  direction: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse';
  fillMode: 'none' | 'forwards' | 'backwards' | 'both';
  respectReducedMotion: boolean;
}

export interface SoulAnimationKeyframes {
  [key: string]: string | number;
}

export interface ConnectionEnergyTheme {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    glow: string;
  };
  particles: {
    count: number;
    size: string;
    speed: number;
    opacity: number;
  };
  pulse: {
    intensity: number;
    frequency: number;
  };
  aura: {
    rings: number;
    maxRadius: string;
    intensity: number;
  };
}

export type SoulAnimationType = 
  | 'breathe'
  | 'pulse'
  | 'glow'
  | 'float'
  | 'drift'
  | 'sparkle'
  | 'ripple'
  | 'reveal'
  | 'connect'
  | 'celebrate';

export type ConnectionEnergy = 'low' | 'medium' | 'high' | 'soulmate';

@Injectable({
  providedIn: 'root'
})
export class SoulAnimationService {
  private animationRegistry = new Map<string, Animation>();
  private activeAnimations = new BehaviorSubject<Map<string, Animation>>(new Map());
  private performanceMode$ = new BehaviorSubject<'low' | 'medium' | 'high'>('medium');

  private readonly energyThemes: Record<ConnectionEnergy, ConnectionEnergyTheme> = {
    low: {
      colors: {
        primary: '#a0aec0',
        secondary: '#718096',
        accent: '#e2e8f0',
        glow: 'rgba(160, 174, 192, 0.3)'
      },
      particles: { count: 3, size: '3px', speed: 0.5, opacity: 0.4 },
      pulse: { intensity: 0.05, frequency: 2000 },
      aura: { rings: 1, maxRadius: '40px', intensity: 0.3 }
    },
    medium: {
      colors: {
        primary: '#667eea',
        secondary: '#764ba2',
        accent: '#e879f9',
        glow: 'rgba(102, 126, 234, 0.5)'
      },
      particles: { count: 6, size: '4px', speed: 0.8, opacity: 0.6 },
      pulse: { intensity: 0.08, frequency: 1500 },
      aura: { rings: 2, maxRadius: '60px', intensity: 0.5 }
    },
    high: {
      colors: {
        primary: '#e879f9',
        secondary: '#667eea',
        accent: '#ffd700',
        glow: 'rgba(232, 121, 249, 0.7)'
      },
      particles: { count: 10, size: '5px', speed: 1.2, opacity: 0.8 },
      pulse: { intensity: 0.12, frequency: 1000 },
      aura: { rings: 3, maxRadius: '80px', intensity: 0.7 }
    },
    soulmate: {
      colors: {
        primary: '#ffd700',
        secondary: '#f093fb',
        accent: '#ffeaa7',
        glow: 'rgba(255, 215, 0, 0.9)'
      },
      particles: { count: 15, size: '6px', speed: 1.5, opacity: 1 },
      pulse: { intensity: 0.15, frequency: 800 },
      aura: { rings: 4, maxRadius: '100px', intensity: 0.9 }
    }
  };

  private readonly defaultConfig: SoulAnimationConfig = {
    duration: 1000,
    easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    delay: 0,
    iterations: 1,
    direction: 'normal',
    fillMode: 'both',
    respectReducedMotion: true
  };

  constructor(private responsiveService: ResponsiveDesignService) {
    this.initializePerformanceMonitoring();
    this.setupReducedMotionDetection();
  }

  /**
   * Create a soul-themed animation
   */
  createSoulAnimation(
    element: HTMLElement,
    animationType: SoulAnimationType,
    config: Partial<SoulAnimationConfig> = {},
    energy: ConnectionEnergy = 'medium'
  ): Observable<Animation> {
    const finalConfig = { ...this.defaultConfig, ...config };
    const theme = this.energyThemes[energy];
    
    // Check if animations should be disabled
    if (this.shouldSkipAnimation(finalConfig)) {
      return EMPTY;
    }

    const animationId = `${animationType}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const keyframes = this.getKeyframesForAnimation(animationType, theme);
    const options: KeyframeAnimationOptions = {
      duration: this.getAdjustedDuration(finalConfig.duration),
      easing: finalConfig.easing,
      delay: finalConfig.delay,
      iterations: finalConfig.iterations,
      direction: finalConfig.direction,
      fill: finalConfig.fillMode
    };

    const animation = element.animate(keyframes, options);
    this.registerAnimation(animationId, animation);

    return new Observable(observer => {
      observer.next(animation);

      animation.addEventListener('finish', () => {
        this.unregisterAnimation(animationId);
        observer.complete();
      });

      animation.addEventListener('cancel', () => {
        this.unregisterAnimation(animationId);
        observer.complete();
      });

      return () => {
        animation.cancel();
        this.unregisterAnimation(animationId);
      };
    });
  }

  /**
   * Create connection animation between two elements
   */
  createConnectionAnimation(
    fromElement: HTMLElement,
    toElement: HTMLElement,
    energy: ConnectionEnergy = 'medium'
  ): Observable<Animation> {
    const fromRect = fromElement.getBoundingClientRect();
    const toRect = toElement.getBoundingClientRect();
    
    // Create connection line element
    const connectionLine = this.createConnectionLine(fromRect, toRect, energy);
    document.body.appendChild(connectionLine);

    return this.createSoulAnimation(connectionLine, 'connect', {
      duration: 2000,
      easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
      fillMode: 'forwards'
    }, energy).pipe(
      map(animation => {
        // Clean up connection line when animation completes
        animation.addEventListener('finish', () => {
          if (connectionLine.parentNode) {
            connectionLine.parentNode.removeChild(connectionLine);
          }
        });
        return animation;
      })
    );
  }

  /**
   * Create particle system animation
   */
  createParticleSystem(
    container: HTMLElement,
    energy: ConnectionEnergy = 'medium',
    duration: number = 5000
  ): Observable<Animation[]> {
    const theme = this.energyThemes[energy];
    const particleCount = theme.particles.count;
    const animations: Animation[] = [];

    return new Observable(observer => {
      for (let i = 0; i < particleCount; i++) {
        const particle = this.createParticle(theme, i);
        container.appendChild(particle);

        this.createSoulAnimation(particle, 'sparkle', {
          duration: duration,
          delay: Math.random() * 2000,
          iterations: 'infinite'
        }, energy).subscribe(animation => {
          animations.push(animation);
          
          if (animations.length === particleCount) {
            observer.next(animations);
          }
        });
      }

      return () => {
        animations.forEach(animation => animation.cancel());
        // Clean up particles
        container.querySelectorAll('.soul-particle').forEach(particle => {
          if (particle.parentNode) {
            particle.parentNode.removeChild(particle);
          }
        });
      };
    });
  }

  /**
   * Create breathing animation for avatar/profile pictures
   */
  createBreathingAnimation(
    element: HTMLElement,
    energy: ConnectionEnergy = 'medium'
  ): Observable<Animation> {
    return this.createSoulAnimation(element, 'breathe', {
      duration: 3000,
      iterations: 'infinite',
      easing: 'cubic-bezier(0.37, 0, 0.63, 1)'
    }, energy);
  }

  /**
   * Create typing indicator animation
   */
  createTypingAnimation(
    dots: NodeListOf<HTMLElement> | HTMLElement[],
    energy: ConnectionEnergy = 'medium'
  ): Observable<Animation[]> {
    const animations: Animation[] = [];

    return new Observable(observer => {
      Array.from(dots).forEach((dot, index) => {
        this.createSoulAnimation(dot, 'pulse', {
          duration: 1400,
          delay: index * 200,
          iterations: 'infinite',
          easing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
        }, energy).subscribe(animation => {
          animations.push(animation);
          
          if (animations.length === dots.length) {
            observer.next(animations);
          }
        });
      });

      return () => {
        animations.forEach(animation => animation.cancel());
      };
    });
  }

  /**
   * Create reveal animation for progressive disclosure
   */
  createRevealAnimation(
    element: HTMLElement,
    direction: 'up' | 'down' | 'left' | 'right' = 'up'
  ): Observable<Animation> {
    return this.createSoulAnimation(element, 'reveal', {
      duration: 600,
      easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)'
    });
  }

  /**
   * Create celebration animation
   */
  createCelebrationAnimation(
    element: HTMLElement,
    energy: ConnectionEnergy = 'soulmate'
  ): Observable<Animation> {
    return this.createSoulAnimation(element, 'celebrate', {
      duration: 1500,
      easing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
    }, energy);
  }

  private getKeyframesForAnimation(
    type: SoulAnimationType,
    theme: ConnectionEnergyTheme
  ): Keyframe[] {
    const keyframes: Record<SoulAnimationType, Keyframe[]> = {
      breathe: [
        { transform: 'scale(1)', opacity: '1' },
        { transform: 'scale(1.05)', opacity: '0.9' },
        { transform: 'scale(1)', opacity: '1' }
      ],
      pulse: [
        { transform: 'scale(1)', opacity: '0.7' },
        { transform: 'scale(1.2)', opacity: '1' },
        { transform: 'scale(1)', opacity: '0.7' }
      ],
      glow: [
        { boxShadow: `0 0 5px ${theme.colors.glow}` },
        { boxShadow: `0 0 20px ${theme.colors.glow}` },
        { boxShadow: `0 0 5px ${theme.colors.glow}` }
      ],
      float: [
        { transform: 'translateY(0px)' },
        { transform: 'translateY(-10px)' },
        { transform: 'translateY(0px)' }
      ],
      drift: [
        { transform: 'translateX(-5px) rotate(-1deg)' },
        { transform: 'translateX(5px) rotate(1deg)' },
        { transform: 'translateX(-5px) rotate(-1deg)' }
      ],
      sparkle: [
        { 
          opacity: '0', 
          transform: 'translateY(0px) scale(0) rotate(0deg)',
          background: theme.colors.primary
        },
        { 
          opacity: '1', 
          transform: 'translateY(-20px) scale(1) rotate(180deg)',
          background: theme.colors.accent
        },
        { 
          opacity: '0', 
          transform: 'translateY(-40px) scale(0) rotate(360deg)',
          background: theme.colors.secondary
        }
      ],
      ripple: [
        { transform: 'scale(0)', opacity: '1' },
        { transform: 'scale(1)', opacity: '0' }
      ],
      reveal: [
        { opacity: '0', transform: 'translateY(20px) scale(0.8)' },
        { opacity: '1', transform: 'translateY(0px) scale(1)' }
      ],
      connect: [
        { transform: 'scaleX(0)', transformOrigin: 'left center' },
        { transform: 'scaleX(1)', transformOrigin: 'left center' }
      ],
      celebrate: [
        { transform: 'scale(1) rotate(0deg)', filter: 'brightness(1) saturate(1)' },
        { transform: 'scale(1.2) rotate(5deg)', filter: 'brightness(1.3) saturate(1.5)' },
        { transform: 'scale(1.1) rotate(-5deg)', filter: 'brightness(1.2) saturate(1.3)' },
        { transform: 'scale(1) rotate(0deg)', filter: 'brightness(1) saturate(1)' }
      ]
    };

    return keyframes[type];
  }

  private createConnectionLine(
    fromRect: DOMRect,
    toRect: DOMRect,
    energy: ConnectionEnergy
  ): HTMLElement {
    const line = document.createElement('div');
    const theme = this.energyThemes[energy];
    
    // Calculate position and size
    const fromCenter = {
      x: fromRect.left + fromRect.width / 2,
      y: fromRect.top + fromRect.height / 2
    };
    const toCenter = {
      x: toRect.left + toRect.width / 2,
      y: toRect.top + toRect.height / 2
    };
    
    const distance = Math.sqrt(
      Math.pow(toCenter.x - fromCenter.x, 2) + 
      Math.pow(toCenter.y - fromCenter.y, 2)
    );
    
    const angle = Math.atan2(toCenter.y - fromCenter.y, toCenter.x - fromCenter.x);
    
    // Style the connection line
    line.className = 'soul-connection-line';
    line.style.cssText = `
      position: fixed;
      top: ${fromCenter.y}px;
      left: ${fromCenter.x}px;
      width: ${distance}px;
      height: 3px;
      background: linear-gradient(90deg, ${theme.colors.primary}, ${theme.colors.secondary});
      transform-origin: 0 50%;
      transform: rotate(${angle}rad);
      border-radius: 2px;
      box-shadow: 0 0 10px ${theme.colors.glow};
      pointer-events: none;
      z-index: 1000;
    `;

    return line;
  }

  private createParticle(theme: ConnectionEnergyTheme, index: number): HTMLElement {
    const particle = document.createElement('div');
    particle.className = 'soul-particle';
    
    const delay = Math.random() * 4;
    const duration = 3 + Math.random() * 2;
    const angle = Math.random() * 360;
    
    particle.style.cssText = `
      position: absolute;
      width: ${theme.particles.size};
      height: ${theme.particles.size};
      background: radial-gradient(circle, ${theme.colors.primary}, ${theme.colors.secondary});
      border-radius: 50%;
      opacity: ${theme.particles.opacity};
      pointer-events: none;
      top: 50%;
      left: 20%;
      animation-delay: ${delay}s;
    `;

    return particle;
  }

  private registerAnimation(id: string, animation: Animation): void {
    this.animationRegistry.set(id, animation);
    const current = this.activeAnimations.value;
    current.set(id, animation);
    this.activeAnimations.next(new Map(current));
  }

  private unregisterAnimation(id: string): void {
    this.animationRegistry.delete(id);
    const current = this.activeAnimations.value;
    current.delete(id);
    this.activeAnimations.next(new Map(current));
  }

  private shouldSkipAnimation(config: SoulAnimationConfig): boolean {
    if (config.respectReducedMotion && this.prefersReducedMotion()) {
      return true;
    }
    
    const performance = this.performanceMode$.value;
    if (performance === 'low') {
      return true;
    }
    
    return false;
  }

  private getAdjustedDuration(baseDuration: number): number {
    const viewport = this.responsiveService.getCurrentViewport();
    
    if (this.prefersReducedMotion()) return 0;
    if (viewport.isMobile) return baseDuration * 0.8;
    
    const performance = this.performanceMode$.value;
    const multipliers = { low: 0.5, medium: 1, high: 1.2 };
    
    return baseDuration * multipliers[performance];
  }

  private prefersReducedMotion(): boolean {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  private initializePerformanceMonitoring(): void {
    // Simple performance detection
    const performanceLevel = this.detectPerformanceLevel();
    this.performanceMode$.next(performanceLevel);
  }

  private detectPerformanceLevel(): 'low' | 'medium' | 'high' {
    // Simple heuristics for performance detection
    const hardwareConcurrency = navigator.hardwareConcurrency || 2;
    const memory = (navigator as any).deviceMemory || 4;
    const connection = (navigator as any).connection;

    if (hardwareConcurrency >= 8 && memory >= 8) return 'high';
    if (hardwareConcurrency >= 4 && memory >= 4) return 'medium';
    if (connection && connection.effectiveType === '2g') return 'low';
    
    return 'medium';
  }

  private setupReducedMotionDetection(): void {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    mediaQuery.addEventListener('change', () => {
      if (mediaQuery.matches) {
        this.cancelAllAnimations();
      }
    });
  }

  /**
   * Cancel all active animations
   */
  cancelAllAnimations(): void {
    this.animationRegistry.forEach(animation => {
      animation.cancel();
    });
    this.animationRegistry.clear();
    this.activeAnimations.next(new Map());
  }

  /**
   * Get active animations count
   */
  getActiveAnimationsCount(): number {
    return this.animationRegistry.size;
  }

  /**
   * Set performance mode
   */
  setPerformanceMode(mode: 'low' | 'medium' | 'high'): void {
    this.performanceMode$.next(mode);
  }

  /**
   * Get energy theme colors
   */
  getEnergyTheme(energy: ConnectionEnergy): ConnectionEnergyTheme {
    return this.energyThemes[energy];
  }

  /**
   * Create custom animation with keyframes
   */
  createCustomAnimation(
    element: HTMLElement,
    keyframes: Keyframe[],
    config: Partial<SoulAnimationConfig> = {}
  ): Observable<Animation> {
    const finalConfig = { ...this.defaultConfig, ...config };
    
    if (this.shouldSkipAnimation(finalConfig)) {
      return EMPTY;
    }

    const animationId = `custom-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const options: KeyframeAnimationOptions = {
      duration: this.getAdjustedDuration(finalConfig.duration),
      easing: finalConfig.easing,
      delay: finalConfig.delay,
      iterations: finalConfig.iterations,
      direction: finalConfig.direction,
      fill: finalConfig.fillMode
    };

    const animation = element.animate(keyframes, options);
    this.registerAnimation(animationId, animation);

    return new Observable(observer => {
      observer.next(animation);

      animation.addEventListener('finish', () => {
        this.unregisterAnimation(animationId);
        observer.complete();
      });

      animation.addEventListener('cancel', () => {
        this.unregisterAnimation(animationId);
        observer.complete();
      });

      return () => {
        animation.cancel();
        this.unregisterAnimation(animationId);
      };
    });
  }
}