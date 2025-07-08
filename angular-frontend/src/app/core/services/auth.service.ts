import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError, catchError, tap, map } from 'rxjs';
import { RegisterData, User, LoginResponse, ApiErrorResponse } from '@core/interfaces/auth.interfaces';
import { environment } from '@environments/environment';
import { StorageService } from '@core/services/storage.service';

/**
 * Authentication service for the Dinner1 "Soul Before Skin" dating application.
 * 
 * Handles user authentication, registration, and session management with:
 * - JWT token-based authentication
 * - Secure local storage of user data
 * - Reactive user state management
 * - Comprehensive error handling
 * 
 * @example
 * ```typescript
 * constructor(private authService: AuthService) {
 *   this.authService.currentUser$.subscribe(user => {
 *     if (user) {
 *       console.log('User logged in:', user.email);
 *     }
 *   });
 * }
 * ```
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiUrl = environment.apiUrl;
  private readonly currentUserSubject = new BehaviorSubject<User | null>(null);
  readonly currentUser$ = this.currentUserSubject.asObservable();

  constructor(
    private readonly http: HttpClient,
    private readonly storage: StorageService
  ) {
    this.loadStoredUser();
  }

  private loadStoredUser(): void {
    const storedUser = this.storage.getJson<User>('user');
    if (storedUser) {
      this.currentUserSubject.next(storedUser);
    }
  }

  /**
   * Authenticates a user with email and password.
   * 
   * Uses OAuth2PasswordRequestForm format expected by FastAPI backend.
   * On successful login, stores user data and JWT token in local storage.
   * 
   * @param email - User's email address
   * @param password - User's password
   * @returns Observable<LoginResponse> containing user data and access token
   * 
   * @example
   * ```typescript
   * this.authService.login('user@example.com', 'password123').subscribe({
   *   next: (response) => console.log('Login successful', response.user),
   *   error: (error) => console.error('Login failed', error)
   * });
   * ```
   */
  login(email: string, password: string): Observable<LoginResponse> {
    // OAuth2PasswordRequestForm expects form data with 'username' and 'password' fields
    const body = new URLSearchParams();
    body.set('username', email); // Backend accepts email as username
    body.set('password', password);

    const headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    };

    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/login`, body.toString(), { headers }).pipe(
      tap(response => {
        if (response.user) {
          this.storage.setJson('user', response.user);
          this.storage.setItem('token', response.access_token);
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
          this.storage.setJson('user', response.user);
          this.storage.setItem('token', response.access_token);
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
    this.storage.removeItem('user');
    this.storage.removeItem('token');
    this.currentUserSubject.next(null);
  }

  getToken(): string | null {
    return this.storage.getItem('token');
  }

  isAuthenticated(): boolean {
    return !!this.currentUserSubject.value;
  }

  isLoggedIn(): Observable<boolean> {
    return this.currentUser$.pipe(
      map(user => !!user)
    );
  }

  updateCurrentUser(user: User): void {
    this.storage.setJson('user', user);
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
