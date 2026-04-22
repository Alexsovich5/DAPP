import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { DfAvatarComponent } from '../ui/avatar/df-avatar.component';

interface Tab { route: string; label: string; }

@Component({
  selector: 'app-desktop-top-nav',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, MatIconModule, MatMenuModule, DfAvatarComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="desktop-top-nav" role="banner">
      <a class="desktop-top-nav__logo" routerLink="/" aria-label="Dinner First home">
        <span class="display-serif">Dinner First</span>
      </a>
      <nav class="desktop-top-nav__tabs" aria-label="Primary">
        <a *ngFor="let tab of tabs"
           class="desktop-top-nav__tab"
           [routerLink]="tab.route"
           routerLinkActive="is-active">{{ tab.label }}</a>
      </nav>
      <div class="desktop-top-nav__actions">
        <button class="desktop-top-nav__bell" mat-icon-button aria-label="Notifications">
          <mat-icon>notifications</mat-icon>
        </button>
        <button class="desktop-top-nav__avatar-trigger"
                [matMenuTriggerFor]="avatarMenu"
                aria-label="Account menu">
          <df-avatar name="You" size="sm"></df-avatar>
        </button>
        <mat-menu #avatarMenu="matMenu">
          <a mat-menu-item routerLink="/profile">Profile</a>
          <a mat-menu-item routerLink="/settings">Settings</a>
          <a mat-menu-item routerLink="/auth/logout">Sign out</a>
        </mat-menu>
      </div>
    </header>
  `,
  styleUrls: ['./desktop-top-nav.component.scss'],
})
export class DesktopTopNavComponent {
  readonly tabs: Tab[] = [
    { route: '/discover',    label: 'Discover' },
    { route: '/connections', label: 'Connections' },
    { route: '/messages',    label: 'Messages' },
    { route: '/revelations', label: 'Revelations' },
  ];
}
