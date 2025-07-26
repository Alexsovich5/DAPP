import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SkeletonLoaderComponent } from '../skeleton-loader/skeleton-loader.component';

@Component({
  selector: 'app-loading-screen',
  standalone: true,
  imports: [CommonModule, SkeletonLoaderComponent],
  template: `
    <div class="loading-screen" [ngClass]="screenType">
      
      <!-- Discovery/Matches Loading -->
      <div *ngIf="screenType === 'discovery'" class="discovery-skeleton">
        <app-skeleton-loader type="text" width="60%" height="2rem"></app-skeleton-loader>
        <div class="cards-grid">
          <app-skeleton-loader 
            *ngFor="let item of [1,2,3,4]" 
            type="card"
            class="match-card-skeleton">
          </app-skeleton-loader>
        </div>
      </div>

      <!-- Conversations Loading -->
      <div *ngIf="screenType === 'conversations'" class="conversations-skeleton">
        <app-skeleton-loader type="text" width="40%" height="1.5rem"></app-skeleton-loader>
        <div class="conversation-list">
          <div *ngFor="let item of [1,2,3,4,5]" class="conversation-item">
            <app-skeleton-loader type="avatar"></app-skeleton-loader>
            <div class="conversation-content">
              <app-skeleton-loader type="text" width="70%" height="1.2rem"></app-skeleton-loader>
              <app-skeleton-loader type="text" width="90%" height="1rem"></app-skeleton-loader>
            </div>
          </div>
        </div>
      </div>

      <!-- Profile Loading -->
      <div *ngIf="screenType === 'profile'" class="profile-skeleton">
        <div class="profile-header">
          <app-skeleton-loader type="avatar" width="80px" height="80px"></app-skeleton-loader>
          <div class="profile-info">
            <app-skeleton-loader type="text" width="60%" height="1.5rem"></app-skeleton-loader>
            <app-skeleton-loader type="text" width="40%" height="1rem"></app-skeleton-loader>
          </div>
        </div>
        <div class="profile-sections">
          <app-skeleton-loader type="text" width="30%" height="1.2rem"></app-skeleton-loader>
          <app-skeleton-loader type="text" width="100%" height="4rem"></app-skeleton-loader>
          <app-skeleton-loader type="text" width="25%" height="1.2rem"></app-skeleton-loader>
          <app-skeleton-loader type="text" width="80%" height="2rem"></app-skeleton-loader>
        </div>
      </div>

      <!-- Soul Connection Animation -->
      <div class="soul-connection-animation">
        <div class="soul-orb primary">✨</div>
        <div class="connection-pulse"></div>
        <div class="soul-orb secondary">💫</div>
      </div>

      <p class="loading-text">{{ loadingText }}</p>
    </div>
  `,
  styles: [`
    .loading-screen {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 400px;
      padding: 2rem;
      position: relative;
    }

    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
      margin-top: 2rem;
      width: 100%;
      max-width: 1200px;
    }

    .conversation-list {
      width: 100%;
      max-width: 600px;
      margin-top: 1.5rem;
    }

    .conversation-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      margin-bottom: 0.5rem;
    }

    .conversation-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .profile-header {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .profile-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .profile-sections {
      width: 100%;
      max-width: 500px;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    // Soul Connection Animation
    .soul-connection-animation {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 2rem;
      margin: 2rem 0;
      position: relative;
    }

    .soul-orb {
      font-size: 3rem;
      animation: pulse 2s ease-in-out infinite;
      
      &.primary {
        animation-delay: 0s;
      }
      
      &.secondary {
        animation-delay: 1s;
      }
    }

    .connection-pulse {
      position: absolute;
      width: 100%;
      height: 2px;
      background: linear-gradient(
        90deg,
        transparent,
        var(--primary-color, #ec4899),
        transparent
      );
      animation: connection 2s ease-in-out infinite;
    }

    .loading-text {
      font-size: 1.1rem;
      color: var(--text-secondary, #6b7280);
      text-align: center;
      margin-top: 1rem;
      font-weight: 500;
    }

    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
        opacity: 0.8;
      }
      50% {
        transform: scale(1.1);
        opacity: 1;
      }
    }

    @keyframes connection {
      0% {
        opacity: 0;
        transform: scaleX(0);
      }
      50% {
        opacity: 1;
        transform: scaleX(1);
      }
      100% {
        opacity: 0;
        transform: scaleX(0);
      }
    }

    // Mobile responsive
    @media (max-width: 768px) {
      .loading-screen {
        padding: 1rem;
        min-height: 300px;
      }

      .cards-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
      }

      .soul-orb {
        font-size: 2.5rem;
      }

      .soul-connection-animation {
        gap: 1.5rem;
      }
    }

    // Accessibility
    @media (prefers-reduced-motion: reduce) {
      .soul-orb, .connection-pulse {
        animation: none;
      }
    }
  `]
})
export class LoadingScreenComponent {
  @Input() screenType: 'discovery' | 'conversations' | 'profile' | 'general' = 'general';
  @Input() loadingText: string = 'Connecting souls...';
}