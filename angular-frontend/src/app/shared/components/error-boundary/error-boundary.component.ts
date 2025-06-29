import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ErrorLoggingService } from '@core/services/error-logging.service';
import { environment } from '@environments/environment';

@Component({
  selector: 'app-error-boundary',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    <div class="error-boundary" *ngIf="hasError">
      <div class="error-content">
        <mat-icon class="error-icon">error_outline</mat-icon>
        
        <h2 class="error-title">{{ errorTitle }}</h2>
        
        <p class="error-message">{{ errorMessage }}</p>
        
        <div class="error-actions">
          <button 
            mat-raised-button 
            color="primary" 
            (click)="retry()"
            class="retry-button"
          >
            <mat-icon>refresh</mat-icon>
            Try Again
          </button>
          
          <button 
            mat-button 
            (click)="reportError()"
            class="report-button"
          >
            <mat-icon>bug_report</mat-icon>
            Report Issue
          </button>
        </div>
        
        <details class="error-details" *ngIf="!environment.production && errorDetails">
          <summary>Technical Details</summary>
          <pre class="error-stack">{{ errorDetails }}</pre>
        </details>
      </div>
    </div>
    
    <ng-content *ngIf="!hasError"></ng-content>
  `,
  styles: [`
    .error-boundary {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 200px;
      padding: 2rem;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 8px;
      margin: 1rem 0;
    }

    .error-content {
      text-align: center;
      max-width: 500px;
    }

    .error-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: #dc2626;
      margin-bottom: 1rem;
    }

    .error-title {
      color: #dc2626;
      font-size: 1.5rem;
      font-weight: 600;
      margin: 0 0 0.5rem 0;
    }

    .error-message {
      color: #6b7280;
      font-size: 1rem;
      line-height: 1.5;
      margin: 0 0 1.5rem 0;
    }

    .error-actions {
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
    }

    .retry-button {
      min-width: 120px;
    }

    .report-button {
      color: #6b7280;
    }

    .error-details {
      margin-top: 1.5rem;
      text-align: left;
    }

    .error-details summary {
      cursor: pointer;
      color: #6b7280;
      font-size: 0.875rem;
      margin-bottom: 0.5rem;
    }

    .error-stack {
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 4px;
      padding: 1rem;
      font-size: 0.75rem;
      overflow-x: auto;
      color: #374151;
      white-space: pre-wrap;
      word-wrap: break-word;
    }

    /* Dark theme support */
    :host-context(.dark-theme) .error-boundary {
      background: #1f1f1f;
      border-color: #333;
    }

    :host-context(.dark-theme) .error-message {
      color: #9ca3af;
    }

    :host-context(.dark-theme) .report-button {
      color: #9ca3af;
    }

    :host-context(.dark-theme) .error-stack {
      background: #111;
      border-color: #333;
      color: #e5e7eb;
    }

    @media (max-width: 480px) {
      .error-boundary {
        padding: 1rem;
      }
      
      .error-actions {
        flex-direction: column;
        align-items: center;
      }
      
      .retry-button,
      .report-button {
        width: 100%;
        max-width: 200px;
      }
    }
  `]
})
export class ErrorBoundaryComponent implements OnInit, OnDestroy {
  @Input() errorTitle = 'Something went wrong';
  @Input() errorMessage = 'An unexpected error occurred. Please try again or contact support if the problem persists.';
  @Input() showTechnicalDetails = false;
  @Input() retryCallback?: () => void;

  hasError = false;
  errorDetails = '';
  environment = environment;

  constructor(private errorLoggingService: ErrorLoggingService) {}

  ngOnInit(): void {
    // Set up error boundary by listening to unhandled errors
    window.addEventListener('error', this.handleError.bind(this));
    window.addEventListener('unhandledrejection', this.handlePromiseRejection.bind(this));
  }

  ngOnDestroy(): void {
    window.removeEventListener('error', this.handleError.bind(this));
    window.removeEventListener('unhandledrejection', this.handlePromiseRejection.bind(this));
  }

  /**
   * Manually trigger error boundary
   */
  showError(error: Error | string, details?: string): void {
    this.hasError = true;
    
    if (typeof error === 'string') {
      this.errorMessage = error;
    } else {
      this.errorMessage = error.message || this.errorMessage;
      this.errorDetails = details || error.stack || '';
    }

    this.errorLoggingService.logError(error, {
      type: 'component_error',
      component: 'error-boundary',
      source: 'manual_trigger'
    });
  }

  /**
   * Reset error boundary
   */
  retry(): void {
    this.hasError = false;
    this.errorDetails = '';
    
    if (this.retryCallback) {
      try {
        this.retryCallback();
      } catch (error) {
        this.showError(error instanceof Error ? error : 'Retry failed');
      }
    } else {
      // Default retry: reload the page
      window.location.reload();
    }
  }

  /**
   * Report error to support
   */
  reportError(): void {
    const errorReport = this.errorLoggingService.exportLogs();
    
    // In a real app, you might:
    // 1. Send to support API
    // 2. Open email client with pre-filled error report
    // 3. Show modal with error report ID
    
    // For now, copy to clipboard
    navigator.clipboard.writeText(errorReport).then(() => {
      alert('Error report copied to clipboard. Please paste this when contacting support.');
    }).catch(() => {
      // Fallback: show the report in a new window
      const reportWindow = window.open('', '_blank');
      if (reportWindow) {
        reportWindow.document.write(`
          <html>
            <head><title>Error Report</title></head>
            <body>
              <h1>Error Report</h1>
              <pre style="white-space: pre-wrap; word-wrap: break-word;">${errorReport}</pre>
            </body>
          </html>
        `);
      }
    });

    this.errorLoggingService.logUserAction('error_reported', {
      timestamp: new Date().toISOString()
    });
  }

  private handleError(event: ErrorEvent): void {
    this.showError(event.error || event.message, event.error?.stack);
  }

  private handlePromiseRejection(event: PromiseRejectionEvent): void {
    const error = event.reason;
    this.showError(
      error instanceof Error ? error : `Promise rejected: ${error}`,
      error instanceof Error ? error.stack : undefined
    );
  }
}