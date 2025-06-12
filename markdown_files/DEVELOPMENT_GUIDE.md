# Dinner1 "Soul Before Skin" - Development Guide

## Overview
This guide walks through implementing the "Soul Before Skin" MVP features on top of the existing Angular 19+ frontend and Python FastAPI backend.

## Development Phases

### Phase 1: Database Schema Enhancement (Week 1)
**Goal**: Extend existing database with soul connection features

#### 1.1 Database Migration Setup
```bash
cd backend_py
source venv/bin/activate
alembic revision --autogenerate -m "Add soul before skin tables"
```

#### 1.2 Enhanced Models
**Location**: `backend_py/app/models/`

**Enhanced User Model** (`user.py`):
```python
# Add to existing User model
emotional_onboarding_completed = Column(Boolean, default=False)
soul_profile_visibility = Column(String(20), default='hidden')
emotional_depth_score = Column(Numeric(5,2))
```

**Enhanced Profile Model** (`profile.py`):
```python
# Rename to EmotionalProfile and add fields
life_philosophy = Column(Text)
core_values = Column(JSON)
personality_traits = Column(JSON)
communication_style = Column(JSON)
responses = Column(JSON)  # Onboarding responses
```

**New Models**:
- `soul_connection.py` - Enhanced match system
- `daily_revelation.py` - Revelation tracking
- `message.py` - Enhanced messaging

#### 1.3 Migration Execution
```bash
alembic upgrade head
```

### Phase 2: Local Matching Algorithms (Week 1-2)
**Goal**: Implement sophisticated local algorithms for compatibility scoring

#### 2.1 Compatibility Service
**Location**: `backend_py/app/services/compatibility.py`

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
        # Implementation of local algorithms
        pass
