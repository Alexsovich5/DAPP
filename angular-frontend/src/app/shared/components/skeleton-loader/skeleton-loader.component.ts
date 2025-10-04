import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-skeleton-loader',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="skeleton-loader"
      [ngClass]="[type, variant, size]"
      [style.width]="width"
      [style.height]="height"
      [style.border-radius]="customBorderRadius"
      [attr.aria-label]="ariaLabel"
      [attr.aria-hidden]="true"
      role="presentation">
      <div class="skeleton-shimmer" *ngIf="animated"></div>

      <!-- Soul orb specific skeleton -->
      <div class="soul-orb-skeleton" *ngIf="type === 'soul-orb'">
        <div class="orb-core"></div>
        <div class="orb-rings">
          <div class="orb-ring" *ngFor="let ring of [1,2,3]"></div>
        </div>
      </div>

      <!-- Compatibility radar skeleton -->
      <div class="radar-skeleton" *ngIf="type === 'compatibility-radar'">
        <div class="radar-center"></div>
        <div class="radar-axes">
          <div class="radar-axis" *ngFor="let axis of [1,2,3,4,5]"></div>
        </div>
        <div class="radar-labels">
          <div class="radar-label" *ngFor="let label of [1,2,3,4,5]"></div>
        </div>
      </div>

      <!-- Profile card skeleton -->
      <div class="profile-skeleton" *ngIf="type === 'profile-card'">
        <div class="profile-avatar"></div>
        <div class="profile-info">
          <div class="profile-name"></div>
          <div class="profile-details"></div>
          <div class="profile-bio"></div>
        </div>
      </div>

      <!-- Message skeleton -->
      <div class="message-skeleton" *ngIf="type === 'message'">
        <div class="message-avatar" *ngIf="variant === 'received'"></div>
        <div class="message-content">
          <div class="message-text"></div>
          <div class="message-time"></div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .skeleton-loader {
      background: linear-gradient(90deg,
        var(--skeleton-base, #f1f5f9) 0%,
        var(--skeleton-highlight, #e2e8f0) 50%,
        var(--skeleton-base, #f1f5f9) 100%);
      background-size: 200% 100%;
      border-radius: 8px;
      overflow: hidden;
      position: relative;
      animation: skeleton-pulse 1.5s ease-in-out infinite;
    }

    /* Basic types */
    .skeleton-loader.card {
      height: 200px;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .skeleton-loader.text {
      height: 1.2em;
      border-radius: 4px;
    }

    .skeleton-loader.button {
      height: 48px;
      width: 120px;
      border-radius: 24px;
    }

    .skeleton-loader.avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
    }

    .skeleton-loader.list-item {
      height: 72px;
      margin-bottom: 8px;
      border-radius: 8px;
    }

    /* Soul-specific skeletons */
    .skeleton-loader.soul-orb {
      width: 120px;
      height: 120px;
      border-radius: 50%;
      background: radial-gradient(circle,
        var(--skeleton-base, #f1f5f9) 30%,
        var(--skeleton-highlight, #e2e8f0) 50%,
        var(--skeleton-base, #f1f5f9) 70%);
      position: relative;
    }

    .soul-orb-skeleton {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      height: 100%;
    }

    .orb-core {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 40%;
      height: 40%;
      border-radius: 50%;
      background: var(--skeleton-highlight, #e2e8f0);
      animation: orb-pulse 2s ease-in-out infinite;
    }

    .orb-rings {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      height: 100%;
    }

    .orb-ring {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      border: 2px solid var(--skeleton-highlight, #e2e8f0);
      border-radius: 50%;
      animation: ring-expand 3s ease-in-out infinite;
    }

    .orb-ring:nth-child(1) {
      width: 60%;
      height: 60%;
      animation-delay: 0s;
    }

    .orb-ring:nth-child(2) {
      width: 80%;
      height: 80%;
      animation-delay: 0.5s;
    }

    .orb-ring:nth-child(3) {
      width: 100%;
      height: 100%;
      animation-delay: 1s;
    }

    /* Compatibility radar skeleton */
    .skeleton-loader.compatibility-radar {
      width: 300px;
      height: 300px;
      border-radius: 16px;
      background: radial-gradient(circle,
        transparent 20%,
        var(--skeleton-base, #f1f5f9) 40%,
        var(--skeleton-highlight, #e2e8f0) 60%,
        var(--skeleton-base, #f1f5f9) 80%);
      position: relative;
    }

    .radar-skeleton {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 80%;
      height: 80%;
    }

    .radar-center {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--skeleton-highlight, #e2e8f0);
    }

    .radar-axes {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      height: 100%;
    }

    .radar-axis {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 50%;
      height: 1px;
      background: var(--skeleton-highlight, #e2e8f0);
      transform-origin: left center;
      animation: axis-fade 2s ease-in-out infinite;
    }

    .radar-axis:nth-child(1) { transform: translate(0, -50%) rotate(0deg); }
    .radar-axis:nth-child(2) { transform: translate(0, -50%) rotate(72deg); }
    .radar-axis:nth-child(3) { transform: translate(0, -50%) rotate(144deg); }
    .radar-axis:nth-child(4) { transform: translate(0, -50%) rotate(216deg); }
    .radar-axis:nth-child(5) { transform: translate(0, -50%) rotate(288deg); }

    .radar-labels {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 120%;
      height: 120%;
    }

    .radar-label {
      position: absolute;
      width: 60px;
      height: 12px;
      background: var(--skeleton-highlight, #e2e8f0);
      border-radius: 6px;
      animation: label-pulse 2.5s ease-in-out infinite;
    }

    .radar-label:nth-child(1) { top: 10%; left: 45%; animation-delay: 0s; }
    .radar-label:nth-child(2) { top: 25%; right: 10%; animation-delay: 0.2s; }
    .radar-label:nth-child(3) { bottom: 25%; right: 10%; animation-delay: 0.4s; }
    .radar-label:nth-child(4) { bottom: 10%; left: 45%; animation-delay: 0.6s; }
    .radar-label:nth-child(5) { top: 25%; left: 10%; animation-delay: 0.8s; }

    /* Profile card skeleton */
    .skeleton-loader.profile-card {
      width: 100%;
      height: 160px;
      border-radius: 16px;
      padding: 1rem;
      background: linear-gradient(135deg,
        var(--skeleton-base, #f1f5f9) 0%,
        var(--skeleton-highlight, #e2e8f0) 50%,
        var(--skeleton-base, #f1f5f9) 100%);
    }

    .profile-skeleton {
      display: flex;
      gap: 1rem;
      height: 100%;
    }

    .profile-avatar {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      background: var(--skeleton-highlight, #e2e8f0);
      flex-shrink: 0;
      animation: avatar-glow 2s ease-in-out infinite;
    }

    .profile-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      padding-top: 0.5rem;
    }

    .profile-name {
      width: 60%;
      height: 20px;
      background: var(--skeleton-highlight, #e2e8f0);
      border-radius: 4px;
      animation: profile-pulse 1.8s ease-in-out infinite;
    }

    .profile-details {
      width: 80%;
      height: 16px;
      background: var(--skeleton-highlight, #e2e8f0);
      border-radius: 4px;
      animation: profile-pulse 1.8s ease-in-out infinite 0.3s;
    }

    .profile-bio {
      width: 100%;
      height: 12px;
      background: var(--skeleton-highlight, #e2e8f0);
      border-radius: 4px;
      animation: profile-pulse 1.8s ease-in-out infinite 0.6s;
    }

    /* Message skeleton */
    .skeleton-loader.message {
      width: 100%;
      height: 60px;
      border-radius: 18px;
      margin-bottom: 8px;
      padding: 0.75rem;
    }

    .skeleton-loader.message.sent {
      background: linear-gradient(90deg,
        var(--primary-color-light, #fce7f3) 0%,
        var(--primary-color-lighter, #fdf2f8) 50%,
        var(--primary-color-light, #fce7f3) 100%);
      margin-left: 20%;
      border-bottom-right-radius: 6px;
    }

    .skeleton-loader.message.received {
      background: var(--skeleton-base, #f1f5f9);
      margin-right: 20%;
      border-bottom-left-radius: 6px;
    }

    .message-skeleton {
      display: flex;
      gap: 0.75rem;
      height: 100%;
      align-items: center;
    }

    .message-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--skeleton-highlight, #e2e8f0);
      flex-shrink: 0;
    }

    .message-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .message-text {
      width: 85%;
      height: 16px;
      background: var(--skeleton-highlight, #e2e8f0);
      border-radius: 4px;
    }

    .message-time {
      width: 40%;
      height: 12px;
      background: var(--skeleton-highlight, #e2e8f0);
      border-radius: 4px;
      opacity: 0.6;
    }

    /* Shimmer effect */
    .skeleton-shimmer {
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg,
        transparent 0%,
        rgba(255, 255, 255, 0.4) 50%,
        transparent 100%);
      animation: skeleton-shimmer 2s ease-in-out infinite;
    }

    /* Size variants */
    .skeleton-loader.xs { font-size: 0.75rem; }
    .skeleton-loader.sm { font-size: 0.875rem; }
    .skeleton-loader.md { font-size: 1rem; }
    .skeleton-loader.lg { font-size: 1.125rem; }
    .skeleton-loader.xl { font-size: 1.25rem; }

    /* Animations */
    @keyframes skeleton-pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }

    @keyframes skeleton-shimmer {
      0% { left: -100%; }
      50% { left: 0%; }
      100% { left: 100%; }
    }

    @keyframes orb-pulse {
      0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
      50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.8; }
    }

    @keyframes ring-expand {
      0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
      50% { transform: translate(-50%, -50%) scale(1.05); opacity: 0.4; }
    }

    @keyframes axis-fade {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 1; }
    }

    @keyframes label-pulse {
      0%, 100% { opacity: 0.7; }
      50% { opacity: 1; }
    }

    @keyframes avatar-glow {
      0%, 100% { opacity: 0.8; }
      50% { opacity: 1; }
    }

    @keyframes profile-pulse {
      0%, 100% { opacity: 0.7; }
      50% { opacity: 1; }
    }

    /* Dark theme support */
    .dark-theme .skeleton-loader {
      --skeleton-base: #374151;
      --skeleton-highlight: #4b5563;
    }

    .dark-theme .skeleton-shimmer {
      background: linear-gradient(90deg,
        transparent 0%,
        rgba(255, 255, 255, 0.1) 50%,
        transparent 100%);
    }

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
      .skeleton-loader,
      .skeleton-shimmer,
      .orb-core,
      .orb-ring,
      .radar-axis,
      .radar-label,
      .profile-avatar,
      .profile-name,
      .profile-details,
      .profile-bio {
        animation: none !important;
      }
    }

    /* Mobile optimizations */
    @media (max-width: 768px) {
      .skeleton-loader.compatibility-radar {
        width: 250px;
        height: 250px;
      }

      .skeleton-loader.profile-card {
        height: 140px;
        padding: 0.75rem;
      }

      .profile-avatar {
        width: 60px;
        height: 60px;
      }

      .profile-info {
        gap: 0.5rem;
      }
    }
  `]
})
export class SkeletonLoaderComponent {
  @Input() type: 'card' | 'text' | 'button' | 'avatar' | 'list-item' | 'soul-orb' | 'compatibility-radar' | 'profile-card' | 'message' = 'text';
  @Input() variant: 'sent' | 'received' | 'default' = 'default';
  @Input() size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'md';
  @Input() width: string = '100%';
  @Input() height: string = 'auto';
  @Input() customBorderRadius?: string;
  @Input() animated: boolean = true;
  @Input() ariaLabel: string = 'Loading content';
}
