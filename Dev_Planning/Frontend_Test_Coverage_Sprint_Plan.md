# Frontend Test Coverage Sprint Plan
## Goal: Increase Coverage from 28% to 80%

**Status**: Sprint 1, Week 1 - Task 1 Complete ✅
**Current Coverage**: 31.74% (was 28.25%)
**Target Coverage**: 80%
**Lines Covered So Far**: 129 / 1,910 needed (6.8%)

---

## Sprint 1: Core Services Foundation (28% → 45%)
**Duration**: 2 weeks
**Target**: Cover 627 lines
**Focus**: High-impact services with 0% coverage

### Week 1 Progress

#### ✅ Task 1: WebSocketPoolService Tests (COMPLETED)
- **File**: `websocket-pool.service.spec.ts`
- **Lines**: 207 → **133 covered (63% coverage)**
- **Tests Created**: 41 comprehensive test cases
- **Coverage Impact**: 28.25% → 31.74% (+3.49%)
- **Status**: Committed and pushed to development branch

**Test Coverage Breakdown**:
- Service Initialization (4 tests)
- Connection Management (6 tests)
- Channel Management (5 tests)
- Message Handling (5 tests)
- Connection Status (3 tests)
- Reconnection Logic (2 tests)
- Heartbeat Monitoring (3 tests)
- Connection Cleanup (3 tests)
- Error Handling (2 tests)
- Service Lifecycle (3 tests)
- Edge Cases (5 tests)

#### 🔄 Task 2: SoulConnectionRealtimeService Tests (IN PROGRESS)
- **File**: `soul-connection-realtime.service.spec.ts`
- **Lines**: 138 uncovered (0% current)
- **Target**: 100% coverage
- **Priority**: HIGH - Real-time connection management
- **Estimated Time**: 4-5 hours

**Key Testing Areas**:
- WebSocket connection initialization
- Real-time message handling
- Connection state management
- Reconnection logic
- Event emission and subscription
- Error handling and recovery
- Service lifecycle management

#### ⏳ Task 3: SwipeGestureService Tests (PENDING)
- **File**: `swipe-gesture.service.spec.ts`
- **Lines**: 119 uncovered (0% current)
- **Target**: 100% coverage
- **Priority**: HIGH - User interaction service
- **Estimated Time**: 3-4 hours

**Key Testing Areas**:
- Touch event handling (touchstart, touchmove, touchend)
- Swipe direction detection (left, right, up, down)
- Velocity calculations
- Gesture recognition thresholds
- Multi-touch handling
- Event debouncing

#### ⏳ Task 4: DiscoverComponent Tests Expansion (PENDING)
- **File**: `discover.component.spec.ts`
- **Lines**: 163 additional lines needed
- **Current**: 344/1833 lines (32.5% coverage)
- **Target**: 50%+ coverage
- **Priority**: HIGH - Main user-facing component
- **Estimated Time**: 5-6 hours

**Missing Test Coverage** (from existing TODO):
- Swipe gesture handling (left, right, up)
- Keyboard navigation for accessibility
- Real-time compatibility updates via WebSocket
- A/B testing variant configurations
- Haptic feedback for different actions
- Card animations and transitions
- Filter changes and debouncing
- Undo functionality for actions
- Super like functionality
- Energy pulse sending
- Presence updates
- Match celebration animations

**Week 1 Target**: 627 lines
**Week 1 Current**: 133 lines (21.2%)
**Week 1 Remaining**: 494 lines

---

### Week 2: Continued Core Services

#### Task 5: RevealService Tests
- **File**: `reveal.service.spec.ts`
- **Lines**: 187 uncovered (0% current)
- **Target**: 100% coverage
- **Priority**: HIGH - Progressive revelation system
- **Estimated Time**: 5-6 hours

**Key Testing Areas**:
- Revelation timeline management (7-day cycle)
- Day-by-day revelation unlocking
- Photo reveal consent logic
- Revelation content validation
- Timeline progression tracking
- Mutual consent verification
- API integration for revelations

#### Task 6: HapticFeedbackService Tests
- **File**: `haptic-feedback.service.spec.ts`
- **Lines**: 79 uncovered (0% current)
- **Target**: 100% coverage
- **Priority**: MEDIUM - User experience enhancement
- **Estimated Time**: 2-3 hours

