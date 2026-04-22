import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { DiscoverComponent } from './discover.component';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { DiscoveryResponse } from '../../core/interfaces/soul-connection.interfaces';

function makeMatch(id: number, name: string, compat = 80): DiscoveryResponse {
  return {
    user_id: id,
    profile_preview: {
      first_name: name,
      age: 28,
      location: 'SF',
      bio: `${name} bio`,
      interests: [],
    },
    compatibility: {
      total_compatibility: compat,
      breakdown: { interests: 80, values: 80, demographics: 80, communication: 80, personality: 80 },
      match_quality: 'Strong',
      explanation: 'You both value honest conversation.',
    },
    is_photo_hidden: true,
  };
}

describe('DiscoverComponent', () => {
  let component: DiscoverComponent;
  let fixture: ComponentFixture<DiscoverComponent>;
  let soulConnectionService: jasmine.SpyObj<SoulConnectionService>;

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('SoulConnectionService', [
      'discoverSoulConnections',
      'initiateSoulConnection',
    ]);
    spy.discoverSoulConnections.and.returnValue(of([]));
    spy.initiateSoulConnection.and.returnValue(of({ id: 42 }));

    await TestBed.configureTestingModule({
      imports: [DiscoverComponent],
      providers: [
        provideRouter([]),
        { provide: SoulConnectionService, useValue: spy },
      ],
    }).compileComponents();

    soulConnectionService = TestBed.inject(SoulConnectionService) as jasmine.SpyObj<SoulConnectionService>;
    fixture = TestBed.createComponent(DiscoverComponent);
    component = fixture.componentInstance;
  });

  it('renders headline with soul count from matches', () => {
    soulConnectionService.discoverSoulConnections.and.returnValue(
      of([makeMatch(1, 'Avery'), makeMatch(2, 'Jordan')])
    );
    fixture.detectChanges();
    const h: HTMLElement = fixture.nativeElement.querySelector('.discover__headline');
    expect(h.textContent).toContain('2 souls for today');
  });

  it('renders a single focal card and up to 2 peek cards', () => {
    soulConnectionService.discoverSoulConnections.and.returnValue(
      of([
        makeMatch(1, 'A'),
        makeMatch(2, 'B'),
        makeMatch(3, 'C'),
        makeMatch(4, 'D'),
      ])
    );
    fixture.detectChanges();
    const focal = fixture.nativeElement.querySelectorAll('.discover__focal');
    const peek = fixture.nativeElement.querySelectorAll('.discover__peek');
    expect(focal.length).toBe(1);
    expect(peek.length).toBe(2);
  });

  it('Begin button uses primary variant; Pass uses secondary', () => {
    soulConnectionService.discoverSoulConnections.and.returnValue(of([makeMatch(1, 'A')]));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('button[data-role="begin"]').getAttribute('variant')).toBe('primary');
    expect(fixture.nativeElement.querySelector('button[data-role="pass"]').getAttribute('variant')).toBe('secondary');
  });

  it('tapping a peek card promotes it to focal', () => {
    soulConnectionService.discoverSoulConnections.and.returnValue(
      of([makeMatch(1, 'A'), makeMatch(2, 'B')])
    );
    fixture.detectChanges();
    fixture.nativeElement.querySelector('.discover__peek').click();
    fixture.detectChanges();
    expect(component.focalIndex).toBe(1);
  });
});
