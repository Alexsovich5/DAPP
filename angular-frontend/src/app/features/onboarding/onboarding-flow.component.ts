import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { DfButtonDirective } from '../../shared/ui';
import { OnboardingQuestionComponent } from './onboarding-question.component';
import { OnboardingApiService, OnboardingData } from '../../core/services/onboarding-api.service';

interface Prompt { prompt: string; helper: string; optional?: boolean; }

@Component({
  selector: 'app-onboarding-flow',
  standalone: true,
  imports: [CommonModule, RouterLink, DfButtonDirective, OnboardingQuestionComponent],
  template: `
    <header class="onboarding-flow__chrome">
      <div class="onboarding-flow__progress" role="progressbar"
           [attr.aria-valuenow]="stepIndex + 1" aria-valuemin="1" aria-valuemax="3">
        <div class="onboarding-flow__progress-fill"
             [style.width.%]="((stepIndex + 1) / prompts.length) * 100"></div>
      </div>
      <a *ngIf="prompts[stepIndex].optional"
         class="onboarding-flow__skip" routerLink="/discover">Skip</a>
    </header>

    <main class="onboarding-flow__main">
      <app-onboarding-question
        [prompt]="prompts[stepIndex].prompt"
        [helper]="prompts[stepIndex].helper"
        [value]="answers[stepIndex]"
        (valueChange)="onAnswer($event)"></app-onboarding-question>
    </main>

    <footer class="onboarding-flow__footer">
      <button dfButton variant="ghost" size="md"
              data-role="back"
              [disabled]="stepIndex === 0"
              (click)="back()">Back</button>
      <button dfButton variant="primary" size="md"
              data-role="continue"
              [disabled]="!canContinue()"
              (click)="next()">
        {{ stepIndex === prompts.length - 1 ? 'Finish' : 'Continue' }}
      </button>
    </footer>
  `,
  styleUrls: ['./onboarding-flow.component.scss'],
})
export class OnboardingFlowComponent {
  stepIndex = 0;
  readonly prompts: Prompt[] = [
    { prompt: 'What do you value most in a relationship?',
      helper: "Take your time. There's no right answer — only honest ones." },
    { prompt: 'Describe your ideal evening with someone special.',
      helper: 'One scene, as vividly as you like.' },
    { prompt: 'What makes you feel truly understood?',
      helper: 'The small thing someone does that lands.', optional: true },
  ];
  answers: string[] = ['', '', ''];

  constructor(
    private readonly router: Router,
    private readonly cdr: ChangeDetectorRef,
    private readonly onboardingApi: OnboardingApiService,
  ) {}

  onAnswer(v: string): void {
    this.answers[this.stepIndex] = v;
    this.cdr.markForCheck();
  }

  canContinue(): boolean {
    const current = this.prompts[this.stepIndex];
    if (current.optional) return true;
    return (this.answers[this.stepIndex] ?? '').trim().length > 0;
  }

  back(): void {
    if (this.stepIndex > 0) { this.stepIndex -= 1; this.cdr.markForCheck(); }
  }

  next(): void {
    if (!this.canContinue()) return;
    if (this.stepIndex < this.prompts.length - 1) {
      this.stepIndex += 1;
      this.cdr.markForCheck();
    } else {
      this.finish();
    }
  }

  private finish(): void {
    const payload: OnboardingData = {
      relationship_values: this.answers[0] ?? '',
      ideal_evening: this.answers[1] ?? '',
      feeling_understood: this.answers[2] ?? '',
      core_values: {},
      personality_traits: {},
      communication_style: {},
      interests: [],
    };
    this.onboardingApi.completeOnboarding(payload).subscribe({
      next: () => this.router.navigate(['/discover']),
      error: () => this.router.navigate(['/discover']),
    });
  }
}
