import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';

@Component({
  selector: 'app-discover-empty-state',
  standalone: true,
  imports: [CommonModule, EmptyStateComponent],
  template: `
    <app-empty-state
      theme="discovery"
      size="large"
      illustration="discovery"
      [title]="title"
      [description]="description"
      [tips]="discoveryTips"
      [showSoulOrb]="showSoulOrb"
      [soulOrbType]="'primary'"
      [soulOrbState]="'dormant'"
      [soulOrbEnergy]="3"
      [primaryAction]="primaryAction"
      [secondaryAction]="secondaryAction"
      (primaryActionClick)="onRefreshMatches()"
      (secondaryActionClick)="onUpdateProfile()">
    </app-empty-state>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
    }
  `]
})
export class DiscoverEmptyStateComponent {
  @Output() refreshMatches = new EventEmitter<void>();
  @Output() updateProfile = new EventEmitter<void>();

  title = "Your Soul Connections Await";
  description = "We're searching the universe for hearts that resonate with yours. Great connections take time to discover.";
  showSoulOrb = false; // Use illustration instead

  discoveryTips = [
    {
      icon: "✨",
      text: "Complete your emotional profile to help us find deeper connections"
    },
    {
      icon: "💫", 
      text: "Share your authentic interests and values for better matches"
    },
    {
      icon: "🌟",
      text: "Be patient - meaningful soul connections are worth the wait"
    },
    {
      icon: "💖",
      text: "Quality over quantity: we prioritize compatible souls over endless options"
    }
  ];

  primaryAction = {
    text: "Search for Soul Matches",
    icon: "🔍"
  };

  secondaryAction = {
    text: "Enhance Your Profile", 
    icon: "✨"
  };

  onRefreshMatches() {
    this.refreshMatches.emit();
  }

  onUpdateProfile() {
    this.updateProfile.emit();
  }
}