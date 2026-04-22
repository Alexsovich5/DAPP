import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { ProfileComponent, ProfileView } from './profile.component';
import { ProfileService, UserProfileData } from '../../core/services/profile.service';

describe('ProfileComponent', () => {
  let fixture: ComponentFixture<ProfileComponent>;
  let comp: ProfileComponent;

  const mockProfileData: UserProfileData = {
    id: 1,
    email: 'test@example.com',
    username: 'testuser',
    first_name: 'Test',
    last_name: 'User',
    is_profile_complete: true,
    location: 'SF',
    date_of_birth: '1995-01-01',
    interests: ['hiking', 'jazz'],
    emotional_responses: {
      relationship_values: 'Loyalty and honesty.',
      ideal_evening: 'A long walk and slow food.',
      feeling_understood: 'Being heard without judgement.',
    },
  };

  beforeEach(async () => {
    const profileSpy = jasmine.createSpyObj('ProfileService', ['getProfile']);
    profileSpy.getProfile.and.returnValue(of(mockProfileData));

    await TestBed.configureTestingModule({
      imports: [ProfileComponent],
      providers: [
        provideRouter([]),
        { provide: ProfileService, useValue: profileSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfileComponent);
    comp = fixture.componentInstance;
  });

  it('renders "Your profile" header and Edit ghost link', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.profile__title')?.textContent?.trim()).toBe('Your profile');
    const edit = el.querySelector('a[data-role="edit"]') as HTMLElement;
    expect(edit).toBeTruthy();
    expect(edit.getAttribute('variant')).toBe('ghost');
    expect(edit.getAttribute('href')).toBe('/profile/edit');
  });

  it('renders large monogram avatar', () => {
    fixture.detectChanges();
    const av = fixture.nativeElement.querySelector('df-avatar');
    expect(av.getAttribute('size')).toBe('lg');
  });

  it('renders three value cards (one per onboarding answer)', () => {
    comp.profile = {
      displayName: 'You',
      onboardingAnswers: ['a', 'b', 'c'],
      interests: [],
      photos: [],
    } as ProfileView;
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('.profile__value-card').length).toBe(3);
  });

  it('renders collapsed photo section by default', () => {
    fixture.detectChanges();
    const sec = fixture.nativeElement.querySelector('.profile__photos');
    expect(sec.classList.contains('is-collapsed')).toBeTrue();
  });

  it('does not render tab headers (flattened)', () => {
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('mat-tab-group, .mat-tab-group')).toBeNull();
  });

  it('renders interests chips row from profile data', () => {
    fixture.detectChanges();
    const chips = fixture.nativeElement.querySelectorAll('.profile__interests df-chip');
    expect(chips.length).toBe(2);
  });
});
