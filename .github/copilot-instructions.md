# GitHub Copilot Instructions for Dinner First "Soul Before Skin" Dating App

**ALWAYS FOLLOW THESE INSTRUCTIONS FIRST**. Only fallback to additional search and context gathering if the information in these instructions is incomplete or found to be in error.

## Working Effectively in the Codebase

### Bootstrap and Build the Complete Application

**CRITICAL TIMING WARNING**: NEVER CANCEL long-running builds or tests. Set timeouts appropriately:

```bash
# 1. Database Setup (Required first step)
docker run -d --name dinner_first-postgres \
  -e POSTGRES_DB=dinner_first \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:15
# Takes ~15 seconds first time (image download), ~3 seconds subsequent starts

# 2. Backend Setup (Python FastAPI)
cd python-backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt  # Takes 48 seconds. NEVER CANCEL.
cp .env.example .env
```

**CRITICAL DATABASE ISSUE**: Database migrations have conflicts. Use this workaround:
```bash
# Skip migrations for now - backend will create tables automatically
# alembic upgrade head  -- DO NOT RUN (has migration conflicts)
```

**Start Backend** (Takes ~5 seconds to start):
```bash
python run.py  # Runs on http://localhost:8000 (NOT port 5000)
# NEVER CANCEL: Backend takes up to 15 seconds to fully initialize
```

**Frontend Setup** (Angular 18+ with Nx):
```bash
cd angular-frontend
npm install  # Takes 53 seconds. NEVER CANCEL.
```

**CRITICAL FRONTEND BUILD ISSUE**: Frontend has compilation errors. Use development server instead:
```bash
# npm run build  -- DO NOT RUN (has TypeScript compilation errors)
npm run start  # Takes ~10 seconds to start, runs on http://localhost:4200
```

### Complete Application Startup (Recommended)

The provided startup script has Docker Compose syntax issues. Use manual startup:
```bash
# DO NOT USE: ./start-app.sh  # Has docker-compose vs docker compose v2 syntax issues

# Manual startup instead (VALIDATED WORKING):
docker start dinner_first-postgres  # Start database (~3 seconds)
cd python-backend && source venv/bin/activate && python run.py  # Backend (~8 seconds)
cd angular-frontend && npm run start  # Frontend in separate terminal (~10 seconds)
# Total startup time: ~30 seconds. NEVER CANCEL individual components.
```

## Validation and Testing

### Manual Validation After Changes

**ALWAYS run complete end-to-end scenarios**:

1. **Health Check Validation** (10 seconds - VALIDATED WORKING):
```bash
# Backend health (Required first)
curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected","api_version":"1.0.0"}

# API Documentation (VALIDATED WORKING)
curl http://localhost:8000/docs  # FastAPI automatic docs with Swagger UI
```

2. **Frontend Development Server** (Required for CORS):
```bash
cd angular-frontend
npm run start  # Must use port 4200 for proper CORS configuration
# Frontend accessible at http://localhost:4200
```

3. **Complete User Journey** (Manual testing required):
   - Registration flow (test with dummy data)
   - Profile creation (soul connection questions)
   - Discovery/matching system
   - Messaging functionality
   - Photo reveal system (7-day cycle)

### Build and Test Commands

**Backend Tests** (15-30 seconds):
```bash
cd python-backend
source venv/bin/activate
pytest --version  # Verify test environment
# Note: Full test suite may have database dependency issues
```

**Backend Linting** (3 seconds):
```bash
black --check --diff app/  # Code formatting check (passes)
flake8 app/ --count --statistics  # Linting check
```

**Frontend Linting** (Currently broken):
```bash
# npm run lint  -- DO NOT RUN (Nx configuration missing)
# Use TypeScript compiler check instead:
npx tsc --noEmit  # Type checking without build
```

**CRITICAL BUILD TIMES AND TIMEOUTS**:
- Backend dependency install: 48s (set timeout: 120s)
- Frontend dependency install: 53s (set timeout: 120s)
- Backend startup: 5-15s (set timeout: 30s)
- Frontend dev server: 10s (set timeout: 30s)
- Frontend build: 13s but FAILS (has compilation errors)
- Database container start: 3s (set timeout: 15s)

