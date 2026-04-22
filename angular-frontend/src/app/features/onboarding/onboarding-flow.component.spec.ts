import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { OnboardingFlowComponent } from './onboarding-flow.component';

describe('OnboardingFlowComponent', () => {
  let fixture: ComponentFixture<OnboardingFlowComponent>;
  let comp: OnboardingFlowComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [OnboardingFlowComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    fixture = TestBed.createComponent(OnboardingFlowComponent);
    comp = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('starts on screen 1 of 3', () => {
    expect(comp.stepIndex).toBe(0);
    const fill: HTMLElement = fixture.nativeElement.querySelector('.onboarding-flow__progress-fill');
    expect(fill.style.width.replace(/\s/g, '')).toMatch(/^33\.3333/);
  });

  it('advances when Continue is clicked and answer is non-empty', () => {
    comp.answers[0] = 'I value trust.';
    fixture.detectChanges();
    fixture.nativeElement.querySelector('button[data-role="continue"]').click();
    fixture.detectChanges();
    expect(comp.stepIndex).toBe(1);
  });

  it('disables Continue when current answer is empty', () => {
    comp.answers[0] = '';
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button[data-role="continue"]');
    expect(btn.disabled).toBeTrue();
  });

  it('Back decrements stepIndex on screens 2-3', () => {
    comp.stepIndex = 1;
    fixture.detectChanges();
    fixture.nativeElement.querySelector('button[data-role="back"]').click();
    fixture.detectChanges();
    expect(comp.stepIndex).toBe(0);
  });
});
