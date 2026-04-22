import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { MessagingComponent } from './messaging.component';
import { MessageService } from '../../core/services/message.service';
import { AuthService } from '../../core/services/auth.service';

describe('MessagingComponent', () => {
  let component: MessagingComponent;
  let fixture: ComponentFixture<MessagingComponent>;
  let messageService: jasmine.SpyObj<MessageService>;

  const mockUser = {
    id: 1,
    email: 'test@example.com',
    username: 'testuser',
    is_profile_complete: true,
    is_active: true,
    first_name: 'Test',
  };

  const mockMessages = [
    {
      id: 10,
      connection_id: 1,
      sender_id: 1,
      recipient_id: 2,
      message_text: 'Hello there',
      message_type: 'text' as const,
      created_at: '2026-04-19T10:00:00Z',
      is_read: true,
      sender_name: 'Test',
      is_own_message: true,
    },
    {
      id: 11,
      connection_id: 1,
      sender_id: 2,
      recipient_id: 1,
      message_text: 'Hi back',
      message_type: 'text' as const,
      created_at: '2026-04-19T10:01:00Z',
      is_read: false,
      sender_name: 'Other',
      is_own_message: false,
    },
  ];

  beforeEach(async () => {
    const messageSpy = jasmine.createSpyObj('MessageService', ['getMessages', 'sendMessage']);
    messageSpy.getMessages.and.returnValue(of(mockMessages));
    messageSpy.sendMessage.and.returnValue(of({ id: 99 }));

    const authSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser$: of(mockUser),
    });

    await TestBed.configureTestingModule({
      imports: [MessagingComponent],
      providers: [
        provideRouter([]),
        { provide: MessageService, useValue: messageSpy },
        { provide: AuthService, useValue: authSpy },
        {
          provide: ActivatedRoute,
          useValue: { params: of({ connectionId: '1' }) },
        },
      ],
    }).compileComponents();

    messageService = TestBed.inject(MessageService) as jasmine.SpyObj<MessageService>;
    fixture = TestBed.createComponent(MessagingComponent);
    component = fixture.componentInstance;
  });

  it('renders the chat page-shell variant', () => {
    fixture.detectChanges();
    const shell = fixture.nativeElement.querySelector('df-page-shell');
    expect(shell).toBeTruthy();
    expect(shell.getAttribute('variant')).toBe('chat');
  });

  it('renders header with back button, avatar, and subtitle', () => {
    fixture.detectChanges();
    const el = fixture.nativeElement;
    expect(el.querySelector('.messaging__header')).toBeTruthy();
    expect(el.querySelector('button[aria-label="Back"]')).toBeTruthy();
    expect(el.querySelector('df-avatar')).toBeTruthy();
    expect(el.querySelector('.messaging__subtitle').textContent).toContain('Day');
  });

  it('renders the day banner chip', () => {
    fixture.detectChanges();
    const chip = fixture.nativeElement.querySelector('.messaging__banner');
    expect(chip).toBeTruthy();
    expect(chip.textContent).toContain('Day 1');
  });

  it('renders composer with attach, input, and send buttons', () => {
    fixture.detectChanges();
    const form = fixture.nativeElement.querySelector('form.messaging__composer');
    expect(form).toBeTruthy();
    expect(form.querySelector('button[aria-label="Attach"]')).toBeTruthy();
    expect(form.querySelector('input[aria-label="Compose message"]')).toBeTruthy();
    expect(form.querySelector('button[aria-label="Send"]')).toBeTruthy();
  });

  it('renders loaded messages as bubbles with outgoing class for current user', () => {
    fixture.detectChanges();
    const bubbles = fixture.nativeElement.querySelectorAll('.messaging__bubble');
    expect(bubbles.length).toBe(2);
    expect(bubbles[0].classList.contains('is-outgoing')).toBe(true);
    expect(bubbles[1].classList.contains('is-outgoing')).toBe(false);
  });

  it('sends a message via MessageService and clears the draft', () => {
    fixture.detectChanges();
    component.draft = 'Hello world';
    component.sendMessage();
    expect(messageService.sendMessage).toHaveBeenCalledWith(1, 'Hello world', 'text');
    expect(component.draft).toBe('');
  });

  it('does not send empty or whitespace-only drafts', () => {
    fixture.detectChanges();
    messageService.sendMessage.calls.reset();
    component.draft = '   ';
    component.sendMessage();
    expect(messageService.sendMessage).not.toHaveBeenCalled();
  });

  it('exposes a revelation prompt scoped to the current day', () => {
    fixture.detectChanges();
    expect(component.revelationPrompt).toBe('A personal value');
  });
});
