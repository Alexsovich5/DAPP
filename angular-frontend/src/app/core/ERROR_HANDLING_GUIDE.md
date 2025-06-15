# Frontend Error Handling Guide

## Overview

This guide documents the centralized error handling system implemented for the Dinner First Angular application. The system provides consistent, user-friendly error handling across all services and components.

## Architecture

### 1. BaseService (`core/services/base.service.ts`)

All services should extend `BaseService` to get automatic error handling:

```typescript
@Injectable()
export class MyService extends BaseService {
  constructor(private http: HttpClient) {
    super();
  }

  getData(): Observable<DataType> {
    return this.http.get<DataType>('/api/data').pipe(
      catchError(this.handleError<DataType>('get data', []))
    );
  }

  updateData(data: DataType): Observable<DataType> {
    return this.http.post<DataType>('/api/data', data).pipe(
      tap(this.handleSuccess('Data updated', true)),
      catchError(this.handleError<DataType>('update data'))
    );
  }
}
```

**Features:**
- Automatic error message extraction from HTTP responses
- User-friendly error notifications via NotificationService
- Success notifications for important operations
- FastAPI validation error handling
- Network/connectivity error detection

### 2. Global Error Handler (`core/handlers/global-error.handler.ts`)

Catches unhandled JavaScript errors and promise rejections:

```typescript
@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  // Handles runtime errors that aren't caught by services
  // Shows user-friendly notifications for critical errors
}
```

**Registered in:** `app.config.ts`

### 3. Enhanced Notification Service (`core/services/notification.service.ts`)

Extended with convenience methods for different notification types:

```typescript
// Error notifications (5 second duration)
notificationService.showError('Something went wrong');

// Success notifications (3 second duration)
notificationService.showSuccess('Operation completed');

// Warning notifications (4 second duration)
notificationService.showWarning('Please check your input');

// Info notifications (3 second duration)
notificationService.showInfo('New features available');
```

### 4. Toast Component (`shared/components/toast/toast.component.ts`)

Displays notifications as toast messages:
- Auto-hide functionality based on notification type
- Material Design styling
- Mobile-responsive
- Different colors/icons for each notification type
- Manual dismiss capability

### 5. Enhanced API Interceptor (`core/interceptors/api.interceptor.ts`)

Integrated with NotificationService for automatic session management:
- Shows "session expired" notifications on 401 errors
- Automatic logout handling
- CORS error detection

## Error Types Handled

### HTTP Errors
- **400**: Bad Request - "Invalid request. Please check your input"
- **401**: Unauthorized - "Session expired, please log in again"
- **403**: Forbidden - "You don't have permission"
- **404**: Not Found - "Resource not found"
- **409**: Conflict - "Operation conflicts with existing data"
- **422**: Validation - Detailed field-level validation errors
- **429**: Rate Limit - "Too many requests, please wait"
- **500**: Server Error - "Server error, please try again later"
- **503**: Service Unavailable - "Service temporarily unavailable"

### Network Errors
- Connection failures
- CORS issues
- Timeout errors

### JavaScript Runtime Errors
- Unhandled exceptions
- Promise rejections
- Component lifecycle errors

## Implementation Guidelines

### For Services

1. **Extend BaseService:**
```typescript
export class MyService extends BaseService {
  constructor(private http: HttpClient) {
    super();
  }
}
```

2. **Use handleError for all HTTP operations:**
```typescript
return this.http.get<T>('/api/endpoint').pipe(
  catchError(this.handleError<T>('operation name', defaultValue))
);
```

3. **Add success notifications for important operations:**
```typescript
return this.http.post<T>('/api/endpoint', data).pipe(
  tap(this.handleSuccess('Operation completed', true)),
  catchError(this.handleError<T>('operation name'))
);
```

### For Components

1. **Simplified error handling:**
```typescript
// Before (old pattern)
this.service.getData().subscribe({
  next: (data) => {
    this.data = data;
    this.snackBar.open('Success!', 'Close');
  },
  error: (err) => {
    this.error = err.message;
    this.snackBar.open('Error occurred', 'Close');
  }
});

// After (new pattern)
this.service.getData().subscribe({
  next: (data) => {
    if (data) {
      this.data = data;
    }
  },
  error: () => {
    // Error handling is automatic via BaseService
  }
});
```

2. **Loading states:**
```typescript
// Use loading states for better UX
this.isLoading = true;
this.service.getData().subscribe({
  next: (data) => {
    this.data = data;
    this.isLoading = false;
  },
  error: () => {
    this.isLoading = false;
  }
});
```

### Best Practices

1. **Don't duplicate error notifications** - BaseService handles them automatically
2. **Always handle loading states** - Provide feedback to users during async operations
3. **Use meaningful operation names** - They appear in error messages
4. **Provide fallback values** - Use default values for non-critical operations
5. **Test error scenarios** - Verify error handling works as expected

## Migration from Old Error Handling

### Remove Manual Error Handling

**Before:**
```typescript
this.http.get('/api/data').pipe(
  catchError(error => {
    console.error('Error:', error);
    this.snackBar.open('Failed to load data', 'Close');
    return of([]);
  })
);
```

**After:**
```typescript
this.http.get('/api/data').pipe(
  catchError(this.handleError('load data', []))
);
```

### Update Component Subscriptions

**Before:**
```typescript
this.service.updateData(data).subscribe({
  next: (result) => {
    this.snackBar.open('Updated successfully!', 'Close');
    this.router.navigate(['/list']);
  },
  error: (err) => {
    this.error = err.message || 'Update failed';
  }
});
```

**After:**
```typescript
this.service.updateData(data).subscribe({
  next: (result) => {
    if (result) {
      this.router.navigate(['/list']);
    }
  },
  error: () => {
    // Error handling is automatic
  }
});
```

## Services Updated

✅ **ProfileService** - Full BaseService integration with success/error notifications
✅ **DiscoverService** - Error handling and success notifications for profile actions
✅ **SoulConnectionService** - Error handling for connection operations
✅ **NotificationService** - Enhanced with error/success/warning/info methods
✅ **API Interceptor** - Integrated with notification system

## Components Updated

✅ **ProfileEditComponent** - Removed duplicate error handling, leverages BaseService
✅ **App Component** - Added ToastComponent for global notifications

## Testing Error Handling

### Manual Testing

1. **Network Errors:**
   - Disconnect internet and perform actions
   - Verify "network error" notifications appear

2. **API Errors:**
   - Test with invalid data (should show validation errors)
   - Test with expired tokens (should show session expired)

3. **Success Scenarios:**
   - Verify success notifications appear for important operations
   - Check auto-hide functionality

### Automated Testing

```typescript
// Test service error handling
it('should handle errors gracefully', () => {
  const errorResponse = new HttpErrorResponse({
    error: { detail: 'Validation error' },
    status: 422
  });
  
  spyOn(notificationService, 'showError');
  
  service.getData().subscribe();
  
  const req = httpMock.expectOne('/api/data');
  req.flush(null, errorResponse);
  
  expect(notificationService.showError).toHaveBeenCalledWith(
    jasmine.stringContaining('Validation error')
  );
});
```

## Future Enhancements

- **Retry Logic**: Automatic retry for transient errors
- **Offline Detection**: Handle offline/online state changes
- **Error Analytics**: Track error patterns for debugging
- **Progressive Enhancement**: Graceful degradation for critical features
- **Recovery Suggestions**: Provide actionable error recovery options