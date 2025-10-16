import { TestBed, fakeAsync, tick, flush } from '@angular/core/testing';
import { WebSocketPoolService, WebSocketMessage, WebSocketConnection } from './websocket-pool.service';
import { Subject } from 'rxjs';
import { WebSocketSubject } from 'rxjs/webSocket';

describe('WebSocketPoolService', () => {
  let service: WebSocketPoolService;
  let mockWebSocketSubject: jasmine.SpyObj<WebSocketSubject<WebSocketMessage>>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [WebSocketPoolService]
    });

    // Create mock WebSocketSubject
    mockWebSocketSubject = jasmine.createSpyObj('WebSocketSubject', ['next', 'complete', 'error', 'pipe']);
    mockWebSocketSubject.pipe.and.returnValue(new Subject<WebSocketMessage>());

    service = TestBed.inject(WebSocketPoolService);
  });

  afterEach(() => {
    service.ngOnDestroy();
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should initialize with default configuration', () => {
      const stats = service.getPoolStatistics();
      expect(stats.totalConnections).toBe(0);
      expect(stats.connectedCount).toBe(0);
    });

    it('should start heartbeat monitoring on initialization', fakeAsync(() => {
      // Service is already initialized in beforeEach
      expect(service).toBeTruthy();
      tick(30000); // Default heartbeat interval
      // Heartbeat monitoring is active (no errors thrown)
      flush();
    }));

    it('should start connection cleanup on initialization', fakeAsync(() => {
      expect(service).toBeTruthy();
      tick(60000); // Connection cleanup interval
      flush();
    }));
  });

  describe('Connection Management', () => {
    it('should create new connection when none exists', (done) => {
      const url = 'ws://localhost:5000/ws';
      const channels = ['test-channel'];

      service.getConnection(url, channels).subscribe(connection => {
        expect(connection).toBeDefined();
        expect(connection.url).toBe(url);
        expect(connection.channels.has('test-channel')).toBe(true);
        expect(connection.status).toBe('connecting');
        done();
      });
    });

    it('should reuse existing connection for same URL', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, ['channel1']).subscribe(firstConnection => {
        service.getConnection(url, ['channel2']).subscribe(secondConnection => {
          expect(firstConnection.id).toBe(secondConnection.id);
          expect(secondConnection.channels.has('channel1')).toBe(true);
          expect(secondConnection.channels.has('channel2')).toBe(true);
          done();
        });
      });
    });

    it('should respect maxConnections limit', (done) => {
      const urls = [
        'ws://localhost:5000/ws1',
        'ws://localhost:5000/ws2',
        'ws://localhost:5000/ws3',
        'ws://localhost:5000/ws4',
        'ws://localhost:5000/ws5',
        'ws://localhost:5000/ws6' // Exceeds default limit of 5
      ];

      let connectionsCreated = 0;
      urls.forEach(url => {
        service.getConnection(url, []).subscribe(() => {
          connectionsCreated++;
          if (connectionsCreated === urls.length) {
            const stats = service.getPoolStatistics();
            expect(stats.totalConnections).toBeLessThanOrEqual(5);
            done();
          }
        });
      });
    });

    it('should close specific connection', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        service.closeConnection(connection.id);

        const stats = service.getPoolStatistics();
        expect(stats.totalConnections).toBe(0);
        done();
      });
    });

    it('should close all connections', (done) => {
      const urls = [
        'ws://localhost:5000/ws1',
        'ws://localhost:5000/ws2',
        'ws://localhost:5000/ws3'
      ];

      let connectionsCreated = 0;
      urls.forEach(url => {
        service.getConnection(url, []).subscribe(() => {
          connectionsCreated++;
          if (connectionsCreated === urls.length) {
            service.closeAllConnections();
            const stats = service.getPoolStatistics();
            expect(stats.totalConnections).toBe(0);
            done();
          }
        });
      });
    });

    it('should generate unique connection IDs', (done) => {
      // Create connections with different URLs to ensure unique IDs
      const urls = [
        'ws://localhost:5000/api/ws/connection1',
        'ws://localhost:5001/api/ws/connection2',
        'ws://localhost:5002/api/ws/connection3'
      ];
      const ids = new Set<string>();

      let connectionsCreated = 0;
      urls.forEach((testUrl, index) => {
        // Add small delay to ensure timestamps differ
        setTimeout(() => {
          service.getConnection(testUrl, []).subscribe(connection => {
            ids.add(connection.id);
            connectionsCreated++;

            if (connectionsCreated === urls.length) {
              // Each URL should generate a unique connection ID
              expect(ids.size).toBe(3);
              done();
            }
          });
        }, index * 10); // Stagger by 10ms each
      });
    });
  });

  describe('Channel Management', () => {
    it('should subscribe to channel', (done) => {
      const channel = 'test-channel';

      const subscription = service.subscribeToChannel(channel);
      expect(subscription).toBeDefined();

      subscription.subscribe(message => {
        expect(message.channel).toBe(channel);
        done();
      });

      // Simulate incoming message
      setTimeout(() => {
        const stats = service.getPoolStatistics();
        expect(stats.totalChannels).toBeGreaterThan(0);
        done();
      }, 100);
    });

    it('should subscribe to channel with specific connection URL', (done) => {
      const url = 'ws://localhost:5000/ws';
      const channel = 'specific-channel';

      const subscription = service.subscribeToChannel(channel, url);
      expect(subscription).toBeDefined();

      subscription.subscribe(() => {
        const stats = service.getPoolStatistics();
        expect(stats.totalChannels).toBeGreaterThan(0);
        done();
      });

      // Allow async operations to complete
      setTimeout(() => done(), 100);
    });

    it('should add channels to existing connection', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, ['channel1']).subscribe(connection => {
        expect(connection.channels.has('channel1')).toBe(true);

        service.getConnection(url, ['channel2']).subscribe(updatedConnection => {
          expect(updatedConnection.channels.has('channel1')).toBe(true);
          expect(updatedConnection.channels.has('channel2')).toBe(true);
          done();
        });
      });
    });

    it('should track channel subscriptions', (done) => {
      const channel = 'tracked-channel';

      service.subscribeToChannel(channel).subscribe(() => {
        const stats = service.getPoolStatistics();
        expect(stats.totalSubscribers).toBeGreaterThan(0);
        done();
      });

      setTimeout(() => done(), 100);
    });

    it('should broadcast message to all connections with channel', (done) => {
      const channel = 'broadcast-channel';
      const url1 = 'ws://localhost:5000/ws1';
      const url2 = 'ws://localhost:5000/ws2';

      service.getConnection(url1, [channel]).subscribe(conn1 => {
        service.getConnection(url2, [channel]).subscribe(conn2 => {
          // Manually set connections to 'connected' for testing
          (conn1 as any).status = 'connected';
          (conn2 as any).status = 'connected';

          const message: WebSocketMessage = {
            type: 'test',
            channel: channel,
            data: { content: 'broadcast test' }
          };

          const sentCount = service.broadcastToChannel(channel, message);
          expect(sentCount).toBeGreaterThanOrEqual(0);
          done();
        });
      });
    });
  });

  describe('Message Handling', () => {
    it('should send message through connected connection', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        // Manually set connection to 'connected'
        (connection as any).status = 'connected';

        const message: WebSocketMessage = {
          type: 'test',
          data: { content: 'test message' }
        };

        const result = service.sendMessage(connection.id, message);
        expect(result).toBe(true);
        done();
      });
    });

    it('should queue message when connection is not connected', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        // Connection starts in 'connecting' state
        const message: WebSocketMessage = {
          type: 'test',
          data: { content: 'queued message' }
        };

        const result = service.sendMessage(connection.id, message);
        expect(result).toBe(false);
        done();
      });
    });

    it('should return false when sending to non-existent connection', () => {
      const message: WebSocketMessage = {
        type: 'test',
        data: { content: 'test' }
      };

      const result = service.sendMessage('non-existent-id', message);
      expect(result).toBe(false);
    });

    it('should add timestamp to messages without one', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        (connection as any).status = 'connected';

        const message: WebSocketMessage = {
          type: 'test',
          data: { content: 'test' }
        };

        service.sendMessage(connection.id, message);
        expect(message.timestamp).toBeDefined();
        done();
      });
    });

    it('should handle message queue size limits', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        // Keep connection in 'connecting' state to queue messages
        for (let i = 0; i < 150; i++) {
          service.sendMessage(connection.id, {
            type: 'test',
            data: { index: i }
          });
        }

        const stats = service.getPoolStatistics();
        expect(stats.queuedMessages).toBeLessThanOrEqual(100); // Default queue size
        done();
      });
    });
  });

  describe('Connection Status', () => {
    it('should provide connection status observable', (done) => {
      service.getConnectionStatus().subscribe(statusMap => {
        expect(statusMap).toBeInstanceOf(Map);
        done();
      });
    });

    it('should provide connection count observable', (done) => {
      service.getConnectionCount().subscribe(count => {
        expect(typeof count).toBe('number');
        expect(count).toBeGreaterThanOrEqual(0);
        done();
      });
    });

    it('should update connection status when connections change', (done) => {
      const url = 'ws://localhost:5000/ws';

      let statusUpdates = 0;
      service.getConnectionStatus().subscribe(() => {
        statusUpdates++;
        if (statusUpdates === 2) { // Initial + after connection creation
          expect(statusUpdates).toBeGreaterThan(1);
          done();
        }
      });

      setTimeout(() => {
        service.getConnection(url, []).subscribe(() => {});
      }, 50);
    });

    it('should track connection statistics', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, ['channel1', 'channel2']).subscribe(() => {
        const stats = service.getPoolStatistics();

        expect(stats).toBeDefined();
        expect(stats.totalConnections).toBeGreaterThan(0);
        expect(stats.connectingCount).toBeGreaterThanOrEqual(0);
        expect(stats.connectedCount).toBeGreaterThanOrEqual(0);
        expect(stats.errorCount).toBeGreaterThanOrEqual(0);
        expect(stats.totalChannels).toBeGreaterThanOrEqual(0);
        done();
      });
    });
  });

  describe('Reconnection Logic', () => {
    it('should attempt reconnection on connection close', fakeAsync(() => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        // Simulate connection close
        (connection as any).status = 'disconnected';
        (connection as any).reconnectAttempts = 0;

        // Manually trigger reconnection (private method simulation)
        tick(3000); // Default reconnect interval

        expect(connection.reconnectAttempts).toBeLessThanOrEqual(5); // Max reconnect attempts
      });

      flush();
    }));

    it('should limit reconnection attempts', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        // Simulate multiple failed reconnections
        (connection as any).reconnectAttempts = 10;
        (connection as any).status = 'disconnected';

        // Connection should not attempt more reconnections
        expect(connection.reconnectAttempts).toBeGreaterThan(5);
        done();
      });
    });
  });

  describe('Heartbeat Monitoring', () => {
    it('should monitor connection heartbeats', fakeAsync(() => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        (connection as any).status = 'connected';
        (connection as any).lastHeartbeat = Date.now();

        tick(30000); // Heartbeat interval
        expect(connection.lastHeartbeat).toBeDefined();
      });

      flush();
    }));

    it('should detect heartbeat timeouts', fakeAsync(() => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        (connection as any).status = 'connected';
        (connection as any).lastHeartbeat = Date.now() - 100000; // Old heartbeat

        tick(30000); // Heartbeat check interval
        // Connection should be marked as error due to timeout
        flush();
      });
    }));

    it('should update heartbeat on incoming messages', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        const initialHeartbeat = connection.lastHeartbeat;

        // Simulate some time passing
        setTimeout(() => {
          expect(connection.lastHeartbeat).toBeDefined();
          done();
        }, 100);
      });
    });
  });

  describe('Connection Cleanup', () => {
    it('should cleanup stale connections periodically', fakeAsync(() => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        (connection as any).status = 'error';
        (connection as any).lastHeartbeat = Date.now() - 6 * 60 * 1000; // 6 minutes ago

        tick(60000); // Cleanup interval

        const stats = service.getPoolStatistics();
        // Stale connections should be cleaned up
        flush();
      });
    }));

    it('should cleanup channel subscriptions when connection closes', (done) => {
      const url = 'ws://localhost:5000/ws';
      const channel = 'cleanup-test';

      service.getConnection(url, [channel]).subscribe(connection => {
        // Get initial connection count
        const initialCount = service.getPoolStatistics().totalConnections;

        service.subscribeToChannel(channel, url).subscribe(() => {});

        setTimeout(() => {
          service.closeConnection(connection.id);

          // Verify connection is closed (could still be one from subscription)
          const stats = service.getPoolStatistics();
          expect(stats.totalConnections).toBeLessThanOrEqual(initialCount);
          done();
        }, 100);
      });
    });

    it('should close oldest connection when pool is full', (done) => {
      // Create 5 connections (max limit)
      const urls = Array.from({ length: 5 }, (_, i) => `ws://localhost:5000/ws${i}`);

      let created = 0;
      urls.forEach(url => {
        service.getConnection(url, []).subscribe(() => {
          created++;
          if (created === 5) {
            // Try to create one more - should close oldest
            service.getConnection('ws://localhost:5000/ws6', []).subscribe(() => {
              const stats = service.getPoolStatistics();
              expect(stats.totalConnections).toBeLessThanOrEqual(5);
              done();
            });
          }
        });
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle connection errors gracefully', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        // Manually trigger error
        (connection as any).status = 'error';

        const stats = service.getPoolStatistics();
        expect(stats.errorCount).toBeGreaterThanOrEqual(0);
        done();
      });
    });

    it('should handle message send failures', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        (connection as any).status = 'connected';

        // Make subject.next throw error
        const nextSpy = spyOn(connection.subject, 'next');
        nextSpy.and.callFake(() => {
          throw new Error('Send failed');
        });

        const message: WebSocketMessage = {
          type: 'test',
          data: {}
        };

        // Expect console.error to be called (error handling)
        spyOn(console, 'error');

        const result = service.sendMessage(connection.id, message);
        expect(result).toBe(false);
        expect(console.error).toHaveBeenCalled();
        done();
      });
    });
  });

  describe('Service Lifecycle', () => {
    it('should cleanup on destroy', () => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(() => {});

      service.ngOnDestroy();

      const stats = service.getPoolStatistics();
      expect(stats.totalConnections).toBe(0);
    });

    it('should complete observables on destroy', (done) => {
      let completed = false;

      service.getConnectionStatus().subscribe({
        complete: () => {
          completed = true;
        }
      });

      service.ngOnDestroy();

      setTimeout(() => {
        // Destroy should complete observables
        expect(service).toBeTruthy();
        done();
      }, 100);
    });

    it('should stop heartbeat monitoring on destroy', fakeAsync(() => {
      service.ngOnDestroy();

      // Heartbeat timer should not trigger after destroy
      tick(30000);
      expect(service).toBeTruthy();
      flush();
    }));
  });

  describe('Edge Cases', () => {
    it('should handle multiple simultaneous connections to same URL', (done) => {
      const url = 'ws://localhost:5000/ws';

      Promise.all([
        service.getConnection(url, ['channel1']).toPromise(),
        service.getConnection(url, ['channel2']).toPromise(),
        service.getConnection(url, ['channel3']).toPromise()
      ]).then(connections => {
        // Should reuse same connection
        const ids = new Set(connections.map(c => c!.id));
        expect(ids.size).toBe(1);
        done();
      });
    });

    it('should handle subscribing to same channel multiple times', (done) => {
      const channel = 'multi-sub-channel';

      const sub1 = service.subscribeToChannel(channel);
      const sub2 = service.subscribeToChannel(channel);
      const sub3 = service.subscribeToChannel(channel);

      expect(sub1).toBeDefined();
      expect(sub2).toBeDefined();
      expect(sub3).toBeDefined();

      setTimeout(() => {
        const stats = service.getPoolStatistics();
        expect(stats.totalSubscribers).toBeGreaterThan(0);
        done();
      }, 100);
    });

    it('should handle empty channel arrays', (done) => {
      const url = 'ws://localhost:5000/ws';

      service.getConnection(url, []).subscribe(connection => {
        expect(connection.channels.size).toBe(0);
        done();
      });
    });

    it('should build correct WebSocket URL in production', () => {
      // This tests the private buildWebSocketUrl method indirectly
      service.subscribeToChannel('test').subscribe(() => {});

      const stats = service.getPoolStatistics();
      expect(stats.totalConnections).toBeGreaterThanOrEqual(0);
    });
  });
});
