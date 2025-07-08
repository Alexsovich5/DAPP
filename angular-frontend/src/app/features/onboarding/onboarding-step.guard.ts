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
    
    // Debug: Check what data we have
    const hasEmotionalData = !!this.storage.getItem('onboarding_emotional');
    const hasPersonalityData = !!this.storage.getItem('onboarding_personality');
    const hasInterestData = !!this.storage.getItem('onboarding_interests');
    
    console.log('Onboarding guard debug:', {
      targetStep,
      emotionalData: hasEmotionalData,
      personalityData: hasPersonalityData,
      interestData: hasInterestData,
      isComplete: isOnboardingComplete
    });

    // If onboarding is marked complete but we don't have the step data, clear the completion flag
    if (isOnboardingComplete && (!hasEmotionalData || !hasPersonalityData || !hasInterestData)) {
      console.log('Onboarding marked complete but missing step data. Clearing completion flag.');
      this.storage.removeItem('onboarding_completed');
    } else if (isOnboardingComplete) {
      // If onboarding is complete and we have all data, redirect to discover
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
      
      console.log('Redirecting to step:', redirectStep, 'Missing:', missingRequirements);
      this.router.navigate(['/onboarding', redirectStep]);
      return false;
    }

    return true;
  }
}