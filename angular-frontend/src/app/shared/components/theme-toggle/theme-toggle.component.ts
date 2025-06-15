import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ThemeService } from '../../../core/services/theme.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatTooltipModule],
  template: `
    <button 
      mat-icon-button 
      [matTooltip]="(isDarkMode$ | async) ? 'Switch to light mode' : 'Switch to dark mode'"
      (click)="toggleTheme()"
      class="theme-toggle-btn"
      [attr.aria-label]="(isDarkMode$ | async) ? 'Switch to light mode' : 'Switch to dark mode'">
      <mat-icon>{{ (isDarkMode$ | async) ? 'light_mode' : 'dark_mode' }}</mat-icon>
    </button>
  `,
  styles: [`
    .theme-toggle-btn {
      transition: all 0.3s ease;
      
      &:hover {
        transform: scale(1.1);
      }
      
      mat-icon {
        font-size: 24px;
        height: 24px;
        width: 24px;
      }
    }
  `]
})
export class ThemeToggleComponent {
  isDarkMode$: Observable<boolean>;

  constructor(private themeService: ThemeService) {
    this.isDarkMode$ = new Observable(subscriber => {
      this.themeService.currentTheme$.subscribe(theme => {
        subscriber.next(theme === 'dark');
      });
    });
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }
}