# Development Guide - Dinner1 "Soul Before Skin" Dating App

## Overview

This guide provides comprehensive instructions for developing and maintaining the Dinner1 dating application, which prioritizes emotional connections through progressive revelation before physical attraction.

## Architecture Overview

### Core Components
- **backend_py/**: FastAPI REST API with SQLAlchemy ORM and JWT authentication
- **angular-frontend/**: Angular 19+ standalone components with SSR support
- **PostgreSQL**: Database with emotional profiling and soul connection models

### Key Features
- **Soul Before Skin**: Progressive revelation over 7-day cycles
- **Local Algorithms**: Compatibility scoring without external AI dependencies
- **Error Boundaries**: Comprehensive error handling and logging
- **TypeScript Path Mapping**: Clean import paths with aliases

## Environment Setup

### Prerequisites
- Node.js 18+ with npm
- Python 3.11+ with pip
- PostgreSQL 13+
- Git

### Backend Setup
```bash
cd backend_py
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
createdb dinner1
alembic upgrade head

# Run development server
python run.py  # Runs on http://localhost:5000
```

### Frontend Setup
```bash
cd angular-frontend
npm install
ng serve --port 5001  # Must use port 5001 for CORS
```

### Environment Variables
Create `.env` in `backend_py/`:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dinner1
SECRET_KEY=your_jwt_secret_here
CORS_ORIGINS=http://localhost:4200,http://localhost:5001
COMPATIBILITY_THRESHOLD=50
REVELATION_CYCLE_DAYS=7
```

## Code Architecture Standards

### Angular Components
- **Use Standalone Components**: All components should be standalone
- **TypeScript Path Mapping**: Use path aliases for clean imports
- **Error Boundaries**: Wrap complex components with error boundaries

Example component structure:
```typescript
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '@core/services/auth.service';
import { ErrorBoundaryComponent } from '@shared/components/error-boundary/error-boundary.component';

@Component({
  selector: 'app-example',
  standalone: true,
  imports: [CommonModule, ErrorBoundaryComponent],
  template: `
    <app-error-boundary [retryCallback]="retryOperation">
      <!-- Component content -->
    </app-error-boundary>
  `
})
export class ExampleComponent implements OnInit {
  constructor(private authService: AuthService) {}
  
  retryOperation = (): void => {
    // Retry logic
  }
}
```

### FastAPI Backend
- **Dependency Injection**: Use FastAPI's dependency system
- **Pydantic Models**: All request/response models use Pydantic
- **Error Handling**: Consistent error responses with proper HTTP status codes

Example API endpoint:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.soul_connection import SoulConnectionCreate, SoulConnectionResponse

router = APIRouter()

@router.post("/connections", response_model=SoulConnectionResponse)
async def create_soul_connection(
    connection_data: SoulConnectionCreate,
    db: Session = Depends(get_db)
):
    try:
        # Implementation
        return connection
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Import Path Standards

### TypeScript Path Mapping
Use these aliases for clean imports:
```typescript
import { AuthService } from '@core/services/auth.service';
import { ErrorBoundaryComponent } from '@shared/components/error-boundary/error-boundary.component';
import { User } from '@core/interfaces/auth.interfaces';
import { environment } from '@environments/environment';
```

### Avoid Relative Imports
❌ **Don't use**: `import { AuthService } from '../../../core/services/auth.service';`
✅ **Use**: `import { AuthService } from '@core/services/auth.service';`

## Error Handling Best Practices

### Global Error Handler
The application uses a global error handler that:
- Logs all errors for debugging
- Shows user-friendly notifications
- Handles HTTP errors appropriately
- Integrates with the error logging service

### Error Boundaries
Wrap complex components with error boundaries:
```typescript
<app-error-boundary 
  [retryCallback]="retryOperation"
  errorTitle="Custom Error Title"
  errorMessage="Custom error message">
  <!-- Component content -->
</app-error-boundary>
```

### API Error Handling
Services extend BaseService for consistent error handling:
```typescript
export class ExampleService extends BaseService {
  getData() {
    return this.http.get<Data>('/api/data')
      .pipe(
        catchError(this.handleError<Data>('getData', []))
      );
  }
}
```

## Database Management

### Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Model Relationships
Follow the soul connection model pattern:
```python
class SoulConnection(Base):
    __tablename__ = "soul_connections"
    
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, ForeignKey("users.id"))
    user2_id = Column(Integer, ForeignKey("users.id"))
    connection_stage = Column(String(30), default="soul_discovery")
    compatibility_score = Column(Numeric(5, 2))
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
```

## Testing Standards

### Angular Testing
```bash
ng test  # Run unit tests
ng e2e   # Run e2e tests
```

### Python Testing
```bash
pytest  # Run all tests
pytest tests/test_auth.py  # Run specific test file
pytest -v  # Verbose output
```

### Test Structure
```typescript
describe('ExampleComponent', () => {
  let component: ExampleComponent;
  let fixture: ComponentFixture<ExampleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExampleComponent]  // Standalone component
    }).compileComponents();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
```

## Performance Optimization

### Angular Optimization
- Use OnPush change detection strategy
- Implement TrackBy functions for *ngFor
- Lazy load feature modules
- Use Angular's built-in performance tools

### Backend Optimization
- Use database indexes for frequently queried fields
- Implement query optimization for N+1 problems
- Use connection pooling for database connections
- Cache frequently accessed data

## Security Best Practices

### Frontend Security
- Sanitize all user inputs
- Use Angular's built-in XSS protection
- Implement proper authentication guards
- Store sensitive data securely

### Backend Security
- Use bcrypt with sufficient rounds (12+)
- Implement rate limiting
- Validate all input data with Pydantic
- Use HTTPS in production

## Deployment Checklist

### Pre-deployment
- [ ] Run all tests
- [ ] Check for TypeScript errors
- [ ] Verify database migrations
- [ ] Update environment variables
- [ ] Check CORS configuration

### Production Configuration
- [ ] Set `environment.production = true`
- [ ] Configure production database
- [ ] Set up proper logging
- [ ] Configure HTTPS
- [ ] Set up monitoring

## Debugging Guide

### Common Issues
1. **CORS Errors**: Ensure frontend runs on port 5001
2. **Database Connection**: Check PostgreSQL is running
3. **Import Errors**: Verify TypeScript path mapping
4. **Auth Issues**: Check JWT secret and expiration

### Debug Tools
- **Frontend**: Angular DevTools, Browser Developer Tools
- **Backend**: FastAPI automatic docs at `/docs`
- **Database**: pgAdmin or command line tools
- **Logging**: Check error logs in ErrorLoggingService

## Contributing Guidelines

### Git Workflow
1. Create feature branch from main
2. Make changes following code standards
3. Write/update tests
4. Commit with descriptive messages
5. Create pull request with detailed description

### Commit Message Format
```
type(scope): description

feat(auth): add soul connection authentication
fix(discover): resolve compatibility scoring bug
docs(readme): update installation instructions
```

### Code Review Checklist
- [ ] Code follows established patterns
- [ ] Tests are included and passing
- [ ] Error handling is implemented
- [ ] Documentation is updated
- [ ] Performance impact is considered

## Resources

### Documentation
- [Angular Documentation](https://angular.io/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Tools
- [Angular CLI](https://angular.io/cli)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Pytest](https://docs.pytest.org/)
- [pgAdmin](https://www.pgadmin.org/)

This guide should be updated as the application evolves and new patterns are established.