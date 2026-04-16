import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BaseService } from './base.service';
import { NotificationService } from './notification.service';
import { ErrorLoggingService } from './error-logging.service';
import { of } from 'rxjs';

// Create a concrete implementation for testing the abstract BaseService
@Injectable()
class TestableBaseService extends BaseService {
  // Expose protected methods for testing
  public testHandleError<T>(operation: string, result?: T) {
    return this.handleError(operation, result);
  }

  public testGetErrorMessage(error: HttpErrorResponse): string {
    return this.getErrorMessage(error);
  }

  public testHandleSuccess<T>(operation: string, showNotification = false) {
    return this.handleSuccess(operation, showNotification);
  }

  public testHandleLoading(loading: { value: boolean }) {
    return this.handleLoading(loading);
  }
}

describe('BaseService', () => {
  let service: TestableBaseService;
  let notificationService: jasmine.SpyObj<NotificationService>;
  let errorLoggingService: jasmine.SpyObj<ErrorLoggingService>;

  beforeEach(() => {
    const notificationSpy = jasmine.createSpyObj('NotificationService', ['showError', 'showSuccess']);
    const errorLoggingSpy = jasmine.createSpyObj('ErrorLoggingService', ['logApiError']);

    TestBed.configureTestingModule({
      providers: [
        TestableBaseService,
        { provide: NotificationService, useValue: notificationSpy },
        { provide: ErrorLoggingService, useValue: errorLoggingSpy }
      ]
    });

    service = TestBed.inject(TestableBaseService);
    notificationService = TestBed.inject(NotificationService) as jasmine.SpyObj<NotificationService>;
    errorLoggingService = TestBed.inject(ErrorLoggingService) as jasmine.SpyObj<ErrorLoggingService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('handleError()', () => {
    it('should handle HTTP error and return default result', (done) => {
      const error = new HttpErrorResponse({
        error: 'Test error',
        status: 500,
        statusText: 'Internal Server Error',
        url: 'http://localhost:5000/api/v1/test'
      });

      const defaultResult = { success: false };
      const errorHandler = service.testHandleError('test operation', defaultResult);

      errorHandler(error).subscribe(result => {
        expect(result).toEqual(defaultResult);
        expect(notificationService.showError).toHaveBeenCalled();
        expect(errorLoggingService.logApiError).toHaveBeenCalledWith(
          'http://localhost:5000/api/v1/test',
          500,
          'Test error',
          jasmine.objectContaining({ operation: 'test operation' })
        );
        done();
      });
    });

    it('should handle HTTP error with undefined default result', (done) => {
      const error = new HttpErrorResponse({
        error: 'Test error',
        status: 404,
        statusText: 'Not Found',
        url: 'http://localhost:5000/api/v1/resource'
      });

      const errorHandler = service.testHandleError('find resource');

      errorHandler(error).subscribe(result => {
        expect(result).toBeUndefined();
        expect(notificationService.showError).toHaveBeenCalledWith('Test error');
        done();
      });
    });

    it('should log error context with headers and params', (done) => {
      const headers = new HttpHeaders().set('Authorization', 'Bearer token');
      const error = new HttpErrorResponse({
        error: 'Unauthorized',
        status: 401,
        statusText: 'Unauthorized',
        url: 'http://localhost:5000/api/v1/users?page=1&limit=10',
        headers
      });

      const errorHandler = service.testHandleError('get users', []);

      errorHandler(error).subscribe(() => {
        expect(errorLoggingService.logApiError).toHaveBeenCalledWith(
          'http://localhost:5000/api/v1/users?page=1&limit=10',
          401,
          'Unauthorized',
          jasmine.objectContaining({
            operation: 'get users',
            headers: jasmine.any(Array),
            params: 'page=1&limit=10'
          })
        );
        done();
      });
    });

    it('should handle error with unknown URL', (done) => {
      const error = new HttpErrorResponse({
        error: 'Network error',
        status: 0,
        statusText: 'Unknown Error'
      });

      const errorHandler = service.testHandleError('network operation', null);

      errorHandler(error).subscribe(() => {
        expect(errorLoggingService.logApiError).toHaveBeenCalledWith(
          'unknown',
          0,
          'Network error',
          jasmine.objectContaining({ operation: 'network operation' })
        );
        done();
      });
    });

    it('should use error message when error.error is not present', (done) => {
      const error = new HttpErrorResponse({
        status: 500,
        statusText: 'Internal Server Error',
        url: 'http://localhost:5000/api/v1/test',
        error: null
      });

      const errorHandler = service.testHandleError('test', {});

      errorHandler(error).subscribe(() => {
        expect(errorLoggingService.logApiError).toHaveBeenCalledWith(
          'http://localhost:5000/api/v1/test',
          500,
          jasmine.stringContaining('Http failure response'),
          jasmine.any(Object)
        );
        done();
      });
    });
  });

  describe('getErrorMessage()', () => {
    it('should return default message when error.error is not present', () => {
      const error = new HttpErrorResponse({
        status: 500,
        statusText: 'Internal Server Error'
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('An unexpected error occurred. Please try again.');
    });

    it('should handle FastAPI validation errors (422) with array detail', () => {
      const error = new HttpErrorResponse({
        status: 422,
        error: {
          detail: [
            { loc: ['body', 'email'], msg: 'invalid email format' },
            { loc: ['body', 'password'], msg: 'password too short' }
          ]
        }
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toContain('body > email: invalid email format');
      expect(message).toContain('body > password: password too short');
    });

    it('should handle FastAPI validation errors with missing loc', () => {
      const error = new HttpErrorResponse({
        status: 422,
        error: {
          detail: [
            { msg: 'validation failed' }
          ]
        }
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toContain('Field: validation failed');
    });

    it('should handle FastAPI validation errors (422) with string detail', () => {
      const error = new HttpErrorResponse({
        status: 422,
        error: {
          detail: 'Invalid request body'
        }
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('Invalid request body');
    });

    it('should handle string error responses', () => {
      const error = new HttpErrorResponse({
        status: 400,
        error: 'Bad request string error'
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('Bad request string error');
    });

    it('should handle error with message property', () => {
      const error = new HttpErrorResponse({
        status: 400,
        error: {
          message: 'Custom error message'
        }
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('Custom error message');
    });

    it('should handle error with detail property', () => {
      const error = new HttpErrorResponse({
        status: 400,
        error: {
          detail: 'Detailed error information'
        }
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('Detailed error information');
    });

    it('should return network error message for status 0', () => {
      const error = new HttpErrorResponse({
        status: 0,
        error: { some: 'error' }
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('Unable to connect to the server. Please check your internet connection.');
    });

    it('should return specific message for 400 Bad Request', () => {
      const error = new HttpErrorResponse({
        status: 400,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('Invalid request. Please check your input and try again.');
    });

    it('should return specific message for 401 Unauthorized', () => {
      const error = new HttpErrorResponse({
        status: 401,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('You are not authorized to perform this action.');
    });

    it('should return specific message for 403 Forbidden', () => {
      const error = new HttpErrorResponse({
        status: 403,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('You do not have permission to access this resource.');
    });

    it('should return specific message for 404 Not Found', () => {
      const error = new HttpErrorResponse({
        status: 404,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('The requested resource was not found.');
    });

    it('should return specific message for 409 Conflict', () => {
      const error = new HttpErrorResponse({
        status: 409,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('This operation conflicts with existing data.');
    });

    it('should return specific message for 429 Too Many Requests', () => {
      const error = new HttpErrorResponse({
        status: 429,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('Too many requests. Please wait a moment and try again.');
    });

    it('should return specific message for 500 Internal Server Error', () => {
      const error = new HttpErrorResponse({
        status: 500,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('A server error occurred. Please try again later.');
    });

    it('should return specific message for 503 Service Unavailable', () => {
      const error = new HttpErrorResponse({
        status: 503,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('The service is temporarily unavailable. Please try again later.');
    });

    it('should return default message for unknown status codes', () => {
      const error = new HttpErrorResponse({
        status: 418,
        error: {}
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('An unexpected error occurred. Please try again.');
    });
  });

  describe('handleSuccess()', () => {
    it('should return result without notification when showNotification is false', () => {
      const testData = { id: 1, name: 'Test' };
      const successHandler = service.testHandleSuccess('create user', false);

      const result = successHandler(testData);

      expect(result).toEqual(testData);
      expect(notificationService.showSuccess).not.toHaveBeenCalled();
    });

    it('should return result with notification when showNotification is true', () => {
      const testData = { id: 1, name: 'Test' };
      const successHandler = service.testHandleSuccess('update profile', true);

      const result = successHandler(testData);

      expect(result).toEqual(testData);
      expect(notificationService.showSuccess).toHaveBeenCalledWith('update profile completed successfully');
    });

    it('should handle success with null result', () => {
      const successHandler = service.testHandleSuccess('delete item', true);

      const result = successHandler(null);

      expect(result).toBeNull();
      expect(notificationService.showSuccess).toHaveBeenCalledWith('delete item completed successfully');
    });

    it('should handle success with undefined result', () => {
      const successHandler = service.testHandleSuccess('void operation', false);

      const result = successHandler(undefined);

      expect(result).toBeUndefined();
      expect(notificationService.showSuccess).not.toHaveBeenCalled();
    });

    it('should handle success with array result', () => {
      const testData = [1, 2, 3, 4, 5];
      const successHandler = service.testHandleSuccess('fetch items', true);

      const result = successHandler(testData);

      expect(result).toEqual(testData);
      expect(notificationService.showSuccess).toHaveBeenCalled();
    });
  });

  describe('handleLoading()', () => {
    it('should set loading to true when start is called', () => {
      const loadingState = { value: false };
      const loadingHandler = service.testHandleLoading(loadingState);

      loadingHandler.start();

      expect(loadingState.value).toBe(true);
    });

    it('should set loading to false when stop is called', () => {
      const loadingState = { value: true };
      const loadingHandler = service.testHandleLoading(loadingState);

      loadingHandler.stop();

      expect(loadingState.value).toBe(false);
    });

    it('should toggle loading state multiple times', () => {
      const loadingState = { value: false };
      const loadingHandler = service.testHandleLoading(loadingState);

      loadingHandler.start();
      expect(loadingState.value).toBe(true);

      loadingHandler.stop();
      expect(loadingState.value).toBe(false);

      loadingHandler.start();
      expect(loadingState.value).toBe(true);

      loadingHandler.stop();
      expect(loadingState.value).toBe(false);
    });

    it('should maintain reference to loading object', () => {
      const loadingState = { value: false };
      const handler1 = service.testHandleLoading(loadingState);
      const handler2 = service.testHandleLoading(loadingState);

      handler1.start();
      expect(loadingState.value).toBe(true);

      handler2.stop();
      expect(loadingState.value).toBe(false);
    });
  });

  describe('Integration tests', () => {
    it('should handle complete error flow with all components', (done) => {
      const error = new HttpErrorResponse({
        error: { detail: 'Resource already exists' },
        status: 409,
        statusText: 'Conflict',
        url: 'http://localhost:5000/api/v1/resources'
      });

      const errorHandler = service.testHandleError('create resource', null);

      errorHandler(error).subscribe(result => {
        expect(result).toBeNull();
        expect(notificationService.showError).toHaveBeenCalledWith('Resource already exists');
        expect(errorLoggingService.logApiError).toHaveBeenCalled();
        done();
      });
    });

    it('should handle success flow with notification', () => {
      const data = { success: true, message: 'Operation completed' };
      const successHandler = service.testHandleSuccess('complete operation', true);

      const result = successHandler(data);

      expect(result).toEqual(data);
      expect(notificationService.showSuccess).toHaveBeenCalledWith('complete operation completed successfully');
    });

    it('should handle loading lifecycle during operation', () => {
      const loading = { value: false };
      const loadingHandler = service.testHandleLoading(loading);

      // Simulate operation start
      loadingHandler.start();
      expect(loading.value).toBe(true);

      // Simulate operation completion
      loadingHandler.stop();
      expect(loading.value).toBe(false);
    });
  });

  describe('Edge cases', () => {
    it('should handle error with empty error object', (done) => {
      const error = new HttpErrorResponse({
        status: 500,
        statusText: 'Unknown Error',
        error: {}
      });

      const errorHandler = service.testHandleError('test', {});

      errorHandler(error).subscribe(() => {
        expect(notificationService.showError).toHaveBeenCalledWith('A server error occurred. Please try again later.');
        done();
      });
    });

    it('should handle error with null error', (done) => {
      const error = new HttpErrorResponse({
        status: 500,
        statusText: 'Unknown Error',
        error: null
      });

      const errorHandler = service.testHandleError('test', {});

      errorHandler(error).subscribe(() => {
        expect(notificationService.showError).toHaveBeenCalledWith('An unexpected error occurred. Please try again.');
        done();
      });
    });

    it('should handle very long operation names in success handler', () => {
      const longOperation = 'a'.repeat(1000);
      const successHandler = service.testHandleSuccess(longOperation, true);

      successHandler({});

      expect(notificationService.showSuccess).toHaveBeenCalledWith(`${longOperation} completed successfully`);
    });

    it('should handle complex nested error detail', () => {
      const error = new HttpErrorResponse({
        status: 422,
        error: {
          detail: [
            { loc: ['body', 'user', 'profile', 'bio'], msg: 'bio too long' }
          ]
        }
      });

      const message = service.testGetErrorMessage(error);
      expect(message).toBe('body > user > profile > bio: bio too long');
    });
  });
});
