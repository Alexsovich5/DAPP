/**
 * Messaging Component Tests
 * Tests for partially-implemented messaging interface - basic structure only
 *
 * NOTE: This component uses WebSocket methods that don't exist yet in the stub service.
 * Tests verify basic component structure and initialization only.
 * TODO: Expand tests when WebSocket service is fully implemented
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ReactiveFormsModule } from '@angular/forms';
import { of } from 'rxjs';

import { MessagingComponent } from './messaging.component';
import { MessageService } from '../../core/services/message.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { ActivatedRoute } from '@angular/router';

describe('MessagingComponent', () => {
  let component: MessagingComponent;
  let fixture: ComponentFixture<MessagingComponent>;
  let messageService: jasmine.SpyObj<MessageService>;
  let webSocketService: jasmine.SpyObj<WebSocketService>;
  let authService: jasmine.SpyObj<AuthService>;

  const mockUser = {
    id: 1,
    email: 'test@example.com',
    username: 'testuser',
    is_profile_complete: true,
    is_active: true,
    first_name: 'Test'
  };

  beforeEach(async () => {
    const messageSpy = jasmine.createSpyObj('MessageService', [
      'getMessages',
      'sendMessage',
      'markAsRead'
    ]);

    const webSocketSpy = jasmine.createSpyObj('WebSocketService', [
      'connect',
      'disconnect'
    ]);

    const soulConnectionSpy = jasmine.createSpyObj('SoulConnectionService', []);

    const authSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser$: of(mockUser)
    });

    const notificationSpy = jasmine.createSpyObj('NotificationService', [
      'showSuccess',
      'showError',
      'showInfo'
    ]);

    await TestBed.configureTestingModule({
      declarations: [MessagingComponent],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NoopAnimationsModule,
        ReactiveFormsModule
      ],
      providers: [
        { provide: MessageService, useValue: messageSpy },
        { provide: WebSocketService, useValue: webSocketSpy },
        { provide: SoulConnectionService, useValue: soulConnectionSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notificationSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            params: of({ connectionId: '1' }),
            queryParams: of({})
          }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MessagingComponent);
    component = fixture.componentInstance;

    messageService = TestBed.inject(MessageService) as jasmine.SpyObj<MessageService>;
    webSocketService = TestBed.inject(WebSocketService) as jasmine.SpyObj<WebSocketService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with default properties', () => {
      expect(component.connectionId).toBe(0);
      expect(component.messages).toEqual([]);
      expect(component.isLoading).toBe(true);
      expect(component.connectionNotFound).toBe(false);
      expect(component.messageControl).toBeDefined();
      expect(component.typingIndicators).toEqual([]);
      expect(component.partnerTyping).toBe(false);
    });

    it('should have messageControl FormControl', () => {
      expect(component.messageControl).toBeDefined();
      expect(component.messageControl.value).toBe('');
    });

    it('should have character limit constant', () => {
      expect(component['CHARACTER_LIMIT']).toBe(2000);
    });

    it('should detect mobile device', () => {
      expect(component.isMobile).toBeDefined();
      expect(typeof component.isMobile).toBe('boolean');
    });
  });

  describe('Component Properties', () => {
    it('should have message control with empty initial value', () => {
      expect(component.messageControl.value).toBe('');
    });

    it('should have connectionId property', () => {
      expect(component.connectionId).toBe(0);
    });

    it('should have messages array', () => {
      expect(Array.isArray(component.messages)).toBe(true);
      expect(component.messages.length).toBe(0);
    });

    it('should have typing indicators array', () => {
      expect(Array.isArray(component.typingIndicators)).toBe(true);
    });

    it('should have UI state properties', () => {
      expect(component.showEmojiPicker).toBe(false);
      expect(component.showQuickResponses).toBe(false);
      expect(component.showConnectionInsights).toBe(false);
      expect(component.highContrastMode).toBe(false);
    });
  });

  describe('Message Validation', () => {
    it('should detect when message is too long', () => {
      const longText = 'a'.repeat(2001);
      component.messageControl.setValue(longText);
      expect(component.isMessageTooLong()).toBe(true);
    });

    it('should allow messages within character limit', () => {
      const normalText = 'Hello, this is a normal message';
      component.messageControl.setValue(normalText);
      expect(component.isMessageTooLong()).toBe(false);
    });

    it('should handle empty messages', () => {
      component.messageControl.setValue('');
      expect(component.isMessageTooLong()).toBe(false);
    });
  });

  describe('Utility Methods', () => {
    it('should insert emoji into message', () => {
      component.messageControl.setValue('Hello ');
      component.insertEmoji('👋');
      expect(component.messageControl.value).toBe('Hello 👋');
    });

    it('should close emoji picker after inserting emoji', () => {
      component.showEmojiPicker = true;
      component.insertEmoji('😊');
      expect(component.showEmojiPicker).toBe(false);
    });

    it('should toggle high contrast mode', () => {
      expect(component.highContrastMode).toBe(false);
      component.toggleHighContrast();
      expect(component.highContrastMode).toBe(true);
      component.toggleHighContrast();
      expect(component.highContrastMode).toBe(false);
    });

    it('should analyze emotional tone in message', () => {
      component.analyzeEmotionalTone('I am so grateful for your support');
      expect(component.currentEmotionalTone).toBe('grateful');

      component.analyzeEmotionalTone('I appreciate your help');
      expect(component.currentEmotionalTone).toBe('appreciative');

      component.analyzeEmotionalTone('I am excited about this');
      expect(component.currentEmotionalTone).toBe('joyful');

      component.analyzeEmotionalTone('Just a regular message');
      expect(component.currentEmotionalTone).toBe('');
    });

    it('should track messages by id', () => {
      const mockMessage = {
        id: 123,
        connection_id: 1,
        sender_id: 1,
        recipient_id: 2,
        message_text: 'Test',
        message_type: 'text' as const,
        created_at: '2025-01-01',
        is_read: false,
        sender_name: 'Test',
        is_own_message: true
      };
      expect(component.trackByMessageId(0, mockMessage)).toBe(123);
    });
  });

  describe('Pagination', () => {
    it('should load next page', () => {
      expect(component.currentPage).toBe(1);
      component.loadNextPage();
      expect(component.currentPage).toBe(2);
      component.loadNextPage();
      expect(component.currentPage).toBe(3);
    });

    it('should have messages per page limit', () => {
      expect(component.messagesPerPage).toBe(50);
    });
  });

  describe('Lifecycle Hooks', () => {
    it('should call ngOnInit', () => {
      expect(component.ngOnInit).toBeDefined();
    });

    it('should call ngOnDestroy', () => {
      expect(component.ngOnDestroy).toBeDefined();
      expect(() => component.ngOnDestroy()).not.toThrow();
    });
  });
});

// TODO: Add comprehensive tests when component is fully implemented
// Future tests should cover:
// - Connection info loading (when SoulConnectionService.getConnectionInfo exists)
// - Message loading and display
// - Real-time message updates via WebSocket (when WebSocketService.onMessage exists)
// - Typing indicator functionality (when WebSocketService typing methods exist)
// - Message sending and validation
// - Emoji picker integration
// - Reply and edit functionality
// - Mobile responsive features
// - Accessibility features
// - Connection insights panel
// - Message export functionality
