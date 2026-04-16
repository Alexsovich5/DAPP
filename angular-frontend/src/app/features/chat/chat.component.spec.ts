import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';
import { ChatComponent } from './chat.component';
import { ChatService } from '@core/services/chat.service';
import { AuthService } from '@core/services/auth.service';
import { RevelationService } from '@core/services/revelation.service';
import { RevelationTimelineResponse } from '@core/interfaces/revelation.interfaces';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { SoulConnectionService } from '@core/services/soul-connection.service';

describe('ChatComponent — revelation banner', () => {
  let component: ChatComponent;
  let fixture: ComponentFixture<ChatComponent>;
  let revelationServiceSpy: jasmine.SpyObj<RevelationService>;

  const MOCK_TIMELINE: RevelationTimelineResponse = {
    connection_id: 5,
    current_day: 3,
    is_cycle_complete: false,
    revelations: [
      {
        id: 1, day_number: 3, revelation_type: 'hope_or_dream',
        content: 'I hope to travel the world someday.',
        sender_id: 99,
        is_read: false, created_at: '', connection_id: 5,
        sender_name: 'Sam', reactions: {}
      }
    ],
    next_revelation_type: 'what_makes_laugh'
  };

  beforeEach(async () => {
    revelationServiceSpy = jasmine.createSpyObj('RevelationService', ['getRevelationTimeline']);
    revelationServiceSpy.getRevelationTimeline.and.returnValue(of(MOCK_TIMELINE));

    const chatServiceSpy = jasmine.createSpyObj('ChatService', [
      'setCurrentUser', 'setupWebSocket', 'getChatData', 'sendMessage',
      'startTyping', 'stopTyping', 'disconnect', 'setCurrentUserId',
      'getEnhancedTypingUsers', 'updateConnectionActivity', 'setEmotionalState',
      'createTypingHandler'
    ]);
    chatServiceSpy.getChatData.and.returnValue(of({ user: null, messages: [] }));
    chatServiceSpy.getEnhancedTypingUsers.and.returnValue(of([]));
    chatServiceSpy.createTypingHandler.and.returnValue((_v: string) => {});

    const authServiceSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser$: of({ id: 1, first_name: 'Me' })
    });

    const soulConnectionServiceSpy = jasmine.createSpyObj('SoulConnectionService', ['getSoulConnection']);
    soulConnectionServiceSpy.getSoulConnection.and.returnValue(of({
      id: 5, connection_stage: 'soul_discovery',
      user1_id: 1, user2_id: 99, initiated_by: 1,
      compatibility_score: 75, reveal_day: 3,
      mutual_reveal_consent: false, first_dinner_completed: false,
      status: 'active', created_at: '', updated_at: ''
    }));

    await TestBed.configureTestingModule({
      imports: [ChatComponent, RouterTestingModule, NoopAnimationsModule],
      providers: [
        { provide: ChatService, useValue: chatServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
        { provide: RevelationService, useValue: revelationServiceSpy },
        { provide: SoulConnectionService, useValue: soulConnectionServiceSpy },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: { get: () => '5' } } }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should call getRevelationTimeline when connectionId is present', () => {
    expect(revelationServiceSpy.getRevelationTimeline).toHaveBeenCalledWith(5);
  });

  it('should set revelationDay from the timeline', () => {
    expect(component.revelationDay).toBe(3);
  });

  it('should set latestPartnerRevelation to partner content (sender_id !== currentUserId)', () => {
    expect(component.latestPartnerRevelation).toBeTruthy();
    expect(component.latestPartnerRevelation?.content).toContain('travel the world');
  });
});

describe('ChatComponent — connection stage display', () => {
  let component: ChatComponent;
  let fixture: ComponentFixture<ChatComponent>;

  beforeEach(async () => {
    const revelationServiceSpy = jasmine.createSpyObj('RevelationService', ['getRevelationTimeline']);
    revelationServiceSpy.getRevelationTimeline.and.returnValue(of({
      connection_id: 5, current_day: 3, is_cycle_complete: false,
      revelations: [], next_revelation_type: 'hope_or_dream'
    }));

    const chatServiceSpy = jasmine.createSpyObj('ChatService', [
      'setCurrentUser', 'setupWebSocket', 'getChatData', 'sendMessage',
      'startTyping', 'stopTyping', 'disconnect', 'setCurrentUserId',
      'getEnhancedTypingUsers', 'updateConnectionActivity', 'setEmotionalState',
      'createTypingHandler'
    ]);
    chatServiceSpy.getChatData.and.returnValue(of({ user: null, messages: [] }));
    chatServiceSpy.getEnhancedTypingUsers.and.returnValue(of([]));
    chatServiceSpy.createTypingHandler.and.returnValue((_v: string) => {});

    const authServiceSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser$: of({ id: 1, first_name: 'Me' })
    });

    const soulConnectionServiceSpy = jasmine.createSpyObj('SoulConnectionService', ['getSoulConnection']);
    soulConnectionServiceSpy.getSoulConnection.and.returnValue(of({
      id: 5, connection_stage: 'revelation_phase',
      user1_id: 1, user2_id: 2, initiated_by: 1,
      compatibility_score: 80, reveal_day: 3,
      mutual_reveal_consent: false, first_dinner_completed: false,
      status: 'active', created_at: '', updated_at: ''
    }));

    await TestBed.configureTestingModule({
      imports: [ChatComponent, RouterTestingModule, NoopAnimationsModule],
      providers: [
        { provide: ChatService, useValue: chatServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
        { provide: RevelationService, useValue: revelationServiceSpy },
        { provide: SoulConnectionService, useValue: soulConnectionServiceSpy },
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: { get: () => '5' } } } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should return readable label for revelation_phase stage', () => {
    component.connectionStage = 'revelation_phase';
    expect(component.connectionStageLabel).toBe('Revelation Phase');
  });

  it('should return readable label for soul_discovery stage', () => {
    component.connectionStage = 'soul_discovery';
    expect(component.connectionStageLabel).toBe('Soul Discovery');
  });

  it('should return empty string when connectionStage is null', () => {
    component.connectionStage = null;
    expect(component.connectionStageLabel).toBe('');
  });
});
