import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject, Observable } from 'rxjs';
import { StorageService } from '@core/services/storage.service';

export type Theme = 'light' | 'dark';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly storageKey = 'dinner-app-theme';
  private readonly themeSubject = new BehaviorSubject<Theme>(this.getInitialTheme());
  private readonly isBrowser: boolean;
  
  readonly currentTheme$ = this.themeSubject.asObservable();

  constructor(
    private readonly storage: StorageService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    
    // Apply initial theme on service creation
    this.applyTheme(this.themeSubject.value);
    
    // Listen for system theme changes (browser only)
    if (this.isBrowser && typeof window !== 'undefined' && window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!this.hasStoredTheme()) {
          this.setTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
  }

  get currentTheme(): Theme {
    return this.themeSubject.value;
  }

  get isDarkMode(): boolean {
    return this.currentTheme === 'dark';
  }

  setTheme(theme: Theme): void {
    if (this.storage) {
      this.storage.setItem(this.storageKey, theme);
    }
    this.themeSubject.next(theme);
    this.applyTheme(theme);
  }

  toggleTheme(): void {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }

  private getInitialTheme(): Theme {
    // Check localStorage first (if storage is available)
    if (this.storage) {
      const storedTheme = this.storage.getItem(this.storageKey) as Theme;
      if (storedTheme === 'light' || storedTheme === 'dark') {
        return storedTheme;
      }
    }

    // Fall back to system preference (browser only)
    if (this.isBrowser && typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }

    // Default to light theme
    return 'light';
  }

  private hasStoredTheme(): boolean {
    return this.storage ? this.storage.getItem(this.storageKey) !== null : false;
  }

  private applyTheme(theme: Theme): void {
    if (!this.isBrowser || typeof document === 'undefined') {
      return;
    }
    
    const body = document.body;
    const htmlElement = document.documentElement;
    
    // Remove existing theme classes
    body.classList.remove('light-theme', 'dark-theme');
    htmlElement.classList.remove('light-theme', 'dark-theme');
    
    // Add new theme class
    const themeClass = `${theme}-theme`;
    body.classList.add(themeClass);
    htmlElement.classList.add(themeClass);
    
    // Update meta theme-color for mobile browsers
    this.updateMetaThemeColor(theme);
  }

  private updateMetaThemeColor(theme: Theme): void {
    if (!this.isBrowser || typeof document === 'undefined') {
      return;
    }
    
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    const color = theme === 'dark' ? '#111827' : '#ffffff';
    
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', color);
    } else {
      const meta = document.createElement('meta');
      meta.name = 'theme-color';
      meta.content = color;
      document.getElementsByTagName('head')[0].appendChild(meta);
    }
  }
}