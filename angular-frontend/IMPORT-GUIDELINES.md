# Import Path Guidelines

## TypeScript Path Mapping

The project uses TypeScript path mapping for cleaner, more maintainable imports. The following aliases are configured:

```typescript
{
  "@app/*": ["app/*"],
  "@core/*": ["app/core/*"],
  "@shared/*": ["app/shared/*"],
  "@features/*": ["app/features/*"],
  "@environments/*": ["environments/*"]
}
```

## Import Rules

### ✅ Preferred Import Patterns

#### 1. Use Path Aliases for Cross-Directory Imports
```typescript
// ✅ Good - Using path aliases
import { AuthService } from '@core/services/auth.service';
import { environment } from '@environments/environment';
import { ToastComponent } from '@shared/components/toast/toast.component';
import { LoginComponent } from '@features/auth/login/login.component';
```

#### 2. Use Relative Imports for Same Directory
```typescript
// ✅ Good - Same directory
import { StorageService } from './storage.service';
import { User } from './auth.interfaces';
```

#### 3. Use Relative Imports for Closely Related Files
```typescript
// ✅ Good - Parent/child relationship
import { ProfileEditComponent } from './profile-edit/profile-edit.component';
import { ProfileViewComponent } from './profile-view/profile-view.component';
```

### ❌ Avoid These Patterns

#### 1. Deep Relative Paths
```typescript
// ❌ Bad - Hard to maintain
import { AuthService } from '../../../core/services/auth.service';
import { environment } from '../../../environments/environment';
```

#### 2. Mixing Patterns Inconsistently
```typescript
// ❌ Bad - Inconsistent
import { AuthService } from '@core/services/auth.service';
import { ThemeService } from '../services/theme.service'; // Should use @core
```

#### 3. Using Absolute Paths for Same Directory
```typescript
// ❌ Bad - Unnecessary
import { StorageService } from '@core/services/storage.service';
// When in the same services directory, use:
import { StorageService } from './storage.service';
```

## Directory-Specific Guidelines

### Core Services (`app/core/`)
```typescript
// From core services to other core
import { StorageService } from './storage.service';

// From core to interfaces
import { User } from '@core/interfaces/auth.interfaces';

// From core to environment
import { environment } from '@environments/environment';
```

### Feature Components (`app/features/`)
```typescript
// From feature to core services
import { AuthService } from '@core/services/auth.service';

// From feature to shared components
import { ToastComponent } from '@shared/components/toast/toast.component';

// Within same feature
import { LoginComponent } from './login/login.component';

// From feature to environment
import { environment } from '@environments/environment';
```

### Shared Components (`app/shared/`)
```typescript
// From shared to core
import { NotificationService } from '@core/services/notification.service';

// Within shared
import { ThemeToggleComponent } from '../theme-toggle/theme-toggle.component';
```

## Benefits

1. **Maintainability**: Easy to refactor directory structures
2. **Readability**: Clear understanding of import relationships
3. **IDE Support**: Better autocomplete and navigation
4. **Consistency**: Uniform import patterns across the codebase
5. **Reduced Errors**: Less chance of broken imports when moving files

## Migration Strategy

When updating existing imports:

1. **Cross-directory imports**: Convert to path aliases (`@core`, `@shared`, etc.)
2. **Same directory imports**: Keep as relative (`./filename`)
3. **Parent/child imports**: Use relative paths (`./child/component`)
4. **Environment imports**: Always use `@environments/environment`

## Examples by Component Type

### Service Files
```typescript
// auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { User } from '@core/interfaces/auth.interfaces'; // Cross-directory
import { StorageService } from './storage.service'; // Same directory
import { environment } from '@environments/environment'; // Environment
```

### Component Files
```typescript
// profile.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '@core/services/auth.service'; // Core service
import { ToastComponent } from '@shared/components/toast/toast.component'; // Shared
import { ProfileEditComponent } from './profile-edit/profile-edit.component'; // Child
```

### Feature Components
```typescript
// discover.component.ts
import { Component } from '@angular/core';
import { DiscoverService } from '@core/services/discover.service'; // Core
import { SoulConnection } from '@core/interfaces/soul-connection.interfaces'; // Interface
import { environment } from '@environments/environment'; // Environment
```

This approach creates a scalable, maintainable import structure that grows with the application.