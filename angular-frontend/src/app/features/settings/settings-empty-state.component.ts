import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';

@Component({
  selector: 'app-settings-empty-state',
  standalone: true,
  imports: [CommonModule, EmptyStateComponent],
  template: `
    <app-empty-state
      theme="neutral"
      size="medium"
      customIcon="⚙️"
      [iconSize]="3"
      [title]="title"
      [description]="description"
      [tips]="settingsTips"
      [tipsTitle]="'Personalize your experience:'"
      [primaryAction]="primaryAction"
      [secondaryAction]="secondaryAction"
      (primaryActionClick)="onConfigureNotifications()"
      (secondaryActionClick)="onSetPreferences()">
    </app-empty-state>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
    }
  `]
})
export class SettingsEmptyStateComponent {
  @Output() configureNotifications = new EventEmitter<void>();
  @Output() setPreferences = new EventEmitter<void>();

  title = "Customize Your Soul Journey";
  description = "Tailor your Dinner First experience to match your preferences and comfort level for meaningful connections.";

  settingsTips = [
    {
      icon: "🔔",
      text: "Set notification preferences for matches and messages"
    },
    {
      icon: "🌙",
      text: "Choose your preferred conversation times and activity periods"
    },
    {
      icon: "🔒",
      text: "Configure privacy settings and photo visibility preferences"
    },
    {
      icon: "💫",
      text: "Adjust matching criteria and distance preferences"
    },
    {
      icon: "🎨",
      text: "Select your preferred theme and display options"
    }
  ];

  primaryAction = {
    text: "Set Up Notifications",
    icon: "🔔"
  };

  secondaryAction = {
    text: "Customize Preferences",
    icon: "⚙️"
  };

  onConfigureNotifications() {
    this.configureNotifications.emit();
  }

  onSetPreferences() {
    this.setPreferences.emit();
  }
}
