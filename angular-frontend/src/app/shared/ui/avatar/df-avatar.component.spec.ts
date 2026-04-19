import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfAvatarComponent } from './df-avatar.component';

@Component({
  standalone: true,
  imports: [DfAvatarComponent],
  template: `
    <df-avatar name="Alexander Sebhat"></df-avatar>
    <df-avatar name="Maya"></df-avatar>
    <df-avatar name="Maya" size="sm"></df-avatar>
    <df-avatar name="Maya" size="lg"></df-avatar>
    <df-avatar name="Maya" photoUrl="/x.jpg"></df-avatar>
  `,
})
class HostComponent {}

describe('DfAvatarComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  function hosts(): HTMLElement[] {
    return fixture.debugElement.queryAll(By.directive(DfAvatarComponent))
      .map(d => d.nativeElement as HTMLElement);
  }

  it('renders monogram from first letters of each word, max 2, uppercase', () => {
    const els = hosts();
    expect(els[0].textContent?.trim()).toBe('AS');
    expect(els[1].textContent?.trim()).toBe('M');
  });

  it('applies size classes (md default)', () => {
    const els = hosts();
    expect(els[0].classList).toContain('df-avatar--md');
    expect(els[2].classList).toContain('df-avatar--sm');
    expect(els[3].classList).toContain('df-avatar--lg');
  });

  it('renders img when photoUrl provided and no monogram text', () => {
    const el = hosts()[4];
    const img = el.querySelector('img');
    expect(img).toBeTruthy();
    expect(img!.getAttribute('src')).toBe('/x.jpg');
    expect(img!.getAttribute('alt')).toBe('Maya');
  });
});
