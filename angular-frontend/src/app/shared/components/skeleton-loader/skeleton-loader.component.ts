import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-skeleton-loader',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="skeleton-loader" [ngClass]="type" [style.width]="width" [style.height]="height">
      <div class="skeleton-shimmer"></div>
    </div>
  `,
  styles: [`
    .skeleton-loader {
      background: var(--surface-color, #f8fafc);
      border-radius: 8px;
      overflow: hidden;
      position: relative;
      
      &.card {
        height: 200px;
        border-radius: 12px;
      }
      
      &.text {
        height: 1.2em;
        border-radius: 4px;
      }
      
      &.button {
        height: 48px;
        width: 120px;
        border-radius: 24px;
      }
      
      &.avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
      }
      
      &.list-item {
        height: 72px;
        margin-bottom: 8px;
        border-radius: 8px;
      }
    }

    .skeleton-shimmer {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.4),
        transparent
      );
      animation: shimmer 1.5s ease-in-out infinite;
    }

    .dark-theme .skeleton-loader {
      background: var(--surface-color, #1f2937);
    }

    .dark-theme .skeleton-shimmer {
      background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.1),
        transparent
      );
    }

    @keyframes shimmer {
      0% {
        transform: translateX(-100%);
      }
      100% {
        transform: translateX(100%);
      }
    }

    // Accessibility
    @media (prefers-reduced-motion: reduce) {
      .skeleton-shimmer {
        animation: none;
      }
    }
  `]
})
export class SkeletonLoaderComponent {
  @Input() type: 'card' | 'text' | 'button' | 'avatar' | 'list-item' = 'text';
  @Input() width: string = '100%';
  @Input() height: string = 'auto';
}