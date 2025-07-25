import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent } from 'rxjs';
import { map, debounceTime } from 'rxjs/operators';

export interface GeolocationResult {
  latitude: number;
  longitude: number;
  accuracy: number;
  timestamp: number;
}

export interface DeviceOrientation {
  alpha: number; // Z axis rotation (0-360)
  beta: number;  // X axis rotation (-180 to 180)
  gamma: number; // Y axis rotation (-90 to 90)
}

export interface CameraCapture {
  blob: Blob;
  dataUrl: string;
  width: number;
  height: number;
}

export interface HapticPattern {
  duration: number;
  intensity?: number;
}

@Injectable({
  providedIn: 'root'
})
export class MobileFeaturesService {
  private currentPosition: GeolocationPosition | null = null;
  private orientationSubject = new BehaviorSubject<DeviceOrientation | null>(null);
  private shakeSubject = new BehaviorSubject<boolean>(false);
  
  public orientation$ = this.orientationSubject.asObservable();
  public shake$ = this.shakeSubject.asObservable();

  constructor() {
    this.initializeOrientationListener();
    this.initializeShakeDetection();
  }

  // Geolocation Services
  async getCurrentLocation(options?: PositionOptions): Promise<GeolocationResult> {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }

      const defaultOptions: PositionOptions = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // Cache for 5 minutes
        ...options
      };

      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.currentPosition = position;
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp
          });
        },
        (error) => {
          reject(this.handleGeolocationError(error));
        },
        defaultOptions
      );
    });
  }

  watchLocation(options?: PositionOptions): Observable<GeolocationResult> {
    return new Observable(observer => {
      if (!navigator.geolocation) {
        observer.error(new Error('Geolocation not supported'));
        return;
      }

      const watchId = navigator.geolocation.watchPosition(
        (position) => {
          this.currentPosition = position;
          observer.next({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp
          });
        },
        (error) => {
          observer.error(this.handleGeolocationError(error));
        },
        {
          enableHighAccuracy: true,
          maximumAge: 60000, // 1 minute for watch
          timeout: 15000,
          ...options
        }
      );

      return () => {
        navigator.geolocation.clearWatch(watchId);
      };
    });
  }

  private handleGeolocationError(error: GeolocationPositionError): Error {
    switch (error.code) {
      case error.PERMISSION_DENIED:
        return new Error('Location access denied by user');
      case error.POSITION_UNAVAILABLE:
        return new Error('Location information unavailable');
      case error.TIMEOUT:
        return new Error('Location request timed out');
      default:
        return new Error('Unknown location error');
    }
  }

  // Camera Services
  async capturePhoto(constraints?: MediaStreamConstraints): Promise<CameraCapture> {
    if (!('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices)) {
      throw new Error('Camera not available');
    }

    const defaultConstraints: MediaStreamConstraints = {
      video: {
        facingMode: 'user',
        width: { ideal: 1080, max: 1920 },
        height: { ideal: 1080, max: 1920 }
      },
      audio: false,
      ...constraints
    };

    try {
      const stream = await navigator.mediaDevices.getUserMedia(defaultConstraints);
      
      return new Promise((resolve, reject) => {
        const video = document.createElement('video');
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d')!;

        video.srcObject = stream;
        video.autoplay = true;
        video.playsInline = true;

        video.addEventListener('loadedmetadata', () => {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;

          // Capture frame
          context.drawImage(video, 0, 0);

          // Clean up stream
          stream.getTracks().forEach(track => track.stop());

          // Convert to blob
          canvas.toBlob((blob) => {
            if (blob) {
              const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
              resolve({
                blob,
                dataUrl,
                width: canvas.width,
                height: canvas.height
              });
            } else {
              reject(new Error('Failed to create image blob'));
            }
          }, 'image/jpeg', 0.8);
        });

        video.addEventListener('error', (error) => {
          stream.getTracks().forEach(track => track.stop());
          reject(error);
        });
      });
    } catch (error) {
      throw new Error(`Camera capture failed: ${error}`);
    }
  }

  async switchCamera(): Promise<MediaStream> {
    if (!('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices)) {
      throw new Error('Camera switching not available');
    }

    const constraints: MediaStreamConstraints = {
      video: {
        facingMode: 'environment', // Back camera
        width: { ideal: 1080 },
        height: { ideal: 1080 }
      }
    };

    return navigator.mediaDevices.getUserMedia(constraints);
  }

  async compressImage(file: File, maxWidth: number = 800, quality: number = 0.8): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d')!;
      const img = new Image();

      img.onload = () => {
        // Calculate new dimensions maintaining aspect ratio
        const ratio = Math.min(maxWidth / img.width, maxWidth / img.height);
        canvas.width = img.width * ratio;
        canvas.height = img.height * ratio;

        // Draw and compress
        context.drawImage(img, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to compress image'));
          }
        }, 'image/jpeg', quality);
      };

      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = URL.createObjectURL(file);
    });
  }

  // Device Orientation
  private initializeOrientationListener(): void {
    if ('DeviceOrientationEvent' in window) {
      fromEvent(window, 'deviceorientation').subscribe((event: any) => {
        this.orientationSubject.next({
          alpha: event.alpha || 0,
          beta: event.beta || 0,
          gamma: event.gamma || 0
        });
      });
    }
  }

  async requestOrientationPermission(): Promise<boolean> {
    if ('DeviceOrientationEvent' in window && typeof (DeviceOrientationEvent as any).requestPermission === 'function') {
      try {
        const permission = await (DeviceOrientationEvent as any).requestPermission();
        return permission === 'granted';
      } catch (error) {
        console.error('Orientation permission error:', error);
        return false;
      }
    }
    return true; // Assume granted for non-iOS devices
  }

  // Shake Detection
  private initializeShakeDetection(): void {
    if ('DeviceMotionEvent' in window) {
      let lastAcceleration = { x: 0, y: 0, z: 0 };
      let lastTime = Date.now();

      fromEvent(window, 'devicemotion')
        .pipe(debounceTime(100))
        .subscribe((event: any) => {
          const acceleration = event.accelerationIncludingGravity;
          if (!acceleration) return;

          const currentTime = Date.now();
          const timeDelta = currentTime - lastTime;

          if (timeDelta > 100) {
            const deltaX = Math.abs(acceleration.x - lastAcceleration.x);
            const deltaY = Math.abs(acceleration.y - lastAcceleration.y);
            const deltaZ = Math.abs(acceleration.z - lastAcceleration.z);

            const shakeThreshold = 15;
            const totalDelta = deltaX + deltaY + deltaZ;

            if (totalDelta > shakeThreshold) {
              this.shakeSubject.next(true);
              setTimeout(() => this.shakeSubject.next(false), 1000);
            }

            lastAcceleration = { x: acceleration.x, y: acceleration.y, z: acceleration.z };
            lastTime = currentTime;
          }
        });
    }
  }

  // Haptic Feedback
  async vibrate(pattern: number | number[] | HapticPattern[]): Promise<boolean> {
    if ('vibrate' in navigator) {
      try {
        let vibrationPattern: number[];

        if (typeof pattern === 'number') {
          vibrationPattern = [pattern];
        } else if (Array.isArray(pattern) && typeof pattern[0] === 'number') {
          vibrationPattern = pattern as number[];
        } else {
          // Convert HapticPattern[] to number[]
          vibrationPattern = (pattern as HapticPattern[])
            .map(p => [p.duration, 100]) // Add pause between patterns
            .flat()
            .slice(0, -1); // Remove last pause
        }

        navigator.vibrate(vibrationPattern);
        return true;
      } catch (error) {
        console.error('Vibration failed:', error);
        return false;
      }
    }
    return false;
  }

  // Quick vibration patterns for dating app
  vibrateNewMessage(): void {
    this.vibrate([100, 50, 100]);
  }

  vibrateNewMatch(): void {
    this.vibrate([200, 100, 200, 100, 200]);
  }

  vibrateRevelationReady(): void {
    this.vibrate([300, 200, 100, 200, 300]);
  }

  vibratePhotoReveal(): void {
    this.vibrate([500]);
  }

  // Battery Status
  async getBatteryInfo(): Promise<{
    level: number;
    charging: boolean;
    chargingTime: number;
    dischargingTime: number;
  } | null> {
    if ('getBattery' in navigator) {
      try {
        const battery = await (navigator as any).getBattery();
        return {
          level: battery.level,
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime
        };
      } catch (error) {
        console.error('Battery API error:', error);
        return null;
      }
    }
    return null;
  }

  // Network Information
  getNetworkInfo(): {
    effectiveType: string;
    downlink: number;
    rtt: number;
    saveData: boolean;
  } | null {
    const connection = (navigator as any).connection;
    if (connection) {
      return {
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData
      };
    }
    return null;
  }

  // Screen Wake Lock
  private wakeLock: any = null;

  async requestWakeLock(): Promise<boolean> {
    if ('wakeLock' in navigator) {
      try {
        this.wakeLock = await (navigator as any).wakeLock.request('screen');
        return true;
      } catch (error) {
        console.error('Wake lock failed:', error);
        return false;
      }
    }
    return false;
  }

  async releaseWakeLock(): Promise<void> {
    if (this.wakeLock) {
      await this.wakeLock.release();
      this.wakeLock = null;
    }
  }

  // Device Detection
  getDeviceInfo(): {
    isMobile: boolean;
    isTablet: boolean;
    isDesktop: boolean;
    platform: string;
    userAgent: string;
    screenSize: { width: number; height: number };
    pixelRatio: number;
  } {
    const userAgent = navigator.userAgent;
    const screenWidth = window.screen.width;
    const screenHeight = window.screen.height;

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
    const isTablet = /(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(userAgent);
    const isDesktop = !isMobile && !isTablet;

    return {
      isMobile: isMobile && !isTablet,
      isTablet,
      isDesktop,
      platform: this.getPlatform(),
      userAgent,
      screenSize: { width: screenWidth, height: screenHeight },
      pixelRatio: window.devicePixelRatio || 1
    };
  }

  private getPlatform(): string {
    const userAgent = navigator.userAgent;
    if (/android/i.test(userAgent)) return 'android';
    if (/iPad|iPhone|iPod/.test(userAgent)) return 'ios';
    if (/Windows Phone/i.test(userAgent)) return 'windows-phone';
    if (/Windows/i.test(userAgent)) return 'windows';
    if (/Macintosh|MacIntel|MacPPC|Mac68K/i.test(userAgent)) return 'macos';
    if (/Linux/i.test(userAgent)) return 'linux';
    return 'unknown';
  }

  // Touch and Gesture Support
  isTouchDevice(): boolean {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }

  // App Badging (for notifications)
  async setBadge(count: number): Promise<boolean> {
    if ('setAppBadge' in navigator) {
      try {
        await (navigator as any).setAppBadge(count);
        return true;
      } catch (error) {
        console.error('Failed to set app badge:', error);
        return false;
      }
    }
    return false;
  }

  async clearBadge(): Promise<boolean> {
    if ('clearAppBadge' in navigator) {
      try {
        await (navigator as any).clearAppBadge();
        return true;
      } catch (error) {
        console.error('Failed to clear app badge:', error);
        return false;
      }
    }
    return false;
  }

  // Clipboard Access
  async copyToClipboard(text: string): Promise<boolean> {
    if ('clipboard' in navigator) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        return false;
      }
    }
    return false;
  }

  async readFromClipboard(): Promise<string | null> {
    if ('clipboard' in navigator) {
      try {
        return await navigator.clipboard.readText();
      } catch (error) {
        console.error('Failed to read from clipboard:', error);
        return null;
      }
    }
    return null;
  }
}