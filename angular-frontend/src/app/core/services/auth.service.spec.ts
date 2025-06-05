import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';
import { User, LoginResponse, RegisterData } from '../interfaces/auth.interfaces';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  // Mock user data
  const mockUser: User = {
    id: '1',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    date_of_birth: '1990-01-01',
    gender: 'male',
    is_profile_complete: false
  };

  const mockLoginResponse: LoginResponse = {
    access_token: 'mock-jwt-token',
    token_type: 'bearer',
    user: mockUser
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AuthService]
    });

    // Clear localStorage before each test
    localStorage.clear();

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    // Verify that no unmatched requests are outstanding
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('login', () => {
    it('should authenticate user and store user data in localStorage on successful login', () => {
      const email = 'test@example.com';
      const password = 'password123';

      service.login(email, password).subscribe(response => {
        expect(response).toEqual(mockLoginResponse);
        expect(localStorage.getItem('token')).toBe(mockLoginResponse.access_token);
        expect(localStorage.getItem('user')).toBe(JSON.stringify(mockLoginResponse.user));
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ email, password });
      req.flush(mockLoginResponse);
    });

    it('should handle login error', () => {
      const email = 'test@example.com';
      const password = 'wrong-password';
      const errorResponse = {
        status: 401,
        statusText: 'Unauthorized',
        error: { detail: 'Invalid credentials' }
      };

      service.login(email, password).subscribe({
        next: () => fail('Expected an error, not a successful response'),
        error: error => {
          expect(error.message).toContain('Invalid credentials');
          expect(localStorage.getItem('token')).toBeNull();
          expect(localStorage.getItem('user')).toBeNull();
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
      req.flush(errorResponse.error, errorResponse);
    });

    it('should handle validation errors during login', () => {
      const email = 'invalid-email';
      const password = '';
      const validationErrorResponse = {
        status: 422,
        statusText: 'Unprocessable Entity',
        error: {
          detail: [
            { loc: ['body', 'email'], msg: 'invalid email format', type: 'value_error' },
            { loc: ['body', 'password'], msg: 'field required', type: 'value_error.missing' }
          ]
        }
      };

      service.login(email, password).subscribe({
        next: () => fail('Expected an error, not a successful response'),
        error: error => {
          expect(error.message).toContain('email: invalid email format');
          expect(error.message).toContain('password: field required');
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
      req.flush(validationErrorResponse.error, validationErrorResponse);
    });
  });

  describe('register', () => {
    it('should register a new user successfully', () => {
      const registerData: RegisterData = {
        email: 'new@example.com',
        password: 'password123',
        first_name: 'New',
        last_name: 'User',
        date_of_birth: '1995-05-15',
        gender: 'female'
      };

      service.register(registerData).subscribe(response => {
        expect(response).toEqual(mockLoginResponse);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/register`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(registerData);
      req.flush(mockLoginResponse);
    });

    it('should handle registration errors', () => {
      const registerData: RegisterData = {
        email: 'existing@example.com',
        password: 'password123',
        first_name: 'New',
        last_name: 'User',
        date_of_birth: '1995-05-15',
        gender: 'female'
      };

      const errorResponse = {
        status: 400,
        statusText: 'Bad Request',
        error: { detail: 'Email already registered' }
      };

      service.register(registerData).subscribe({
        next: () => fail('Expected an error, not a successful response'),
        error: error => {
          expect(error.message).toContain('Email already registered');
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/register`);
      req.flush(errorResponse.error, errorResponse);
    });
  });

  describe('forgotPassword', () => {
    it('should send password reset request', () => {
      const email = 'test@example.com';
      const mockResponse = { message: 'Password reset link sent to your email' };

      service.forgotPassword(email).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/forgot-password`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ email });
      req.flush(mockResponse);
    });
  });

  describe('logout', () => {
    it('should clear user data from localStorage and update currentUserSubject', () => {
      // Set up initial state
      localStorage.setItem('token', 'test-token');
      localStorage.setItem('user', JSON.stringify(mockUser));

      // Force reload of user from localStorage
      service['loadStoredUser']();

      // Verify user is loaded
      service.currentUser$.subscribe(user => {
        expect(user).toEqual(mockUser);
      }).unsubscribe();

      // Perform logout
      service.logout();

      // Verify state after logout
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();

      service.currentUser$.subscribe(user => {
        expect(user).toBeNull();
      }).unsubscribe();
    });
  });

  describe('getToken', () => {
    it('should return token from localStorage', () => {
      localStorage.setItem('token', 'test-token');
      expect(service.getToken()).toBe('test-token');
    });

    it('should return null if no token in localStorage', () => {
      expect(service.getToken()).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true if user is authenticated', () => {
      // Set user in the service
      localStorage.setItem('user', JSON.stringify(mockUser));
      service['loadStoredUser']();

      expect(service.isAuthenticated()).toBe(true);
    });

    it('should return false if user is not authenticated', () => {
      expect(service.isAuthenticated()).toBe(false);
    });
  });

  describe('loadStoredUser', () => {
    it('should load user from localStorage on initialization', () => {
      localStorage.setItem('user', JSON.stringify(mockUser));

      // Create a new instance to test initialization
      const newService = TestBed.inject(AuthService);

      newService.currentUser$.subscribe(user => {
        expect(user).toEqual(mockUser);
      }).unsubscribe();
    });

    it('should handle invalid JSON in localStorage', () => {
      localStorage.setItem('user', 'invalid-json');

      // Create a new instance to test initialization
      const newService = TestBed.inject(AuthService);

      newService.currentUser$.subscribe(user => {
        expect(user).toBeNull();
      }).unsubscribe();

      expect(localStorage.getItem('user')).toBeNull();
    });
  });
});
