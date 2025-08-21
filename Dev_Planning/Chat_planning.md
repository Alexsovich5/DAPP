# Sprint: "Backlog Cleanup & Structural Reinforcement"

**Sprint Goal:**  
Improve code maintainability, enforce testing and CI standards, and enhance documentation.

**Sprint Duration:**  
Two weeks (e.g., 2025-MM-DD to 2025-MM-DD)

---

## 1. Sprint Planning & Kickoff

- Define sprint objective aligned with backlog recommendations.
- Select backlog stories:
  - Rename `backend_py/` → `python-backend/` consistency (#1)
  - Fix CORS/port mismatch in dev setup (#2)
  - Establish layered FastAPI structure (#3)
  - Extract matching logic into services (#4)
  - Move tests to structured layout; add coverage + Sonar integration (#5)
  - Add request tests, DB tests (#6)
  - Pick CI method; create pipeline for lint/test/coverage (#7)
  - Add pre-commit, Makefile (#8)
  - Provide `env.example`; consolidate Compose (#9)
  - Add DB indices, caching, logging, metrics (#10)
  - Add architecture docs and diagrams (#11)

- Estimate tasks (e.g., story points or time).
- Assign team members / define owners.

---

## 2. Back-End Renaming & Architecture

**Tasks:**
- [ ] Rename or update docs/scripts to use `python-backend/` consistently.
- [ ] Update README, development guides, and scripts accordingly.
- [ ] Set up FastAPI project scaffolding with modules:
  - `api/routers/`, `services/`, `repositories/`, `schemas/`, etc.
- [ ] Extract matching logic into a `services/matching/` package with interfaces.

**Acceptance Criteria:**
- Repo is consistent and paths resolve; CI builds.
- FastAPI structure follows a clear separation of concerns.
- Matching logic is modular and independently testable.

---

## 3. Testing & CI

**Tasks:**
- [ ] Move all tests under `python-backend/tests/` using subfolders: `unit/`, `integration/`, `e2e/`.
- [ ] Add request tests using `httpx.AsyncClient`.
- [ ] Add DB integration tests with Testcontainers or SQLite fixtures.
- [ ] Integrate `pytest-cov` and publish to SonarQube.
- [ ] Choose GitHub Actions or GitLab CI; set up pipelines:
  - Steps: lint, format, type-check, test, coverage.
- [ ] Add pre-commit (black, ruff, isort, markdownlint) and a top-level Makefile.

**Acceptance Criteria:**
- CI passes with lint, tests, and coverage reports.
- Pre-commit prevents formatting/lint failure.
- Makefile simplifies common dev commands.

---

## 4. Configuration & Docker Compose Cleanup

**Tasks:**
- [ ] Create centralized `env.example` (dev, staging, prod).
- [ ] Clean up Compose files; unify via profiles or single file with overrides.
- [ ] Sync ports and CORS config between README, Angular frontend, backend.

**Acceptance Criteria:**
- `.env.example` is comprehensive and accurate.
- Docker dev environment works “out of the box.”
- No mismatches between CORS origins, ports, and docs.

---

## 5. Observability, Performance Improvements

**Tasks:**
- [ ] Add typical DB indices for hot query patterns.
- [ ] Add caching (Redis) for static reads.
- [ ] Instrument the app: request IDs, structured logging, Prometheus metrics.
- [ ] Add background job scaffolding for matching tasks.

**Acceptance Criteria:**
- Basic metrics appear in Prometheus (endpoint latencies, DB usage).
- Logs include `X-Request-Id`, are structured, reveal route/user.
- Caching reduces response time for key endpoints.

---

## 6. Documentation & Architecture

**Tasks:**
- [ ] Add C4-style architecture diagrams (system context & container view).
- [ ] Add sequence diagrams for sign-up, matching flows.
- [ ] Expand OpenAPI docs: tags, examples, error schema, health checks.
- [ ] Document service boundaries: `python-backend/` vs `microservices/`.

**Acceptance Criteria:**
- Diagrams are embedded in README or `docs/`.
- API docs show up in `/docs`; health and ready endpoints present.
- Onboarding documentation is clear and consistent.

---

## 7. Sprint Wrap-up & Retrospective

- Demo key improvements: structure, tests, CI, metrics, docs.
- Review checklist:
  - Naming consistency
  - Test suite & coverage
  - CI/CD pipeline health
  - Dev setup ease
  - Metrics/logs observed
  - Documentation clarity
- Identify blockers or carry-over tasks.
- Record retrospective notes:
  - What went well?
  - What could be improved?
  - Action items for next sprint.

---

**Sprint Backlog Summary**

| Task Area                  | Description                                          |
|---------------------------|------------------------------------------------------|
| Naming & Architecture      | Consistent structure, modular code layering          |
| Testing & CI               | Coverage, pipelines, pre-commit hygiene              |
| Configuration              | `.env.example`, Compose profiles, docs-sync          |
| Observability & Performance| Logging, metrics, caching, indices                  |
| Documentation              | Diagrams, API docs, onboarding material              |

---

Let's align on dates and which CI platform (GitHub vs GitLab) you prefer, and I can help refine task estimates or even generate parts of the Makefile, pre-commit config, or CI pipeline.
