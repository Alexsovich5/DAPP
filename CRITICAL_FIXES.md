# Critical Frontend-Backend Communication Fixes

## 1. Backend Schema Updates Required

### Update User Model (backend_py/app/models/user.py)
```python
# Add missing fields:
date_of_birth = Column(Date, nullable=True)
bio = Column(String(500), nullable=True)
location = Column(String(255), nullable=True)
interests = Column(JSON, nullable=True)
dietary_preferences = Column(JSON, nullable=True)
```

### Update Auth Schema (backend_py/app/schemas/auth.py)
```python
class UserCreate(UserBase):
    password: str
    dateOfBirth: Optional[date] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    interests: Optional[List[str]] = None
    dietaryPreferences: Optional[List[str]] = None
```

## 2. Missing API Endpoints

### Add to auth.py router:
- `GET /auth/me` - get current user
- `POST /auth/refresh-token` - refresh JWT token
- `POST /auth/forgot-password` - password reset

### Fix profile endpoint mismatch:
- Frontend calls `PUT /profile` 
- Backend has `PUT /profiles/me`
- Need alias or frontend update

## 3. CORS Configuration Fix

### In main.py:
```python
allow_credentials=True  # Change from False
```

### Frontend API service needs:
```typescript
withCredentials: true
```

## 4. Database Connection Issues

### Add environment variables:
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dinner_app
POSTGRES_DB=dinner_app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## 5. Profile Data Transformation

### Backend needs to handle:
- `cuisine_preferences` → `favorite_cuisines` mapping
- Nested object flattening for `locationPreferences` and `matchPreferences`
- Array handling for `dietaryPreferences`

## 6. Authentication Flow Fix

### Current Issue:
- Frontend expects user profile data in login response
- Backend only returns token
- Need combined user+profile response

## Impact: 
These mismatches prevent all registration, login, and profile operations from working.