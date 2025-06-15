import { ErrorHandler, Injectable, inject } from '@angular/core';
import { NotificationService } from '../services/notification.service';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  private notificationService = inject(NotificationService);

  handleError(error: unknown): void {
    console.error('Global error caught:', error);

    // Don't show notifications for HTTP errors - those are handled by services
    if (this.isHttpError(error)) {
      return;
    }

    // Handle JavaScript runtime errors
    if (error instanceof Error) {
      this.handleJavaScriptError(error);
      return;
    }

    // Handle promise rejections
    if (this.isPromiseRejection(error)) {
      this.handlePromiseRejection(error);
      return;
    }

    // Fallback for unknown errors
    this.notificationService.showError('An unexpected error occurred. Please refresh the page and try again.');
  }

  private isHttpError(error: unknown): boolean {
    return error instanceof Error && 
           (error.name === 'HttpErrorResponse' || 
            error.message.includes('Http'));
  }

  private isPromiseRejection(error: unknown): boolean {
    return typeof error === 'object' && 
           error !== null && 
           'rejection' in (error as any);
  }

  private handleJavaScriptError(error: Error): void {
    // Don't overwhelm users with technical JavaScript errors
    if (this.isUserFacingError(error)) {
      this.notificationService.showError(error.message);
    } else {
      this.notificationService.showError('A technical error occurred. Please refresh the page and try again.');
    }
  }

  private handlePromiseRejection(error: any): void {
    const rejection = error.rejection;
    
    if (rejection instanceof Error) {
      this.handleJavaScriptError(rejection);
    } else if (typeof rejection === 'string') {
      this.notificationService.showError(rejection);
    } else {
      this.notificationService.showError('An operation failed. Please try again.');
    }
  }

  private isUserFacingError(error: Error): boolean {
    const userFacingPatterns = [
      /network/i,
      /connection/i,
      /timeout/i,
      /offline/i,
      /permission/i,
      /unauthorized/i,
      /forbidden/i
    ];

    return userFacingPatterns.some(pattern => pattern.test(error.message));
  }
}