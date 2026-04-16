import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { RevelationsComponent } from './revelations.component';
import { RevelationService } from '../../core/services/revelation.service';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { HapticFeedbackService } from '../../core/services/haptic-feedback.service';
import { RevelationKeyboardNavigationService } from './revelation-keyboard-navigation.service';
import { RevelationTimelineResponse } from '../../core/interfaces/revelation.interfaces';

describe('RevelationsComponent — photo consent', () => {
  let component: RevelationsComponent;
  let fixture: ComponentFixture<RevelationsComponent>;
  let dialogSpy: jasmine.SpyObj<MatDialog>;
  let revelationServiceSpy: jasmine.SpyObj<RevelationService>;
  let soulConnectionServiceSpy: jasmine.SpyObj<SoulConnectionService>;
  let hapticFeedbackServiceSpy: jasmine.SpyObj<HapticFeedbackService>;
  let keyboardNavigationServiceSpy: jasmine.SpyObj<RevelationKeyboardNavigationService>;

  beforeEach(async () => {
    dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);
    revelationServiceSpy = jasmine.createSpyObj('RevelationService', [
      'getRevelationTimeline',
      'getRevelationPrompts',
      'createRevelation',
      'updateRevelation',
      'reactToRevelation',
      'givePhotoConsent'
    ]);
    soulConnectionServiceSpy = jasmine.createSpyObj('SoulConnectionService', ['updateSoulConnection']);
    hapticFeedbackServiceSpy = jasmine.createSpyObj('HapticFeedbackService', [
      'triggerRevelationStepCelebration',
      'triggerSelectionFeedback',
      'triggerPhotoRevealCelebration'
    ]);
    keyboardNavigationServiceSpy = jasmine.createSpyObj('RevelationKeyboardNavigationService', [
      'initialize',
      'destroy',
      'updateNavigableElements',
      'navigateToDay',
      'focusRevelationForm',
      'navigateTimelineItems'
    ], {
      navigationEvents$: of({})
    });

    revelationServiceSpy.getRevelationTimeline.and.returnValue(of({
      connection_id: 1,
      current_day: 7,
      revelations: [],
      next_revelation_type: 'photo_reveal',
      is_cycle_complete: true
    } as RevelationTimelineResponse));
    revelationServiceSpy.getRevelationPrompts.and.returnValue(of([]));
    dialogSpy.open.and.returnValue({ afterClosed: () => of(true) } as any);
    soulConnectionServiceSpy.updateSoulConnection.and.returnValue(of({} as any));

    await TestBed.configureTestingModule({
      imports: [RevelationsComponent],
      providers: [
        { provide: RevelationService, useValue: revelationServiceSpy },
        { provide: SoulConnectionService, useValue: soulConnectionServiceSpy },
        { provide: HapticFeedbackService, useValue: hapticFeedbackServiceSpy },
        { provide: RevelationKeyboardNavigationService, useValue: keyboardNavigationServiceSpy },
        {
          provide: ActivatedRoute,
          useValue: { queryParams: of({}) }
        },
        {
          provide: Router,
          useValue: jasmine.createSpyObj('Router', ['navigate'])
        }
      ]
    })
    .overrideProvider(MatDialog, { useValue: dialogSpy })
    .compileComponents();

    fixture = TestBed.createComponent(RevelationsComponent);
    component = fixture.componentInstance;
  });

  it('should open consent dialog when current_day reaches 7', () => {
    component.checkForPhotoReveal({ connection_id: 1, current_day: 7, revelations: [], is_cycle_complete: true } as any);
    expect(dialogSpy.open).toHaveBeenCalled();
  });

  it('should call updateSoulConnection with mutual_reveal_consent: true on consent', fakeAsync(() => {
    component.connectionId = 1;
    component.checkForPhotoReveal({ connection_id: 1, current_day: 7, revelations: [], is_cycle_complete: true } as any);
    tick();
    expect(soulConnectionServiceSpy.updateSoulConnection).toHaveBeenCalledWith(
      1, { mutual_reveal_consent: true }
    );
  }));
});
