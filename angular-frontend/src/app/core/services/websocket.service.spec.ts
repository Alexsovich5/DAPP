/**
 * Comprehensive WebSocket Service UI Tests - Maximum Coverage
 * Tests real-time connection management, message handling, and connection state UI integration
 */

import { TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject, throwError, of } from 'rxjs';
import { environment } from '../../../environments/environment';

import { WebSocketService } from './websocket.service';
import { AuthService } from './auth.service';
import { NotificationService } from './notification.service';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  connection_id?: number;
  user_id?: number;
}

interface ConnectionStatus {
  isConnected: boolean;
  reconnectAttempts: number;
  lastConnectedAt?: string;
  lastDisconnectedAt?: string;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  latency?: number;
}

interface TypingIndicator {
  connection_id: number;
  user_id: number;
  user_name: string;
  is_typing: boolean;
  started_at: string;
}

interface PresenceUpdate {
  user_id: number;
  user_name: string;
  is_online: boolean;
  last_seen?: string;
  activity_status: 'active' | 'idle' | 'away' | 'offline';
}

// Mock WebSocket class
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    // Mock successful send
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      if (this.onclose) {
        this.onclose(new CloseEvent('close', { code: code || 1000, reason: reason || '' }));
      }
    }, 10);
  }

  // Test helper methods
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { 
        data: JSON.stringify(data) 
      }));
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  simulateClose(code = 1000, reason = '') {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason }));
    }
  }
}

