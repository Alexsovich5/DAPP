import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';

@Component({
  selector: 'app-profile-empty-state',
  standalone: true,
  imports: [CommonModule, EmptyStateComponent],
  template: `
    <app-empty-state
      theme="profile"
      size="large"
      illustration="profile"
      [title]="title"
      [description]="description"
      [tips]="profileTips"
      [tipsTitle]="'Complete your soul profile:'"
      [showProgress]="true"
      [progressValue]="progressValue"
      [progressText]="progressText"
      [showSoulOrb]="showSoulOrb"
      [soulOrbType]="'primary'"
      [soulOrbState]="'dormant'"
      [soulOrbEnergy]="1"
      [primaryAction]="primaryAction"
      [secondaryAction]="secondaryAction"
      (primaryActionClick)="onCompleteProfile()"
      (secondaryActionClick)="onAddPhotos()">
    </app-empty-state>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
    }
  `]
})
export class ProfileEmptyStateComponent {
  @Output() completeProfile = new EventEmitter<void>();
  @Output() addPhotos = new EventEmitter<void>();

  title = "Your Soul Profile Awaits Completion";
  description = "Share your authentic self to attract meaningful connections. A complete profile increases your match quality by 75%.";
  showSoulOrb = false; // Use illustration instead

  // This would be calculated based on actual profile completion
  progressValue = 35; // Example: 35% complete
  progressText = "35% complete - Add your emotional essence to shine brighter";

  profileTips = [
    {
      icon: "💭",
      text: "Share your life philosophy and core values that guide you"
    },
    {
      icon: "🎯",
      text: "Describe your interests and passions in authentic detail"
    },
    {
      icon: "💖",
      text: "Express what you're looking for in a meaningful connection"
    },
    {
      icon: "✨",
      text: "Add thoughtful photos that reflect your genuine personality"
    },
    {
      icon: "🌟",
      text: "Write prompts that invite deeper conversation and understanding"
    }
  ];

  primaryAction = {
    text: "Complete Your Profile",
    icon: "✨"
  };

  secondaryAction = {
    text: "Add Photos",
    icon: "📸"
  };

  onCompleteProfile() {
    this.completeProfile.emit();
  }

  onAddPhotos() {
    this.addPhotos.emit();
  }
}
