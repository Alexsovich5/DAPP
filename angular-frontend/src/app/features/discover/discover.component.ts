import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { DiscoverService } from '../../core/services/discover.service';

interface PotentialMatch {
  _id: string;
  firstName: string;
  lastName: string;
  profilePictures: string[];
  bio?: string;
  dateOfBirth: string;
  interests?: string[];
  dietaryPreferences?: string[];
  lastActive?: Date;
  distance?: number;
  matchPercentage?: number;
}

@Component({
  selector: 'app-discover',
  templateUrl: './discover.component.html',
  styleUrls: ['./discover.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatDividerModule,
    MatChipsModule,
    MatTooltipModule
  ],
  animations: [
    trigger('cardAnimation', [
      state('default', style({
        transform: 'none'
      })),
      state('like', style({
        transform: 'translate(150%) rotate(30deg)',
        opacity: 0
      })),
      state('dislike', style({
        transform: 'translate(-150%) rotate(-30deg)',
        opacity: 0
      })),
      transition('default => like', animate('400ms ease-out')),
      transition('default => dislike', animate('400ms ease-out'))
    ])
  ]
})
export class DiscoverComponent implements OnInit {
  profiles: PotentialMatch[] = [];
  currentMatch: PotentialMatch | null = null;
  isLoading = false;
  error: string | null = null;
  animationState = 'default';
  swipeCoord?: [number, number];
  swipeTime?: number;
  showSwipeHint = true;
  readonly SWIPE_THRESHOLD = 50;

  constructor(private readonly discoverService: DiscoverService) {}

  ngOnInit(): void {
    this.loadProfiles();
  }

  loadProfiles(): void {
    this.isLoading = true;
    this.error = null;
    this.discoverService.getMatches().subscribe({
      next: (profiles) => {
        this.profiles = profiles;
        this.currentMatch = profiles[0] ?? null;
      },
      error: (err) => {
        this.error = err.message ?? 'Failed to load matches';
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }

  calculateAge(dateOfBirth: string): number {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  }

  isRecentlyActive(lastActive: Date | undefined): boolean {
    if (!lastActive) return false;
    const now = new Date();
    const activeTime = new Date(lastActive);
    return now.getTime() - activeTime.getTime() < 5 * 60 * 1000; // 5 minutes
  }

  getLastActiveText(lastActive: Date | undefined): string {
    if (!lastActive) return 'Offline';
    const now = new Date();
    const activeTime = new Date(lastActive);
    const diffMinutes = Math.floor((now.getTime() - activeTime.getTime()) / (60 * 1000));

    if (diffMinutes < 5) return 'Online';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;

    return activeTime.toLocaleDateString();
  }

  onSwipeStart(event: TouchEvent): void {
    const touch = event.touches[0];
    this.swipeCoord = [touch.clientX, touch.clientY];
    this.swipeTime = new Date().getTime();
  }

  onSwipeMove(event: TouchEvent): void {
    if (!this.swipeCoord) return;

    const touch = event.touches[0];
    const deltaX = touch.clientX - this.swipeCoord[0];
    const deltaY = touch.clientY - this.swipeCoord[1];

    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      event.preventDefault();
    }
  }

  onSwipeEnd(event: TouchEvent): void {
    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - (this.swipeCoord?.[0] ?? 0);
    const deltaY = touch.clientY - (this.swipeCoord?.[1] ?? 0);
    const time = new Date().getTime() - (this.swipeTime ?? 0);

    if (time < 500) { // Short swipe
      if (Math.abs(deltaX) > this.SWIPE_THRESHOLD) {
        if (deltaX > 0) {
          this.onLike(this.currentMatch?._id ?? '');
        } else {
          this.onDislike(this.currentMatch?._id ?? '');
        }
      }
    }

    this.swipeCoord = undefined;
    this.swipeTime = undefined;
  }

  onLike(matchId: string): void {
    if (!matchId || this.animationState !== 'default') return;

    this.animationState = 'like';
    this.discoverService.likeProfile(matchId).subscribe({
      next: () => {
        this.showNextProfile();
      },
      error: (err: Error) => {
        this.error = err.message ?? 'Failed to like profile';
        this.animationState = 'default';
      }
    });
  }

  onDislike(matchId: string): void {
    if (!matchId || this.animationState !== 'default') return;

    this.animationState = 'dislike';
    this.discoverService.dislikeProfile(matchId).subscribe({
      next: () => {
        this.showNextProfile();
      },
      error: (err: Error) => {
        this.error = err.message ?? 'Failed to pass on profile';
        this.animationState = 'default';
      }
    });
  }

  private showNextProfile(): void {
    setTimeout(() => {
      this.profiles = this.profiles.slice(1);
      this.currentMatch = this.profiles[0] ?? null;
      this.animationState = 'default';
      if (this.profiles.length === 0) {
        this.loadProfiles();
      }
    }, 400);
  }
}
