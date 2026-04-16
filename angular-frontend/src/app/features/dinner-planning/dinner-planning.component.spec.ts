import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { DinnerPlanningComponent } from './dinner-planning.component';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatSnackBar } from '@angular/material/snack-bar';

describe('DinnerPlanningComponent', () => {
  let fixture: ComponentFixture<DinnerPlanningComponent>;
  let component: DinnerPlanningComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DinnerPlanningComponent, RouterTestingModule, NoopAnimationsModule],
      providers: [
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: { get: () => '1' } } } },
        { provide: MatSnackBar, useValue: { open: jasmine.createSpy('open') } }
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(DinnerPlanningComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should render the dinner planning heading', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Plan Your First Dinner');
  });

  it('should have the date field in the form', () => {
    expect(component.dinnerForm.get('date')).toBeTruthy();
  });

  it('should have the notes field in the form', () => {
    expect(component.dinnerForm.get('notes')).toBeTruthy();
  });

  it('should mark form invalid when date is empty', () => {
    component.dinnerForm.get('date')?.setValue('');
    expect(component.dinnerForm.invalid).toBeTrue();
  });

  it('should mark form valid when date is set', () => {
    component.dinnerForm.get('date')?.setValue(new Date());
    expect(component.dinnerForm.valid).toBeTrue();
  });

  it('should toggle cuisine selection', () => {
    component.selectCuisine('Italian');
    expect(component.selectedCuisine).toBe('Italian');
    component.selectCuisine('Italian');
    expect(component.selectedCuisine).toBeNull();
  });
});
