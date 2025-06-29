import { Injectable } from '@angular/core';
import { environment } from '@environments/environment';

export interface ErrorLog {
  timestamp: Date;
  level: 'error' | 'warn' | 'info' | 'debug';
  message: string;
  error?: Error;
  context?: Record<string, any>;
  userId?: string;
  url?: string;
  userAgent?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ErrorLoggingService {
  private readonly maxLogs = 1000;
  private logs: ErrorLog[] = [];

  constructor() {}

  /**
   * Log an error with full context information
   */
  logError(error: Error | string, context?: Record<string, any>): void {
    const errorLog: ErrorLog = {
      timestamp: new Date(),
      level: 'error',
      message: typeof error === 'string' ? error : error.message,
      error: typeof error === 'string' ? undefined : error,
      context,
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    this.addLog(errorLog);
    
    // Log to console in development
    if (!environment.production) {
      console.error('Error logged:', errorLog);
    }
    
    // In production, you might send to a logging service
    if (environment.production) {
      this.sendToLoggingService(errorLog);
    }
  }

  /**
   * Log a warning message
   */
  logWarning(message: string, context?: Record<string, any>): void {
    const warningLog: ErrorLog = {
      timestamp: new Date(),
      level: 'warn',
      message,
      context,
      url: window.location.href
    };

    this.addLog(warningLog);
    
    if (!environment.production) {
      console.warn('Warning logged:', warningLog);
    }
  }

  /**
   * Log an info message
   */
  logInfo(message: string, context?: Record<string, any>): void {
    const infoLog: ErrorLog = {
      timestamp: new Date(),
      level: 'info',
      message,
      context,
      url: window.location.href
    };

    this.addLog(infoLog);
    
    if (!environment.production) {
      console.info('Info logged:', infoLog);
    }
  }

  /**
   * Log API errors with additional context
   */
  logApiError(
    endpoint: string, 
    status: number, 
    error: any, 
    requestData?: any
  ): void {
    this.logError(error, {
      type: 'api_error',
      endpoint,
      status,
      requestData,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Log user action for debugging
   */
  logUserAction(action: string, data?: any): void {
    this.logInfo(`User action: ${action}`, {
      type: 'user_action',
      action,
      data,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Get recent logs for debugging
   */
  getRecentLogs(count: number = 50): ErrorLog[] {
    return this.logs.slice(-count);
  }

  /**
   * Clear all logs
   */
  clearLogs(): void {
    this.logs = [];
  }

  /**
   * Export logs as JSON for support
   */
  exportLogs(): string {
    return JSON.stringify({
      timestamp: new Date().toISOString(),
      logs: this.logs,
      environment: {
        production: environment.production,
        userAgent: navigator.userAgent,
        url: window.location.href
      }
    }, null, 2);
  }

  private addLog(log: ErrorLog): void {
    this.logs.push(log);
    
    // Keep only the most recent logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }
  }

  private sendToLoggingService(log: ErrorLog): void {
    // In a real application, you would send logs to a service like:
    // - Sentry
    // - LogRocket
    // - DataDog
    // - Custom logging endpoint
    
    // For now, we'll just store in localStorage as a fallback
    try {
      const storedLogs = JSON.parse(localStorage.getItem('error_logs') || '[]');
      storedLogs.push(log);
      
      // Keep only last 100 logs in storage
      const recentLogs = storedLogs.slice(-100);
      localStorage.setItem('error_logs', JSON.stringify(recentLogs));
    } catch (error) {
      console.error('Failed to store error log:', error);
    }
  }
}