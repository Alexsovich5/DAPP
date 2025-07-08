import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router, ActivatedRouteSnapshot, CanActivate } from '@angular/router';
import { StorageService } from '../../core/services/storage.service';

@Injectable({
  providedIn: 'root'
})
export class OnboardingStepGuard implements CanActivate {
  private isBrowser: boolean;

  constructor(
    private router: Router,
    private storage: StorageService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  canActivate(route: ActivatedRouteSnapshot): boolean {
    // During SSR, allow navigation (guards will re-evaluate on client)
    if (!this.isBrowser || !this.storage) {
      return true;
    }

    const targetStep = route.url[0]?.path;
    
    // Define step order and requirements
    const stepRequirements = {
      'emotional-questions': [],
      'personality-assessment': ['onboarding_emotional'],
      'interest-selection': ['onboarding_emotional', 'onboarding_personality'],
      'complete': ['onboarding_emotional', 'onboarding_personality', 'onboarding_interests']
    };

    const requirements = stepRequirements[targetStep as keyof typeof stepRequirements];
    
    if (!requirements) {
      return true; // Unknown step, allow for now
    }

    // Check if onboarding is already completed
    const isOnboardingComplete = this.storage.getItem('onboarding_completed') === 'true';
    if (isOnboardingComplete && targetStep !== 'complete') {
      // If onboarding is complete, redirect to discover
      this.router.navigate(['/discover']);
      return false;
    }

    // Check if all required previous steps are completed
    const missingRequirements = requirements.filter(req => 
      !this.storage.getItem(req)
    );

    if (missingRequirements.length > 0) {
      // Redirect to first missing step
      let redirectStep = 'emotional-questions';
      
      if (!this.storage.getItem('onboarding_emotional')) {
        redirectStep = 'emotional-questions';
      } else if (!this.storage.getItem('onboarding_personality')) {
        redirectStep = 'personality-assessment';
      } else if (!this.storage.getItem('onboarding_interests')) {
        redirectStep = 'interest-selection';
      }
      
      this.router.navigate(['/onboarding', redirectStep]);
      return false;
    }

    return true;
  }
}