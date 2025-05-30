# Dinner1 Dating App

A unique dating application that connects people over their shared love of food and dining experiences.

## Project Structure

The application is divided into two main components:

- **Backend**: Python/FastAPI with SQLAlchemy ORM and PostgreSQL
- **Frontend**: React/TypeScript with Material-UI for responsive design
  - Mobile-first responsive design using MUI's Grid and Box components
  - Responsive navigation with mobile menu support
  - Touch-friendly interface elements
  - Adaptive layouts for different screen sizes

## Backend Architecture

The backend follows a modular architecture with:

- FastAPI REST endpoints for authentication, user profiles, and match management
- SQLAlchemy ORM for database interactions
- JWT-based authentication
- CORS middleware for security
- Alembic for database migrations

### Key Features

- User authentication (signup, login, password reset)
- Profile management (photos, bio, interests, dietary preferences)
- Location-based matching
- Preference-based filtering (age, gender, dietary preferences)
- Match management

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
DATABASE_URL=postgresql://user:password@localhost:5432/dinner1
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

## API Documentation

API documentation is automatically generated and available at `/docs` when the FastAPI server is running.

## License

This project is proprietary and owned by Dinner1.