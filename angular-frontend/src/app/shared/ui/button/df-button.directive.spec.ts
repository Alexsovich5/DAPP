import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfButtonDirective } from './df-button.directive';

@Component({
  standalone: true,
  imports: [DfButtonDirective],
  template: `
    <button dfButton>default</button>
    <button dfButton variant="primary" size="md">primary md</button>
    <button dfButton variant="secondary" size="sm">secondary sm</button>
    <button dfButton variant="ghost" size="lg">ghost lg</button>
    <button dfButton variant="danger">danger default size</button>
    <a dfButton variant="primary" href="/x">link</a>
  `,
})
class HostComponent {}

describe('DfButtonDirective', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('applies base class to every host element', () => {
    const hosts = fixture.debugElement.queryAll(By.directive(DfButtonDirective));
    expect(hosts.length).toBe(6);
    hosts.forEach(h => expect(h.nativeElement.classList).toContain('df-btn'));
  });

  it('defaults to primary variant and md size', () => {
    const el = fixture.debugElement.queryAll(By.directive(DfButtonDirective))[0].nativeElement;
    expect(el.classList).toContain('df-btn--primary');
    expect(el.classList).toContain('df-btn--md');
  });

  it('applies variant classes for primary/secondary/ghost/danger', () => {
    const els = fixture.debugElement
      .queryAll(By.directive(DfButtonDirective))
      .map(d => d.nativeElement as HTMLElement);
    expect(els[1].classList).toContain('df-btn--primary');
    expect(els[2].classList).toContain('df-btn--secondary');
    expect(els[3].classList).toContain('df-btn--ghost');
    expect(els[4].classList).toContain('df-btn--danger');
  });

  it('applies size classes sm/md/lg', () => {
    const els = fixture.debugElement
      .queryAll(By.directive(DfButtonDirective))
      .map(d => d.nativeElement as HTMLElement);
    expect(els[1].classList).toContain('df-btn--md');
    expect(els[2].classList).toContain('df-btn--sm');
    expect(els[3].classList).toContain('df-btn--lg');
  });

  it('works on anchor elements too', () => {
    const anchor = fixture.debugElement.queryAll(By.directive(DfButtonDirective))[5].nativeElement;
    expect(anchor.tagName).toBe('A');
    expect(anchor.classList).toContain('df-btn');
    expect(anchor.classList).toContain('df-btn--primary');
  });
});