**Key Testing Areas**:
- Vibration pattern generation
- Device capability detection
- Feedback intensity levels
- Pattern customization
- Browser compatibility handling
- Fallback behavior

#### Task 7: A11yAnnouncerDirective Tests Expansion
- **File**: `a11y-announcer.directive.spec.ts`
- **Lines**: 71 additional lines needed
- **Current**: 7/78 lines (9% coverage)
- **Target**: 90%+ coverage
- **Priority**: HIGH - Accessibility critical
- **Estimated Time**: 2-3 hours

**Key Testing Areas**:
- ARIA live region announcements
- Screen reader message formatting
- Announcement priority levels
- Message queuing and timing
- Politeness settings (polite, assertive, off)
- DOM manipulation for announcements

---

## Sprint 2: Accessibility & Interaction (45% → 60%)
**Duration**: 2 weeks
**Target**: Cover 554 lines
**Focus**: Accessibility directives and user interaction components

### Week 3: Accessibility Features

#### Task 8: FocusTrapDirective Tests
- **Lines**: 73 uncovered (0% current)
- **Priority**: HIGH - Accessibility compliance
- **Estimated Time**: 3 hours

#### Task 9: KeyboardNavDirective Tests
- **Lines**: 67 uncovered (0% current)
- **Priority**: HIGH - Keyboard accessibility
- **Estimated Time**: 3 hours

#### Task 10: SkipLinkDirective Tests
- **Lines**: 28 uncovered (0% current)
- **Priority**: MEDIUM - Navigation accessibility
- **Estimated Time**: 1-2 hours

#### Task 11: MatchCardComponent Tests Expansion
- **Lines**: 193 additional lines needed
- **Current**: 179/372 lines (48.1% coverage)
- **Target**: 80%+ coverage
- **Estimated Time**: 5-6 hours

### Week 4: User Interaction Components

#### Task 12: SwipeCardComponent Tests Expansion
- **Lines**: 193 additional lines needed
- **Current**: 63/256 lines (24.6% coverage)
- **Target**: 90%+ coverage
- **Estimated Time**: 5-6 hours

---

## Sprint 3: Advanced Features & Testing (60% → 70%)
**Duration**: 2 weeks
**Target**: Cover 369 lines
**Focus**: Advanced services and feature components

### Week 5: Advanced Services

#### Task 13: AbTestingService Tests
- **Lines**: 100 uncovered (0% current)
- **Priority**: MEDIUM - Feature experimentation
- **Estimated Time**: 3-4 hours

#### Task 14: AnalyticsService Tests
- **Lines**: 94 uncovered (0% current)
- **Priority**: MEDIUM - Usage tracking
- **Estimated Time**: 3-4 hours

#### Task 15: CacheService Tests
- **Lines**: 77 uncovered (0% current)
- **Priority**: MEDIUM - Performance optimization
- **Estimated Time**: 3 hours

### Week 6: Feature Components

#### Task 16: ConnectionsComponent Tests Expansion
- **Lines**: 98 additional lines needed
- **Current**: 81/179 lines (45.3% coverage)
- **Target**: 90%+ coverage
- **Estimated Time**: 3-4 hours

---

## Sprint 4: Remaining Services & Polish (70% → 80%)
**Duration**: 2 weeks
**Target**: Cover 360 lines
**Focus**: Remaining services and final coverage improvements

### Week 7: Service Completion

#### Task 17: CompatibilityService Tests
- **Lines**: 73 uncovered (19.6% current)
- **Target**: 90%+ coverage
- **Estimated Time**: 3 hours

#### Task 18: NotificationService Tests
- **Lines**: 70 uncovered (15.7% current)
- **Target**: 90%+ coverage
- **Estimated Time**: 3 hours

#### Task 19: PresenceService Tests
- **Lines**: 68 uncovered (0% current)
- **Target**: 100% coverage
- **Estimated Time**: 3 hours

#### Task 20: GeolocationService Tests
- **Lines**: 53 uncovered (0% current)
- **Target**: 100% coverage
- **Estimated Time**: 2-3 hours

### Week 8: Final Coverage Push

