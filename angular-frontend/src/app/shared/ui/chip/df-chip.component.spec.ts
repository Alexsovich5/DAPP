import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfChipComponent } from './df-chip.component';

@Component({
  standalone: true,
  imports: [DfChipComponent],
  template: `
    <df-chip purpose="stage">Day 3</df-chip>
    <df-chip purpose="interest">Hiking</df-chip>
    <df-chip purpose="counter">127/500</df-chip>
  `,
})
class HostComponent {}

describe('DfChipComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('renders three chips with distinct purpose classes', () => {
    const chips = fixture.debugElement.queryAll(By.directive(DfChipComponent))
      .map(d => d.nativeElement as HTMLElement);
    expect(chips.length).toBe(3);
    expect(chips[0].classList).toContain('df-chip');
    expect(chips[0].classList).toContain('df-chip--stage');
    expect(chips[1].classList).toContain('df-chip--interest');
    expect(chips[2].classList).toContain('df-chip--counter');
  });

  it('projects content', () => {
    const chip = fixture.debugElement.query(By.directive(DfChipComponent)).nativeElement as HTMLElement;
    expect(chip.textContent?.trim()).toBe('Day 3');
  });
});