## Key Project Structure

### Backend (Python FastAPI)
```
python-backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Database, auth, config
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic
│   └── middleware/       # Security, logging
├── alembic/              # Database migrations (BROKEN)
├── tests/                # Test suite
├── run.py               # Application entry point
└── requirements.txt     # Dependencies (validated working)
```

### Frontend (Angular 18+)
```
angular-frontend/
├── src/app/
│   ├── core/             # Services, guards, interceptors
│   ├── shared/           # Reusable components
│   ├── features/         # Feature modules
│   └── environments/     # Environment configs (MISSING)
├── public/               # Static assets
└── package.json         # Dependencies (validated working)
```

## Common Issues and Workarounds

### Database Issues
- **Migration conflicts**: Skip alembic, let backend auto-create tables
- **Connection refused**: Ensure PostgreSQL container is running first
- **Wrong database name**: Use "dinner_first" not "dinner1"

### Frontend Issues  
- **Build failures**: Use development server (`npm run start`) instead of build
- **Environment files missing**: Check `src/environments/` directory
- **TypeScript errors**: Multiple compilation issues in discovery component
- **Lint configuration missing**: Nx lint target not configured

### Backend Issues
- **Port confusion**: Backend runs on port 8000, not 5000
- **CORS configuration**: Configured for localhost:4200 and localhost:5001
- **Virtual environment**: Always activate venv before running commands

### Docker Issues
- **docker-compose vs docker compose**: Script uses old syntax, environment has v2
- **Container conflicts**: Remove existing containers before fresh start

## Development Workflow Commands

### Daily Development (Validated working):
```bash
# Start database
docker start dinner_first-postgres || docker run -d --name dinner_first-postgres \
  -e POSTGRES_DB=dinner_first -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:15

# Backend development
cd python-backend && source venv/bin/activate && python run.py

# Frontend development (separate terminal)
cd angular-frontend && npm run start
```

### Before Committing Changes:
```bash
# Backend validation (3 seconds)
cd python-backend && source venv/bin/activate
black --check app/
# pytest  # May fail due to database issues

# Frontend validation
cd angular-frontend
npx tsc --noEmit  # Type check only
# npm run build  # DO NOT RUN - has compilation errors
```

### CI/CD Preparation:
The repository has comprehensive GitHub Actions workflow (`.github/workflows/ci-cd.yml`) but may fail due to:
- Frontend compilation errors
- Database migration conflicts
- Missing environment files

## Critical URLs and Access Points

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (FastAPI auto-docs)
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:4200 (development server)
- **Database**: PostgreSQL on localhost:5432 (dinner_first)

## Architecture Notes

This is a "Soul Before Skin" dating platform with:
- **Angular 18+** frontend with standalone components
- **FastAPI** backend with SQLAlchemy ORM
- **PostgreSQL** database with complex relationship models
- **JWT authentication** with bcrypt password hashing
- **Local matching algorithms** (no external AI APIs)
- **Progressive revelation system** (7-day emotional connection cycle)

## Environment Variables

Backend requires `.env` file in `python-backend/`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dinner_first
SECRET_KEY=your_super_secure_secret_key_here_min_32_characters
CORS_ORIGINS=http://localhost:4200,http://localhost:5001
```

## NEVER DO THIS

- Cancel builds or installs before completion (they take 45-60 seconds)
- Run `alembic upgrade head` (has migration conflicts)
- Run `npm run build` on frontend (has compilation errors)
- Run `npm run lint` on frontend (Nx configuration missing)
- Assume backend runs on port 5000 (it runs on port 8000)
- Skip database container startup (required for backend)

## When Instructions Don't Work

If these instructions fail or seem incomplete:
1. Check the specific error message against known issues above
2. Verify Docker is running and PostgreSQL container is accessible
3. Ensure virtual environment is activated for Python commands
4. Check that ports 4200 and 8000 are not already in use
5. Look for additional context in `DEVELOPMENT_GUIDE.md` and `README.md`
6. Consider database or dependency version conflicts

Always test your changes with the complete user journey: registration → profile → discovery → matching → messaging → photo reveal.