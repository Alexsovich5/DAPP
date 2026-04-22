import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { Subscription } from 'rxjs';
import { ProfileService, UserProfileData } from '../../core/services/profile.service';
import {
  DfAvatarComponent,
  DfButtonDirective,
  DfChipComponent,
} from '../../shared/ui';

export interface ProfileView {
  displayName: string;
  location?: string;
  age?: number;
  interests: string[];
  onboardingAnswers: string[];
  photos: { url: string }[];
}

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatIconModule,
    DfButtonDirective,
    DfAvatarComponent,
    DfChipComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss'],
})
export class ProfileComponent implements OnInit, OnDestroy {
  profile: ProfileView | null = null;
  photosCollapsed = true;
  readonly valueLabels = ['VALUES', 'IDEAL EVENING', 'FEELING UNDERSTOOD'];

  private readonly subs = new Subscription();

  constructor(
    private readonly profileService: ProfileService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.subs.add(
      this.profileService.getProfile().subscribe({
        next: (data) => {
          this.profile = this.toView(data);
          this.cdr.markForCheck();
        },
      }),
    );
  }

  ngOnDestroy(): void {
    this.subs.unsubscribe();
  }

  uploadPhoto(): void {
    // Photo upload is handled on the edit screen; kept as a hook for future inline upload.
  }

  private toView(data: UserProfileData): ProfileView {
    const first = data.first_name ?? '';
    const last = data.last_name ?? '';
    const displayName = `${first} ${last}`.trim() || data.username;
    const responses = data.emotional_responses ?? {};
    return {
      displayName,
      location: data.location,
      age: this.computeAge(data.date_of_birth),
      interests: data.interests ?? [],
      onboardingAnswers: [
        responses['relationship_values'] ?? '',
        responses['ideal_evening'] ?? '',
        responses['feeling_understood'] ?? '',
      ].filter((answer) => answer.length > 0),
      photos: data.profile_picture ? [{ url: data.profile_picture }] : [],
    };
  }

  private computeAge(dob?: string): number | undefined {
    if (!dob) return undefined;
    const birth = new Date(dob);
    if (Number.isNaN(birth.getTime())) return undefined;
    const now = new Date();
    let age = now.getFullYear() - birth.getFullYear();
    const m = now.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) age--;
    return age;
  }
}
