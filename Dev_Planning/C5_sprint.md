## C5 Sprint Plan

### Sprint Goal
Stabilize the backend after recent refactors, restore and tighten the test suite, and harden real-time and security middleware for production readiness.

### Success Criteria
- CI green on default pipeline: unit + integration tests (excluding performance) pass.
- Coverage ≥ 75% this sprint (with a plan to raise to 85% next sprint).
- No test collection errors; imports aligned with refactored modules.
- WebSocket manager consistently exported and used across app/tests.

### Scope
- Test suite repair and hardening
- Router and service contract alignment (imports, renamed APIs)
- Real-time manager consistency and docs
- Error handling unification baseline

### Backlog
1. Tests: Unblock and align
   - Add compatibility exports/re-exports for renamed modules/classes/functions.
   - Update failing test imports or mark `xfail` for deprecated paths with rationale.
   - Tighten permissive assertions; validate response schemas and DB side effects.
   - Seed randomness; default SQLite for unit tests; gate destructive DB ops.

2. Coverage uplift (target low-coverage hotspots)
   - Routers: `profiles.py`, `users.py`, `messages.py`, `websocket.py`, `revelations.py`, `monitoring.py`, `notifications.py`.
   - Services: `compatibility.py`, `message_service.py`, `revelation_service.py`, `user_safety_simplified.py`.
   - Add minimal “contract tests” per router (happy path + primary failure).

3. Real-time system consistency
   - Ensure a single exported manager (e.g., `app.services.realtime.manager`).
   - Alias `ConnectionManager = RealtimeConnectionManager` for test compatibility.
   - Document multi-worker caveats; draft plan for Redis-backed presence/queues.

4. Error handling baseline
   - Add global HTTP/generic exception handlers returning a consistent JSON shape and security headers.
   - Ensure routers raise domain errors mapped centrally.

5. CI pipeline hygiene
   - Default job: `pytest -m "not performance"`.
   - Nightly job: `pytest -m performance` (non-blocking).
   - Coverage gate: 75% now; plan to 85% after test stabilization.

### Deliverables
- Passing CI with updated tests and compatibility shims.
- New/updated tests for low-coverage routers/services.
- Real-time manager consistency and short README notes in `services/`.
- Global error handler registration and baseline tests.

### Risks & Mitigations
- Refactor churn breaking more imports → Add re-export layers; incremental PRs.
- Performance test flakiness → Exclude from default CI; run in scheduled pipeline.
- Multi-worker real-time limitations → Document and plan Redis migration.

### Timeline (2 weeks)
Week 1:
- Day 1-2: Fix imports, test collection, seed randomness, DB fixture safety.
- Day 3-4: Tighten assertions; add contract tests for `profiles`, `users`, `messages`.
- Day 5: Real-time manager consolidation; baseline error handlers.

Week 2:
- Day 1-2: Coverage uplift on `revelations`, `notifications`, `monitoring` routers.
- Day 3: Services coverage: `compatibility`, `message_service`.
- Day 4: CI polish, docs, and review.
- Day 5: Buffer and release.

### Owners
- Backend Lead: Align services/routers and compatibility exports.
- QA/Testing: Assertion tightening, contract tests, CI configuration.
- DevOps: Pipeline markers, coverage gates, nightly performance job.

### Out of Scope (this sprint)
- Full Redis migration for real-time (design only).
- Raising coverage to 85% (planned next sprint).


