import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { DesktopTopNavComponent } from './desktop-top-nav.component';

describe('DesktopTopNavComponent', () => {
  let fixture: ComponentFixture<DesktopTopNavComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [DesktopTopNavComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(DesktopTopNavComponent);
    fixture.detectChanges();
  });

  it('renders 4 primary nav links (not Profile)', () => {
    const anchors = fixture.nativeElement.querySelectorAll('a.desktop-top-nav__tab');
    expect(anchors.length).toBe(4);
  });

  it('renders logo link pointing to root', () => {
    const logo = fixture.nativeElement.querySelector('a.desktop-top-nav__logo');
    expect(logo).toBeTruthy();
    expect(logo.getAttribute('href')).toBe('/');
  });

  it('renders notification bell and avatar dropdown trigger', () => {
    const bell = fixture.nativeElement.querySelector('.desktop-top-nav__bell');
    const avatar = fixture.nativeElement.querySelector('.desktop-top-nav__avatar-trigger');
    expect(bell).toBeTruthy();
    expect(avatar).toBeTruthy();
  });
});
