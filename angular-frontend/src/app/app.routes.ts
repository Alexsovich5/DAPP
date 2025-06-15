import { Routes } from '@angular/router';
import { AuthGuard } from './features/auth/auth.guard';
import { OnboardingStepGuard } from './features/onboarding/onboarding-step.guard';
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
    loadComponent: () => import('./features/onboarding/onboarding.component').then(m => m.OnboardingComponent),
    canActivate: [AuthGuard],
    children: [
      { path: '', redirectTo: 'emotional-questions', pathMatch: 'full' },
      {
        path: 'emotional-questions',
        loadComponent: () => import('./features/onboarding/emotional-questions/emotional-questions.component').then(m => m.EmotionalQuestionsComponent)
      },
      {
        path: 'personality-assessment',
        loadComponent: () => import('./features/onboarding/personality-assessment/personality-assessment.component').then(m => m.PersonalityAssessmentComponent),
        canActivate: [OnboardingStepGuard]
      },
      {
        path: 'interest-selection',
        loadComponent: () => import('./features/onboarding/interest-selection/interest-selection.component').then(m => m.InterestSelectionComponent),
        canActivate: [OnboardingStepGuard]
      },
      {
        path: 'complete',
        loadComponent: () => import('./features/onboarding/onboarding-complete/onboarding-complete.component').then(m => m.OnboardingCompleteComponent),
        canActivate: [OnboardingStepGuard]
      }
    ]
  },
  {
    path: 'profile',
    loadComponent: () => import('./features/profile/profile.component').then(m => m.ProfileComponent),
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
    path: 'matches',
    loadComponent: () => import('./features/matches/matches.component').then(m => m.MatchesComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'messages',
    loadComponent: () => import('./features/messages/messages.component').then(m => m.MessagesComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'revelations',
    loadComponent: () => import('./features/revelations/revelations.component').then(m => m.RevelationsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'notifications',
    loadComponent: () => import('./features/notifications/notifications.component').then(m => m.NotificationsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'settings',
    loadComponent: () => import('./features/settings/settings.component').then(m => m.SettingsComponent),
    canActivate: [AuthGuard]
  },
  { path: '**', redirectTo: '' }
];
