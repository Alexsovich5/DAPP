# Dinner First "Soul Before Skin" Dating App

A revolutionary dating application that prioritizes emotional connection through progressive revelation before physical attraction. The platform uses local algorithms to match users based on emotional compatibility, values alignment, and shared interests.

## Project Structure

The application consists of two main components:

- **Backend** (`backend_py/`): FastAPI REST API with SQLAlchemy ORM, JWT authentication, and PostgreSQL
- **Frontend** (`angular-frontend/`): Angular 19+ with standalone components, TypeScript path mapping, and comprehensive error handling

## Key Features

- **Soul Before Skin Philosophy**: Progressive revelation over 7-day cycles
- **Local Compatibility Algorithms**: Sophisticated matching without external AI dependencies
- **Emotional Onboarding**: Deep personality and values assessment
- **Error Boundaries**: Comprehensive error handling and logging
- **TypeScript Path Mapping**: Clean import paths with aliases (@core, @shared, etc.)
- **Standalone Architecture**: Modern Angular components with consistent patterns

## Quick Start

**Prerequisites**: Node.js 18+, Python 3.11+, PostgreSQL 13+

```bash
# Database setup
createdb dinner_first

# Backend
cd backend_py && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && alembic upgrade head
python run.py  # Runs on http://localhost:5000

# Frontend (new terminal)
cd angular-frontend && npm install
ng serve --port 5001  # Must use port 5001 for CORS
```

Access: http://localhost:5001

## Architecture Overview

### Backend (`backend_py/`)
- **FastAPI**: REST API with automatic OpenAPI documentation
- **SQLAlchemy**: ORM with emotional profiling models
- **Alembic**: Database migrations
- **Local Algorithms**: Compatibility scoring without external dependencies

### Frontend (`angular-frontend/`)
- **Angular 19+**: Standalone components with SSR support
- **TypeScript**: Path mapping for clean imports
- **Error Boundaries**: Comprehensive error handling
- **Material Design**: Consistent UI components

### Core Features
- **Soul Connection Discovery**: Local algorithm-based matching
- **Progressive Revelations**: 7-day emotional disclosure cycle
- **Emotional Onboarding**: Personality and values assessment
- **Real-time Messaging**: WebSocket-based communication

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js (v16+)
- PostgreSQL
- pip (Python package manager)
- npm or yarn

### Environment Variables

Create a `.env` file in the backend_py directory with:

```
DATABASE_URL=postgresql://user:password@localhost:5432/dinner_first
SECRET_KEY=your_jwt_secret_here
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000
```

### Installation

1. Clone the repository
2. Set up the backend:
   ```
   cd backend_py
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   ```
3. Set up the frontend:
   ```
   cd frontend
   npm install
   ```

### Running the Application

1. Start the backend server:
   ```
   cd backend_py
   uvicorn app.main:app --reload
   ```
2. Start the frontend development server:
   ```
   cd frontend
   npm start
   ```

### Available Scripts

#### Backend
- `uvicorn app.main:app --reload` - Start development server with hot reload
- `pytest` - Run tests
- `alembic upgrade head` - Run database migrations
- `alembic revision --autogenerate -m "description"` - Generate new migration

#### Frontend
- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run lint` - Lint code
- `npm run format` - Format code with Prettier

## Documentation

- **[CLAUDE.md](./CLAUDE.md)**: Complete project instructions and architecture details
- **[DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)**: Comprehensive development standards and best practices
- **[REMEDIATION.md](./REMEDIATION.md)**: Complete record of all bug fixes and improvements
- **API Documentation**: Available at http://localhost:5000/docs when backend is running

## Development Standards

### Code Quality
- **TypeScript Path Mapping**: Use `@core/*`, `@shared/*`, `@features/*` aliases
- **Error Boundaries**: Wrap complex components for graceful error handling
- **Standalone Components**: Modern Angular architecture without modules
- **Comprehensive Logging**: Error tracking and debugging support

### Testing
```bash
# Frontend testing
ng test
ng build

# Backend testing
pytest
python -m pytest tests/
```

### Database Management
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Contributing

1. Follow the [Development Guide](./DEVELOPMENT_GUIDE.md)
2. Use established code patterns and error handling
3. Write tests for new features
4. Update documentation as needed

## License

This project is proprietary and owned by Dinner First.