import { TestBed, ComponentFixture } from '@angular/core/testing';
import { OnboardingQuestionComponent } from './onboarding-question.component';

describe('OnboardingQuestionComponent', () => {
  let fixture: ComponentFixture<OnboardingQuestionComponent>;
  let comp: OnboardingQuestionComponent;

  beforeEach(() => {
    fixture = TestBed.createComponent(OnboardingQuestionComponent);
    comp = fixture.componentInstance;
    comp.prompt = 'What do you value most in a relationship?';
    comp.helper = "Take your time. There's no right answer — only honest ones.";
    comp.value = '';
    fixture.detectChanges();
  });

  it('renders prompt in display-serif', () => {
    const el: HTMLElement = fixture.nativeElement.querySelector('.onboarding-question__prompt');
    expect(el.classList.contains('display-serif')).toBeTrue();
    expect(el.textContent).toContain('What do you value');
  });

  it('renders counter N / 500', () => {
    comp.value = 'hello';
    fixture.detectChanges();
    const c: HTMLElement = fixture.nativeElement.querySelector('.onboarding-question__counter');
    expect(c.textContent?.trim()).toBe('5 / 500');
  });

  it('flags warning at 450 chars, danger at 500 chars', () => {
    comp.value = 'a'.repeat(450);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.onboarding-question__counter')!.classList.contains('is-warning')).toBeTrue();
    comp.value = 'a'.repeat(500);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.onboarding-question__counter')!.classList.contains('is-danger')).toBeTrue();
  });

  it('emits valueChange when textarea input fires', (done) => {
    comp.valueChange.subscribe((v: string) => { expect(v).toBe('hi'); done(); });
    const ta: HTMLTextAreaElement = fixture.nativeElement.querySelector('textarea');
    ta.value = 'hi';
    ta.dispatchEvent(new Event('input'));
  });
});
