import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';

@Component({
  selector: 'app-revelations-empty-state',
  standalone: true,
  imports: [CommonModule, EmptyStateComponent],
  template: `
    <app-empty-state
      theme="revelations"
      size="large"
      illustration="revelations"
      [title]="title"
      [description]="description"
      [tips]="revelationTips"
      [tipsTitle]="'Your 7-day soul journey:'"
      [showProgress]="true"
      [progressValue]="0"
      [progressText]="progressText"
      [showSoulOrb]="showSoulOrb"
      [soulOrbType]="'primary'"
      [soulOrbState]="'dormant'"
      [soulOrbEnergy]="1"
      [primaryAction]="primaryAction"
      [secondaryAction]="secondaryAction"
      (primaryActionClick)="onStartJourney()"
      (secondaryActionClick)="onLearnAboutRevelations()">
    </app-empty-state>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
    }
  `]
})
export class RevelationsEmptyStateComponent {
  @Output() startJourney = new EventEmitter<void>();
  @Output() learnAboutRevelations = new EventEmitter<void>();

  title = "Begin Your Soul Journey";
  description = "Share meaningful revelations with your matches over 7 days. Each day brings you closer to authentic connection before photo reveals.";
  showSoulOrb = false; // Use illustration instead
  progressText = "Ready to begin your revelation journey";

  revelationTips = [
    {
      icon: "looks_one",
      text: "Day 1: Share a core value that guides your life decisions"
    },
    {
      icon: "looks_two",
      text: "Day 2: Describe a meaningful experience that shaped you"
    },
    {
      icon: "looks_3",
      text: "Day 3: Share a hope or dream close to your heart"
    },
    {
      icon: "looks_4",
      text: "Day 4: Reveal what genuinely makes you laugh and feel joy"
    },
    {
      icon: "looks_5",
      text: "Day 5: Share a challenge you overcame and learned from"
    },
    {
      icon: "looks_6",
      text: "Day 6: Describe your vision of an ideal emotional connection"
    },
    {
      icon: "filter_7",
      text: "Day 7: Mutual photo reveal and plan your first soul dinner"
    }
  ];

  primaryAction = {
    text: "Begin Soul Revelations",
    icon: "auto_awesome"
  };

  secondaryAction = {
    text: "Learn More",
    icon: "menu_book"
  };

  onStartJourney() {
    this.startJourney.emit();
  }

  onLearnAboutRevelations() {
    this.learnAboutRevelations.emit();
  }
}
