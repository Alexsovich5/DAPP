import { Injectable } from '@angular/core';
import { Router, CanActivate, UrlTree } from '@angular/router';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from '../../core/services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
    private readonly authService: AuthService,
    private readonly router: Router
  ) {}

  canActivate(): Observable<boolean | UrlTree> {
    // Convert the method call to an observable using 'of'
    return of(this.authService.isAuthenticated()).pipe(
      map(isAuthenticated => {
        if (isAuthenticated) {
          return true;
        }
        return this.router.createUrlTree(['/login']);
      })
    );
  }
}
