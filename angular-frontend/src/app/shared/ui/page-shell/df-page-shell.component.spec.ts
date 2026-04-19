import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfPageShellComponent } from './df-page-shell.component';

@Component({
  standalone: true,
  imports: [DfPageShellComponent],
  template: `
    <df-page-shell>default</df-page-shell>
    <df-page-shell variant="reading">reading</df-page-shell>
    <df-page-shell variant="chat">chat</df-page-shell>
    <df-page-shell variant="grid">grid</df-page-shell>
  `,
})
class HostComponent {}

describe('DfPageShellComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('defaults to grid variant', () => {
    const host = fixture.debugElement.queryAll(By.directive(DfPageShellComponent))[0].nativeElement as HTMLElement;
    expect(host.classList).toContain('df-page-shell');
    expect(host.classList).toContain('df-page-shell--grid');
  });

  it('applies variant classes', () => {
    const hosts = fixture.debugElement.queryAll(By.directive(DfPageShellComponent))
      .map(d => d.nativeElement as HTMLElement);
    expect(hosts[1].classList).toContain('df-page-shell--reading');
    expect(hosts[2].classList).toContain('df-page-shell--chat');
    expect(hosts[3].classList).toContain('df-page-shell--grid');
  });
});
