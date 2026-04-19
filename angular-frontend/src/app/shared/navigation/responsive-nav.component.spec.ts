import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of, BehaviorSubject } from 'rxjs';
import { ResponsiveNavComponent } from './responsive-nav.component';

describe('ResponsiveNavComponent', () => {
  let fixture: ComponentFixture<ResponsiveNavComponent>;
  let observer: jasmine.SpyObj<BreakpointObserver>;
  let matches$: BehaviorSubject<{ matches: boolean; breakpoints: {} }>;

  beforeEach(() => {
    matches$ = new BehaviorSubject<{ matches: boolean; breakpoints: {} }>({ matches: false, breakpoints: {} });
    observer = jasmine.createSpyObj('BreakpointObserver', ['observe']);
    observer.observe.and.returnValue(matches$.asObservable());

    TestBed.configureTestingModule({
      imports: [ResponsiveNavComponent],
      providers: [
        provideRouter([]),
        { provide: BreakpointObserver, useValue: observer },
      ],
    });
    fixture = TestBed.createComponent(ResponsiveNavComponent);
    fixture.detectChanges();
  });

  it('renders desktop nav when viewport is >= 768px', () => {
    matches$.next({ matches: true, breakpoints: {} });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-desktop-top-nav')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-mobile-tab-bar')).toBeFalsy();
  });

  it('renders mobile tab bar when viewport is < 768px', () => {
    matches$.next({ matches: false, breakpoints: {} });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-mobile-tab-bar')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-desktop-top-nav')).toBeFalsy();
  });
});
