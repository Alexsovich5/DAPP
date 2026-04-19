import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSidenavModule } from '@angular/material/sidenav';
import { ThemeService } from './core/services/theme.service';
import { OfflineService } from './core/services/offline.service';
import { ToastComponent } from './shared/components/toast/toast.component';
import { ResponsiveNavComponent } from './shared/navigation/responsive-nav.component';
import { OnboardingManagerComponent } from './shared/components/onboarding-manager/onboarding-manager.component';
import { OfflineStatusComponent } from './shared/components/offline-status/offline-status.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatSidenavModule,
    ToastComponent,
    ResponsiveNavComponent,
    OnboardingManagerComponent,
    OfflineStatusComponent
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'dinner-app';

  constructor(
    private themeService: ThemeService,
    private offlineService: OfflineService
  ) {
    // Theme service will automatically initialize and apply saved theme
    // Offline service constructor already handles PWA initialization
  }
}
