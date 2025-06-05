import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandlerFn,
  HttpEvent,
  HttpInterceptorFn,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { inject } from '@angular/core';
import { environment } from '../../../environments/environment';
import { AuthService } from '../services/auth.service';

export const ApiInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn): Observable<HttpEvent<unknown>> => {
  const authService = inject(AuthService);

  // Check if the request is going to our API
  if (req.url.includes(environment.apiUrl)) {
    // Get the auth token if available
    const token = authService.getToken();

    // Handle OPTIONS requests specially to avoid CORS issues
    if (req.method === 'OPTIONS') {
      // Don't modify OPTIONS requests - let them pass through
      return next(req);
    } else {
      // For non-OPTIONS requests, add standard headers
      const headers: { [key: string]: string } = {
        'Accept': 'application/json'
      };

      // Only add Content-Type for requests that have a body
      if (req.body !== null && req.method !== 'GET' && req.method !== 'DELETE') {
        headers['Content-Type'] = 'application/json';
      }

      // Add authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      req = req.clone({
        setHeaders: headers,
        // Only use withCredentials if your FastAPI backend supports it
        // Remove this line if you're getting CORS errors
        withCredentials: false
      });
    }
  }

  // Process the request and handle errors
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMsg = '';

      // Handle CORS errors specifically
      if (error.status === 0 && error.error instanceof ProgressEvent) {
        errorMsg = 'Network error - please check if the backend server is running and CORS is properly configured';
        console.error('CORS or Network Error:', error);
        return throwError(() => new Error(errorMsg));
      }

      // Handle validation errors from FastAPI
      if (error.status === 422) {
        // FastAPI returns validation errors in a specific format
        const validationErrors = error.error?.detail || [];
        if (validationErrors.length) {
          errorMsg = validationErrors.map((err: any) =>
            `${err.loc.join('.')}: ${err.msg}`
          ).join(', ');
        } else {
          errorMsg = 'Validation error: Please check your input data';
        }
      } else if (error.error instanceof ErrorEvent) {
        // Client-side error
        errorMsg = `Error: ${error.error.message}`;
      } else {
        // Server-side error
        errorMsg = `Error Code: ${error.status}, Message: ${error.message || error.error?.detail || 'Unknown error'}`;

        // Handle authentication errors
        if (error.status === 401) {
          authService.logout();
        }
      }

      console.error('API Error:', error);
      return throwError(() => new Error(errorMsg));
    })
  );
};
