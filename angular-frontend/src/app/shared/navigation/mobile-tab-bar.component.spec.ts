import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MobileTabBarComponent } from './mobile-tab-bar.component';

describe('MobileTabBarComponent', () => {
  let fixture: ComponentFixture<MobileTabBarComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [MobileTabBarComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(MobileTabBarComponent);
    fixture.detectChanges();
  });

  it('renders exactly 5 tab links', () => {
    const anchors = fixture.nativeElement.querySelectorAll('a.mobile-tab-bar__tab');
    expect(anchors.length).toBe(5);
  });

  it('tabs point to /discover, /connections, /messages, /revelations, /profile in order', () => {
    const anchors: HTMLAnchorElement[] = Array.from(
      fixture.nativeElement.querySelectorAll('a.mobile-tab-bar__tab')
    );
    expect(anchors.map(a => a.getAttribute('href'))).toEqual([
      '/discover', '/connections', '/messages', '/revelations', '/profile',
    ]);
  });

  it('each tab has aria-label for screen readers', () => {
    const anchors: HTMLAnchorElement[] = Array.from(
      fixture.nativeElement.querySelectorAll('a.mobile-tab-bar__tab')
    );
    anchors.forEach(a => expect(a.getAttribute('aria-label')).toBeTruthy());
  });
});