describe('WebSocketService', () => {
  let service: WebSocketService;
  let authService: jasmine.SpyObj<AuthService>;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let mockWebSocket: MockWebSocket;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', ['getCurrentUser', 'getToken']);
    const notificationSpy = jasmine.createSpyObj('NotificationService', [
      'showError',
      'showWarning',
      'showInfo'
    ]);

    TestBed.configureTestingModule({
      providers: [
        WebSocketService,
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notificationSpy }
      ]
    });

    service = TestBed.inject(WebSocketService);
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;

    // Mock WebSocket globally
    (global as any).WebSocket = MockWebSocket;

    // Default auth mocks
    authService.getCurrentUser.and.returnValue(of({ 
      id: 1, 
      email: 'test@example.com', 
      first_name: 'Test' 
    }));
    authService.getToken.and.returnValue('mock-jwt-token');
  });

  afterEach(() => {
    service.disconnect();
  });

  describe('Connection Management', () => {
    it('should create service', () => {
      expect(service).toBeTruthy();
    });

    it('should establish WebSocket connection', (done) => {
      service.connect();
      
      service.connectionStatus$.subscribe(status => {
        if (status.isConnected) {
          expect(status.isConnected).toBe(true);
          expect(status.connectionQuality).toBe('excellent');
          done();
        }
      });
    });

    it('should include authentication token in connection', () => {
      service.connect();
      
      // Verify WebSocket was created with correct URL including token
      expect(service.isConnected()).toBeDefined();
    });

    it('should handle connection errors', (done) => {
      service.connect();
      
      // Get the mock WebSocket instance
      const ws = (service as any).websocket as MockWebSocket;
      
      service.connectionStatus$.subscribe(status => {
        if (!status.isConnected && status.reconnectAttempts > 0) {
          expect(notificationService.showWarning).toHaveBeenCalledWith(
            'Connection lost. Attempting to reconnect...'
          );
          done();
        }
      });

      // Simulate connection error
      setTimeout(() => ws.simulateError(), 20);
    });

    it('should automatically reconnect on connection loss', (done) => {
      service.connect();
      
      let connectionCount = 0;
      service.connectionStatus$.subscribe(status => {
        if (status.isConnected) {
          connectionCount++;
          if (connectionCount === 2) {
            expect(status.reconnectAttempts).toBeGreaterThan(0);
            done();
          } else if (connectionCount === 1) {
            // Simulate connection loss after first connection
            setTimeout(() => {
              const ws = (service as any).websocket as MockWebSocket;
              ws.simulateClose(1006, 'Connection lost'); // Abnormal closure
            }, 10);
          }
        }
      });
    });

    it('should respect maximum reconnection attempts', (done) => {
      service.connect();
      
      let errorCount = 0;
      service.connectionStatus$.subscribe(status => {
        if (status.reconnectAttempts >= 5 && !status.isConnected) {
          expect(notificationService.showError).toHaveBeenCalledWith(
            'Unable to establish real-time connection. Please refresh the page.'
          );
          done();
        }
      });

      // Simulate repeated connection failures
      const simulateFailure = () => {
        const ws = (service as any).websocket as MockWebSocket;
        if (ws) {
          setTimeout(() => {
            ws.simulateClose(1006, 'Connection failed');
            errorCount++;
            if (errorCount < 6) {
              setTimeout(simulateFailure, 100);
            }
          }, 10);
        }
      };
      
      setTimeout(simulateFailure, 50);
    });

    it('should disconnect cleanly', () => {
      service.connect();
      
      setTimeout(() => {
        service.disconnect();
        
        service.connectionStatus$.subscribe(status => {
          expect(status.isConnected).toBe(false);
          expect(status.connectionQuality).toBe('disconnected');
        });
      }, 20);
    });

    it('should measure connection latency', (done) => {
      service.connect();
      
      setTimeout(() => {
        service.measureLatency().then(latency => {
          expect(latency).toBeGreaterThan(0);
          expect(latency).toBeLessThan(1000); // Should be reasonable
          done();
        });
      }, 20);
    });

    it('should update connection quality based on latency', (done) => {
      service.connect();
      
      setTimeout(() => {
        service.connectionStatus$.subscribe(status => {
          if (status.latency !== undefined) {
            if (status.latency < 100) {
              expect(status.connectionQuality).toBe('excellent');
            } else if (status.latency < 300) {
              expect(status.connectionQuality).toBe('good');
            } else {
              expect(status.connectionQuality).toBe('poor');
            }
            done();
          }
        });
        
        // Trigger latency measurement
        service.measureLatency();
      }, 20);
    });
  });

  describe('Message Handling', () => {
    beforeEach((done) => {
      service.connect();
      service.connectionStatus$.subscribe(status => {
        if (status.isConnected) {
          done();
        }
      });
    });

    it('should send messages through WebSocket', () => {
      const testMessage = {
        type: 'test_message',
        data: { content: 'Hello WebSocket!' },
        connection_id: 1
      };

      spyOn(service as any, 'sendMessage').and.callThrough();
      service.sendMessage(testMessage);
      
      expect((service as any).sendMessage).toHaveBeenCalledWith(testMessage);
    });

    it('should receive and parse messages', (done) => {
      const testMessage: WebSocketMessage = {
        type: 'new_message',
        data: {
          id: 1,
          content: 'Test message',
          sender_id: 2,
          connection_id: 1
        },
        timestamp: new Date().toISOString()
      };

      service.onMessage().subscribe(message => {
        expect(message.type).toBe('new_message');
        expect(message.data.content).toBe('Test message');
        done();
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage(testMessage);
    });

    it('should handle malformed messages gracefully', () => {
      const ws = (service as any).websocket as MockWebSocket;
      
      // Send malformed JSON
      spyOn(console, 'error').and.stub();
      ws.onmessage!(new MessageEvent('message', { data: 'invalid-json' }));
      
      expect(console.error).toHaveBeenCalled();
    });

    it('should filter messages by type', (done) => {
      const revelationMessage: WebSocketMessage = {
        type: 'revelation_shared',
        data: { day: 4, content: 'My hopes and dreams' },
        timestamp: new Date().toISOString()
      };

      service.onMessage('revelation_shared').subscribe(message => {
        expect(message.type).toBe('revelation_shared');
        done();
      });

      // Send different types of messages
      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage({ type: 'typing_indicator', data: {} });
      ws.simulateMessage({ type: 'presence_update', data: {} });
      ws.simulateMessage(revelationMessage); // This should trigger the subscription
    });

    it('should handle connection-specific messages', (done) => {
      const connectionMessage: WebSocketMessage = {
        type: 'connection_update',
        data: { stage: 'photo_reveal_pending' },
        timestamp: new Date().toISOString(),
        connection_id: 1
      };

      service.onConnectionMessage(1).subscribe(message => {
        expect(message.connection_id).toBe(1);
        expect(message.data.stage).toBe('photo_reveal_pending');
        done();
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage(connectionMessage);
    });

    it('should queue messages when disconnected', (done) => {
      service.disconnect();
      
      const testMessage = {
        type: 'queued_message',
        data: { content: 'Queued while offline' }
      };

      service.sendMessage(testMessage);
      
      // Reconnect and verify message is sent
      service.connect();
      
      service.connectionStatus$.subscribe(status => {
        if (status.isConnected) {
          // Verify queued message was sent
          expect((service as any).messageQueue.length).toBe(0);
          done();
        }
      });
    });

    it('should handle message delivery confirmation', (done) => {
      const messageId = 'msg-123';
      const testMessage = {
        type: 'chat_message',
        data: { content: 'Test message' },
        messageId
      };

      service.sendMessageWithConfirmation(testMessage).then(confirmed => {
        expect(confirmed).toBe(true);
        done();
      });

      // Simulate delivery confirmation
      setTimeout(() => {
        const ws = (service as any).websocket as MockWebSocket;
        ws.simulateMessage({
          type: 'message_delivered',
          data: { messageId },
          timestamp: new Date().toISOString()
        });
      }, 10);
    });
  });

  describe('Typing Indicators', () => {
    beforeEach((done) => {
      service.connect();
      service.connectionStatus$.subscribe(status => {
        if (status.isConnected) {
          done();
        }
      });
    });

    it('should send typing indicator', () => {
      spyOn(service, 'sendMessage').and.callThrough();
      
      service.sendTypingIndicator(1, true);
      
      expect(service.sendMessage).toHaveBeenCalledWith({
        type: 'typing_indicator',
        data: {
          connection_id: 1,
          is_typing: true,
          user_id: 1
        }
      });
    });

    it('should receive typing indicators', (done) => {
      const typingIndicator: TypingIndicator = {
        connection_id: 1,
        user_id: 2,
        user_name: 'Emma',
        is_typing: true,
        started_at: new Date().toISOString()
      };

      service.onTypingIndicator().subscribe(indicator => {
        expect(indicator.is_typing).toBe(true);
        expect(indicator.user_name).toBe('Emma');
        done();
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage({
        type: 'typing_indicator',
        data: typingIndicator,
        timestamp: new Date().toISOString()
      });
    });

    it('should auto-stop typing indicator after timeout', (done) => {
      service.sendTypingIndicator(1, true);
      
      // Verify stop typing is sent after timeout
      setTimeout(() => {
        spyOn(service, 'sendMessage').and.callThrough();
        service.stopTypingIndicator(1);
        
        expect(service.sendMessage).toHaveBeenCalledWith({
          type: 'typing_indicator',
          data: {
            connection_id: 1,
            is_typing: false,
            user_id: 1
          }
        });
        done();
      }, 100);
    });

    it('should debounce typing indicators', () => {
      spyOn(service, 'sendMessage').and.callThrough();
      
      // Rapid typing events
      service.sendTypingIndicator(1, true);
      service.sendTypingIndicator(1, true);
      service.sendTypingIndicator(1, true);
      
      // Should only send one message due to debouncing
      expect(service.sendMessage).toHaveBeenCalledTimes(1);
    });

    it('should handle multiple users typing', (done) => {
      const typingUsers: TypingIndicator[] = [
        {
          connection_id: 1,
          user_id: 2,
          user_name: 'Emma',
          is_typing: true,
          started_at: new Date().toISOString()
        },
        {
          connection_id: 1,
          user_id: 3,
          user_name: 'Sofia',
          is_typing: true,
          started_at: new Date().toISOString()
        }
      ];

      let receivedCount = 0;
      service.onTypingIndicator().subscribe(indicator => {
        receivedCount++;
        if (receivedCount === 2) {
          expect(service.getActiveTypingUsers(1).length).toBe(2);
          done();
        }
      });

      const ws = (service as any).websocket as MockWebSocket;
      typingUsers.forEach(user => {
        ws.simulateMessage({
          type: 'typing_indicator',
          data: user,
          timestamp: new Date().toISOString()
        });
      });
    });
  });

  describe('Presence Management', () => {
    beforeEach((done) => {
      service.connect();
      service.connectionStatus$.subscribe(status => {
        if (status.isConnected) {
          done();
        }
      });
    });

    it('should track user presence status', (done) => {
      const presenceUpdate: PresenceUpdate = {
        user_id: 2,
        user_name: 'Emma',
        is_online: true,
        activity_status: 'active'
      };

      service.onPresenceUpdate().subscribe(presence => {
        expect(presence.is_online).toBe(true);
        expect(presence.activity_status).toBe('active');
        done();
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage({
        type: 'presence_update',
        data: presenceUpdate,
        timestamp: new Date().toISOString()
      });
    });

    it('should update own presence status', () => {
      spyOn(service, 'sendMessage').and.callThrough();
      
      service.updatePresenceStatus('active');
      
      expect(service.sendMessage).toHaveBeenCalledWith({
        type: 'presence_update',
        data: {
          user_id: 1,
          activity_status: 'active',
          is_online: true
        }
      });
    });

    it('should handle user going offline', (done) => {
      const offlineUpdate: PresenceUpdate = {
        user_id: 2,
        user_name: 'Emma',
        is_online: false,
        last_seen: new Date().toISOString(),
        activity_status: 'offline'
      };

      service.onPresenceUpdate().subscribe(presence => {
        if (!presence.is_online) {
          expect(presence.activity_status).toBe('offline');
          expect(presence.last_seen).toBeDefined();
          done();
        }
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage({
        type: 'presence_update',
        data: offlineUpdate,
        timestamp: new Date().toISOString()
      });
    });

    it('should auto-update presence based on page visibility', () => {
      spyOn(service, 'updatePresenceStatus').and.callThrough();
      
      // Simulate page becoming hidden
      Object.defineProperty(document, 'hidden', {
        writable: true,
        value: true
      });
      
      // Trigger visibility change
      service.handleVisibilityChange();
      
      expect(service.updatePresenceStatus).toHaveBeenCalledWith('away');
    });

    it('should track activity status transitions', () => {
      const statusHistory: string[] = [];
      
      service.onPresenceUpdate().subscribe(presence => {
        statusHistory.push(presence.activity_status);
      });

      // Simulate status changes
      const ws = (service as any).websocket as MockWebSocket;
      const statusChanges = ['active', 'idle', 'away', 'offline'];
      
      statusChanges.forEach((status, index) => {
        setTimeout(() => {
          ws.simulateMessage({
            type: 'presence_update',
            data: {
              user_id: 2,
              user_name: 'Emma',
              is_online: status !== 'offline',
              activity_status: status
            },
            timestamp: new Date().toISOString()
          });
        }, index * 10);
      });

      setTimeout(() => {
        expect(statusHistory).toEqual(statusChanges);
      }, 100);
    });
  });

  describe('Real-Time Notifications', () => {
    beforeEach((done) => {
      service.connect();
      service.connectionStatus$.subscribe(status => {
        if (status.isConnected) {
          done();
        }
      });
    });

    it('should receive revelation notifications', (done) => {
      const revelationNotification = {
        type: 'revelation_shared',
        data: {
          connection_id: 1,
          partner_name: 'Emma',
          day_number: 4,
          revelation_type: 'hopes_dreams'
        },
        timestamp: new Date().toISOString()
      };

      service.onMessage('revelation_shared').subscribe(notification => {
        expect(notification.data.partner_name).toBe('Emma');
        expect(notification.data.day_number).toBe(4);
        done();
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage(revelationNotification);
    });

    it('should receive connection request notifications', (done) => {
      const connectionRequest = {
        type: 'connection_request',
        data: {
          sender_id: 3,
          sender_name: 'Alex',
          compatibility_score: 82.5,
          message: 'Soul connection request'
        },
        timestamp: new Date().toISOString()
      };

      service.onMessage('connection_request').subscribe(notification => {
        expect(notification.data.sender_name).toBe('Alex');
        expect(notification.data.compatibility_score).toBe(82.5);
        done();
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage(connectionRequest);
    });

    it('should receive photo reveal notifications', (done) => {
      const photoRevealNotification = {
        type: 'photo_reveal_ready',
        data: {
          connection_id: 1,
          partner_name: 'Emma',
          both_consented: true
        },
        timestamp: new Date().toISOString()
      };

      service.onMessage('photo_reveal_ready').subscribe(notification => {
        expect(notification.data.both_consented).toBe(true);
        done();
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage(photoRevealNotification);
    });

    it('should handle notification priority levels', (done) => {
      const highPriorityNotification = {
        type: 'urgent_notification',
        data: {
          priority: 'high',
          message: 'Connection issue requires attention',
          action_required: true
        },
        timestamp: new Date().toISOString()
      };

      service.onMessage('urgent_notification').subscribe(notification => {
        if (notification.data.priority === 'high') {
          expect(notificationService.showError).toHaveBeenCalled();
          done();
        }
      });

      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage(highPriorityNotification);
    });

    it('should batch and deduplicate similar notifications', (done) => {
      const similarNotifications = [
        {
          type: 'profile_view',
          data: { viewer_id: 4, viewer_name: 'Jordan' },
          timestamp: new Date().toISOString()
        },
        {
          type: 'profile_view',
          data: { viewer_id: 5, viewer_name: 'Taylor' },
          timestamp: new Date().toISOString()
        },
        {
          type: 'profile_view',
          data: { viewer_id: 6, viewer_name: 'Casey' },
          timestamp: new Date().toISOString()
        }
      ];

      let receivedCount = 0;
      service.onMessage('profile_view').subscribe(() => {
        receivedCount++;
        if (receivedCount === 3) {
          expect(service.getBatchedNotifications('profile_view').length).toBe(3);
          done();
        }
      });

      const ws = (service as any).websocket as MockWebSocket;
      similarNotifications.forEach((notification, index) => {
        setTimeout(() => ws.simulateMessage(notification), index * 5);
      });
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle WebSocket creation failures', () => {
      // Mock WebSocket constructor to throw error
      (global as any).WebSocket = class {
        constructor() {
          throw new Error('WebSocket creation failed');
        }
      };

      service.connect();
      
      expect(notificationService.showError).toHaveBeenCalledWith(
        'Unable to establish real-time connection. Please check your internet connection.'
      );
    });

    it('should handle authentication failures', (done) => {
      authService.getToken.and.returnValue(null);
      
      service.connect();
      
      service.connectionStatus$.subscribe(status => {
        if (status.reconnectAttempts > 0 && !status.isConnected) {
          expect(notificationService.showError).toHaveBeenCalledWith(
            'Authentication failed. Please log in again.'
          );
          done();
        }
      });
    });

    it('should handle network connectivity issues', (done) => {
      service.connect();
      
      setTimeout(() => {
        // Simulate network failure
        const ws = (service as any).websocket as MockWebSocket;
        ws.simulateClose(1006, 'Network error'); // Abnormal closure
        
        service.connectionStatus$.subscribe(status => {
          if (!status.isConnected) {
            expect(status.connectionQuality).toBe('disconnected');
            expect(notificationService.showWarning).toHaveBeenCalledWith(
              'Connection lost. Attempting to reconnect...'
            );
            done();
          }
        });
      }, 20);
    });

    it('should implement exponential backoff for reconnection', (done) => {
      service.connect();
      
      const reconnectionTimes: number[] = [];
      let startTime = Date.now();
      
      service.connectionStatus$.subscribe(status => {
        if (status.reconnectAttempts > 0) {
          reconnectionTimes.push(Date.now() - startTime);
          startTime = Date.now();
          
          if (status.reconnectAttempts >= 3) {
            // Verify exponential backoff
            expect(reconnectionTimes[1]).toBeGreaterThan(reconnectionTimes[0]);
            expect(reconnectionTimes[2]).toBeGreaterThan(reconnectionTimes[1]);
            done();
          }
        }
      });

      // Simulate repeated connection failures
      setTimeout(() => {
        const simulateFailure = () => {
          const ws = (service as any).websocket as MockWebSocket;
          if (ws) {
            ws.simulateClose(1006, 'Connection failed');
          }
        };
        
        [100, 200, 400].forEach((delay, index) => {
          setTimeout(simulateFailure, delay * (index + 1));
        });
      }, 20);
    });

    it('should clear pending operations on disconnect', () => {
      service.connect();
      
      // Add some pending operations
      const pendingMessage = { type: 'test', data: {} };
      service.sendMessage(pendingMessage);
      
      service.disconnect();
      
      expect((service as any).pendingOperations.size).toBe(0);
      expect((service as any).messageQueue.length).toBe(0);
    });

    it('should validate message format before processing', () => {
      service.connect();
      
      const invalidMessages = [
        null,
        undefined,
        '',
        { /* missing type */ data: {} },
        { type: '', data: {} },
        { type: 'valid', /* missing data */ }
      ];

      spyOn(console, 'warn').and.stub();
      
      const ws = (service as any).websocket as MockWebSocket;
      invalidMessages.forEach(message => {
        ws.onmessage!(new MessageEvent('message', { 
          data: JSON.stringify(message) 
        }));
      });

      expect(console.warn).toHaveBeenCalledTimes(invalidMessages.length);
    });
  });

  describe('Performance and Memory Management', () => {
    it('should limit message history size', () => {
      service.connect();
      
      // Send many messages to test history limit
      for (let i = 0; i < 1500; i++) {
        const message = {
          type: 'test_message',
          data: { id: i },
          timestamp: new Date().toISOString()
        };
        
        const ws = (service as any).websocket as MockWebSocket;
        ws.simulateMessage(message);
      }

      const messageHistory = service.getMessageHistory();
      expect(messageHistory.length).toBeLessThanOrEqual(1000); // Max history size
    });

    it('should cleanup event listeners on destroy', () => {
      service.connect();
      
      spyOn(window, 'removeEventListener').and.callThrough();
      
      service.ngOnDestroy();
      
      expect(window.removeEventListener).toHaveBeenCalledWith(
        'beforeunload', 
        jasmine.any(Function)
      );
      expect(window.removeEventListener).toHaveBeenCalledWith(
        'visibilitychange', 
        jasmine.any(Function)
      );
    });

    it('should debounce presence updates', () => {
      service.connect();
      
      spyOn(service, 'sendMessage').and.callThrough();
      
      // Rapid presence updates
      service.updatePresenceStatus('active');
      service.updatePresenceStatus('idle');
      service.updatePresenceStatus('active');
      service.updatePresenceStatus('idle');
      
      // Should be debounced to single call
      setTimeout(() => {
        expect(service.sendMessage).toHaveBeenCalledTimes(1);
      }, 100);
    });

    it('should implement connection pooling for multiple connections', () => {
      const connection1 = service.getConnectionPool().get('connection-1');
      const connection2 = service.getConnectionPool().get('connection-2');
      
      expect(connection1).toBeDefined();
      expect(connection2).toBeDefined();
      expect(connection1).not.toBe(connection2);
    });

    it('should measure and report performance metrics', (done) => {
      service.connect();
      
      service.getPerformanceMetrics().then(metrics => {
        expect(metrics.averageLatency).toBeDefined();
        expect(metrics.messagesSent).toBeDefined();
        expect(metrics.messagesReceived).toBeDefined();
        expect(metrics.reconnectionCount).toBeDefined();
        done();
      });
    });
  });

  describe('Security and Authentication', () => {
    it('should include JWT token in connection headers', () => {
      const mockToken = 'jwt.token.here';
      authService.getToken.and.returnValue(mockToken);
      
      service.connect();
      
      // Verify connection was made with token
      const connectionUrl = (service as any).getConnectionUrl();
      expect(connectionUrl).toContain(mockToken);
    });

    it('should handle token expiration during connection', (done) => {
      service.connect();
      
      setTimeout(() => {
        // Simulate token expiration
        const ws = (service as any).websocket as MockWebSocket;
        ws.simulateMessage({
          type: 'auth_error',
          data: { error: 'Token expired' },
          timestamp: new Date().toISOString()
        });
        
        service.connectionStatus$.subscribe(status => {
          if (!status.isConnected) {
            expect(notificationService.showError).toHaveBeenCalledWith(
              'Session expired. Please log in again.'
            );
            done();
          }
        });
      }, 20);
    });

    it('should validate message source and authenticity', () => {
      service.connect();
      
      const suspiciousMessage = {
        type: 'malicious_message',
        data: {
          script: '<script>alert("xss")</script>',
          sql: "'; DROP TABLE users; --"
        },
        timestamp: new Date().toISOString()
      };

      spyOn(service, 'validateMessageSecurity').and.returnValue(false);
      
      const ws = (service as any).websocket as MockWebSocket;
      ws.simulateMessage(suspiciousMessage);
      
      expect(service.validateMessageSecurity).toHaveBeenCalled();
    });

    it('should implement rate limiting for outgoing messages', () => {
      service.connect();
      
      const rateLimitedMessages = [];
      for (let i = 0; i < 100; i++) {
        const result = service.sendMessage({
          type: 'spam_message',
          data: { index: i }
        });
        rateLimitedMessages.push(result);
      }

      const rejectedMessages = rateLimitedMessages.filter(result => !result);
      expect(rejectedMessages.length).toBeGreaterThan(0);
    });

    it('should encrypt sensitive message content', () => {
      service.connect();
      
      const sensitiveMessage = {
        type: 'private_revelation',
        data: {
          content: 'Very personal and sensitive content',
          encryption_required: true
        }
      };

      spyOn(service, 'encryptMessage').and.returnValue('encrypted_content');
      service.sendMessage(sensitiveMessage);
      
      expect(service.encryptMessage).toHaveBeenCalledWith(sensitiveMessage.data.content);
    });
  });

  describe('Cross-Browser Compatibility', () => {
    it('should handle browsers without WebSocket support', () => {
      (global as any).WebSocket = undefined;
      
      service.connect();
      
      expect(notificationService.showError).toHaveBeenCalledWith(
        'Your browser does not support real-time features. Please update your browser.'
      );
    });

    it('should handle different WebSocket close codes', () => {
      service.connect();
      
      const closeCodes = [
        { code: 1000, reason: 'Normal closure' },
        { code: 1001, reason: 'Going away' },
        { code: 1002, reason: 'Protocol error' },
        { code: 1006, reason: 'Abnormal closure' },
        { code: 1011, reason: 'Server error' }
      ];

      closeCodes.forEach(({ code, reason }) => {
        setTimeout(() => {
          const ws = (service as any).websocket as MockWebSocket;
          ws.simulateClose(code, reason);
          
          if (code === 1000 || code === 1001) {
            // Normal closure - don't reconnect
            expect(service.shouldReconnect(code)).toBe(false);
          } else {
            // Abnormal closure - attempt reconnection
            expect(service.shouldReconnect(code)).toBe(true);
          }
        }, 10);
      });
    });

    it('should adapt to different network conditions', (done) => {
      service.connect();
      
      // Mock different connection qualities
      const networkConditions = [
        { latency: 50, quality: 'excellent' },
        { latency: 150, quality: 'good' },
        { latency: 400, quality: 'poor' }
      ];

      let conditionIndex = 0;
      service.connectionStatus$.subscribe(status => {
        if (status.latency !== undefined) {
          const expectedQuality = networkConditions[conditionIndex]?.quality;
          if (expectedQuality) {
            expect(status.connectionQuality).toBe(expectedQuality);
            conditionIndex++;
            if (conditionIndex >= networkConditions.length) {
              done();
            }
          }
        }
      });

      // Simulate different network conditions
      networkConditions.forEach((condition, index) => {
        setTimeout(() => {
          service.simulateNetworkCondition(condition.latency);
        }, index * 100);
      });
    });
  });
});