#### Task 21: ProfileComponent Tests Expansion
- **Lines**: 96 additional lines needed
- **Current**: 91/187 lines (48.7% coverage)
- **Target**: 90%+ coverage
- **Estimated Time**: 3-4 hours

#### Task 22: Final Coverage Improvements
- **Focus**: Files at 50-70% coverage
- **Target**: Push all above 80%
- **Estimated Time**: Variable

---

## Testing Patterns & Best Practices

### Service Testing Pattern
```typescript
describe('ServiceName', () => {
  let service: ServiceName;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ServiceName]
    });
    service = TestBed.inject(ServiceName);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  // Test groups: initialization, core functionality, error handling, edge cases
});
```

### Component Testing Pattern
```typescript
describe('ComponentName', () => {
  let component: ComponentName;
  let fixture: ComponentFixture<ComponentName>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComponentName, CommonModule],
      providers: [/* mock services */]
    }).compileComponents();

    fixture = TestBed.createComponent(ComponentName);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // Test groups: initialization, user interactions, data binding, lifecycle
});
```

### Directive Testing Pattern
```typescript
@Component({
  template: `<div appDirectiveName [config]="config"></div>`
})
class TestComponent {
  config = {};
}

describe('DirectiveName', () => {
  let fixture: ComponentFixture<TestComponent>;
  let directive: DirectiveName;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [TestComponent],
      imports: [DirectiveName]
    }).compileComponents();

    fixture = TestBed.createComponent(TestComponent);
    directive = fixture.debugElement.query(By.directive(DirectiveName)).injector.get(DirectiveName);
    fixture.detectChanges();
  });

  // Test groups: initialization, DOM manipulation, event handling
});
```

---

## Success Metrics

### Coverage Targets by Sprint
- **Sprint 1 End**: 45% (currently 31.74%)
- **Sprint 2 End**: 60%
- **Sprint 3 End**: 70%
- **Sprint 4 End**: 80%

### Quality Gates
- All tests must pass before merging
- No test should be marked as `.skip()` or `pending`
- Each test must have at least one expectation
- Edge cases and error paths must be tested
- Async operations properly tested with fakeAsync/tick

### CI/CD Requirements
- Tests run on every PR
- Coverage report generated on every commit
- Minimum 65% coverage threshold enforced
- Backend tests remain at 84%+ coverage

---

## Risk Mitigation

### Identified Risks
1. **Complex async operations** - Use fakeAsync and tick for deterministic testing
2. **WebSocket testing** - Mock WebSocketSubject and test reconnection logic
3. **Real-time features** - Use jasmine spies to verify event emissions
4. **Browser APIs** - Mock navigator, window, and device-specific APIs
5. **Time-dependent code** - Use jasmine clock for controlling time

### Blockers to Watch
- Missing service dependencies requiring additional mocks
- Complex gesture recognition needing touch event simulation
- WebSocket connection stability in tests
- Async timing issues causing flaky tests

---

## Resource Requirements

### Total Estimated Time
- **Sprint 1**: 80-100 hours (2 weeks, 2 developers)
- **Sprint 2**: 80-100 hours (2 weeks, 2 developers)
- **Sprint 3**: 60-80 hours (2 weeks, 1-2 developers)
- **Sprint 4**: 60-80 hours (2 weeks, 1-2 developers)

**Total**: 280-360 hours (8 weeks)

### Tools Required
- Karma + Jasmine (already configured)
- karma-coverage (already configured)
- ChromeHeadless for CI/CD (already configured)
- Development environment with Node.js 22+

---

## Next Steps

### Immediate Action (Current)
1. ✅ Complete WebSocketPoolService tests - **DONE**
2. 🔄 Create SoulConnectionRealtimeService tests - **IN PROGRESS**
3. Create SwipeGestureService tests
4. Expand DiscoverComponent tests

### This Week Goals
- Complete all Week 1 tasks (627 lines)
- Reach 35-40% overall coverage
- Ensure all 284+ tests remain passing

### Daily Progress Tracking
- Run coverage report after each test file completion
- Update sprint plan with actual vs estimated time
- Identify and document any new blockers
- Commit and push after each major test file completion

---

**Last Updated**: 2025-10-16
**Sprint Start Date**: 2025-10-16
**Expected Completion**: 2025-12-11 (8 weeks)
