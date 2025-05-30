# Dinner App - Run Scripts

This directory contains scripts to easily start and stop all services required for the Dinner App.

## Prerequisites

Before running the scripts, ensure you have the following installed:

- **Docker** and **Docker Compose** (for PostgreSQL database)
- **Node.js** and **npm** (for Angular frontend)
- **Python 3** (for FastAPI backend)

## Quick Start

### Starting the Application

```bash
./start.sh
```

This script will:
1. ✅ Check all prerequisites
2. 🗄️ Start PostgreSQL database (Docker container)
3. 🔧 Start FastAPI backend (Python virtual environment)
4. 📱 Start Angular frontend (Node.js development server)
5. 🌐 Open the application at the URLs shown

### Stopping the Application

```bash
./stop.sh
```

This script will:
1. 🛑 Stop Angular frontend (port 4200)
2. 🛑 Stop FastAPI backend (port 8000)
3. 🛑 Stop PostgreSQL container
4. 🧹 Clean up any remaining processes

## Service URLs

When running, the application will be available at:

- **Frontend (Angular)**: http://localhost:4200
- **Backend API (FastAPI)**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Database (PostgreSQL)**: localhost:5432

## What Each Script Does

### start.sh

**Prerequisites Check:**
- Verifies Docker, Docker Compose, Node.js, npm, and Python 3 are installed
- Shows clear error messages if any prerequisites are missing

**Database Setup:**
- Starts PostgreSQL 15 in a Docker container
- Waits for the database to be ready before proceeding
- Runs database migrations automatically

**Backend Setup:**
- Creates Python virtual environment (if not exists)
- Installs Python dependencies (if needed)
- Runs Alembic database migrations
- Starts FastAPI server on port 8000

**Frontend Setup:**
- Installs npm dependencies (if needed)
- Starts Angular development server on port 4200

**Monitoring:**
- Continuously monitors all services
- Shows colored status messages
- Handles graceful shutdown with Ctrl+C

### stop.sh

**Process Termination:**
- Safely stops all services on their respective ports
- Kills any remaining project-related processes
- Stops Docker containers
- Shows clear status messages throughout

## Features

### Smart Dependency Management
- Only installs dependencies when needed (checks timestamps)
- Creates virtual environments automatically
- Handles missing dependencies gracefully

### Port Conflict Detection
- Checks if services are already running
- Shows warnings for occupied ports
- Allows partial restarts

### Error Handling
- Comprehensive error checking at each step
- Clear, colored error messages
- Graceful cleanup on interruption

### Cross-Platform Compatibility
- Works on macOS, Linux, and Windows (with WSL)
- Uses standard Unix commands
- Handles different shell environments

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# If you see "port already in use" errors:
./stop.sh  # Stop all services first
./start.sh # Then restart
```

**2. Database Connection Issues**
```bash
# If backend can't connect to database:
docker-compose down  # Stop database
docker-compose up -d postgres  # Restart database
```

**3. Python Dependencies Issues**
```bash
# If Python packages are causing issues:
rm -rf backend_py/venv  # Remove virtual environment
./start.sh  # Will recreate environment
```

**4. Node Dependencies Issues**
```bash
# If npm packages are causing issues:
cd interface/Angular
rm -rf node_modules package-lock.json
npm install
cd ../..
./start.sh
```

### Manual Service Control

If you need to start services individually:

```bash
# Database only
docker-compose up -d postgres

# Backend only (from backend_py directory)
source venv/bin/activate
python run.py

# Frontend only (from interface/Angular directory)
npm start
```

### Logs and Debugging

**View Docker logs:**
```bash
docker-compose logs postgres
```

**View individual service logs:**
- Backend logs: Shown in terminal when running
- Frontend logs: Shown in terminal when running
- Database logs: Use `docker-compose logs postgres`

### Reset Everything

If you need a complete reset:

```bash
./stop.sh
docker-compose down -v  # Removes database volumes
rm -rf backend_py/venv
rm -rf interface/Angular/node_modules
./start.sh
```

## Development Tips

### Hot Reload
Both frontend and backend support hot reload:
- **Angular**: Automatically reloads on file changes
- **FastAPI**: Automatically restarts on Python file changes

### Environment Variables
Backend configuration is in `backend_py/.env`:
- Database connection string
- JWT secret key
- CORS origins
- Debug settings

### Database Management
- **Migrations**: Run automatically by start script
- **Manual migrations**: `cd backend_py && alembic upgrade head`
- **Database reset**: `docker-compose down -v && docker-compose up -d postgres`

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Angular       │    │   FastAPI       │    │   PostgreSQL    │
│   Frontend      │───▶│   Backend       │───▶│   Database      │
│   Port: 4200    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

- **Frontend**: Angular 19 with Material UI
- **Backend**: Python FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL 15 in Docker container
- **Authentication**: JWT tokens
- **File Storage**: Local file system (uploads/ directory)