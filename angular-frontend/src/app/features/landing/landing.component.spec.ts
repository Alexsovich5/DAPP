// landing.component.spec.ts
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LandingComponent } from './landing.component';

describe('LandingComponent', () => {
  let fixture: ComponentFixture<LandingComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [LandingComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(LandingComponent);
    fixture.detectChanges();
  });

  it('renders hero lines Soul / before / skin', () => {
    const el = fixture.nativeElement as HTMLElement;
    const lines = Array.from(el.querySelectorAll('.landing__hero-line')).map(n => n.textContent?.trim());
    expect(lines).toEqual(['Soul', 'before', 'skin.']);
  });

  it('renders exactly one primary CTA linking to /auth/register', () => {
    const el = fixture.nativeElement as HTMLElement;
    const primary = el.querySelectorAll('a[dfButton][variant="primary"], button[dfButton][variant="primary"]');
    expect(primary.length).toBe(1);
    expect((primary[0] as HTMLAnchorElement).getAttribute('href')).toBe('/auth/register');
  });

  it('renders how-it-works card with three rows', () => {
    const rows = fixture.nativeElement.querySelectorAll('.landing__how-row');
    expect(rows.length).toBe(3);
  });

  it('does not render hero orbs or favorite/auto_awesome icons', () => {
    const html = fixture.nativeElement.innerHTML as string;
    expect(html).not.toMatch(/hero-orb|hero__orb/);
    expect(html).not.toMatch(/>favorite<|>auto_awesome</);
  });
});
