import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { DfInputDirective } from '../../shared/ui';

@Component({
  selector: 'app-onboarding-question',
  standalone: true,
  imports: [CommonModule, DfInputDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <p class="onboarding-question__prompt display-serif">{{ prompt }}</p>
    <p class="onboarding-question__helper">{{ helper }}</p>
    <textarea dfInput
      class="onboarding-question__field"
      [value]="value"
      (input)="onInput($event)"
      maxlength="500"
      rows="4"
      [attr.aria-label]="prompt"></textarea>
    <p class="onboarding-question__counter"
       [class.is-warning]="count >= 450 && count < 500"
       [class.is-danger]="count >= 500">
      {{ count }} / 500
    </p>
  `,
  styleUrls: ['./onboarding-question.component.scss'],
})
export class OnboardingQuestionComponent {
  @Input() prompt = '';
  @Input() helper = '';
  @Input() value = '';
  @Output() valueChange = new EventEmitter<string>();

  get count(): number { return this.value?.length ?? 0; }

  onInput(ev: Event): void {
    const next = (ev.target as HTMLTextAreaElement).value.slice(0, 500);
    this.value = next;
    this.valueChange.emit(next);
  }
}
