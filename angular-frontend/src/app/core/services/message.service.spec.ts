/**
 * MessageService Tests
 * Comprehensive tests for message management and HTTP operations
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { MessageService, Message, MessageSendResponse, MessageEditResponse, MessageDeleteResponse } from './message.service';
import { environment } from '@environments/environment';

describe('MessageService', () => {
  let service: MessageService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [MessageService]
    });

    service = TestBed.inject(MessageService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should have apiUrl from environment', () => {
      expect(service['apiUrl']).toBe(environment.apiUrl);
    });
  });

  describe('getMessages()', () => {
    it('should GET messages for a connection', () => {
      const connectionId = 123;
      const mockMessages: Message[] = [
        {
          id: 1,
          connection_id: connectionId,
          sender_id: 10,
          recipient_id: 20,
          message_text: 'Hello',
          message_type: 'text',
          created_at: '2025-10-17T00:00:00Z',
          is_read: false,
          sender_name: 'User1',
          is_own_message: true
        },
        {
          id: 2,
          connection_id: connectionId,
          sender_id: 20,
          recipient_id: 10,
          message_text: 'Hi there',
          message_type: 'text',
          created_at: '2025-10-17T00:01:00Z',
          is_read: true,
          sender_name: 'User2',
          is_own_message: false
        }
      ];

      service.getMessages(connectionId).subscribe(messages => {
        expect(messages).toEqual(mockMessages);
        expect(messages.length).toBe(2);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockMessages);
    });

    it('should return empty array when no messages exist', () => {
      const connectionId = 456;

      service.getMessages(connectionId).subscribe(messages => {
        expect(messages).toEqual([]);
        expect(messages.length).toBe(0);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      req.flush([]);
    });

    it('should handle messages with optional fields', () => {
      const connectionId = 789;
      const messageWithOptionals: Message[] = [{
        id: 1,
        connection_id: connectionId,
        sender_id: 10,
        recipient_id: 20,
        message_text: 'Test',
        message_type: 'text',
        created_at: '2025-10-17T00:00:00Z',
        is_read: false,
        sender_name: 'User',
        is_own_message: true,
        emotional_tone: 'happy',
        reply_to_message_id: 5
      }];

      service.getMessages(connectionId).subscribe(messages => {
        expect(messages[0].emotional_tone).toBe('happy');
        expect(messages[0].reply_to_message_id).toBe(5);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      req.flush(messageWithOptionals);
    });

    it('should handle different message types', () => {
      const connectionId = 111;
      const messageTypes: Message[] = [
        { id: 1, connection_id: connectionId, sender_id: 1, recipient_id: 2, message_text: 'Text', message_type: 'text', created_at: '2025-10-17T00:00:00Z', is_read: false, sender_name: 'User', is_own_message: true },
        { id: 2, connection_id: connectionId, sender_id: 1, recipient_id: 2, message_text: 'Reveal', message_type: 'revelation_share', created_at: '2025-10-17T00:01:00Z', is_read: false, sender_name: 'User', is_own_message: true },
        { id: 3, connection_id: connectionId, sender_id: 1, recipient_id: 2, message_text: 'Consent', message_type: 'photo_consent', created_at: '2025-10-17T00:02:00Z', is_read: false, sender_name: 'User', is_own_message: true },
        { id: 4, connection_id: connectionId, sender_id: 1, recipient_id: 2, message_text: 'System', message_type: 'system', created_at: '2025-10-17T00:03:00Z', is_read: false, sender_name: 'System', is_own_message: false }
      ];

      service.getMessages(connectionId).subscribe(messages => {
        expect(messages.length).toBe(4);
        expect(messages[0].message_type).toBe('text');
        expect(messages[1].message_type).toBe('revelation_share');
        expect(messages[2].message_type).toBe('photo_consent');
        expect(messages[3].message_type).toBe('system');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      req.flush(messageTypes);
    });

    it('should handle HTTP errors', () => {
      const connectionId = 999;
      spyOn(console, 'error');

      service.getMessages(connectionId).subscribe({
        next: () => fail('should have failed with 404 error'),
        error: (error) => {
          expect(error.status).toBe(404);
          expect(console.error).toHaveBeenCalled();
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });

    it('should use correct endpoint URL', () => {
      const connectionId = 123;

      service.getMessages(connectionId).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      expect(req.request.url).toBe(`${environment.apiUrl}/messages/${connectionId}`);
      req.flush([]);
    });
  });

  describe('sendMessage()', () => {
    it('should POST a text message', () => {
      const connectionId = 123;
      const messageText = 'Hello world';
      const mockResponse: MessageSendResponse = {
        id: 1,
        message_text: messageText,
        created_at: '2025-10-17T00:00:00Z'
      };

      service.sendMessage(connectionId, messageText).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.message_text).toBe(messageText);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        message_text: messageText,
        message_type: 'text'
      });
      req.flush(mockResponse);
    });

    it('should POST with custom message type', () => {
      const connectionId = 456;
      const messageText = 'Revelation text';
      const messageType = 'revelation_share';

      service.sendMessage(connectionId, messageText, messageType).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      expect(req.request.body).toEqual({
        message_text: messageText,
        message_type: messageType
      });
      req.flush({ id: 1, message_text: messageText, created_at: '2025-10-17T00:00:00Z' });
    });

    it('should default to "text" message type when not specified', () => {
      const connectionId = 789;
      const messageText = 'Default type message';

      service.sendMessage(connectionId, messageText).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      expect(req.request.body.message_type).toBe('text');
      req.flush({ id: 1, message_text: messageText, created_at: '2025-10-17T00:00:00Z' });
    });

    it('should handle empty message text', () => {
      const connectionId = 111;
      const messageText = '';

      service.sendMessage(connectionId, messageText).subscribe(response => {
        expect(response.message_text).toBe('');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      expect(req.request.body.message_text).toBe('');
      req.flush({ id: 1, message_text: '', created_at: '2025-10-17T00:00:00Z' });
    });

    it('should handle long message text', () => {
      const connectionId = 222;
      const messageText = 'a'.repeat(1000);

      service.sendMessage(connectionId, messageText).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      expect(req.request.body.message_text.length).toBe(1000);
      req.flush({ id: 1, message_text: messageText, created_at: '2025-10-17T00:00:00Z' });
    });

    it('should handle special characters in message text', () => {
      const connectionId = 333;
      const messageText = 'Hello 👋 \n\t "quotes" \'apostrophes\'';

      service.sendMessage(connectionId, messageText).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      expect(req.request.body.message_text).toBe(messageText);
      req.flush({ id: 1, message_text: messageText, created_at: '2025-10-17T00:00:00Z' });
    });

    it('should handle HTTP errors', () => {
      const connectionId = 444;
      spyOn(console, 'error');

      service.sendMessage(connectionId, 'Test').subscribe({
        next: () => fail('should have failed with 500 error'),
        error: (error) => {
          expect(error.status).toBe(500);
          expect(console.error).toHaveBeenCalled();
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      req.flush('Server Error', { status: 500, statusText: 'Server Error' });
    });
  });

  describe('markAsRead()', () => {
    it('should POST to mark messages as read', () => {
      const messageIds = [1, 2, 3];
      const mockResponse = { success: true };

      service.markAsRead(messageIds).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.success).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/mark-read`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ message_ids: messageIds });
      req.flush(mockResponse);
    });

    it('should handle single message ID', () => {
      const messageIds = [5];

      service.markAsRead(messageIds).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/mark-read`);
      expect(req.request.body.message_ids).toEqual([5]);
      req.flush({ success: true });
    });

    it('should handle empty array', () => {
      const messageIds: number[] = [];

      service.markAsRead(messageIds).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/mark-read`);
      expect(req.request.body.message_ids).toEqual([]);
      req.flush({ success: true });
    });

    it('should handle large number of message IDs', () => {
      const messageIds = Array.from({ length: 100 }, (_, i) => i + 1);

      service.markAsRead(messageIds).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/mark-read`);
      expect(req.request.body.message_ids.length).toBe(100);
      req.flush({ success: true });
    });

    it('should handle HTTP errors', () => {
      const messageIds = [1, 2, 3];
      spyOn(console, 'error');

      service.markAsRead(messageIds).subscribe({
        next: () => fail('should have failed with 403 error'),
        error: (error) => {
          expect(error.status).toBe(403);
          expect(console.error).toHaveBeenCalled();
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/mark-read`);
      req.flush('Forbidden', { status: 403, statusText: 'Forbidden' });
    });

    it('should use correct endpoint URL', () => {
      service.markAsRead([1]).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/mark-read`);
      expect(req.request.url).toBe(`${environment.apiUrl}/messages/mark-read`);
      req.flush({ success: true });
    });
  });

  describe('deleteMessage()', () => {
    it('should DELETE a message', () => {
      const messageId = 123;
      const mockResponse: MessageDeleteResponse = { success: true };

      service.deleteMessage(messageId).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.success).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      expect(req.request.method).toBe('DELETE');
      req.flush(mockResponse);
    });

    it('should handle failed deletion', () => {
      const messageId = 456;
      const mockResponse: MessageDeleteResponse = { success: false };

      service.deleteMessage(messageId).subscribe(response => {
        expect(response.success).toBe(false);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      req.flush(mockResponse);
    });

    it('should handle HTTP errors', () => {
      const messageId = 789;
      spyOn(console, 'error');

      service.deleteMessage(messageId).subscribe({
        next: () => fail('should have failed with 404 error'),
        error: (error) => {
          expect(error.status).toBe(404);
          expect(console.error).toHaveBeenCalled();
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });

    it('should use correct endpoint URL', () => {
      const messageId = 999;

      service.deleteMessage(messageId).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      expect(req.request.url).toBe(`${environment.apiUrl}/messages/${messageId}`);
      req.flush({ success: true });
    });
  });

  describe('editMessage()', () => {
    it('should PUT to edit a message', () => {
      const messageId = 123;
      const newText = 'Updated message text';
      const mockResponse: MessageEditResponse = {
        success: true,
        message: {
          id: messageId,
          connection_id: 1,
          sender_id: 10,
          recipient_id: 20,
          message_text: newText,
          message_type: 'text',
          created_at: '2025-10-17T00:00:00Z',
          is_read: true,
          sender_name: 'User',
          is_own_message: true
        }
      };

      service.editMessage(messageId, newText).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.success).toBe(true);
        expect(response.message.message_text).toBe(newText);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual({ message_text: newText });
      req.flush(mockResponse);
    });

    it('should handle empty new text', () => {
      const messageId = 456;
      const newText = '';

      service.editMessage(messageId, newText).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      expect(req.request.body.message_text).toBe('');
      req.flush({
        success: true,
        message: { id: messageId, connection_id: 1, sender_id: 1, recipient_id: 2, message_text: '', message_type: 'text', created_at: '2025-10-17T00:00:00Z', is_read: false, sender_name: 'User', is_own_message: true }
      });
    });

    it('should handle special characters in new text', () => {
      const messageId = 789;
      const newText = 'Updated 🎉 with "quotes" and \n newlines';

      service.editMessage(messageId, newText).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      expect(req.request.body.message_text).toBe(newText);
      req.flush({
        success: true,
        message: { id: messageId, connection_id: 1, sender_id: 1, recipient_id: 2, message_text: newText, message_type: 'text', created_at: '2025-10-17T00:00:00Z', is_read: false, sender_name: 'User', is_own_message: true }
      });
    });

    it('should handle HTTP errors', () => {
      const messageId = 999;
      spyOn(console, 'error');

      service.editMessage(messageId, 'New text').subscribe({
        next: () => fail('should have failed with 403 error'),
        error: (error) => {
          expect(error.status).toBe(403);
          expect(console.error).toHaveBeenCalled();
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      req.flush('Forbidden', { status: 403, statusText: 'Forbidden' });
    });

    it('should use correct endpoint URL', () => {
      const messageId = 111;

      service.editMessage(messageId, 'Text').subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${messageId}`);
      expect(req.request.url).toBe(`${environment.apiUrl}/messages/${messageId}`);
      req.flush({
        success: true,
        message: { id: messageId, connection_id: 1, sender_id: 1, recipient_id: 2, message_text: 'Text', message_type: 'text', created_at: '2025-10-17T00:00:00Z', is_read: false, sender_name: 'User', is_own_message: true }
      });
    });
  });

  describe('getMessageHistory()', () => {
    it('should GET message history with pagination', () => {
      const connectionId = 123;
      const beforeMessageId = 100;
      const mockMessages: Message[] = [
        { id: 99, connection_id: connectionId, sender_id: 1, recipient_id: 2, message_text: 'Old message 1', message_type: 'text', created_at: '2025-10-16T00:00:00Z', is_read: true, sender_name: 'User', is_own_message: true },
        { id: 98, connection_id: connectionId, sender_id: 2, recipient_id: 1, message_text: 'Old message 2', message_type: 'text', created_at: '2025-10-15T00:00:00Z', is_read: true, sender_name: 'User2', is_own_message: false }
      ];

      service.getMessageHistory(connectionId, beforeMessageId).subscribe(messages => {
        expect(messages).toEqual(mockMessages);
        expect(messages.length).toBe(2);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}/history?before=${beforeMessageId}`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('before')).toBe(beforeMessageId.toString());
      req.flush(mockMessages);
    });

    it('should return empty array when no history exists', () => {
      const connectionId = 456;
      const beforeMessageId = 50;

      service.getMessageHistory(connectionId, beforeMessageId).subscribe(messages => {
        expect(messages).toEqual([]);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}/history?before=${beforeMessageId}`);
      req.flush([]);
    });

    it('should handle HTTP errors', () => {
      const connectionId = 789;
      const beforeMessageId = 10;
      spyOn(console, 'error');

      service.getMessageHistory(connectionId, beforeMessageId).subscribe({
        next: () => fail('should have failed with 500 error'),
        error: (error) => {
          expect(error.status).toBe(500);
          expect(console.error).toHaveBeenCalled();
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}/history?before=${beforeMessageId}`);
      req.flush('Server Error', { status: 500, statusText: 'Server Error' });
    });

    it('should use correct endpoint URL and query params', () => {
      const connectionId = 999;
      const beforeMessageId = 200;

      service.getMessageHistory(connectionId, beforeMessageId).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}/history?before=${beforeMessageId}`);
      expect(req.request.url).toBe(`${environment.apiUrl}/messages/${connectionId}/history`);
      expect(req.request.params.get('before')).toBe('200');
      req.flush([]);
    });
  });

  describe('Error Handling', () => {
    it('should log errors to console', () => {
      spyOn(console, 'error');

      service.getMessages(123).subscribe({
        next: () => fail('should have failed'),
        error: () => {
          expect(console.error).toHaveBeenCalledWith('MessageService error:', jasmine.any(Object));
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/123`);
      req.flush('Error', { status: 500, statusText: 'Server Error' });
    });

    it('should propagate errors through observable', () => {
      service.sendMessage(123, 'Test').subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error).toBeDefined();
          expect(error.status).toBe(400);
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/messages/123`);
      req.flush('Bad Request', { status: 400, statusText: 'Bad Request' });
    });
  });

  describe('Integration Tests', () => {
    it('should handle multiple concurrent requests', () => {
      service.getMessages(1).subscribe();
      service.sendMessage(1, 'Hello').subscribe();
      service.markAsRead([1, 2]).subscribe();

      const requests = httpMock.match(req => req.url.includes('/messages'));
      expect(requests.length).toBe(3);

      requests[0].flush([]);
      requests[1].flush({ id: 1, message_text: 'Hello', created_at: '2025-10-17T00:00:00Z' });
      requests[2].flush({ success: true });
    });

    it('should handle sequential operations', () => {
      const connectionId = 123;

      // Get messages
      service.getMessages(connectionId).subscribe(messages => {
        expect(messages.length).toBe(1);
      });
      const getReq = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      getReq.flush([{ id: 1, connection_id: connectionId, sender_id: 1, recipient_id: 2, message_text: 'Test', message_type: 'text', created_at: '2025-10-17T00:00:00Z', is_read: false, sender_name: 'User', is_own_message: true }]);

      // Send message
      service.sendMessage(connectionId, 'Reply').subscribe(response => {
        expect(response.id).toBe(2);
      });
      const sendReq = httpMock.expectOne(`${environment.apiUrl}/messages/${connectionId}`);
      sendReq.flush({ id: 2, message_text: 'Reply', created_at: '2025-10-17T00:01:00Z' });

      // Mark as read
      service.markAsRead([1, 2]).subscribe(result => {
        expect(result.success).toBe(true);
      });
      const readReq = httpMock.expectOne(`${environment.apiUrl}/messages/mark-read`);
      readReq.flush({ success: true });
    });
  });
});
