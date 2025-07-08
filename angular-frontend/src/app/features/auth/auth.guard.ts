import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router, CanActivate, UrlTree, ActivatedRouteSnapshot } from '@angular/router';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from '../../core/services/auth.service';
import { StorageService } from '../../core/services/storage.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  private isBrowser: boolean;

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
    private readonly storage: StorageService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  canActivate(route: ActivatedRouteSnapshot): Observable<boolean | UrlTree> {
    // During SSR, allow navigation (will be re-evaluated on client)
    if (!this.isBrowser || !this.storage) {
      return of(true);
    }

    return of(this.authService.isAuthenticated()).pipe(
      map(isAuthenticated => {
        if (!isAuthenticated) {
          return this.router.createUrlTree(['/login']);
        }

        // Check if onboarding is completed for non-onboarding routes
        const currentPath = route.routeConfig?.path;
        const isOnboardingRoute = currentPath?.startsWith('onboarding');
        const isOnboardingComplete = this.storage.getItem('onboarding_completed') === 'true';

        if (!isOnboardingRoute && !isOnboardingComplete) {
          // User is authenticated but hasn't completed onboarding
          return this.router.createUrlTree(['/onboarding']);
        }

        return true;
      })
    );
  }
}
