import { Routes } from '@angular/router';
import { AuthGuard } from './features/auth/auth.guard';
import { LandingComponent } from './features/landing/landing.component';

export const routes: Routes = [
  { path: '', component: LandingComponent },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'register',
    loadComponent: () => import('./features/auth/register/register.component').then(m => m.RegisterComponent)
  },
  {
    path: 'forgot-password',
    loadComponent: () => import('./features/auth/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
  },
  {
    path: 'onboarding',
    loadComponent: () => import('./features/onboarding/onboarding-flow.component').then(m => m.OnboardingFlowComponent),
    canActivate: [AuthGuard],
  },
  {
    path: 'profile',
    loadComponent: () => import('./features/profile/profile.component').then(m => m.ProfileComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'profile/edit',
    loadComponent: () =>
      import('./features/profile/profile-edit/profile-edit.component').then(m => m.ProfileEditComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'discover',
    loadComponent: () => import('./features/discover/discover.component').then(m => m.DiscoverComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'chat',
    loadComponent: () => import('./features/chat/chat.component').then(m => m.ChatComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'preferences',
    loadComponent: () => import('./features/preferences/preferences.component').then(m => m.PreferencesComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'conversations',
    loadComponent: () => import('./features/messages/messages.component').then(m => m.MessagesComponent),
    canActivate: [AuthGuard]
  },
  // Legacy routes for backward compatibility
  {
    path: 'matches',
    redirectTo: 'conversations',
    pathMatch: 'full'
  },
  {
    path: 'messages',
    redirectTo: 'conversations',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    redirectTo: 'discover',
    pathMatch: 'full'
  },
  {
    path: 'auth/login',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'auth/register',
    redirectTo: 'register',
    pathMatch: 'full'
  },
  {
    path: 'revelations',
    loadComponent: () => import('./features/revelations/revelations.component').then(m => m.RevelationsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'revelations/compose/:connectionId',
    loadComponent: () => import('./features/revelations/revelations.component').then(m => m.RevelationsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'connections',
    loadComponent: () =>
      import('./features/connections/connection-management.component')
        .then(m => m.ConnectionManagementComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'dinner-planning',
    loadComponent: () =>
      import('./features/dinner-planning/dinner-planning.component').then(
        m => m.DinnerPlanningComponent
      ),
    canActivate: [AuthGuard]
  },
  {
    path: 'settings',
    loadComponent: () => import('./features/settings/settings.component').then(m => m.SettingsComponent),
    canActivate: [AuthGuard]
  },
  { path: '**', redirectTo: '' }
];
