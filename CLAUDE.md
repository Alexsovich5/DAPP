# Dinner First: Soul Before Skin - MVP Prototype

## Project Overview

**Dinner First** is a revolutionary "Soul Before Skin" dating platform that prioritizes emotional connection through progressive revelation before physical attraction. The MVP demonstrates core emotional connection concepts without photos initially.

**Core Philosophy**: "If someone enters your life, they should make it better."

**MVP Goal**: Validate the core concept of emotional-first connections with local algorithm-based matching and simple user experience.

## Architecture

### Core Components
- **backend_py/** - FastAPI REST API with SQLAlchemy ORM, JWT auth, Alembic migrations
- **interface/Angular/** - Angular 19+ frontend with standalone components and SSR
- **dinner-first-cicd-test/** - GitLab CI/CD infrastructure with Docker and Terraform

### Technology Stack (MVP)

**Frontend**: Angular 19+ (Existing Codebase)
- TypeScript with standalone components
- Angular Material for UI consistency
- Angular Services with RxJS for state management
- Angular Router for navigation
- Angular HttpClient for API communication
- Angular Reactive Forms for user input
- Server-Side Rendering (SSR) support

**Backend**: FastAPI with Python 3.11+ (Existing Codebase)
- FastAPI framework with automatic OpenAPI docs
- PostgreSQL with SQLAlchemy ORM
- JWT authentication with bcrypt password hashing
- Alembic for database migrations
- Pydantic models for data validation
- CORS middleware for Angular frontend
- Pytest for API testing

**Database**: PostgreSQL (Existing Setup)
- SQLAlchemy models: User, Profile, Match
- Alembic migrations for schema management
- Local development database

## Enhanced Database Schema (Soul Before Skin)

### Existing Tables (Enhanced)
```sql
-- Enhanced Users table
users (
    id, email, username, hashed_password,
    first_name, last_name, date_of_birth, gender,
    emotional_onboarding_completed BOOLEAN DEFAULT FALSE,
    soul_profile_visibility VARCHAR(20) DEFAULT 'hidden',
    emotional_depth_score DECIMAL(5,2),
    created_at, updated_at
)

-- Enhanced Profiles (renamed to emotional_profiles)
emotional_profiles (
    id, user_id,
    life_philosophy TEXT,
    core_values JSONB,
    interests TEXT[],
    personality_traits JSONB,
    communication_style JSONB,
    emotional_depth_score DECIMAL(5,2),
    responses JSONB,  -- Store onboarding question responses
    created_at, updated_at
)

-- Enhanced Matches (renamed to soul_connections)
soul_connections (
    id, user1_id, user2_id,
    connection_stage VARCHAR(30) DEFAULT 'soul_discovery',
    compatibility_score DECIMAL(5,2),
    compatibility_breakdown JSONB,
    reveal_day INTEGER DEFAULT 1,
    mutual_reveal_consent BOOLEAN DEFAULT FALSE,
    first_dinner_completed BOOLEAN DEFAULT FALSE,
    created_at, updated_at
)
```

### New Tables for Soul Before Skin
```sql
-- Daily revelations system
daily_revelations (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER REFERENCES soul_connections(id),
    sender_id INTEGER REFERENCES users(id),
    day_number INTEGER,
    revelation_type VARCHAR(30),
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)

-- Enhanced messaging
messages (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER REFERENCES soul_connections(id),
    sender_id INTEGER REFERENCES users(id),
    message_text TEXT,
    message_type VARCHAR(20) DEFAULT 'text',
    created_at TIMESTAMP DEFAULT NOW()
)
```

## Local Matching Algorithms (No External AI)

### 1. Interest Overlap Algorithm (Jaccard Similarity)

**Python Implementation**:
```python
def calculate_interest_similarity(user1_interests: List[str], user2_interests: List[str]) -> float:
    """
    Calculate Jaccard similarity coefficient for interests overlap
    Returns: 0.0 to 1.0 (higher = more similar)
    """
    set1 = set(user1_interests)
    set2 = set(user2_interests)

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    if union == 0:
        return 0.0

    return intersection / union

# Weight: 25% of total compatibility score
```

### 2. Values Alignment Scoring

**Question Response Matching**:
```python
def calculate_values_compatibility(user1_responses: Dict, user2_responses: Dict) -> float:
    """
    Compare responses to core values questions using keyword matching
    """
    compatibility_scores = []

    # Define value keywords for each question
    value_keywords = {
        "relationship_values": {
            "commitment": ["loyal", "faithful", "dedicated", "devoted"],
            "growth": ["learn", "improve", "develop", "evolve"],
            "adventure": ["explore", "travel", "new", "experience"],
            "stability": ["secure", "steady", "reliable", "consistent"]
        },
        "connection_style": {
            "deep_talks": ["meaningful", "deep", "philosophy", "soul"],
            "shared_activities": ["together", "activities", "hobbies", "fun"],
            "quality_time": ["present", "attention", "focus", "listen"],
            "physical_affection": ["touch", "affection", "close", "intimate"]
        }
    }

    for question_key in user1_responses.keys():
        if question_key in user2_responses:
            score = compare_response_values(
                user1_responses[question_key],
                user2_responses[question_key],
                value_keywords.get(question_key, {})
            )
            compatibility_scores.append(score)

    return sum(compatibility_scores) / len(compatibility_scores) if compatibility_scores else 0.0

# Weight: 30% of total compatibility score
```

### 3. Demographic Compatibility

**Age and Location Scoring**:
```python
def calculate_demographic_compatibility(user1: User, user2: User) -> float:
    """Calculate compatibility based on age difference and location proximity"""
    age_score = calculate_age_compatibility(user1.age, user2.age)
    location_score = calculate_location_compatibility(user1.location, user2.location)

    return (age_score * 0.4) + (location_score * 0.6)

def calculate_age_compatibility(age1: int, age2: int) -> float:
    """Age compatibility with bell curve - optimal within 5 years"""
    age_diff = abs(age1 - age2)

    if age_diff == 0:
        return 1.0
    elif age_diff <= 2:
        return 0.9
    elif age_diff <= 5:
        return 0.8
    elif age_diff <= 8:
        return 0.6
    elif age_diff <= 12:
        return 0.4
    else:
        return 0.2

# Weight: 20% of total compatibility score
```

### 4. Master Compatibility Calculator

```python
class CompatibilityCalculator:
    def __init__(self):
        self.weights = {
            "interests": 0.25,
            "values": 0.30,
            "demographics": 0.20,
            "communication": 0.15,
            "personality": 0.10
        }

    def calculate_overall_compatibility(self, user1: User, user2: User) -> Dict:
        """Calculate comprehensive compatibility score between two users"""
        # Calculate individual scores using local algorithms
        interest_score = calculate_interest_similarity(
            user1.emotional_profile.interests,
            user2.emotional_profile.interests
        )

        values_score = calculate_values_compatibility(
            user1.emotional_profile.core_values,
            user2.emotional_profile.core_values
        )

        demographic_score = calculate_demographic_compatibility(user1, user2)

        # Calculate weighted total
        total_score = (
            interest_score * self.weights["interests"] +
            values_score * self.weights["values"] +
            demographic_score * self.weights["demographics"]
        )

        return {
            "total_compatibility": round(total_score * 100, 1),
            "breakdown": {
                "interests": round(interest_score * 100, 1),
                "values": round(values_score * 100, 1),
                "demographics": round(demographic_score * 100, 1)
            },
            "match_quality": self.get_match_quality_label(total_score)
        }
```

## MVP Core Features (Enhanced)

### 1. Enhanced Emotional Onboarding
**Building on existing auth system**:
- Enhanced registration with emotional questions
- 3 essential soul-mapping questions:
  1. "What do you value most in a relationship?"
  2. "Describe your ideal evening with someone special"
  3. "What makes you feel truly understood?"
- Simple interest selection interface
- Basic profile completion tracking

### 2. Local Algorithm-Based Matching
**Smart matching without AI**:
- Users can choose to hide photos initially
- Multi-factor compatibility scoring using local algorithms
- Interest overlap using Jaccard similarity coefficient
- Values alignment through keyword matching
- Demographic compatibility scoring
- All processing done locally without external API calls

### 3. Progressive Revelation System (7-Day Cycle)
**Simplified revelation timeline**:
- Day 1: Share a personal value
- Day 2: Describe a meaningful experience
- Day 3: Share a hope or dream
- Day 4: Describe what makes you laugh
- Day 5: Share a challenge you've overcome
- Day 6: Describe your ideal connection
- Day 7: Photo reveal (if both consent)

### 4. Enhanced Messaging System
**Building on existing message structure**:
- Text-based conversations between matched users
- Revelation sharing interface integrated with messages
- Basic emoji reactions to messages
- Photo sharing after revelation completion
- Message history and status tracking

### 5. Soul Connection Management
**Enhanced profile and connection features**:
- View and edit emotional profile information
- Manage revelation preferences and timeline
- Connection history with compatibility breakdown
- Basic privacy and consent settings

## Enhanced API Endpoints

### Existing Endpoints (Enhanced)
```python
# Enhanced auth endpoints
POST /api/v1/auth/register  # Enhanced with emotional questions
POST /api/v1/auth/login
GET  /api/v1/auth/me

# Enhanced user endpoints
GET  /api/v1/users/me
GET  /api/v1/users/potential-matches  # With local algorithm scoring
GET  /api/v1/users/{user_id}

# Enhanced profile endpoints
POST /api/v1/profiles  # Now creates emotional_profile
GET  /api/v1/profiles/me
PUT  /api/v1/profiles/me
GET  /api/v1/profiles/{user_id}

# Enhanced matching endpoints
POST /api/v1/matches  # Now creates soul_connections
GET  /api/v1/matches/sent
GET  /api/v1/matches/received
PUT  /api/v1/matches/{match_id}
```

### New Soul Before Skin Endpoints
```python
# Emotional onboarding
POST /api/v1/onboarding/complete
GET  /api/v1/onboarding/status

# Soul connections with local algorithms
GET  /api/v1/connections/discover  # Local compatibility scoring
POST /api/v1/connections/initiate
GET  /api/v1/connections/active
PUT  /api/v1/connections/{connection_id}/stage

# Progressive revelations
POST /api/v1/revelations/create
GET  /api/v1/revelations/timeline/{connection_id}
PUT  /api/v1/revelations/{revelation_id}/react

# Enhanced messaging
GET  /api/v1/messages/{connection_id}
POST /api/v1/messages/{connection_id}
POST /api/v1/messages/{connection_id}/revelation
```

## Angular Application Structure (Enhanced)

```
interface/Angular/src/app/
├── core/                    # Existing core services enhanced
│   ├── auth/               # Enhanced with emotional onboarding
│   ├── services/           # Enhanced API services
│   └── interceptors/       # HTTP interceptors
├── shared/                 # Enhanced shared components
│   ├── components/         # Reusable UI components
│   ├── models/            # Enhanced with soul connection models
│   └── pipes/             # Custom pipes
├── features/              # Enhanced feature modules
│   ├── auth/              # Enhanced login/register with emotional questions
│   ├── onboarding/        # New: Emotional onboarding flow
│   ├── discovery/         # Enhanced: Soul-based matching
│   ├── connections/       # Enhanced: Soul connections management
│   ├── revelations/       # New: Daily revelation features
│   ├── messages/          # Enhanced: Messaging with revelations
│   └── profile/           # Enhanced: Emotional profile management
├── layout/                # App layout components
└── app-routing.module.ts  # Enhanced routing
```

## Essential Development Commands

### Start / Stop (Docker — required)
```bash
# Start everything (PostgreSQL + backend + frontend)
./start-app.sh          # or: docker compose -f docker-compose.dev.yml up --build

# Stop all services
./start-app.sh down     # or: docker compose -f docker-compose.dev.yml down

# Tail logs
./start-app.sh logs             # all services
./start-app.sh logs backend     # backend only
./start-app.sh logs frontend    # frontend only

# Wipe database and restart fresh
./start-app.sh reset
```

### Backend (inside container)
```bash
# Run tests
docker compose -f docker-compose.dev.yml exec backend pytest

# Create a new migration
docker compose -f docker-compose.dev.yml exec backend \
  alembic revision --autogenerate -m "description"

# Apply migrations manually (runs automatically on startup)
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Open a shell
docker compose -f docker-compose.dev.yml exec backend sh
```

### Angular Frontend (inside container)
```bash
# Generate a component
docker compose -f docker-compose.dev.yml exec frontend \
  npx ng generate component features/onboarding/emotional-questions

# Generate a service
docker compose -f docker-compose.dev.yml exec frontend \
  npx ng generate service core/services/soul-connection

# Run unit tests (runs on host, not in container)
cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

## Environment Setup

All environment variables are defined in `docker-compose.dev.yml`.
No `.env` file is required for local development — defaults are pre-configured.

For production, copy `python-backend/.env.example` to `python-backend/.env` and fill in secrets.

## Development Workflow

1. **Ensure Docker Desktop is running**

2. **Start the full stack**:
   ```bash
   ./start-app.sh
   ```
   On first run this builds images and runs `alembic upgrade head` automatically.

3. **Test connectivity**:
   ```bash
   curl http://localhost:8000/health
   ```

## Key Access Points
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Angular Frontend**: http://localhost:4200
- **Health Check**: http://localhost:8000/health
- **Soul Connection Discovery**: http://localhost:4200/discover
- **Emotional Onboarding**: http://localhost:4200/onboarding

## Critical Requirements
- **Docker Desktop** must be running — no local PostgreSQL, Python, or Node.js required
- **Backend** runs on port 8000 (FastAPI + uvicorn with hot-reload)
- **Frontend** runs on port 4200 (Angular `ng serve`)
- **Database migrations** run automatically on backend container startup
- **Local algorithms** only — no external API dependencies
- **Emotional onboarding** required before accessing matching features

## MVP Validation Metrics

### User Engagement (Local Tracking)
- Emotional onboarding completion rate (target: >80%)
- Daily revelation completion rate (target: >60%)
- Connection request acceptance rate (target: >40%)
- Photo reveal rate after 7 days (target: >50%)
- Local algorithm matching accuracy

### Technical Performance
- Page load times (<2 seconds)
- Local algorithm processing (<500ms)
- Mobile responsiveness (Angular responsive design)
- Local database query performance

## Success Criteria for MVP

### Primary Goals
1. **Concept Validation**: Users understand "Soul Before Skin" approach
2. **Technical Proof**: Local algorithms provide meaningful matches
3. **User Retention**: Users complete 7-day revelation cycle
4. **Feedback Collection**: Gather user experience data

### Secondary Goals
1. **Performance**: Fast, responsive local processing
2. **Usability**: Intuitive interface built on existing Angular architecture
3. **Scalability**: Architecture ready for future AI enhancements
4. **Code Quality**: Clean, maintainable extension of existing codebase

## Budget Estimate (MVP Enhancement)

### Development Costs (Building on Existing Codebase)
- **Enhanced Frontend**: $8,000-12,000 (2-3 weeks)
- **Enhanced Backend**: $8,000-12,000 (2-3 weeks)
- **Local Algorithms**: $5,000-8,000 (1-2 weeks)
- **Testing & Integration**: $2,000-4,000 (1 week)

**Total MVP Enhancement**: $23,000-36,000

### Operational Costs (3 months local development)
- **Local Development**: $0 (no cloud costs)
- **PostgreSQL Local**: $0
- **No External APIs**: $0

**Total Enhanced MVP**: $23,000-36,000

This approach leverages your existing Angular 19+ and FastAPI codebase while adding the revolutionary "Soul Before Skin" features with sophisticated local algorithms, keeping development costs low and avoiding external dependencies.

## Git Workflow & Branch Management

### Branch Strategy
Follow GitFlow best practices for organized development:

**Branch Types:**
- `main` - Production-ready code, stable releases only
- `development` - Integration branch for completed features
- `feature/[feature-name]` - Individual feature development
- `bugfix/[issue-name]` - Bug fixes and hotfixes
- `hotfix/[critical-fix]` - Emergency production fixes

### Pull Request Workflow

**For Feature Development:**
```
feature/issue → development PR = for integrating work
development → main PR = for releasing work
```

**PR Creation Process:**
1. **Feature Development**:
   - Create feature branch from `development`
   - Implement and test feature completely
   - Create PR: `feature/soul-connections → development`
   - Include comprehensive testing and documentation

2. **Release Process**:
   - After features are integrated and tested in `development`
   - Create PR: `development → main`
   - Include release notes and version updates
   - Deploy to production after merge

**PR Requirements:**
- Clear, descriptive title and comprehensive description
- All tests passing (backend: pytest, frontend: ng test)
- Code review from at least one team member
- Security review for production-facing changes
- Performance testing for algorithmic changes
- Documentation updates included

**Commit Message Standards:**
- Use conventional commits format
- Include scope and breaking changes
- Reference issue numbers when applicable
- Do NOT mention Claude, Claude Code, or any AI tool in commit messages
- No external tool attribution in commit messages

### Development Best Practices
- **Always branch from `development`** for new features
- **Keep feature branches focused** - one feature per branch
- **Test thoroughly** before creating PRs
- **Update documentation** with code changes
- **Run security and lint checks** before committing
- **Squash commits** in feature branches before merging
