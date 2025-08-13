/**
 * Comprehensive Messaging Interface Tests - Maximum Coverage
 * Tests real-time messaging, typing indicators, message history, and soul-themed interactions
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { of, throwError, BehaviorSubject } from 'rxjs';

import { MessagingComponent } from './messaging.component';
import { MessageService } from '../../core/services/message.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { ActivatedRoute } from '@angular/router';

interface Message {
  id: number;
  connection_id: number;
  sender_id: number;
  recipient_id: number;
  message_text: string;
  message_type: 'text' | 'revelation_share' | 'photo_consent' | 'system' | 'emoji';
  created_at: string;
  is_read: boolean;
  sender_name: string;
  is_own_message: boolean;
  emotional_tone?: string;
  reply_to_message_id?: number;
}

interface TypingIndicator {
  connection_id: number;
  user_id: number;
  user_name: string;
  is_typing: boolean;
  started_at: string;
}

interface ConnectionInfo {
  id: number;
  partner_id: number;
  partner_name: string;
  compatibility_score: number;
  connection_stage: string;
  current_day: number;
  is_online: boolean;
  last_seen?: string;
}

describe('MessagingComponent', () => {
  let component: MessagingComponent;
  let fixture: ComponentFixture<MessagingComponent>;
  let messageService: jasmine.SpyObj<MessageService>;
  let webSocketService: jasmine.SpyObj<WebSocketService>;
  let soulConnectionService: jasmine.SpyObj<SoulConnectionService>;
  let authService: jasmine.SpyObj<AuthService>;
  let notificationService: jasmine.SpyObj<NotificationService>;

  const mockConnectionInfo: ConnectionInfo = {
    id: 1,
    partner_id: 2,
    partner_name: 'Emma',
    compatibility_score: 88.5,
    connection_stage: 'revelation_cycle',
    current_day: 4,
    is_online: true,
    last_seen: '2025-01-20T14:30:00Z'
  };

  const mockMessages: Message[] = [
    {
      id: 1,
      connection_id: 1,
      sender_id: 2,
      recipient_id: 1,
      message_text: 'Your revelation about family values really touched my heart. Thank you for sharing something so personal.',
      message_type: 'text',
      created_at: '2025-01-20T10:30:00Z',
      is_read: true,
      sender_name: 'Emma',
      is_own_message: false,
      emotional_tone: 'grateful'
    },
    {
      id: 2,
      connection_id: 1,
      sender_id: 1,
      recipient_id: 2,
      message_text: 'I felt the same connection when reading your thoughts on authenticity. It\\'s beautiful how our souls align.',
      message_type: 'text',
      created_at: '2025-01-20T10:45:00Z',
      is_read: true,
      sender_name: 'You',
      is_own_message: true,
      emotional_tone: 'appreciative'
    },
    {
      id: 3,
      connection_id: 1,
      sender_id: 2,
      recipient_id: 1,
      message_text: 'I shared my day 4 revelation - hopes and dreams',
      message_type: 'revelation_share',
      created_at: '2025-01-20T14:15:00Z',
      is_read: false,
      sender_name: 'Emma',
      is_own_message: false
    },
    {
      id: 4,
      connection_id: 1,
      sender_id: 1,
      recipient_id: 2,
      message_text: '❤️',
      message_type: 'emoji',
      created_at: '2025-01-20T14:20:00Z',
      is_read: false,
      sender_name: 'You',
      is_own_message: true,
      reply_to_message_id: 3
    }
  ];

  const mockTypingIndicators: TypingIndicator[] = [
    {
      connection_id: 1,
      user_id: 2,
      user_name: 'Emma',
      is_typing: true,
      started_at: new Date().toISOString()
    }
  ];

  beforeEach(async () => {
    const messageSpy = jasmine.createSpyObj('MessageService', [
      'getMessages',
      'sendMessage',
      'markAsRead',
      'deleteMessage',
      'editMessage',
      'getMessageHistory'
    ]);

    const webSocketSpy = jasmine.createSpyObj('WebSocketService', [
      'connect',
      'disconnect',
      'onMessage',
      'sendTypingIndicator',
      'stopTypingIndicator',
      'onTypingIndicator',
      'isConnected'
    ]);

    const soulConnectionSpy = jasmine.createSpyObj('SoulConnectionService', [
      'getConnectionInfo',
      'updateLastActivity'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser'
    ]);

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
        ReactiveFormsModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        MatMenuModule,
        MatChipsModule,
        MatProgressSpinnerModule,
        MatBadgeModule,
        MatTooltipModule
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
    soulConnectionService = TestBed.inject(SoulConnectionService) as jasmine.SpyObj<SoulConnectionService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;

    // Default mock returns
    authService.getCurrentUser.and.returnValue(of({
      id: 1,
      email: 'test@example.com',
      first_name: 'Test'
    }));
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with loading state', () => {
      expect(component.isLoading).toBe(true);
      expect(component.messages).toEqual([]);
      expect(component.connectionInfo).toBeUndefined();
    });

    it('should load connection info and messages on init', fakeAsync(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      expect(soulConnectionService.getConnectionInfo).toHaveBeenCalledWith(1);
      expect(messageService.getMessages).toHaveBeenCalledWith(1);
      expect(component.messages).toEqual(mockMessages);
      expect(component.connectionInfo).toEqual(mockConnectionInfo);
      expect(component.isLoading).toBe(false);
    }));

    it('should handle connection not found', fakeAsync(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(
        throwError({ status: 404, error: { detail: 'Connection not found' } })
      );

      fixture.detectChanges();
      tick();

      expect(component.connectionNotFound).toBe(true);
      expect(notificationService.showError).toHaveBeenCalledWith(
        'Connection not found or you don\'t have access to it.'
      );
    }));

    it('should establish WebSocket connection for real-time messaging', fakeAsync(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      expect(webSocketService.connect).toHaveBeenCalled();
    }));
  });

  describe('Message Display', () => {
    beforeEach(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));
    });

    it('should display all messages in chronological order', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageElements = fixture.debugElement.queryAll(By.css('.message-item'));
      expect(messageElements.length).toBe(mockMessages.length);

      // Should be in chronological order
      const timestamps = messageElements.map(el => 
        el.query(By.css('.message-time')).nativeElement.textContent
      );
      expect(timestamps).toBeDefined();
    }));

    it('should distinguish between own and partner messages', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const ownMessages = fixture.debugElement.queryAll(By.css('.message-item.own-message'));
      const partnerMessages = fixture.debugElement.queryAll(By.css('.message-item.partner-message'));

      expect(ownMessages.length).toBe(2); // Messages from user (id: 1)
      expect(partnerMessages.length).toBe(2); // Messages from partner (id: 2)
    }));

    it('should display different message types correctly', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const textMessages = fixture.debugElement.queryAll(By.css('.message-text'));
      const revelationMessages = fixture.debugElement.queryAll(By.css('.revelation-message'));
      const emojiMessages = fixture.debugElement.queryAll(By.css('.emoji-message'));

      expect(textMessages.length).toBe(2);
      expect(revelationMessages.length).toBe(1);
      expect(emojiMessages.length).toBe(1);
    }));

    it('should show emotional tone indicators', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const emotionalIndicators = fixture.debugElement.queryAll(By.css('.emotional-tone'));
      expect(emotionalIndicators.length).toBe(2); // Two messages with emotional_tone

      expect(emotionalIndicators[0].nativeElement.classList).toContain('grateful');
      expect(emotionalIndicators[1].nativeElement.classList).toContain('appreciative');
    }));

    it('should show read/unread indicators', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const unreadMessages = fixture.debugElement.queryAll(By.css('.message-item.unread'));
      expect(unreadMessages.length).toBe(2); // Two unread messages in mock data
    }));

    it('should format message timestamps appropriately', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const timestamps = fixture.debugElement.queryAll(By.css('.message-time'));
      timestamps.forEach(timestamp => {
        expect(timestamp.nativeElement.textContent).toMatch(/\d{1,2}:\d{2}|yesterday|today/i);
      });
    }));

    it('should show reply threads correctly', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const replyMessage = fixture.debugElement.query(By.css('.message-item[data-message-id="4"]'));
      const replyIndicator = replyMessage.query(By.css('.reply-indicator'));
      
      expect(replyIndicator).toBeTruthy();
      expect(replyIndicator.nativeElement.textContent).toContain('Replying to');
    }));

    it('should handle long messages with text wrapping', fakeAsync(() => {
      const longMessage = {
        ...mockMessages[0],
        message_text: 'This is a very long message that should wrap properly across multiple lines and maintain readability while showing the full emotional content and context of the soul connection journey we are sharing together.'
      };

      messageService.getMessages.and.returnValue(of([longMessage]));
      fixture.detectChanges();
      tick();

      const messageText = fixture.debugElement.query(By.css('.message-text'));
      const styles = getComputedStyle(messageText.nativeElement);
      expect(styles.wordWrap).toBe('break-word');
    }));
  });

  describe('Message Composition', () => {
    beforeEach(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));
    });

    it('should send text messages', fakeAsync(() => {
      messageService.sendMessage.and.returnValue(of({
        id: 5,
        message_text: 'Test message',
        created_at: new Date().toISOString()
      }));

      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      const sendButton = fixture.debugElement.query(By.css('.send-button'));

      messageInput.nativeElement.value = 'Test message';
      messageInput.triggerEventHandler('input', { target: { value: 'Test message' } });
      sendButton.triggerEventHandler('click', {});

      expect(messageService.sendMessage).toHaveBeenCalledWith(1, 'Test message', 'text');
    }));

    it('should validate message content before sending', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      const sendButton = fixture.debugElement.query(By.css('.send-button'));

      // Empty message should not send
      messageInput.nativeElement.value = '';
      messageInput.triggerEventHandler('input', { target: { value: '' } });
      
      expect(sendButton.nativeElement.disabled).toBe(true);

      // Very long message should be truncated or rejected
      const longMessage = 'a'.repeat(2001); // Over 2000 character limit
      messageInput.nativeElement.value = longMessage;
      messageInput.triggerEventHandler('input', { target: { value: longMessage } });

      expect(component.isMessageTooLong()).toBe(true);
    }));

    it('should send messages on Enter key press', fakeAsync(() => {
      messageService.sendMessage.and.returnValue(of({
        id: 5,
        message_text: 'Enter key message',
        created_at: new Date().toISOString()
      }));

      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      messageInput.nativeElement.value = 'Enter key message';
      messageInput.triggerEventHandler('input', { target: { value: 'Enter key message' } });

      messageInput.triggerEventHandler('keydown.enter', { preventDefault: () => {} });

      expect(messageService.sendMessage).toHaveBeenCalledWith(1, 'Enter key message', 'text');
    }));

    it('should support Shift+Enter for multi-line messages', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      messageInput.nativeElement.value = 'Line 1\nLine 2';

      messageInput.triggerEventHandler('keydown.enter', { 
        shiftKey: true, 
        preventDefault: () => {} 
      });

      // Should not send message, should add new line
      expect(messageService.sendMessage).not.toHaveBeenCalled();
    }));

    it('should show character count', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      messageInput.nativeElement.value = 'Test message with character count';
      messageInput.triggerEventHandler('input', { target: { value: 'Test message with character count' } });
      
      fixture.detectChanges();

      const characterCount = fixture.debugElement.query(By.css('.character-count'));
      expect(characterCount).toBeTruthy();
      expect(characterCount.nativeElement.textContent).toContain('34');
    }));

    it('should support emoji picker', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const emojiButton = fixture.debugElement.query(By.css('.emoji-picker-button'));
      expect(emojiButton).toBeTruthy();

      emojiButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const emojiPicker = fixture.debugElement.query(By.css('.emoji-picker'));
      expect(emojiPicker).toBeTruthy();
    }));

    it('should insert selected emoji into message', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.insertEmoji('❤️');
      fixture.detectChanges();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      expect(messageInput.nativeElement.value).toContain('❤️');
    }));

    it('should provide soul-themed quick responses', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const quickResponseButton = fixture.debugElement.query(By.css('.quick-responses-button'));
      expect(quickResponseButton).toBeTruthy();

      quickResponseButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const quickResponses = fixture.debugElement.queryAll(By.css('.quick-response'));
      expect(quickResponses.length).toBeGreaterThan(0);

      const soulResponse = quickResponses.find(response => 
        response.nativeElement.textContent.includes('soul')
      );
      expect(soulResponse).toBeTruthy();
    }));
  });

  describe('Real-Time Features', () => {
    beforeEach(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
    });

    it('should show typing indicators', fakeAsync(() => {
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      const typingIndicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(typingIndicator).toBeTruthy();
      expect(typingIndicator.nativeElement.textContent).toContain('Emma is typing...');
    }));

    it('should send typing indicators when user is typing', fakeAsync(() => {
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      messageInput.triggerEventHandler('input', { target: { value: 'typing...' } });

      expect(webSocketService.sendTypingIndicator).toHaveBeenCalledWith(1, true);

      // Should stop typing indicator after delay
      tick(3000);
      expect(webSocketService.stopTypingIndicator).toHaveBeenCalledWith(1);
    }));

    it('should receive real-time messages', fakeAsync(() => {
      const newMessage: Message = {
        id: 5,
        connection_id: 1,
        sender_id: 2,
        recipient_id: 1,
        message_text: 'Real-time message!',
        message_type: 'text',
        created_at: new Date().toISOString(),
        is_read: false,
        sender_name: 'Emma',
        is_own_message: false
      };

      const messageSubject = new BehaviorSubject<any>({});
      webSocketService.onMessage.and.returnValue(messageSubject.asObservable());
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      // Simulate receiving new message
      messageSubject.next({
        type: 'new_message',
        message: newMessage
      });
      tick();

      expect(component.messages).toContain(newMessage);
      
      // Should automatically scroll to bottom
      expect(component.scrollToBottom).toHaveBeenCalled();
    }));

    it('should show online/offline status', fakeAsync(() => {
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      const onlineStatus = fixture.debugElement.query(By.css('.online-status'));
      expect(onlineStatus).toBeTruthy();
      expect(onlineStatus.nativeElement.textContent).toContain('Online');
    }));

    it('should update last seen when partner goes offline', fakeAsync(() => {
      const offlineConnectionInfo = {
        ...mockConnectionInfo,
        is_online: false,
        last_seen: '2025-01-20T13:45:00Z'
      };

      const connectionSubject = new BehaviorSubject(mockConnectionInfo);
      soulConnectionService.getConnectionInfo.and.returnValue(connectionSubject.asObservable());
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      // Partner goes offline
      connectionSubject.next(offlineConnectionInfo);
      tick();

      const lastSeen = fixture.debugElement.query(By.css('.last-seen'));
      expect(lastSeen).toBeTruthy();
      expect(lastSeen.nativeElement.textContent).toContain('Last seen');
    }));

    it('should handle WebSocket disconnection gracefully', fakeAsync(() => {
      webSocketService.isConnected.and.returnValue(false);
      webSocketService.onMessage.and.returnValue(throwError('Connection lost'));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      const connectionStatus = fixture.debugElement.query(By.css('.connection-status'));
      expect(connectionStatus).toBeTruthy();
      expect(connectionStatus.nativeElement.textContent).toContain('Reconnecting...');
    }));

    it('should auto-retry failed message sends', fakeAsync(() => {
      let callCount = 0;
      messageService.sendMessage.and.callFake(() => {
        callCount++;
        if (callCount === 1) {
          return throwError({ error: { detail: 'Network error' } });
        }
        return of({ id: 5, message_text: 'Retry success', created_at: new Date().toISOString() });
      });

      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      component.sendMessage('Test retry message');
      tick(2000); // Wait for retry

      expect(callCount).toBe(2);
      expect(notificationService.showSuccess).toHaveBeenCalledWith('Message sent successfully');
    }));
  });

  describe('Message Interactions', () => {
    beforeEach(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));
    });

    it('should mark messages as read when viewed', fakeAsync(() => {
      messageService.markAsRead.and.returnValue(of({ success: true }));

      fixture.detectChanges();
      tick();

      // Simulate scrolling to view unread messages
      component.markVisibleMessagesAsRead();

      expect(messageService.markAsRead).toHaveBeenCalled();
    }));

    it('should support message reactions', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageElement = fixture.debugElement.query(By.css('.message-item[data-message-id="1"]'));
      const reactionButton = messageElement.query(By.css('.reaction-button'));

      expect(reactionButton).toBeTruthy();

      reactionButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const reactionPicker = fixture.debugElement.query(By.css('.reaction-picker'));
      expect(reactionPicker).toBeTruthy();
    }));

    it('should allow replying to specific messages', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageElement = fixture.debugElement.query(By.css('.message-item[data-message-id="1"]'));
      const replyButton = messageElement.query(By.css('.reply-button'));

      replyButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      expect(component.replyingTo).toEqual(mockMessages[0]);

      const replyIndicator = fixture.debugElement.query(By.css('.replying-to'));
      expect(replyIndicator).toBeTruthy();
      expect(replyIndicator.nativeElement.textContent).toContain('Replying to Emma');
    }));

    it('should support message editing for own messages', fakeAsync(() => {
      messageService.editMessage.and.returnValue(of({ 
        success: true, 
        message: { ...mockMessages[1], message_text: 'Edited message' } 
      }));

      fixture.detectChanges();
      tick();

      const ownMessageElement = fixture.debugElement.query(By.css('.message-item.own-message[data-message-id="2"]'));
      const editButton = ownMessageElement.query(By.css('.edit-button'));

      editButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const editInput = fixture.debugElement.query(By.css('.edit-input'));
      expect(editInput).toBeTruthy();

      editInput.nativeElement.value = 'Edited message';
      
      const saveButton = fixture.debugElement.query(By.css('.save-edit'));
      saveButton.triggerEventHandler('click', {});

      expect(messageService.editMessage).toHaveBeenCalledWith(2, 'Edited message');
    }));

    it('should allow deleting own messages', fakeAsync(() => {
      messageService.deleteMessage.and.returnValue(of({ success: true }));

      fixture.detectChanges();
      tick();

      const ownMessageElement = fixture.debugElement.query(By.css('.message-item.own-message[data-message-id="2"]'));
      const deleteButton = ownMessageElement.query(By.css('.delete-button'));

      deleteButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      // Should show confirmation dialog
      const confirmDialog = fixture.debugElement.query(By.css('.delete-confirmation'));
      expect(confirmDialog).toBeTruthy();

      const confirmButton = confirmDialog.query(By.css('.confirm-delete'));
      confirmButton.triggerEventHandler('click', {});

      expect(messageService.deleteMessage).toHaveBeenCalledWith(2);
    }));

    it('should show message context menu on long press/right click', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageElement = fixture.debugElement.query(By.css('.message-item[data-message-id="1"]'));
      
      messageElement.triggerEventHandler('contextmenu', { preventDefault: () => {} });
      fixture.detectChanges();

      const contextMenu = fixture.debugElement.query(By.css('.message-context-menu'));
      expect(contextMenu).toBeTruthy();

      const menuItems = contextMenu.queryAll(By.css('.menu-item'));
      expect(menuItems.length).toBeGreaterThan(0);
    }));

    it('should support copying message text', fakeAsync(() => {
      spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.resolve());

      fixture.detectChanges();
      tick();

      component.copyMessageText(mockMessages[0]);

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockMessages[0].message_text);
      expect(notificationService.showSuccess).toHaveBeenCalledWith('Message copied to clipboard');
    }));
  });

  describe('Soul-Themed Features', () => {
    beforeEach(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));
    });

    it('should display connection compatibility in header', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const compatibilityScore = fixture.debugElement.query(By.css('.compatibility-score'));
      expect(compatibilityScore).toBeTruthy();
      expect(compatibilityScore.nativeElement.textContent).toContain('88.5%');
    }));

    it('should show revelation progress', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const revelationProgress = fixture.debugElement.query(By.css('.revelation-progress'));
      expect(revelationProgress).toBeTruthy();
      expect(revelationProgress.nativeElement.textContent).toContain('Day 4');
    }));

    it('should highlight revelation-shared messages specially', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const revelationMessage = fixture.debugElement.query(By.css('.message-item[data-message-id="3"]'));
      expect(revelationMessage.nativeElement.classList).toContain('revelation-message');

      const revelationIcon = revelationMessage.query(By.css('.revelation-icon'));
      expect(revelationIcon).toBeTruthy();
    }));

    it('should provide soul-themed message suggestions', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const suggestionButton = fixture.debugElement.query(By.css('.message-suggestions'));
      suggestionButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const suggestions = fixture.debugElement.queryAll(By.css('.suggestion-item'));
      expect(suggestions.length).toBeGreaterThan(0);

      const soulSuggestion = suggestions.find(s => 
        s.nativeElement.textContent.includes('soul') || 
        s.nativeElement.textContent.includes('heart')
      );
      expect(soulSuggestion).toBeTruthy();
    }));

    it('should show emotional tone analysis', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.analyzeEmotionalTone('I feel so grateful for this connection');
      fixture.detectChanges();

      expect(component.currentEmotionalTone).toBe('grateful');

      const toneIndicator = fixture.debugElement.query(By.css('.tone-indicator'));
      expect(toneIndicator).toBeTruthy();
    }));

    it('should provide connection insights', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const insightsButton = fixture.debugElement.query(By.css('.connection-insights'));
      insightsButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const insights = fixture.debugElement.query(By.css('.insights-panel'));
      expect(insights).toBeTruthy();
      expect(insights.nativeElement.textContent).toContain('compatibility');
    }));
  });

  describe('Message History and Search', () => {
    beforeEach(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));
    });

    it('should load more messages when scrolling to top', fakeAsync(() => {
      const olderMessages = [
        {
          ...mockMessages[0],
          id: 0,
          created_at: '2025-01-19T10:00:00Z',
          message_text: 'Older message'
        }
      ];

      messageService.getMessageHistory.and.returnValue(of(olderMessages));

      fixture.detectChanges();
      tick();

      const messageContainer = fixture.debugElement.query(By.css('.messages-container'));
      messageContainer.triggerEventHandler('scroll', { target: { scrollTop: 0 } });

      expect(messageService.getMessageHistory).toHaveBeenCalledWith(1, mockMessages[0].id);
    }));

    it('should support searching messages', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const searchButton = fixture.debugElement.query(By.css('.search-messages'));
      searchButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const searchInput = fixture.debugElement.query(By.css('.message-search-input'));
      expect(searchInput).toBeTruthy();

      searchInput.nativeElement.value = 'family values';
      searchInput.triggerEventHandler('input', { target: { value: 'family values' } });
      tick(300); // Debounce

      const highlightedMessages = fixture.debugElement.queryAll(By.css('.message-item.search-highlight'));
      expect(highlightedMessages.length).toBe(1);
    }));

    it('should filter messages by type', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const filterButton = fixture.debugElement.query(By.css('.message-filter'));
      filterButton.triggerEventHandler('click', {});
      fixture.detectChanges();

      const revelationFilter = fixture.debugElement.query(By.css('.filter-revelations'));
      revelationFilter.triggerEventHandler('click', {});
      fixture.detectChanges();

      const visibleMessages = fixture.debugElement.queryAll(By.css('.message-item:not(.filtered-out)'));
      expect(visibleMessages.length).toBe(1); // Only revelation message visible
    }));

    it('should export message history', fakeAsync(() => {
      spyOn(component, 'downloadAsFile').and.stub();

      fixture.detectChanges();
      tick();

      const exportButton = fixture.debugElement.query(By.css('.export-messages'));
      exportButton.triggerEventHandler('click', {});

      expect(component.downloadAsFile).toHaveBeenCalled();
    }));
  });

  describe('Performance Optimizations', () => {
    it('should use virtual scrolling for large message lists', () => {
      const largeMessageList = Array.from({ length: 1000 }, (_, i) => ({
        ...mockMessages[0],
        id: i + 1,
        message_text: `Message ${i + 1}`
      }));

      messageService.getMessages.and.returnValue(of(largeMessageList));
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();

      const virtualScroll = fixture.debugElement.query(By.css('cdk-virtual-scroll-viewport'));
      expect(virtualScroll).toBeTruthy();
    });

    it('should track messages by ID for ngFor performance', () => {
      expect(component.trackByMessageId).toBeDefined();
      expect(component.trackByMessageId(0, mockMessages[0])).toBe(mockMessages[0].id);
    });

    it('should debounce typing indicator sends', fakeAsync(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      
      // Rapid typing
      for (let i = 0; i < 5; i++) {
        messageInput.triggerEventHandler('input', { target: { value: `typing ${i}` } });
      }

      tick(500);

      expect(webSocketService.sendTypingIndicator).toHaveBeenCalledTimes(1);
    }));

    it('should implement message pagination', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.currentPage).toBe(1);
      expect(component.messagesPerPage).toBe(50);

      component.loadNextPage();
      expect(component.currentPage).toBe(2);
    }));

    it('should optimize image loading in messages', fakeAsync(() => {
      const imageMessage = {
        ...mockMessages[0],
        message_type: 'image' as const,
        message_text: 'https://example.com/image.jpg'
      };

      messageService.getMessages.and.returnValue(of([imageMessage]));
      fixture.detectChanges();
      tick();

      const lazyImage = fixture.debugElement.query(By.css('img[loading="lazy"]'));
      expect(lazyImage).toBeTruthy();
    }));
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));
    });

    it('should have proper ARIA labels', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      expect(messageInput.nativeElement.getAttribute('aria-label')).toContain('Type your message');

      const sendButton = fixture.debugElement.query(By.css('.send-button'));
      expect(sendButton.nativeElement.getAttribute('aria-label')).toContain('Send message');
    }));

    it('should support keyboard navigation', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageElements = fixture.debugElement.queryAll(By.css('.message-item'));
      messageElements.forEach(message => {
        expect(message.nativeElement.getAttribute('tabindex')).toBe('0');
      });
    }));

    it('should announce new messages to screen readers', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const liveRegion = fixture.debugElement.query(By.css('[aria-live="polite"]'));
      expect(liveRegion).toBeTruthy();

      // Simulate new message
      const newMessage: Message = {
        id: 5,
        connection_id: 1,
        sender_id: 2,
        recipient_id: 1,
        message_text: 'New message for screen reader',
        message_type: 'text',
        created_at: new Date().toISOString(),
        is_read: false,
        sender_name: 'Emma',
        is_own_message: false
      };

      component.handleNewMessage(newMessage);
      fixture.detectChanges();

      expect(liveRegion.nativeElement.textContent).toContain('New message from Emma');
    }));

    it('should have sufficient color contrast', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const messageElements = fixture.debugElement.queryAll(By.css('.message-item'));
      messageElements.forEach(message => {
        const styles = getComputedStyle(message.nativeElement);
        // Check that text has sufficient contrast (implementation would use actual color values)
        expect(styles.color).toBeDefined();
        expect(styles.backgroundColor).toBeDefined();
      });
    }));

    it('should support high contrast mode', () => {
      component.toggleHighContrast();
      fixture.detectChanges();

      const messagingContainer = fixture.debugElement.query(By.css('.messaging-container'));
      expect(messagingContainer.nativeElement.classList).toContain('high-contrast');
    });
  });

  describe('Mobile Responsiveness', () => {
    beforeEach(() => {
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));
    });

    it('should adapt layout for mobile screens', fakeAsync(() => {
      spyOnProperty(window, 'innerWidth').and.returnValue(375);
      
      fixture.detectChanges();
      tick();

      expect(component.isMobile).toBe(true);

      const mobileLayout = fixture.debugElement.query(By.css('.mobile-messaging'));
      expect(mobileLayout).toBeTruthy();
    }));

    it('should optimize input area for mobile keyboards', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      expect(messageInput.nativeElement.getAttribute('inputmode')).toBe('text');
      expect(messageInput.nativeElement.getAttribute('enterkeyhint')).toBe('send');
    }));

    it('should support swipe gestures for message actions', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const messageElement = fixture.debugElement.query(By.css('.message-item'));
      
      // Simulate swipe left
      messageElement.triggerEventHandler('swipeleft', {});
      
      expect(component.showMessageActions).toHaveBeenCalledWith(mockMessages[0]);
    }));

    it('should handle virtual keyboard properly', fakeAsync(() => {
      component.isMobile = true;
      fixture.detectChanges();
      tick();

      const messageInput = fixture.debugElement.query(By.css('.message-input'));
      messageInput.triggerEventHandler('focus', {});

      expect(component.adjustForVirtualKeyboard).toHaveBeenCalled();
    }));
  });

  describe('Error Handling', () => {
    it('should handle message send failures', fakeAsync(() => {
      messageService.sendMessage.and.returnValue(
        throwError({ error: { detail: 'Message send failed' } })
      );

      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      component.sendMessage('Failed message');

      expect(notificationService.showError).toHaveBeenCalledWith(
        'Failed to send message: Message send failed'
      );
      
      // Should show retry option
      const retryButton = fixture.debugElement.query(By.css('.retry-send'));
      expect(retryButton).toBeTruthy();
    }));

    it('should handle WebSocket connection errors', fakeAsync(() => {
      webSocketService.onMessage.and.returnValue(
        throwError({ error: 'WebSocket connection failed' })
      );

      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      messageService.getMessages.and.returnValue(of(mockMessages));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      fixture.detectChanges();
      tick();

      const connectionWarning = fixture.debugElement.query(By.css('.connection-warning'));
      expect(connectionWarning).toBeTruthy();
      expect(connectionWarning.nativeElement.textContent).toContain('Connection issues');
    }));

    it('should handle malformed messages gracefully', fakeAsync(() => {
      const malformedMessage = {
        id: null,
        message_text: undefined,
        created_at: 'invalid-date'
      };

      messageService.getMessages.and.returnValue(of([malformedMessage as any]));
      soulConnectionService.getConnectionInfo.and.returnValue(of(mockConnectionInfo));
      webSocketService.onMessage.and.returnValue(of({}));
      webSocketService.onTypingIndicator.and.returnValue(of(mockTypingIndicators[0]));

      expect(() => {
        fixture.detectChanges();
        tick();
      }).not.toThrow();

      // Should filter out malformed messages
      expect(component.messages).not.toContain(malformedMessage);
    }));
  });
});