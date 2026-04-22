import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { BreakpointObserver } from '@angular/cdk/layout';
import { Observable, map } from 'rxjs';
import { DesktopTopNavComponent } from './desktop-top-nav.component';
import { MobileTabBarComponent } from './mobile-tab-bar.component';

@Component({
  selector: 'app-responsive-nav',
  standalone: true,
  imports: [CommonModule, DesktopTopNavComponent, MobileTabBarComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ng-container *ngIf="isDesktop$ | async; else mobileTpl">
      <app-desktop-top-nav></app-desktop-top-nav>
    </ng-container>
    <ng-template #mobileTpl>
      <app-mobile-tab-bar></app-mobile-tab-bar>
    </ng-template>
  `,
})
export class ResponsiveNavComponent {
  readonly isDesktop$: Observable<boolean>;

  constructor(breakpoints: BreakpointObserver) {
    this.isDesktop$ = breakpoints.observe('(min-width: 768px)').pipe(map(s => s.matches));
  }
}
