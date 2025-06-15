import { Injectable } from '@angular/core';
import { Router, ActivatedRouteSnapshot, CanActivate } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class OnboardingStepGuard implements CanActivate {
  constructor(private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot): boolean {
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

    // Check if all required previous steps are completed
    const missingRequirements = requirements.filter(req => 
      !localStorage.getItem(req)
    );

    if (missingRequirements.length > 0) {
      // Redirect to first missing step
      let redirectStep = 'emotional-questions';
      
      if (!localStorage.getItem('onboarding_emotional')) {
        redirectStep = 'emotional-questions';
      } else if (!localStorage.getItem('onboarding_personality')) {
        redirectStep = 'personality-assessment';
      } else if (!localStorage.getItem('onboarding_interests')) {
        redirectStep = 'interest-selection';
      }
      
      this.router.navigate(['/onboarding', redirectStep]);
      return false;
    }

    return true;
  }
}