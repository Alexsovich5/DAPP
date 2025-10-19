import { TestBed } from '@angular/core/testing';
import { ErrorLoggingService, ErrorLog } from './error-logging.service';
import { environment } from '@environments/environment';

describe('ErrorLoggingService', () => {
  let service: ErrorLoggingService;
  let originalEnvironment: typeof environment;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ErrorLoggingService]
    });
    service = TestBed.inject(ErrorLoggingService);

    // Store original environment
    originalEnvironment = { ...environment };

    // Clear localStorage before each test
    localStorage.clear();

    // Spy on console methods
    spyOn(console, 'error');
    spyOn(console, 'warn');
    spyOn(console, 'info');
  });

  afterEach(() => {
    // Restore original environment
    Object.assign(environment, originalEnvironment);
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('logError()', () => {
    it('should log an error with string message', () => {
      const errorMessage = 'Test error message';
      const context = { userId: '123', action: 'test' };

      service.logError(errorMessage, context);

      const logs = service.getRecentLogs(1);
      expect(logs.length).toBe(1);
      expect(logs[0].level).toBe('error');
      expect(logs[0].message).toBe(errorMessage);
      expect(logs[0].context).toEqual(context);
      expect(logs[0].error).toBeUndefined();
      expect(logs[0].url).toBe(window.location.href);
      expect(logs[0].userAgent).toBe(navigator.userAgent);
    });

    it('should log an error with Error object', () => {
      const error = new Error('Test error');
      const context = { component: 'TestComponent' };

      service.logError(error, context);

      const logs = service.getRecentLogs(1);
      expect(logs.length).toBe(1);
      expect(logs[0].level).toBe('error');
      expect(logs[0].message).toBe('Test error');
      expect(logs[0].error).toEqual(error);
      expect(logs[0].context).toEqual(context);
    });

    it('should log error without context', () => {
      service.logError('Simple error');

      const logs = service.getRecentLogs(1);
      expect(logs.length).toBe(1);
      expect(logs[0].message).toBe('Simple error');
      expect(logs[0].context).toBeUndefined();
    });

    it('should log to console in development mode', () => {
      (environment as any).production = false;

      service.logError('Dev error');

      expect(console.error).toHaveBeenCalledWith('Error logged:', jasmine.any(Object));
    });

    it('should not log to console in production mode', () => {
      // Set production mode and clear localStorage for clean test state
      (environment as any).production = true;
      localStorage.clear();

      service.logError('Prod error');

      expect(console.error).not.toHaveBeenCalled();

      // Restore development mode
      (environment as any).production = false;
    });

    it('should send to logging service in production', () => {
      (environment as any).production = true;
      localStorage.clear();
      spyOn<any>(service, 'sendToLoggingService');

      service.logError('Production error');

      expect((service as any).sendToLoggingService).toHaveBeenCalled();

      // Restore development mode
      (environment as any).production = false;
    });

    it('should include timestamp in error log', () => {
      const beforeTime = new Date();
      service.logError('Test error');
      const afterTime = new Date();

      const logs = service.getRecentLogs(1);
      expect(logs[0].timestamp).toBeDefined();
      expect(logs[0].timestamp.getTime()).toBeGreaterThanOrEqual(beforeTime.getTime());
      expect(logs[0].timestamp.getTime()).toBeLessThanOrEqual(afterTime.getTime());
    });
  });

  describe('logWarning()', () => {
    it('should log a warning message', () => {
      const message = 'Warning message';
      const context = { feature: 'test-feature' };

      service.logWarning(message, context);

      const logs = service.getRecentLogs(1);
      expect(logs.length).toBe(1);
      expect(logs[0].level).toBe('warn');
      expect(logs[0].message).toBe(message);
      expect(logs[0].context).toEqual(context);
      expect(logs[0].url).toBe(window.location.href);
    });

    it('should log warning without context', () => {
      service.logWarning('Simple warning');

      const logs = service.getRecentLogs(1);
      expect(logs[0].message).toBe('Simple warning');
      expect(logs[0].context).toBeUndefined();
    });

    it('should log to console in development mode', () => {
      (environment as any).production = false;

      service.logWarning('Dev warning');

      expect(console.warn).toHaveBeenCalledWith('Warning logged:', jasmine.any(Object));
    });

    it('should not log to console in production mode', () => {
      // Set production mode and clear localStorage for clean test state
      (environment as any).production = true;
      localStorage.clear();

      service.logWarning('Prod warning');

      expect(console.warn).not.toHaveBeenCalled();

      // Restore development mode
      (environment as any).production = false;
    });
  });

  describe('logInfo()', () => {
    it('should log an info message', () => {
      const message = 'Info message';
      const context = { module: 'test-module' };

      service.logInfo(message, context);

      const logs = service.getRecentLogs(1);
      expect(logs.length).toBe(1);
      expect(logs[0].level).toBe('info');
      expect(logs[0].message).toBe(message);
      expect(logs[0].context).toEqual(context);
    });

    it('should log info without context', () => {
      service.logInfo('Simple info');

      const logs = service.getRecentLogs(1);
      expect(logs[0].message).toBe('Simple info');
      expect(logs[0].context).toBeUndefined();
    });

    it('should log to console in development mode', () => {
      (environment as any).production = false;

      service.logInfo('Dev info');

      expect(console.info).toHaveBeenCalledWith('Info logged:', jasmine.any(Object));
    });

    it('should not log to console in production mode', () => {
      // Set production mode and clear localStorage for clean test state
      (environment as any).production = true;
      localStorage.clear();

      service.logInfo('Prod info');

      expect(console.info).not.toHaveBeenCalled();

      // Restore development mode
      (environment as any).production = false;
    });
  });

  describe('logApiError()', () => {
    it('should log API error with all details', () => {
      const endpoint = '/api/v1/users';
      const status = 500;
      const error = 'Internal Server Error';
      const requestData = { userId: '123', action: 'update' };

      service.logApiError(endpoint, status, error, requestData);

      const logs = service.getRecentLogs(1);
      expect(logs.length).toBe(1);
      expect(logs[0].level).toBe('error');
      expect(logs[0].message).toBe(error);
      expect(logs[0].context).toEqual({
        type: 'api_error',
        endpoint,
        status,
        requestData,
        timestamp: jasmine.any(String)
      });
    });

    it('should log API error without request data', () => {
      service.logApiError('/api/v1/test', 404, 'Not Found');

      const logs = service.getRecentLogs(1);
      expect(logs[0].context).toEqual({
        type: 'api_error',
        endpoint: '/api/v1/test',
        status: 404,
        requestData: undefined,
        timestamp: jasmine.any(String)
      });
    });

    it('should log API error with Error object', () => {
      const error = new Error('Network timeout');

      service.logApiError('/api/v1/profiles', 408, error, { timeout: 5000 });

      const logs = service.getRecentLogs(1);
      expect(logs[0].error).toEqual(error);
      expect(logs[0].message).toBe('Network timeout');
    });
  });

  describe('logUserAction()', () => {
    it('should log user action with data', () => {
      const action = 'profile_update';
      const data = { field: 'bio', oldValue: 'old', newValue: 'new' };

      service.logUserAction(action, data);

      const logs = service.getRecentLogs(1);
      expect(logs.length).toBe(1);
      expect(logs[0].level).toBe('info');
      expect(logs[0].message).toBe(`User action: ${action}`);
      expect(logs[0].context).toEqual({
        type: 'user_action',
        action,
        data,
        timestamp: jasmine.any(String)
      });
    });

    it('should log user action without data', () => {
      service.logUserAction('button_click');

      const logs = service.getRecentLogs(1);
      expect(logs[0].message).toBe('User action: button_click');
      expect(logs[0].context?.['data']).toBeUndefined();
    });
  });

  describe('getRecentLogs()', () => {
    it('should return recent logs with default count of 50', () => {
      // Add 60 logs
      for (let i = 0; i < 60; i++) {
        service.logInfo(`Log ${i}`);
      }

      const logs = service.getRecentLogs();
      expect(logs.length).toBe(50);
      expect(logs[0].message).toBe('Log 10'); // First of last 50
      expect(logs[49].message).toBe('Log 59'); // Last log
    });

    it('should return specified number of recent logs', () => {
      for (let i = 0; i < 20; i++) {
        service.logInfo(`Log ${i}`);
      }

      const logs = service.getRecentLogs(10);
      expect(logs.length).toBe(10);
      expect(logs[0].message).toBe('Log 10');
      expect(logs[9].message).toBe('Log 19');
    });

    it('should return all logs if count is greater than total', () => {
      service.logInfo('Log 1');
      service.logInfo('Log 2');

      const logs = service.getRecentLogs(100);
      expect(logs.length).toBe(2);
    });

    it('should return empty array when no logs exist', () => {
      const logs = service.getRecentLogs();
      expect(logs).toEqual([]);
    });
  });

  describe('clearLogs()', () => {
    it('should clear all logs', () => {
      service.logError('Error 1');
      service.logWarning('Warning 1');
      service.logInfo('Info 1');

      expect(service.getRecentLogs().length).toBe(3);

      service.clearLogs();

      expect(service.getRecentLogs().length).toBe(0);
    });

    it('should allow adding logs after clearing', () => {
      service.logInfo('Before clear');
      service.clearLogs();
      service.logInfo('After clear');

      const logs = service.getRecentLogs();
      expect(logs.length).toBe(1);
      expect(logs[0].message).toBe('After clear');
    });
  });

  describe('exportLogs()', () => {
    it('should export logs as JSON string', () => {
      service.logError('Error log');
      service.logWarning('Warning log');

      const exported = service.exportLogs();
      const parsed = JSON.parse(exported);

      expect(parsed.timestamp).toBeDefined();
      expect(parsed.logs).toBeDefined();
      expect(parsed.logs.length).toBe(2);
      expect(parsed.environment).toBeDefined();
      expect(parsed.environment.production).toBe(environment.production);
      expect(parsed.environment.userAgent).toBe(navigator.userAgent);
      expect(parsed.environment.url).toBe(window.location.href);
    });

    it('should export with proper formatting', () => {
      service.logInfo('Test');

      const exported = service.exportLogs();

      // Check it's properly formatted with indentation
      expect(exported).toContain('\n');
      expect(exported).toContain('  '); // 2-space indentation
    });

    it('should export empty logs array when no logs exist', () => {
      const exported = service.exportLogs();
      const parsed = JSON.parse(exported);

      expect(parsed.logs).toEqual([]);
    });
  });

  describe('Log storage management', () => {
    it('should maintain only the most recent 1000 logs', () => {
      // Add 1100 logs
      for (let i = 0; i < 1100; i++) {
        service.logInfo(`Log ${i}`);
      }

      const allLogs = service.getRecentLogs(2000);
      expect(allLogs.length).toBe(1000);
      expect(allLogs[0].message).toBe('Log 100'); // First kept log
      expect(allLogs[999].message).toBe('Log 1099'); // Last log
    });

    it('should handle rapid logging without data loss', () => {
      for (let i = 0; i < 50; i++) {
        service.logError(`Error ${i}`);
        service.logWarning(`Warning ${i}`);
        service.logInfo(`Info ${i}`);
      }

      const logs = service.getRecentLogs(200);
      expect(logs.length).toBe(150);
    });
  });

  describe('Production logging to localStorage', () => {
    beforeEach(() => {
      // Set production mode BEFORE service creation for proper test isolation
      (environment as any).production = true;
      // Clear localStorage to ensure clean state
      localStorage.clear();
    });

    afterEach(() => {
      // Restore development mode
      (environment as any).production = false;
      localStorage.clear();
    });

    it('should store logs in localStorage in production', () => {
      // Verify environment.production is set
      expect(environment.production).toBe(true);

      service.logError('Production error', { critical: true });

      const storedLogs = JSON.parse(localStorage.getItem('error_logs') || '[]');
      expect(storedLogs.length).toBe(1);
      expect(storedLogs[0].message).toBe('Production error');
    });

    it('should maintain only last 100 logs in localStorage', () => {
      // Pre-populate localStorage with 95 logs
      const existingLogs: ErrorLog[] = [];
      for (let i = 0; i < 95; i++) {
        existingLogs.push({
          timestamp: new Date(),
          level: 'error',
          message: `Old log ${i}`,
          url: window.location.href
        });
      }
      localStorage.setItem('error_logs', JSON.stringify(existingLogs));

      // Add 10 more logs
      for (let i = 0; i < 10; i++) {
        service.logError(`New log ${i}`);
      }

      const storedLogs = JSON.parse(localStorage.getItem('error_logs') || '[]');
      expect(storedLogs.length).toBe(100);
      expect(storedLogs[0].message).toBe('Old log 5'); // First of last 100
      expect(storedLogs[99].message).toBe('New log 9'); // Last log
    });

    it('should handle localStorage errors gracefully', () => {
      spyOn(localStorage, 'setItem').and.throwError('Quota exceeded');

      // Should not throw error
      expect(() => service.logError('Test error')).not.toThrow();
      expect(console.error).toHaveBeenCalledWith('Failed to store error log:', jasmine.any(Error));
    });

    it('should parse existing logs from localStorage', () => {
      const existingLog: ErrorLog = {
        timestamp: new Date(),
        level: 'error',
        message: 'Existing error',
        url: window.location.href
      };
      localStorage.setItem('error_logs', JSON.stringify([existingLog]));

      service.logError('New error');

      const storedLogs = JSON.parse(localStorage.getItem('error_logs') || '[]');
      expect(storedLogs.length).toBe(2);
      expect(storedLogs[0].message).toBe('Existing error');
      expect(storedLogs[1].message).toBe('New error');
    });
  });

  describe('Integration tests', () => {
    it('should handle mixed log levels in order', () => {
      service.logError('Error 1');
      service.logWarning('Warning 1');
      service.logInfo('Info 1');
      service.logError('Error 2');

      const logs = service.getRecentLogs();
      expect(logs.length).toBe(4);
      expect(logs[0].message).toBe('Error 1');
      expect(logs[1].message).toBe('Warning 1');
      expect(logs[2].message).toBe('Info 1');
      expect(logs[3].message).toBe('Error 2');
    });

    it('should handle complex context objects', () => {
      const complexContext = {
        user: { id: '123', name: 'Test User' },
        request: { url: '/api/test', method: 'POST' },
        nested: { deeply: { nested: { value: 'test' } } }
      };

      service.logError('Complex error', complexContext);

      const logs = service.getRecentLogs(1);
      expect(logs[0].context).toEqual(complexContext);
    });

    it('should maintain separate in-memory and localStorage logs in production', () => {
      (environment as any).production = true;

      service.logError('Test error 1');
      service.logError('Test error 2');

      // In-memory logs
      const memoryLogs = service.getRecentLogs();
      expect(memoryLogs.length).toBe(2);

      // localStorage logs
      const storedLogs = JSON.parse(localStorage.getItem('error_logs') || '[]');
      expect(storedLogs.length).toBe(2);
    });
  });

  describe('Edge cases', () => {
    it('should handle very long error messages', () => {
      const longMessage = 'a'.repeat(10000);

      service.logError(longMessage);

      const logs = service.getRecentLogs(1);
      expect(logs[0].message).toBe(longMessage);
      expect(logs[0].message.length).toBe(10000);
    });

    it('should handle error messages with special characters', () => {
      const specialMessage = 'Error: <script>alert("xss")</script> \n\t\r';

      service.logError(specialMessage);

      const logs = service.getRecentLogs(1);
      expect(logs[0].message).toBe(specialMessage);
    });

    it('should handle null context gracefully', () => {
      service.logError('Error', null as any);

      const logs = service.getRecentLogs(1);
      expect(logs[0].context).toBeNull();
    });

    it('should handle circular references in context', () => {
      const circularContext: any = { name: 'test' };
      circularContext.self = circularContext;

      // Should not throw when logging
      expect(() => service.logError('Circular error', circularContext)).not.toThrow();
    });
  });
});
