import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfInputDirective } from './df-input.directive';

@Component({
  standalone: true,
  imports: [DfInputDirective],
  template: `
    <input dfInput type="text" />
    <textarea dfInput rows="3"></textarea>
  `,
})
class HostComponent {}

describe('DfInputDirective', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('applies df-input class to input and textarea', () => {
    const hosts = fixture.debugElement.queryAll(By.directive(DfInputDirective))
      .map(d => d.nativeElement as HTMLElement);
    expect(hosts.length).toBe(2);
    hosts.forEach(el => expect(el.classList).toContain('df-input'));
  });
});
