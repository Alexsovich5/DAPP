# Angular Architecture Guidelines

## Component Architecture Decision

**Decision**: Use **Standalone Components** as the primary architectural pattern for this application.

### Rationale

1. **Modern Angular**: Standalone components are the recommended approach in Angular 14+ and the future direction
2. **Simplicity**: Reduces boilerplate code and module complexity
3. **Tree-shaking**: Better bundle optimization
4. **Developer Experience**: Easier to understand and maintain
5. **Performance**: Faster compilation and better lazy loading

### Implementation Guidelines

#### ✅ Use Standalone Components For:
- **All feature components** (auth, profile, discover, etc.)
- **Shared components** (navigation, toast, theme-toggle)
- **Page-level components** (landing, settings, preferences)
- **Small utility components**

#### ⚠️ Consider Modules Only For:
- **Complex feature sets** with multiple related components (rare cases)
- **Third-party library integration** that requires module configuration
- **Legacy code migration** (temporary only)

### Code Standards

#### Component Template
```typescript
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
// Import other required modules/components

@Component({
  selector: 'app-example',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    // Other imports
  ],
  template: `<!-- template -->`,
  styleUrls: ['./example.component.scss']
})
export class ExampleComponent {
  // Component logic
}
```

#### Routing Configuration
```typescript
// Use loadComponent for standalone components
{
  path: 'feature',
  loadComponent: () => import('./feature/feature.component').then(m => m.FeatureComponent)
}
```

### Migration Strategy

1. **Phase 1**: Remove unused `.module.ts` files ✅
2. **Phase 2**: Update routing to use `loadComponent` ✅  
3. **Phase 3**: Ensure all components follow standalone pattern ✅
4. **Phase 4**: Update documentation and guidelines ✅

### Benefits Achieved

- **Reduced bundle size**: Eliminated module overhead
- **Improved DX**: Less configuration required
- **Better performance**: Enhanced lazy loading
- **Future-proof**: Aligned with Angular's direction
- **Easier testing**: Simplified component testing

### Directory Structure

```
src/app/
├── core/                    # Core services and guards
├── shared/                  # Shared standalone components
│   └── components/          # Reusable UI components
├── features/                # Feature standalone components
│   ├── auth/               # Authentication components
│   ├── profile/            # Profile management
│   ├── discover/           # User discovery
│   └── ...                 # Other features
└── layout/                 # Layout components
```

### Import Consistency

- Use absolute imports from `src/app/` root when possible
- Keep relative imports for closely related files
- Prefer TypeScript path mapping for clean imports

### Testing Guidelines

- Test standalone components in isolation
- Mock dependencies using Angular testing utilities
- Use component test harnesses for complex interactions