```

#### 2.2 Algorithm Implementations
- **Jaccard Similarity** for interests overlap
- **Keyword Matching** for values alignment
- **Demographic Scoring** for age/location compatibility
- **Personality Matching** based on responses

### Phase 3: Enhanced API Endpoints (Week 2)
**Goal**: Create new soul connection endpoints

#### 3.1 Soul Connection Router
**Location**: `backend_py/app/api/v1/routers/soul_connections.py`

```python
@router.get("/discover")
async def discover_soul_connections(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Local algorithm-based matching
    pass

@router.post("/initiate")
async def initiate_soul_connection(
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create new soul connection
    pass
```

#### 3.2 Revelation Router
**Location**: `backend_py/app/api/v1/routers/revelations.py`

```python
@router.post("/create")
async def create_revelation(
    revelation: RevelationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Daily revelation creation
    pass
```

### Phase 4: Angular Frontend Enhancement (Week 2-3)
**Goal**: Implement soul connection UI/UX

#### 4.1 Enhanced Authentication
**Location**: `interface/Angular/src/app/features/auth/`

**Enhanced Registration**:
```typescript
// register.component.ts
export class RegisterComponent {
  emotionalQuestions = [
    { id: 1, text: "What do you value most in a relationship?" },
    { id: 2, text: "Describe your ideal evening with someone special" },
    { id: 3, text: "What makes you feel truly understood?" }
  ];
  
  onSubmit() {
    // Enhanced registration with emotional questions
  }
}
```

#### 4.2 Emotional Onboarding Module
**Location**: `interface/Angular/src/app/features/onboarding/`

```bash
ng generate module features/onboarding
ng generate component features/onboarding/emotional-questions
ng generate component features/onboarding/interest-selection
ng generate component features/onboarding/personality-assessment
```

#### 4.3 Soul Discovery Component
**Location**: `interface/Angular/src/app/features/discovery/`

```typescript
// soul-discovery.component.ts
export class SoulDiscoveryComponent {
  potentialConnections: SoulConnection[] = [];
  
  ngOnInit() {
    this.loadPotentialConnections();
  }
  
  loadPotentialConnections() {
    this.soulConnectionService.discoverConnections()
      .subscribe(connections => {
        this.potentialConnections = connections;
      });
  }
}
```

#### 4.4 Progressive Revelation System
**Location**: `interface/Angular/src/app/features/revelations/`

```typescript
// revelation-timeline.component.ts
export class RevelationTimelineComponent {
  revelationCycle = [
    { day: 1, prompt: "Share a personal value" },
    { day: 2, prompt: "Describe a meaningful experience" },
    { day: 3, prompt: "Share a hope or dream" },
    { day: 4, prompt: "Describe what makes you laugh" },
    { day: 5, prompt: "Share a challenge you've overcome" },
    { day: 6, prompt: "Describe your ideal connection" },
    { day: 7, prompt: "Photo reveal (if both consent)" }
  ];
}
```

### Phase 5: Enhanced Messaging System (Week 3)
**Goal**: Integrate revelations with messaging

#### 5.1 Message Service Enhancement
**Location**: `interface/Angular/src/app/core/services/message.service.ts`

```typescript
@Injectable()
export class MessageService {
  sendMessage(connectionId: number, message: string): Observable<Message> {
    return this.http.post<Message>(`${this.apiUrl}/messages/${connectionId}`, {
      message_text: message
    });
  }
  
  sendRevelation(connectionId: number, revelation: Revelation): Observable<Message> {
    return this.http.post<Message>(`${this.apiUrl}/messages/${connectionId}/revelation`, revelation);
  }
}
```

#### 5.2 Enhanced Chat Interface
```typescript
// chat.component.ts
export class ChatComponent {
  showRevelationPrompt = false;
  currentRevelationDay = 1;
  
  sendRevelation(content: string) {
    const revelation = {
      day_number: this.currentRevelationDay,
      content: content,
      revelation_type: 'daily_share'
    };
    
    this.messageService.sendRevelation(this.connectionId, revelation)
      .subscribe(() => {
        this.loadMessages();
      });
  }
}
```

## Development Tasks Breakdown

### Backend Tasks (2-3 weeks)
1. **Database Enhancement** (3-4 days)
   - Create new models for soul connections
   - Write and test migrations
   - Update existing models with soul fields

2. **Local Algorithms Implementation** (5-7 days)
   - Jaccard similarity for interests
   - Values alignment keyword matching
   - Demographic compatibility scoring
   - Master compatibility calculator

3. **API Endpoints** (4-5 days)
   - Soul connection discovery
   - Revelation management
   - Enhanced messaging endpoints
   - Compatibility scoring endpoints

4. **Testing & Documentation** (2-3 days)
   - Unit tests for algorithms
   - API endpoint tests
   - Performance optimization

### Frontend Tasks (2-3 weeks)
1. **Authentication Enhancement** (2-3 days)
   - Add emotional questions to registration
   - Onboarding flow implementation
   - Profile completion tracking

2. **Soul Discovery Interface** (4-5 days)
   - Potential connections display
   - Compatibility breakdown UI
   - Connection initiation workflow

3. **Revelation System** (4-5 days)
   - Daily revelation interface
   - Timeline visualization
   - Photo reveal workflow

4. **Enhanced Messaging** (3-4 days)
   - Revelation integration in chat
   - Message type differentiation
   - Timeline display in messages

5. **UI/UX Polish** (2-3 days)
   - Angular Material theming
   - Responsive design
   - Loading states and animations

## Technical Implementation Details

### Local Algorithm Performance
- **Target**: <500ms for compatibility calculation
- **Optimization**: Cache user profiles in memory
- **Scalability**: Implement pagination for discovery

### Database Optimization
```sql
-- Indexes for performance
CREATE INDEX idx_users_emotional_onboarding ON users(emotional_onboarding_completed);
CREATE INDEX idx_soul_connections_stage ON soul_connections(connection_stage);
CREATE INDEX idx_daily_revelations_connection ON daily_revelations(connection_id, day_number);
```

### Angular State Management
```typescript
// soul-connection.state.ts
interface SoulConnectionState {
  potentialConnections: SoulConnection[];
  activeConnections: SoulConnection[];
  currentRevelations: Revelation[];
  compatibilityScores: Map<number, CompatibilityScore>;
}
```

## Testing Strategy

### Backend Testing
```bash
# Unit tests for algorithms
pytest tests/unit/test_compatibility_algorithms.py

# Integration tests for endpoints
pytest tests/integration/test_soul_connections.py

# Performance tests
pytest tests/performance/test_algorithm_speed.py
```

### Frontend Testing
```bash
# Component tests
ng test --include="**/soul-discovery/**"

# E2E tests for onboarding flow
ng e2e --suite=onboarding

# Performance testing
ng build --configuration=production
```

## Deployment Preparation

### Environment Configuration
```bash
# Backend environment
COMPATIBILITY_THRESHOLD=50
REVELATION_CYCLE_DAYS=7
EMOTIONAL_DEPTH_WEIGHT=0.3
MAX_DAILY_CONNECTIONS=10

# Frontend environment
soulBeforeSkin: {
  revelationCycleDays: 7,
  compatibilityThreshold: 50,
  defaultPhotoHidden: true,
  emotionalOnboardingRequired: true
}
```

### Performance Monitoring
- Algorithm execution time logging
- Database query performance metrics
- User engagement tracking
- Connection success rate monitoring

## Quality Assurance

### Code Quality
- ESLint for Angular code consistency
- Black/Flake8 for Python code formatting
- Type safety with TypeScript strict mode
- Comprehensive error handling

### User Experience
- Emotional onboarding completion >80%
- Page load times <2 seconds
- Mobile responsiveness on all devices
- Accessibility compliance (WCAG 2.1)

## Success Metrics

### Technical KPIs
- Algorithm processing speed: <500ms
- Database query performance: <100ms
- Frontend bundle size: <2MB
- Test coverage: >85%

### User Experience KPIs
- Onboarding completion rate: >80%
- Daily revelation completion: >60%
- Connection acceptance rate: >40%
- 7-day cycle completion: >50%

This development guide provides a clear roadmap for implementing the "Soul Before Skin" MVP while building on the existing codebase architecture.