# Dinner1 Angular Implementation Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technical Stack](#technical-stack)
3. [Getting Started](#getting-started)
4. [Project Structure](#project-structure)
5. [Core Features](#core-features)
6. [Authentication System](#authentication-system)
7. [Data Models](#data-models)
8. [API Integration](#api-integration)
9. [State Management](#state-management)
10. [Styling Guidelines](#styling-guidelines)
11. [Testing](#testing)
12. [Performance Optimization](#performance-optimization)
13. [Deployment](#deployment)
14. [Troubleshooting](#troubleshooting)
15. [Contributing Guidelines](#contributing-guidelines)

## Project Overview

Dinner1 is a dating application focused on matching users based on their dining and food preferences. This Angular implementation is designed with a modular architecture, robust state management, and responsive UI components.

**Key Features:**
- User authentication (registration, login, password recovery)
- Profile management with cuisine and dietary preferences
- Match discovery based on food preferences
- Real-time chat functionality
- Preference settings management
- Responsive UI with Angular Material

## Technical Stack

### Frontend Framework
- **Angular 17+** (Standalone Components Architecture)
- **TypeScript 5.2+**

### UI Components
- **Angular Material** - Comprehensive UI component library
- **Material Icons** - Icon system

### State Management
- **RxJS** - Reactive programming library
- **Angular Services** - For feature-specific state

### Form Management
- **Angular Reactive Forms** - For complex form handling and validation

### Routing
- **Angular Router** - For navigation and route protection

### HTTP Client
- **Angular HttpClient** - For API communication with interceptors

### Testing
- **Jasmine** - Testing framework
- **Karma** - Test runner
- **Cypress** (optional) - End-to-end testing

### Build Tools
- **Angular CLI** - Project scaffolding and build management
- **Webpack** (integrated with Angular CLI) - Module bundling

## Getting Started

### Prerequisites
- Node.js (v18.13.0 or higher)
- npm (v9.0.0 or higher)
- Angular CLI (latest version)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-organization/dinner1-app.git
cd dinner1-app/interface/Angular
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
   - Copy `src/environments/environment.template.ts` to `src/environments/environment.ts`
   - Fill in the required API endpoints and configuration

4. Start the development server:
```bash
npm start
```

5. Open your browser and navigate to `http://localhost:4200`

## Project Structure

The application follows a feature-based structure:

```
src/
├── app/
│   ├── core/             # Core functionality (services, interceptors, guards)
│   │   ├── interceptors/  # HTTP interceptors
│   │   ├── interfaces/    # Core interfaces
│   │   ├── services/      # Singleton services
│   │   └── guards/        # Route guards
│   ├── features/         # Feature modules
│   │   ├── auth/          # Authentication feature
│   │   ├── profile/       # Profile management
│   │   ├── discover/      # Match discovery
│   │   ├── chat/          # Messaging system
│   │   └── preferences/   # User preferences
│   ├── shared/           # Shared components, directives, pipes
│   │   ├── components/    # Reusable components
│   │   ├── directives/    # Custom directives
│   │   └── pipes/         # Custom pipes
│   ├── models/           # Data models and interfaces
│   └── utils/            # Utility functions
├── assets/               # Static assets
│   ├── images/           # Image assets
│   └── icons/            # Icon assets
└── environments/         # Environment configuration
```

## Core Features

### Landing Page
The public-facing introduction to the application with:
- Feature showcase
- User testimonials
- Registration call-to-action
- Login access

### Authentication System
Complete authentication flow with:
- User registration with email verification
- Login with session management
- Password recovery
- Protected routes using Angular Guards

### Profile Management
User profile system including:
- Profile creation and editing
- Profile photo upload and management
- Bio and personal information management
- Profile completion tracking

### Discovery System
Match discovery based on food preferences:
- Preference-based algorithm
- Card-based UI for potential matches
- Like/Dislike functionality
- Match confirmation system

### Chat Functionality
Real-time chat system between matched users:
- Message list view
- Conversation threads
- Real-time updates
- Message status indicators

### Preferences Management
Comprehensive preferences system:
- Food preferences (cuisines, dining styles)
- Dietary restrictions
- Location-based preferences
- Dating preferences (age, gender, etc.)

## Authentication System

### Implementation Details

The authentication system is built around:

1. **AuthService** (`src/app/core/services/auth.service.ts`):
   - Handles authentication operations (login, register, logout)
   - Manages tokens and session state
   - Exposes authentication status via observables

2. **AuthGuard** (`src/app/core/guards/auth.guard.ts`):
   - Protects routes from unauthorized access
   - Redirects to login when authentication is required

3. **Auth Interceptor** (`src/app/core/interceptors/api.interceptor.ts`):
   - Attaches authentication tokens to outgoing requests
   - Handles token refresh
   - Processes authentication errors (401, 403)

### Token Storage

Authentication tokens are stored securely using:
- `localStorage` for persistent sessions
- In-memory storage for session-only authentication

### Authentication Flow

1. **Registration Process**:
   - User submits registration form with email, password, and basic profile information
   - Backend validates and creates account
   - User receives verification email (optional)
   - Upon verification, user can log in

2. **Login Process**:
   - User submits credentials
   - Backend validates and returns tokens
   - Tokens are stored appropriately
   - User is redirected to the protected area

3. **Logout Process**:
   - User initiates logout
   - Tokens are cleared
   - User is redirected to the landing page

## Data Models

### User Model
```typescript
interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  profile_picture?: string;
  date_of_birth: string;
  gender: string;
  is_profile_complete: boolean;
  bio?: string;
  interests?: string[];
  dietary_preferences?: string[];
  location_preferences?: LocationPreferences;
  match_preferences?: MatchPreferences;
  created_at?: string;
  updated_at?: string;
}
```

### Profile Model
```typescript
interface Profile {
  user_id: string;
  bio: string;
  profile_photo: string;
  gallery_photos: string[];
  dietary_preferences: string[];
  cuisine_preferences: string[];
  location: string;
  is_complete: boolean;
}
```

### Message Model
```typescript
interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  timestamp: string;
  read: boolean;
}
```

### Match Model
```typescript
interface Match {
  id: string;
  user_id: string;
  matched_user_id: string;
  status: 'pending' | 'matched' | 'rejected';
  created_at: string;
}
```

## API Integration

### API Service Structure

The application uses a hierarchical service structure:
- **BaseApiService**: Provides common HTTP functionality
- Feature-specific services (UserService, ProfileService, etc.)

### Interceptors

1. **API Interceptor** (`src/app/core/interceptors/api.interceptor.ts`):
   - Adds authentication headers to all API requests
   - Handles CORS preflight requests properly
   - Formats error responses for consistency
   - Manages retries for transient errors

2. **Error Interceptor**:
   - Captures and processes HTTP errors
   - Transforms errors into user-friendly messages
   - Triggers global error handling

### Error Handling

The application implements a centralized error handling strategy:
- HTTP error interceptors capture API errors
- ErrorService processes and categorizes errors
- UI components display appropriate error messages
- Serious errors are logged for troubleshooting

## State Management

### Service-Based State

The application uses Angular services with RxJS for state management:
- Feature-specific services maintain feature state
- BehaviorSubject/ReplaySubject store state values
- Components subscribe to state observables

Example pattern:
```typescript
@Injectable({
  providedIn: 'root'
})
export class ProfileService {
  private profileSubject = new BehaviorSubject<Profile | null>(null);
  public profile$ = this.profileSubject.asObservable();
  
  // State mutation methods
  updateProfile(profile: Profile): Observable<Profile> {
    return this.http.put<Profile>('/api/profile', profile).pipe(
      tap(updatedProfile => this.profileSubject.next(updatedProfile))
    );
  }
}
```

### State Persistence

- User session state is persisted in localStorage
- Application preferences use localStorage with fallback
- Form data uses session storage for multi-step forms

## Styling Guidelines

### CSS Architecture

The application follows a component-scoped CSS approach:
- Component styles in `.scss` files
- Global styles in `src/styles.scss`
- Theming variables in separate files
- Angular Material customization via theme files

### Responsive Design

- Mobile-first approach
- Responsive breakpoints for different device sizes
- Flexbox and CSS Grid for layouts
- Conditional rendering based on screen size

### Theme System

The application uses Angular Material's theming system:
- Primary, accent, and warn color palettes
- Light and dark theme options
- Typography scale
- Custom component themes

## Testing

### Unit Testing

- Services and components have unit tests
- Jasmine for test framework
- Test doubles (mocks, stubs, spies) for dependencies
- Coverage requirements (min 80% for critical paths)

### Integration Testing

- Feature level tests
- Testing component interactions
- Form validation testing
- HTTP request/response testing

### E2E Testing

- Critical user flows (registration, login, matching)
- Navigation testing
- Cross-browser compatibility

## Performance Optimization

### Loading Strategies

- Lazy loading for feature modules
- Preloading for critical modules
- Code splitting for optimal bundle sizes

### Rendering Optimization

- OnPush change detection for performance
- Virtual scrolling for large lists
- Optimized Angular Material usage
- Memoization for expensive computations

### Network Optimization

- Request caching strategies
- Optimized HTTP polling
- Compressed assets (images, etc.)
- GraphQL considerations (if applicable)

## Deployment

### Build Configuration

- Environment-specific configuration
- Production build optimizations
- Bundle analysis

### Deployment Options

- Static hosting (AWS S3, Netlify, etc.)
- Server deployment (Node.js express server)
- Containerized deployment (Docker)

### CI/CD Pipeline

- Automated testing in pipeline
- Build verification
- Deployment automation
- Environment promotion strategy

## Troubleshooting

### Common Issues

1. **Authentication Problems**:
   - Token expiration issues
   - CORS configuration
   - Cookie settings

2. **Performance Issues**:
   - Change detection loops
   - Memory leaks from unsubscribed observables
   - Large component trees

3. **API Communication**:
   - Network timeouts
   - API versioning conflicts
   - Payload format issues

### Debugging Tools

- Angular DevTools browser extension
- RxJS debugging techniques
- Network request inspection
- Error logging system

## Contributing Guidelines

### Code Standards

- Follow Angular style guide
- Use ESLint and Prettier for code quality
- Follow naming conventions
- Document public APIs

### Pull Request Process

1. Create feature branches from develop
2. Follow conventional commits
3. Ensure tests pass
4. Require code review before merging
5. Squash commits on merge

### Development Workflow

1. Pick up issues from the board
2. Local development with proper configuration
3. Implement with tests
4. Submit PR with description
5. Address review feedback
6. Merge when approved