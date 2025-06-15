import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { NotificationService } from './notification.service';

@Injectable()
export abstract class BaseService {
  protected notificationService = inject(NotificationService);

  /**
   * Handle Http operation that failed.
   * Let the app continue.
   * @param operation - name of the operation that failed
   * @param result - optional value to return as the observable result
   */
  protected handleError<T>(operation = 'operation', result?: T) {
    return (error: HttpErrorResponse): Observable<T> => {
      // Log error for debugging
      console.error(`${operation} failed:`, error);

      // Get user-friendly error message
      const message = this.getErrorMessage(error);
      
      // Show notification to user
      this.notificationService.showError(message);

      // Let the app keep running by returning an empty result
      return of(result as T);
    };
  }

  /**
   * Extract user-friendly error message from HTTP error
   */
  protected getErrorMessage(error: HttpErrorResponse): string {
    if (!error.error) {
      return 'An unexpected error occurred. Please try again.';
    }

    // Handle FastAPI validation errors
    if (error.status === 422 && error.error.detail) {
      if (Array.isArray(error.error.detail)) {
        return error.error.detail
          .map((err: any) => `${err.loc?.join(' > ') || 'Field'}: ${err.msg}`)
          .join(', ');
      }
      return error.error.detail;
    }

    // Handle other API errors
    if (typeof error.error === 'string') {
      return error.error;
    }

    if (error.error.message) {
      return error.error.message;
    }

    if (error.error.detail) {
      return error.error.detail;
    }

    // Network/connection errors
    if (error.status === 0) {
      return 'Unable to connect to the server. Please check your internet connection.';
    }

    // HTTP status based messages
    switch (error.status) {
      case 400:
        return 'Invalid request. Please check your input and try again.';
      case 401:
        return 'You are not authorized to perform this action.';
      case 403:
        return 'You do not have permission to access this resource.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return 'This operation conflicts with existing data.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'A server error occurred. Please try again later.';
      case 503:
        return 'The service is temporarily unavailable. Please try again later.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  }

  /**
   * Handle operation success with optional notification
   */
  protected handleSuccess<T>(operation: string, showNotification = false) {
    return (result: T): T => {
      if (showNotification) {
        this.notificationService.showSuccess(`${operation} completed successfully`);
      }
      return result;
    };
  }

  /**
   * Handle operation with loading state
   */
  protected handleLoading(loading: { value: boolean }) {
    return {
      start: () => loading.value = true,
      stop: () => loading.value = false
    };
  }
}