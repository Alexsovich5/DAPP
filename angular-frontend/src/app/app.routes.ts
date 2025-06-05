import { Routes } from '@angular/router';
import { AuthGuard } from './features/auth/auth.guard';
import { LandingComponent } from './features/landing/landing.component';

export const routes: Routes = [
  { path: '', component: LandingComponent },
  {
    path: 'login',
    loadChildren: () => import('./features/auth/login/login.module').then(m => m.LoginModule)
  },
  {
    path: 'register',
    loadChildren: () => import('./features/auth/register/register.module').then(m => m.RegisterModule)
  },
  {
    path: 'forgot-password',
    loadChildren: () => import('./features/auth/forgot-password/forgot-password.module').then(m => m.ForgotPasswordModule)
  },
  {
    path: 'onboarding',
    loadChildren: () => import('./features/onboarding/onboarding.module').then(m => m.OnboardingModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'profile',
    loadChildren: () => import('./features/profile/profile.module').then(m => m.ProfileModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'discover',
    loadChildren: () => import('./features/discover/discover.module').then(m => m.DiscoverModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'connections',
    loadChildren: () => import('./features/connections/connections.module').then(m => m.ConnectionsModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'revelations',
    loadChildren: () => import('./features/revelations/revelations.module').then(m => m.RevelationsModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'chat',
    loadChildren: () => import('./features/chat/chat.module').then(m => m.ChatModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'preferences',
    loadChildren: () => import('./features/preferences/preferences.module').then(m => m.PreferencesModule),
    canActivate: [AuthGuard]
  },
  { path: '**', redirectTo: '' }
];
