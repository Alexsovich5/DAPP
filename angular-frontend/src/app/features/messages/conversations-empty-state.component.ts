import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';

@Component({
  selector: 'app-conversations-empty-state',
  standalone: true,
  imports: [CommonModule, EmptyStateComponent],
  template: `
    <app-empty-state
      theme="conversations"
      size="large"
      illustration="conversations"
      [title]="title"
      [description]="description"
      [tips]="conversationTips"
      [tipsTitle]="'How to start meaningful conversations:'"
      [showSoulOrb]="showSoulOrb"
      [soulOrbType]="'secondary'"
      [soulOrbState]="'connecting'"
      [soulOrbEnergy]="2"
      [primaryAction]="primaryAction"
      [secondaryAction]="secondaryAction"
      (primaryActionClick)="onDiscoverMatches()"
      (secondaryActionClick)="onLearnConversationTips()">
    </app-empty-state>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
    }
  `]
})
export class ConversationsEmptyStateComponent {
  @Output() discoverMatches = new EventEmitter<void>();
  @Output() learnConversationTips = new EventEmitter<void>();

  title = "Your First Heart Connection Awaits";
  description = "Once you connect with compatible souls, your conversations will bloom here. Start by discovering potential matches.";
  showSoulOrb = false; // Use illustration instead

  conversationTips = [
    {
      icon: "💭",
      text: "Ask about their dreams and aspirations rather than surface topics"
    },
    {
      icon: "🎯", 
      text: "Share personal stories and experiences that shaped you"
    },
    {
      icon: "🌱",
      text: "Focus on values and beliefs rather than just hobbies"
    },
    {
      icon: "💝",
      text: "Be vulnerable and authentic - it creates deeper bonds"
    },
    {
      icon: "🌟",
      text: "Listen actively and ask follow-up questions to show genuine interest"
    }
  ];

  primaryAction = {
    text: "Find Soul Connections",
    icon: "💫"
  };

  secondaryAction = {
    text: "Conversation Guide", 
    icon: "📖"
  };

  onDiscoverMatches() {
    this.discoverMatches.emit();
  }

  onLearnConversationTips() {
    this.learnConversationTips.emit();
  }
}