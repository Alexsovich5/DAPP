import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { OnboardingComponent } from './onboarding.component';
import { EmotionalQuestionsComponent } from './emotional-questions/emotional-questions.component';
import { PersonalityAssessmentComponent } from './personality-assessment/personality-assessment.component';
import { InterestSelectionComponent } from './interest-selection/interest-selection.component';
import { OnboardingCompleteComponent } from './onboarding-complete/onboarding-complete.component';

@NgModule({
  declarations: [
    OnboardingComponent,
    EmotionalQuestionsComponent,
    PersonalityAssessmentComponent,
    InterestSelectionComponent,
    OnboardingCompleteComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterModule.forChild([
      {
        path: '',
        component: OnboardingComponent,
        children: [
          { path: '', redirectTo: 'emotional-questions', pathMatch: 'full' },
          { path: 'emotional-questions', component: EmotionalQuestionsComponent },
          { path: 'personality-assessment', component: PersonalityAssessmentComponent },
          { path: 'interest-selection', component: InterestSelectionComponent },
          { path: 'complete', component: OnboardingCompleteComponent }
        ]
      }
    ])
  ]
})
export class OnboardingModule { }