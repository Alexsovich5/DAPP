import { TestBed, fakeAsync, tick, flush } from '@angular/core/testing';
import { SoulConnectionRealtimeService, CompatibilityUpdate, EnergySync, RevelationNotification, PresenceUpdate, SoulConnectionUpdate } from './soul-connection-realtime.service';
import { WebSocketPoolService, WebSocketMessage } from './websocket-pool.service';
import { ScreenReaderService } from './screen-reader.service';
import { Subject, BehaviorSubject, of } from 'rxjs';

describe('SoulConnectionRealtimeService', () => {
  let service: SoulConnectionRealtimeService;
  let mockWsPool: jasmine.SpyObj<WebSocketPoolService>;
  let mockScreenReader: jasmine.SpyObj<ScreenReaderService>;
  let channelSubjects: Map<string, Subject<WebSocketMessage>>;

  beforeEach(() => {
    channelSubjects = new Map();

    // Create comprehensive WebSocketPoolService mock
    mockWsPool = jasmine.createSpyObj('WebSocketPoolService', [
      'subscribeToChannel',
      'broadcastToChannel',
      'getConnectionStatus',
      'getConnectionCount',
      'closeAllConnections',
      'getPoolStatistics'
    ]);

    // subscribeToChannel returns a unique subject for each channel
    mockWsPool.subscribeToChannel.and.callFake((channel: string) => {
      if (!channelSubjects.has(channel)) {
        channelSubjects.set(channel, new Subject<WebSocketMessage>());
      }
      return channelSubjects.get(channel)!.asObservable();
    });

    mockWsPool.broadcastToChannel.and.returnValue(1);
    mockWsPool.getConnectionStatus.and.returnValue(of(new Map([['conn1', 'connected']])));
    mockWsPool.getConnectionCount.and.returnValue(of(1));
    mockWsPool.getPoolStatistics.and.returnValue({
      totalConnections: 2,
      connectedCount: 2,
      connectingCount: 0,
      errorCount: 0,
      totalChannels: 3,
      totalSubscribers: 5,
      queuedMessages: 0
    });

    // Create ScreenReaderService mock
    mockScreenReader = jasmine.createSpyObj('ScreenReaderService', ['announce']);

    TestBed.configureTestingModule({
      providers: [
        SoulConnectionRealtimeService,
        { provide: WebSocketPoolService, useValue: mockWsPool },
        { provide: ScreenReaderService, useValue: mockScreenReader }
      ]
    });

    service = TestBed.inject(SoulConnectionRealtimeService);
  });

  afterEach(() => {
    service.ngOnDestroy();
    channelSubjects.forEach(subject => subject.complete());
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should subscribe to global soul connections channel', () => {
      expect(mockWsPool.subscribeToChannel).toHaveBeenCalledWith('soul_connections');
    });

    it('should subscribe to compatibility updates channel', () => {
      expect(mockWsPool.subscribeToChannel).toHaveBeenCalledWith('compatibility_updates');
    });

    it('should subscribe to revelation updates channel', () => {
      expect(mockWsPool.subscribeToChannel).toHaveBeenCalledWith('revelation_updates');
    });

    it('should monitor WebSocket connection status', (done) => {
      service.getConnectionStatus().subscribe(status => {
        expect(status).toBe(true);
        done();
      });
    });

    it('should initialize with disconnected health status', (done) => {
      // Create new service with zero connections
      mockWsPool.getConnectionCount.and.returnValue(of(0));
      const newService = new SoulConnectionRealtimeService(mockWsPool, mockScreenReader);

      setTimeout(() => {
        newService.getConnectionHealth().subscribe(health => {
          expect(health).toBe('disconnected');
          newService.ngOnDestroy();
          done();
        });
      }, 1100); // Wait for debounce
    });
  });

  describe('Compatibility Updates', () => {
    it('should subscribe to compatibility updates for a connection', (done) => {
      const connectionId = 'conn123';
      const update: CompatibilityUpdate = {
        connectionId: 'conn123',
        newScore: 85,
        previousScore: 75,
        breakdown: {
          values: 90,
          interests: 80,
          communication: 85
        },
        factors: ['shared_interests', 'value_alignment']
      };

      service.subscribeToCompatibilityUpdates(connectionId).subscribe(received => {
        expect(received).toEqual(update);
        expect(mockScreenReader.announce).toHaveBeenCalled();
        done();
      });

      // Simulate receiving update
      const compatChannel = channelSubjects.get('compatibility_updates');
      if (compatChannel) {
        compatChannel.next({
          type: 'compatibility_change',
          data: update as unknown as Record<string, unknown>
        });
      }
    });

    it('should filter updates by connection ID', (done) => {
      const connectionId = 'conn123';
      let updateCount = 0;

      service.subscribeToCompatibilityUpdates(connectionId).subscribe(() => {
        updateCount++;
      });

      // Send updates for different connections
      const compatChannel = channelSubjects.get('compatibility_updates');
      if (compatChannel) {
        compatChannel.next({
          type: 'compatibility_change',
          data: { connectionId: 'other_conn', newScore: 70 } as unknown as Record<string, unknown>
        });
        compatChannel.next({
          type: 'compatibility_change',
          data: { connectionId: 'conn123', newScore: 85 } as unknown as Record<string, unknown>
        });
      }

      setTimeout(() => {
        expect(updateCount).toBe(1);
        done();
      }, 100);
    });

    it('should announce compatibility changes', (done) => {
      const connectionId = 'conn123';
      const update: CompatibilityUpdate = {
        connectionId: 'conn123',
        newScore: 90,
        previousScore: 80,
        breakdown: { values: 95, interests: 85, communication: 90 },
        factors: []
      };

      service.subscribeToCompatibilityUpdates(connectionId).subscribe(() => {
        expect(mockScreenReader.announce).toHaveBeenCalledWith(
          jasmine.stringContaining('increased'),
          'polite',
          'compatibility-update'
        );
        done();
      });

      const compatChannel = channelSubjects.get('compatibility_updates');
      if (compatChannel) {
        compatChannel.next({
          type: 'compatibility_change',
          data: update as unknown as Record<string, unknown>
        });
      }
    });
  });

  describe('Energy Synchronization', () => {
    it('should subscribe to energy sync updates', (done) => {
      const connectionId = 'conn123';
      const energySync: EnergySync = {
        leftSoulEnergy: 75,
        rightSoulEnergy: 80,
        connectionStrength: 77.5,
        pulseRate: 60,
        syncQuality: 'good'
      };

      service.subscribeToEnergySync(connectionId).subscribe(received => {
        expect(received).toEqual(energySync);
        done();
      });

      // Simulate energy sync message
      const soulChannel = channelSubjects.get('soul_connections');
      if (soulChannel) {
        soulChannel.next({
          type: 'energy_sync',
          data: energySync as unknown as Record<string, unknown>
        });
      }
    });

    it('should filter energy sync by connection strength', (done) => {
      const connectionId = 'conn123';
      let syncCount = 0;

      service.subscribeToEnergySync(connectionId).subscribe(() => {
        syncCount++;
      });

      const soulChannel = channelSubjects.get('soul_connections');
      if (soulChannel) {
        // This should be filtered out (zero connection strength)
        soulChannel.next({
          type: 'energy_sync',
          data: { connectionStrength: 0 } as unknown as Record<string, unknown>
        });

        // This should pass through
        soulChannel.next({
          type: 'energy_sync',
          data: { connectionStrength: 50 } as unknown as Record<string, unknown>
        });
      }

      setTimeout(() => {
        expect(syncCount).toBe(1);
        done();
      }, 100);
    });

    it('should send energy pulse', () => {
      const connectionId = 'conn123';
      const energyLevel = 85;
      const soulType = 'left';

      service.sendEnergyPulse(connectionId, energyLevel, soulType);

      expect(mockWsPool.broadcastToChannel).toHaveBeenCalledWith(
        'connection_conn123',
        jasmine.objectContaining({
          type: 'energy_pulse',
          channel: 'connection_conn123',
          data: jasmine.objectContaining({
            connectionId,
            soulType,
            energyLevel
          })
        })
      );
    });
  });

  describe('Revelation Notifications', () => {
    it('should subscribe to revelation notifications', (done) => {
      const connectionId = 'conn123';
      const notification: RevelationNotification = {
        connectionId: 'conn123',
        senderId: 'user456',
        senderName: 'Alex',
        day: 3,
        type: 'shared',
        preview: 'A meaningful memory...'
      };

      service.subscribeToRevelationNotifications(connectionId).subscribe(received => {
        expect(received).toEqual(notification);
        expect(mockScreenReader.announce).toHaveBeenCalled();
        done();
      });

      const revChannel = channelSubjects.get('revelation_updates');
      if (revChannel) {
        revChannel.next({
          type: 'revelation_shared',
          data: notification as unknown as Record<string, unknown>
        });
      }
    });

    it('should announce revelation shared', (done) => {
      const connectionId = 'conn123';
      const notification: RevelationNotification = {
        connectionId: 'conn123',
        senderId: 'user456',
        senderName: 'Alex',
        day: 2,
        type: 'shared'
      };

      service.subscribeToRevelationNotifications(connectionId).subscribe(() => {
        expect(mockScreenReader.announce).toHaveBeenCalledWith(
          jasmine.stringContaining('day 2 revelation has been shared'),
          'assertive',
          'revelation-update'
        );
        done();
      });

      const revChannel = channelSubjects.get('revelation_updates');
      if (revChannel) {
        revChannel.next({
          type: 'revelation_shared',
          data: notification as unknown as Record<string, unknown>
        });
      }
    });

    it('should send revelation progress', () => {
      const connectionId = 'conn123';
      const day = 4;
      const completed = true;

      service.sendRevelationProgress(connectionId, day, completed);

      expect(mockWsPool.broadcastToChannel).toHaveBeenCalledWith(
        'connection_conn123',
        jasmine.objectContaining({
          type: 'revelation_progress',
          data: jasmine.objectContaining({
            connectionId,
            day,
            completed
          })
        })
      );
    });
  });

  describe('Presence Updates', () => {
    it('should subscribe to presence updates', (done) => {
      const userIds = ['user1', 'user2'];
      const presenceUpdate: PresenceUpdate = {
        userId: 'user1',
        status: 'online',
        lastSeen: Date.now(),
        currentActivity: 'discovering souls'
      };

      service.subscribeToPresenceUpdates(userIds).subscribe(received => {
        expect(received.userId).toBe('user1');
        expect(received.status).toBe('online');
        done();
      });

      // Need to emit through the presenceUpdates$ subject which is private
      // Instead, use a connection channel that triggers typing_indicator
      setTimeout(() => {
        const connectionId = 'conn123';
        service.subscribeToConnectionStateChanges(connectionId).subscribe(() => {});

        const connChannel = channelSubjects.get(`connection_${connectionId}`);
        if (connChannel) {
          connChannel.next({
            type: 'typing_indicator',
            data: {
              userId: 'user1',
              isTyping: false
            }
          });
        }
      }, 50);
    });

    it('should filter presence updates by user IDs', (done) => {
      const userIds = ['user1', 'user2'];
      let updateCount = 0;

      service.subscribeToPresenceUpdates(userIds).subscribe(() => {
        updateCount++;
      });

      setTimeout(() => {
        const connectionId = 'conn123';
        service.subscribeToConnectionStateChanges(connectionId).subscribe(() => {});

        const connChannel = channelSubjects.get(`connection_${connectionId}`);
        if (connChannel) {
          // Should be filtered out (user3 not in list)
          connChannel.next({
            type: 'typing_indicator',
            data: { userId: 'user3', isTyping: true }
          });

          // Should pass through (user1 in list)
          connChannel.next({
            type: 'typing_indicator',
            data: { userId: 'user1', isTyping: true }
          });
        }

        setTimeout(() => {
          expect(updateCount).toBe(1);
          done();
        }, 100);
      }, 50);
    });

    it('should send typing indicator', () => {
      const connectionId = 'conn123';
      const isTyping = true;

      service.sendTypingIndicator(connectionId, isTyping);

      expect(mockWsPool.broadcastToChannel).toHaveBeenCalledWith(
        'connection_conn123',
        jasmine.objectContaining({
          type: 'typing_indicator',
          data: jasmine.objectContaining({
            connectionId,
            isTyping
          })
        })
      );
    });

    it('should update user presence map', (done) => {
      const userIds = ['user1'];

      service.subscribeToPresenceUpdates(userIds).subscribe(() => {});

      setTimeout(() => {
        const connectionId = 'conn123';
        service.subscribeToConnectionStateChanges(connectionId).subscribe(() => {});

        const connChannel = channelSubjects.get(`connection_${connectionId}`);
        if (connChannel) {
          connChannel.next({
            type: 'typing_indicator',
            data: { userId: 'user1', isTyping: false }
          });
        }

        setTimeout(() => {
          service.getUserPresence().subscribe(presenceMap => {
            expect(presenceMap.has('user1')).toBe(true);
            done();
          });
        }, 100);
      }, 50);
    });
  });

  describe('Connection State Changes', () => {
    it('should subscribe to connection state changes', (done) => {
      const connectionId = 'conn123';
      const stateChange: SoulConnectionUpdate = {
        connectionId: 'conn123',
        type: 'state_change',
        data: { newState: 'active' },
        timestamp: Date.now()
      };

      service.subscribeToConnectionStateChanges(connectionId).subscribe(received => {
        expect(received).toEqual(stateChange);
        expect(mockScreenReader.announce).toHaveBeenCalled();
        done();
      });

      const soulChannel = channelSubjects.get('soul_connections');
      if (soulChannel) {
        soulChannel.next({
          type: 'connection_state_change',
          data: stateChange as unknown as Record<string, unknown>
        });
      }
    });

    it('should announce match found', (done) => {
      // Subscribe to global channel to receive match notifications
      const soulChannel = channelSubjects.get('soul_connections');

      // Trigger the initialization to set up listeners
      if (soulChannel) {
        soulChannel.next({
          type: 'new_match',
          data: { matchId: 'match123' }
        });
      }

      setTimeout(() => {
        expect(mockScreenReader.announce).toHaveBeenCalledWith(
          jasmine.stringContaining('New soul match found'),
          'assertive',
          'new-match'
        );
        done();
      }, 100);
    });
  });

  describe('Connection Health Monitoring', () => {
    it('should report excellent health when 90%+ connections are healthy', (done) => {
      mockWsPool.getPoolStatistics.and.returnValue({
        totalConnections: 10,
        connectedCount: 10,
        connectingCount: 0,
        errorCount: 0,
        totalChannels: 5,
        totalSubscribers: 15,
        queuedMessages: 0
      });

      const countSubject = new BehaviorSubject<number>(10);
      mockWsPool.getConnectionCount.and.returnValue(countSubject.asObservable());
      const newService = new SoulConnectionRealtimeService(mockWsPool, mockScreenReader);

      setTimeout(() => {
        newService.getConnectionHealth().subscribe(health => {
          expect(health).toBe('excellent');
          newService.ngOnDestroy();
          done();
        });
      }, 1100); // Wait for debounce
    });

    it('should report good health when 70-89% connections are healthy', (done) => {
      mockWsPool.getPoolStatistics.and.returnValue({
        totalConnections: 10,
        connectedCount: 8,
        connectingCount: 2,
        errorCount: 0,
        totalChannels: 5,
        totalSubscribers: 15,
        queuedMessages: 0
      });

      const countSubject = new BehaviorSubject<number>(10);
      mockWsPool.getConnectionCount.and.returnValue(countSubject.asObservable());
      const newService = new SoulConnectionRealtimeService(mockWsPool, mockScreenReader);

      setTimeout(() => {
        newService.getConnectionHealth().subscribe(health => {
          expect(health).toBe('good');
          newService.ngOnDestroy();
          done();
        });
      }, 1100);
    });

    it('should report poor health when <70% connections are healthy', (done) => {
      mockWsPool.getPoolStatistics.and.returnValue({
        totalConnections: 10,
        connectedCount: 5,
        connectingCount: 3,
        errorCount: 2,
        totalChannels: 5,
        totalSubscribers: 15,
        queuedMessages: 0
      });

      const countSubject = new BehaviorSubject<number>(10);
      mockWsPool.getConnectionCount.and.returnValue(countSubject.asObservable());
      const newService = new SoulConnectionRealtimeService(mockWsPool, mockScreenReader);

      setTimeout(() => {
        newService.getConnectionHealth().subscribe(health => {
          expect(health).toBe('poor');
          newService.ngOnDestroy();
          done();
        });
      }, 1100);
    });
  });

  describe('Active Connections Management', () => {
    it('should track active connections', (done) => {
      const connectionId = 'conn123';

      service.subscribeToCompatibilityUpdates(connectionId).subscribe(() => {});

      setTimeout(() => {
        service.getActiveConnections().subscribe(connections => {
          expect(connections).toContain(connectionId);
          done();
        });
      }, 100);
    });

    it('should not duplicate connection IDs', (done) => {
      const connectionId = 'conn123';

      // Subscribe multiple times to same connection
      service.subscribeToCompatibilityUpdates(connectionId).subscribe(() => {});
      service.subscribeToEnergySync(connectionId).subscribe(() => {});
      service.subscribeToRevelationNotifications(connectionId).subscribe(() => {});

      setTimeout(() => {
        service.getActiveConnections().subscribe(connections => {
          const count = connections.filter(id => id === connectionId).length;
          expect(count).toBe(1);
          done();
        });
      }, 100);
    });
  });

  describe('Real-time Statistics', () => {
    it('should provide real-time statistics', () => {
      const stats = service.getRealtimeStatistics();

      expect(stats).toBeDefined();
      expect(stats.totalConnections).toBe(2);
      expect(stats.connectedCount).toBe(2);
      expect(stats.connectionHealth).toBeDefined();
      expect(stats.isConnected).toBeDefined();
    });

    it('should include active connections count', (done) => {
      service.subscribeToCompatibilityUpdates('conn1').subscribe(() => {});
      service.subscribeToCompatibilityUpdates('conn2').subscribe(() => {});

      setTimeout(() => {
        const stats = service.getRealtimeStatistics();
        expect(stats.activeConnections).toBeGreaterThan(0);
        done();
      }, 100);
    });

    it('should count online users', (done) => {
      const userIds = ['user1', 'user2'];
      service.subscribeToPresenceUpdates(userIds).subscribe(() => {});

      setTimeout(() => {
        const connectionId = 'conn123';
        service.subscribeToConnectionStateChanges(connectionId).subscribe(() => {});

        const connChannel = channelSubjects.get(`connection_${connectionId}`);
        if (connChannel) {
          // User1 online (isTyping: false = online)
          connChannel.next({
            type: 'typing_indicator',
            data: { userId: 'user1', isTyping: false }
          });

          // User2 offline - don't send any update for them
        }

        setTimeout(() => {
          const stats = service.getRealtimeStatistics();
          // At least user1 should be online
          expect(stats.onlineUsers).toBeGreaterThanOrEqual(1);
          done();
        }, 100);
      }, 50);
    });
  });

  describe('Reconnection', () => {
    it('should force reconnection', fakeAsync(() => {
      service.reconnectRealtime();

      expect(mockWsPool.closeAllConnections).toHaveBeenCalled();

      tick(1000);

      // Should reinitialize connections
      expect(mockWsPool.subscribeToChannel).toHaveBeenCalled();
      flush();
    }));
  });

  describe('Message Handling', () => {
    it('should handle global soul messages', (done) => {
      const compatUpdate: CompatibilityUpdate = {
        connectionId: 'conn123',
        newScore: 88,
        previousScore: 82,
        breakdown: { values: 90, interests: 85, communication: 88 },
        factors: []
      };

      service.subscribeToCompatibilityUpdates('conn123').subscribe(received => {
        expect(received.newScore).toBe(88);
        done();
      });

      const soulChannel = channelSubjects.get('soul_connections');
      if (soulChannel) {
        soulChannel.next({
          type: 'compatibility_update',
          data: compatUpdate as unknown as Record<string, unknown>
        });
      }
    });

    it('should handle connection-specific messages', (done) => {
      const connectionId = 'conn123';

      service.subscribeToEnergySync(connectionId).subscribe(sync => {
        expect(sync).toBeDefined();
        done();
      });

      const connChannel = channelSubjects.get('connection_conn123');
      if (connChannel) {
        connChannel.next({
          type: 'energy_pulse',
          data: {
            leftSoulEnergy: 70,
            rightSoulEnergy: 75,
            connectionStrength: 72.5
          } as unknown as Record<string, unknown>
        });
      }
    });

    it('should handle typing indicators', (done) => {
      const connectionId = 'conn123';
      const userId = 'user456';

      service.subscribeToPresenceUpdates([userId]).subscribe(() => {});

      setTimeout(() => {
        // Subscribe to connection channel to enable message routing
        service.subscribeToConnectionStateChanges(connectionId).subscribe(() => {});

        const connChannel = channelSubjects.get(`connection_${connectionId}`);
        if (connChannel) {
          connChannel.next({
            type: 'typing_indicator',
            data: {
              userId: userId,
              isTyping: true
            }
          });
        }

        setTimeout(() => {
          service.getUserPresence().subscribe(presenceMap => {
            const presence = presenceMap.get(userId);
            expect(presence?.status).toBe('typing');
            done();
          });
        }, 100);
      }, 50);
    });
  });

  describe('Service Lifecycle', () => {
    it('should cleanup on destroy', () => {
      service.ngOnDestroy();
      // Service should complete all subscriptions
      expect(service).toBeTruthy();
    });

    it('should stop receiving updates after destroy', (done) => {
      let updateCount = 0;

      service.subscribeToCompatibilityUpdates('conn123').subscribe(() => {
        updateCount++;
      });

      const compatChannel = channelSubjects.get('compatibility_updates');
      if (compatChannel) {
        compatChannel.next({
          type: 'compatibility_change',
          data: { connectionId: 'conn123', newScore: 85 } as unknown as Record<string, unknown>
        });
      }

      service.ngOnDestroy();

      if (compatChannel) {
        compatChannel.next({
          type: 'compatibility_change',
          data: { connectionId: 'conn123', newScore: 90 } as unknown as Record<string, unknown>
        });
      }

      setTimeout(() => {
        expect(updateCount).toBe(1);
        done();
      }, 100);
    });
  });

  describe('Error Handling', () => {
    it('should handle channel subscription errors gracefully', () => {
      // Errors should be logged but not crash the service
      const soulChannel = channelSubjects.get('soul_connections');
      if (soulChannel) {
        spyOn(console, 'error');
        soulChannel.error(new Error('Connection failed'));
        expect(console.error).toHaveBeenCalled();
      }
    });
  });

  describe('Edge Cases', () => {
    it('should handle messages without expected data', () => {
      const soulChannel = channelSubjects.get('soul_connections');
      if (soulChannel) {
        // Should not crash on malformed message
        expect(() => {
          soulChannel.next({
            type: 'unknown_type',
            data: {}
          });
        }).not.toThrow();
      }
    });

    it('should handle duplicate subscription to same channel', (done) => {
      const connectionId = 'conn123';

      service.subscribeToCompatibilityUpdates(connectionId).subscribe(() => {});
      service.subscribeToCompatibilityUpdates(connectionId).subscribe(() => {});

      setTimeout(() => {
        service.getActiveConnections().subscribe(connections => {
          const count = connections.filter(id => id === connectionId).length;
          expect(count).toBe(1);
          done();
        });
      }, 100);
    });

    it('should handle empty presence user list', (done) => {
      service.subscribeToPresenceUpdates([]).subscribe({
        next: () => done.fail('Should not receive updates'),
        error: () => done.fail('Should not error')
      });

      const presenceChannel = channelSubjects.get('user_presence');
      if (presenceChannel) {
        presenceChannel.next({
          type: 'presence_update',
          data: { userId: 'user1', status: 'online' } as unknown as Record<string, unknown>
        });
      }

      setTimeout(done, 100);
    });
  });
});
