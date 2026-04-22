import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';

interface Tab {
  route: string;
  icon: string;
  label: string;
}

@Component({
  selector: 'app-mobile-tab-bar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, MatIconModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <nav class="mobile-tab-bar" aria-label="Primary">
      <a *ngFor="let tab of tabs"
         class="mobile-tab-bar__tab"
         [routerLink]="tab.route"
         routerLinkActive="is-active"
         [attr.aria-label]="tab.label">
        <mat-icon class="mobile-tab-bar__icon">{{ tab.icon }}</mat-icon>
        <span class="mobile-tab-bar__label">{{ tab.label }}</span>
      </a>
    </nav>
  `,
  styleUrls: ['./mobile-tab-bar.component.scss'],
})
export class MobileTabBarComponent {
  readonly tabs: Tab[] = [
    { route: '/discover',    icon: 'explore',    label: 'Discover' },
    { route: '/connections', icon: 'group',      label: 'Connections' },
    { route: '/messages',    icon: 'forum',      label: 'Messages' },
    { route: '/revelations', icon: 'auto_stories', label: 'Revelations' },
    { route: '/profile',     icon: 'person',     label: 'Profile' },
  ];
}
