import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError, catchError, tap } from 'rxjs';
import { RegisterData, User, LoginResponse, ApiErrorResponse } from '../interfaces/auth.interfaces';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiUrl = environment.apiUrl;
  private readonly currentUserSubject = new BehaviorSubject<User | null>(null);
  readonly currentUser$ = this.currentUserSubject.asObservable();

  constructor(private readonly http: HttpClient) {
    this.loadStoredUser();
  }

  private loadStoredUser(): void {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        this.currentUserSubject.next(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem('user');
      }
    }
  }

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/login`, { email, password }).pipe(
      tap(response => {
        if (response.user) {
          localStorage.setItem('user', JSON.stringify(response.user));
          localStorage.setItem('token', response.access_token);
          this.currentUserSubject.next(response.user);
        }
      }),
      catchError(this.handleError)
    );
  }

  register(userData: RegisterData): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/register`, userData).pipe(
      tap(response => {
        // Registration now returns LoginResponse, so automatically log the user in
        if (response.user && response.access_token) {
          localStorage.setItem('user', JSON.stringify(response.user));
          localStorage.setItem('token', response.access_token);
          this.currentUserSubject.next(response.user);
        }
      }),
      catchError(this.handleError)
    );
  }

  forgotPassword(email: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/auth/forgot-password`, { email }).pipe(
      catchError(this.handleError)
    );
  }

  logout(): void {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    this.currentUserSubject.next(null);
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  isAuthenticated(): boolean {
    return !!this.currentUserSubject.value;
  }

  updateCurrentUser(user: User): void {
    localStorage.setItem('user', JSON.stringify(user));
    this.currentUserSubject.next(user);
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An unknown error occurred';

    if (error.status === 422) {
      // Handle validation errors
      const validationErrors = error.error?.detail || [];
      if (Array.isArray(validationErrors) && validationErrors.length) {
        errorMessage = validationErrors.map((err: any) =>
          `${err.loc.slice(1).join('.')}: ${err.msg}`
        ).join(', ');
      } else {
        errorMessage = 'Validation error: Please check your input data';
      }
    } else if (error.error?.detail) {
      // Handle other API errors with detail
      errorMessage = typeof error.error.detail === 'string'
        ? error.error.detail
        : 'Server error occurred';
    } else if (error.message) {
      errorMessage = error.message;
    }

    console.error('Auth service error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
