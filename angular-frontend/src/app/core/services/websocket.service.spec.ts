/**
 * WebSocket Service Tests
 * Basic tests for WebSocket service stub
 */

import { TestBed } from '@angular/core/testing';
import { WebSocketService } from './websocket.service';
import { AuthService } from './auth.service';
import { NotificationService } from './notification.service';

describe('WebSocketService', () => {
  let service: WebSocketService;
  let authService: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', ['getToken']);
    const notificationSpy = jasmine.createSpyObj('NotificationService', ['showNotification']);

    TestBed.configureTestingModule({
      providers: [
        WebSocketService,
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notificationSpy }
      ]
    });

    service = TestBed.inject(WebSocketService);
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;

    authService.getToken.and.returnValue('mock-jwt-token');
  });

  it('should create service', () => {
    expect(service).toBeTruthy();
  });

  it('should have messages$ observable', () => {
    expect(service.messages$).toBeDefined();
  });

  it('should have connectionStatus$ observable', () => {
    expect(service.connectionStatus$).toBeDefined();
  });

  it('should call connect with token', () => {
    spyOn(console, 'log');
    service.connect('test-token');
    expect(console.log).toHaveBeenCalledWith('WebSocket connect called with token:', 'test-token');
  });

  it('should call disconnect', () => {
    service.disconnect();
    expect(service.getConnectionStatus().isConnected).toBe(false);
  });

  it('should call sendMessage', () => {
    spyOn(console, 'log');
    const message = { type: 'test', data: {}, timestamp: new Date().toISOString() };
    service.sendMessage(message);
    expect(console.log).toHaveBeenCalledWith('Sending message:', message);
  });

  it('should return connection status', () => {
    const status = service.getConnectionStatus();
    expect(status).toBeDefined();
    expect(status.isConnected).toBe(false);
  });
});
