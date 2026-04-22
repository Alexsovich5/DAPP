import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfCardComponent } from './df-card.component';

@Component({
  standalone: true,
  imports: [DfCardComponent],
  template: `
    <df-card>default connection card</df-card>
    <df-card layout="connection">explicit connection</df-card>
    <df-card layout="revelation">revelation card</df-card>
  `,
})
class HostComponent {}

describe('DfCardComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('defaults to connection layout', () => {
    const card = fixture.debugElement.queryAll(By.directive(DfCardComponent))[0].nativeElement as HTMLElement;
    expect(card.classList).toContain('df-card');
    expect(card.classList).toContain('df-card--connection');
  });

  it('applies layout classes', () => {
    const cards = fixture.debugElement.queryAll(By.directive(DfCardComponent))
      .map(d => d.nativeElement as HTMLElement);
    expect(cards[1].classList).toContain('df-card--connection');
    expect(cards[2].classList).toContain('df-card--revelation');
  });
});
