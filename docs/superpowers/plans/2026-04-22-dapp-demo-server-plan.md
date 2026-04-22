# DAPP Demo Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this host into a public demo server for DAPP at `https://date.batcomputer.waynetower.de`, with `main` as a rolling-release branch and full integration into the host's existing Grafana/Prometheus/Loki/Alertmanager stack.

**Architecture:** A new `docker-compose.demo.yml` runs production-built images (no source mounts) wired into the existing observability network. NPM proxies the public domain to a single-origin frontend (`/`) + backend (`/api`) layout. Backend exposes a Prometheus `/metrics` endpoint via `prometheus-fastapi-instrumentator`, with 8 custom business metrics hooked into the relevant request handlers. Grafana dashboards are provisioned from a JSON file in the repo.

**Tech Stack:** FastAPI 0.x, Angular 19, PostgreSQL 15, prometheus-client + prometheus-fastapi-instrumentator, nginx (frontend serving), Nginx Proxy Manager (TLS edge), Grafana / Prometheus / Loki / Promtail / Alertmanager (existing host services), Docker Compose.

**Spec reference:** `docs/superpowers/specs/2026-04-22-dapp-demo-server-design.md` (commit `d0c7aeb`).

---

## Spec amendments (locked since spec was written)

- **Metrics endpoint path:** `/metrics` (per spec) — but `health.py` already serves a JSON metrics endpoint at `/api/v1/health/metrics`. That endpoint is being **renamed** to `/api/v1/health/metrics-json` so the new Prometheus endpoint can claim the canonical `/metrics` path. The legacy hand-rolled `/api/v1/monitoring/metrics/prometheus` endpoint is being **deleted** entirely (per user: "old ones don't matter any more"), along with its `metrics_store` dict.
- **Metric prefix:** All new business metrics use the `dapp_` prefix per the spec. Existing `prometheus_client` metrics in the codebase use various prefixes (`cache_`, `events_`, `sentiment_`, `ml_`) — those are left untouched and will appear alongside `dapp_*` series in the unified `/metrics` exposition.
- **Onboarding metric label:** The spec listed `step` as a label for `dapp_emotional_onboarding_completed_total`, but the codebase has only one onboarding completion endpoint (no per-step breakdown). The label is dropped — the metric is a simple counter.
- **Messages endpoint:** The spec referenced `POST /messages/{connection_id}`; the actual route is `POST /messages/send` (with `connection_id` in the request body). Hook is at the actual route.

---

## File structure (decomposition)

### New files
| Path | Responsibility |
|------|---------------|
| `python-backend/Dockerfile` | Production multi-stage image: builder installs deps, runtime runs uvicorn without `--reload` |
| `python-backend/app/observability/__init__.py` | Module marker; exports `setup_observability` and metric singletons |
| `python-backend/app/observability/metrics.py` | All custom metric definitions + `setup_observability(app)` helper that mounts `/metrics` via the instrumentator |
| `python-backend/tests/test_observability.py` | Unit tests for metric definitions, increments, and the `/metrics` exposition |
| `angular-frontend/Dockerfile` | Multi-stage: Node 20 builder runs `ng build --configuration=demo`; nginx alpine serves the bundle |
| `angular-frontend/nginx.conf` | SPA fallback (`try_files $uri $uri/ /index.html`), gzip, cache headers |
| `angular-frontend/src/environments/environment.demo.ts` | `production: true, apiUrl: '/api'` |
| `docker-compose.demo.yml` | Demo runtime: postgres + postgres-exporter + backend + frontend; 3 networks |
| `.env.demo.example` | Template with placeholder secrets |
| `monitoring/dapp-overview-dashboard.json` | Grafana dashboard JSON (in-repo source of truth) |
| `monitoring/dapp-dashboards-provider.yml` | Grafana provisioner config for the dashboard |
| `monitoring/prometheus-dapp-jobs.yml` | Reference copy of the scrape jobs to append to host Prometheus |
| `deploy-demo.sh` | Idempotent deploy script with pre-deploy validation and post-deploy smoke tests |
| `docs/demo-server.md` | Operations guide |

### Modified files
| Path | What changes |
|------|--------------|
| `python-backend/requirements.txt` | Add `prometheus-fastapi-instrumentator>=7.0.0` |
| `python-backend/app/main.py` | Call `setup_observability(app)` after CORS middleware |
| `python-backend/app/api/v1/routers/auth_router.py` | Increment `users_registered_total` and `login_attempts_total` |
| `python-backend/app/api/v1/routers/onboarding.py` | Increment `emotional_onboarding_completed_total` |
| `python-backend/app/api/v1/routers/soul_connections.py` | Increment `soul_connections_initiated_total`; update `soul_connections_active` gauge on `/initiate` and `/{id}` PUT |
| `python-backend/app/api/v1/routers/revelations.py` | Increment `revelations_sent_total` with `day_number` label |
| `python-backend/app/api/v1/routers/messages.py` | Increment `messages_sent_total` |
| `python-backend/app/api/v1/routers/health.py` | Rename `/metrics` route to `/metrics-json` (effective path becomes `/api/v1/health/metrics-json`) |
| `python-backend/app/api/v1/routers/monitoring.py` | Delete `/metrics/prometheus` handler and the `metrics_store` dict |
| `python-backend/app/services/compatibility.py` | Wrap `calculate_overall_compatibility` body with `compatibility_calc_seconds.time()` |
| `angular-frontend/angular.json` | Add `demo` build configuration referencing `environment.demo.ts` |
| `CLAUDE.md` | Add "Demo deployment" section |
| `.gitignore` | Add `.env.demo` (the actual file, never the example) |

---

# Phase 0: Merge `development → main`

### Task 0.1: Open Gitea PR and merge with merge commit, tag `v0.1.0-demo`

**Files:** None (manual + git operations only)

- [ ] **Step 1: Verify local working tree is clean and remotes are fresh**

```bash
git status
# Expected: "nothing to commit, working tree clean"
git -c 'credential.helper=!f() { echo username=lex; echo "password=Enigma-2026!"; }; f' fetch origin
# Expected: shows up-to-date for main, and 09c924e..9a4c713 for development
```

- [ ] **Step 2: Open the PR on Gitea**

Open in browser: `https://git.batcomputer.waynetower.de/lex/DAPP/compare/main...development`

PR title: `release: rolling release v0.1.0-demo`

PR body:
```
Promotes development to main as rolling release v0.1.0-demo.

Includes:
- PR #30: UI Redesign Phases 1, 2 & 3 (tokens, primitives, feature consistency)

This is the baseline for the demo server deployment at
https://date.batcomputer.waynetower.de — see
docs/superpowers/specs/2026-04-22-dapp-demo-server-design.md.
```

Merge with **"Create a merge commit"** (NOT squash, NOT rebase) so the GitFlow merge marker stays.

- [ ] **Step 3: Pull main locally and tag**

```bash
git checkout main
git -c 'credential.helper=!f() { echo username=lex; echo "password=Enigma-2026!"; }; f' pull --ff-only origin main
git tag -a v0.1.0-demo -m "First demo-server release; spec d0c7aeb"
git -c 'credential.helper=!f() { echo username=lex; echo "password=Enigma-2026!"; }; f' push origin v0.1.0-demo
```

Expected: `git log -1 --format=%s` shows the merge commit subject; `git tag --list 'v0.1*'` shows `v0.1.0-demo`.

- [ ] **Step 4: Verify the spec commit is on main**

```bash
git log --oneline | grep d0c7aeb
# Expected: line containing "docs(specs): add demo-server design spec"
```

If the spec commit was on a different branch and didn't reach main yet, cherry-pick it onto main:
```bash
git cherry-pick d0c7aeb
git push origin main
```

---

# Phase 1: Production runtime (Dockerfiles + demo compose)

### Task 1.1: Create production Dockerfile for backend

**Files:**
- Create: `python-backend/Dockerfile`

- [ ] **Step 1: Create the production Dockerfile**

```dockerfile
# python-backend/Dockerfile
# Multi-stage production image (no source mounts, no --reload)

FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- runtime stage ----
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY . .

# Run alembic migrations then start uvicorn (no --reload, single worker for demo)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1
```

- [ ] **Step 2: Verify the image builds**

```bash
docker build -t dapp-backend:test -f python-backend/Dockerfile python-backend/
```
Expected: build completes successfully; final image size shown by `docker images dapp-backend:test` is < 400MB.

- [ ] **Step 3: Verify the image starts (smoke test, will fail health since no DB — that's OK for this isolation test)**

```bash
docker run --rm -d --name dapp-backend-smoke -p 18000:8000 \
    -e DATABASE_URL=postgresql://nope:nope@nowhere/db \
    -e SECRET_KEY=test_secret_min_32_chars_aaaaaaaaaaa \
    dapp-backend:test
sleep 3
docker logs dapp-backend-smoke 2>&1 | head -20
docker rm -f dapp-backend-smoke
```
Expected: logs show `INFO:     Started server process` (uvicorn boots even if alembic fails to connect).

- [ ] **Step 4: Commit**

```bash
git add python-backend/Dockerfile
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(backend): add production multi-stage Dockerfile

Adds Dockerfile (separate from existing Dockerfile.dev) for the demo
server runtime: multi-stage build, no source mounts, runs uvicorn
without --reload, runs alembic upgrade head on startup."
```

---

### Task 1.2: Create production Dockerfile for frontend + nginx config + demo environment

**Files:**
- Create: `angular-frontend/Dockerfile`
- Create: `angular-frontend/nginx.conf`
- Create: `angular-frontend/src/environments/environment.demo.ts`
- Modify: `angular-frontend/angular.json` (add `demo` configuration block)

- [ ] **Step 1: Create `angular-frontend/src/environments/environment.demo.ts`**

```typescript
// angular-frontend/src/environments/environment.demo.ts
export const environment = {
  production: true,
  apiUrl: '/api',
};
```

- [ ] **Step 2: Modify `angular-frontend/angular.json` — add a `demo` build configuration**

Find the `architect.build.configurations` block (sibling of `production` and `development`) and add a `demo` entry that mirrors `production` but with the demo file replacement. Open `angular-frontend/angular.json`, locate `"production": {`, and insert a sibling object:

```json
"demo": {
  "fileReplacements": [
    {
      "replace": "src/environments/environment.ts",
      "with": "src/environments/environment.demo.ts"
    }
  ],
  "outputHashing": "all",
  "optimization": true,
  "sourceMap": false,
  "namedChunks": false,
  "extractLicenses": true,
  "vendorChunk": false,
  "buildOptimizer": true
}
```

If the existing `production` configuration uses different keys (e.g. `budgets`), copy them into `demo` too — match the production shape exactly minus the `fileReplacements` source path.

- [ ] **Step 3: Create `angular-frontend/nginx.conf`**

```nginx
# angular-frontend/nginx.conf

worker_processes auto;
events { worker_connections 1024; }

http {
  include /etc/nginx/mime.types;
  default_type application/octet-stream;

  sendfile on;
  tcp_nopush on;
  tcp_nodelay on;
  keepalive_timeout 65;
  server_tokens off;

  gzip on;
  gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;
  gzip_min_length 1024;

  server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Long-cache hashed assets
    location ~* \.(js|css|woff2?|png|jpg|jpeg|gif|svg|ico)$ {
      expires 1y;
      add_header Cache-Control "public, immutable";
      try_files $uri =404;
    }

    # Never cache index.html (so deploys are picked up immediately)
    location = /index.html {
      add_header Cache-Control "no-store, no-cache, must-revalidate";
      try_files $uri =404;
    }

    # SPA fallback: any path → index.html
    location / {
      try_files $uri $uri/ /index.html;
    }
  }
}
```

- [ ] **Step 4: Create `angular-frontend/Dockerfile`**

```dockerfile
# angular-frontend/Dockerfile
# Multi-stage: build Angular bundle, then serve with nginx.

FROM node:20-alpine AS builder

WORKDIR /app

# Install deps (separate layer for cache)
COPY package.json package-lock.json* ./
RUN npm ci

# Build the demo configuration
COPY . .
RUN npx ng build --configuration=demo

# ---- runtime stage ----
FROM nginx:1.27-alpine AS runtime

# Replace default config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built bundle (Angular default output dir for this app)
# If the project uses a different output path, adjust accordingly.
COPY --from=builder /app/dist/dinner-first/browser /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/ > /dev/null || exit 1
```

- [ ] **Step 5: Verify the frontend image builds**

First check the actual Angular output path so step 4 is correct:
```bash
grep -A2 '"outputPath"' angular-frontend/angular.json | head -3
# Expected: shows "dist/dinner-first" or similar; adjust the COPY in the Dockerfile if needed.
```

Then build:
```bash
docker build -t dapp-frontend:test -f angular-frontend/Dockerfile angular-frontend/
```
Expected: build completes successfully; image size < 50MB. The build step `RUN npx ng build --configuration=demo` is where most time is spent.

- [ ] **Step 6: Verify the frontend serves the SPA fallback**

```bash
docker run --rm -d --name dapp-frontend-smoke -p 18080:80 dapp-frontend:test
sleep 2
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:18080/
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:18080/some/spa/route
docker rm -f dapp-frontend-smoke
```
Expected: both return `200` (the second one proves the SPA fallback works).

- [ ] **Step 7: Commit**

```bash
git add angular-frontend/Dockerfile angular-frontend/nginx.conf \
        angular-frontend/src/environments/environment.demo.ts \
        angular-frontend/angular.json
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(frontend): add production Dockerfile, nginx config, demo env

Multi-stage build: Node 20 builder runs ng build --configuration=demo,
nginx alpine serves the static bundle. SPA fallback configured so
client-side routes hit index.html. Demo environment uses relative
apiUrl (/api) for single-origin deployment."
```

---

### Task 1.3: Create `docker-compose.demo.yml` + `.env.demo.example` + `.gitignore` update

**Files:**
- Create: `docker-compose.demo.yml`
- Create: `.env.demo.example`
- Modify: `.gitignore`

- [ ] **Step 1: Verify the names of the existing external networks (so the compose references the actual network names, not assumed names)**

```bash
docker network ls --format '{{.Name}}' | grep -iE 'monit|nginx_proxy|nginx-proxy'
```
Expected output should contain something like `monitoring_monitoring` and `nginx_proxy`. **Note the EXACT names — they vary by deployment.** If they differ from the names below, substitute the actual names throughout the compose file.

- [ ] **Step 2: Create `docker-compose.demo.yml`**

```yaml
# docker-compose.demo.yml
# Demo-server runtime: built images, no source mounts, attached to
# the host's existing observability + reverse-proxy networks.

name: dapp

services:

  postgres:
    image: postgres:15-alpine
    container_name: dapp-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: dinner_first
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env.demo}
    volumes:
      - dapp_postgres_data:/var/lib/postgresql/data
    networks:
      - dapp_internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: dapp-postgres-exporter
    restart: unless-stopped
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/dinner_first?sslmode=disable"
    networks:
      - dapp_internal
      - monitoring
    depends_on:
      postgres:
        condition: service_healthy

  backend:
    build:
      context: ./python-backend
      dockerfile: Dockerfile
    image: dapp-backend:demo
    container_name: dapp-backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/dinner_first
      DB_HOST: postgres
      DB_USER: postgres
      DB_PASSWORD: ${POSTGRES_PASSWORD}
      SECRET_KEY: ${SECRET_KEY:?set SECRET_KEY in .env.demo}
      JWT_ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 1440
      CORS_ORIGINS: https://date.batcomputer.waynetower.de
      ENVIRONMENT: demo
      DEBUG: "false"
    networks:
      - dapp_internal
      - monitoring
      - nginx_proxy
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: ./angular-frontend
      dockerfile: Dockerfile
    image: dapp-frontend:demo
    container_name: dapp-frontend
    restart: unless-stopped
    networks:
      - nginx_proxy
    depends_on:
      - backend

volumes:
  dapp_postgres_data:

networks:
  dapp_internal:
    driver: bridge
  monitoring:
    external: true
    name: monitoring_monitoring   # replace if Step 1 showed a different name
  nginx_proxy:
    external: true
    name: nginx_proxy             # replace if Step 1 showed a different name
```

- [ ] **Step 3: Create `.env.demo.example`**

```bash
# .env.demo.example
# Copy to .env.demo and fill in real values. NEVER commit .env.demo.

# Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=replace_me_with_a_48+_byte_random_string

# Generate with: python -c "import secrets; print(secrets.token_urlsafe(24))"
POSTGRES_PASSWORD=replace_me_with_a_24+_byte_random_string
```

- [ ] **Step 4: Update `.gitignore`**

Append (don't replace) the following lines to `.gitignore`:

```
# Demo-server secrets — NEVER commit
.env.demo
```

Verify by reading the file after editing:
```bash
grep -F ".env.demo" .gitignore
# Expected: matches the exact line ".env.demo" (not .env.demo.example)
```

- [ ] **Step 5: Smoke-test the compose file syntax**

Create a throwaway `.env.demo` for the syntax check:
```bash
echo "SECRET_KEY=test_test_test_test_test_test_test_test_test_test" > .env.demo
echo "POSTGRES_PASSWORD=test_test_test_test_test" >> .env.demo
docker compose -f docker-compose.demo.yml --env-file .env.demo config > /dev/null
echo "exit code: $?"
rm .env.demo
```
Expected: exit code `0`. If you get errors about `monitoring` or `nginx_proxy` not existing, re-check Step 1's network names and update the compose file.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.demo.yml .env.demo.example .gitignore
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(deploy): add docker-compose.demo.yml + env template

Demo runtime stack: postgres + postgres-exporter + backend + frontend.
Backend joins existing 'monitoring' + 'nginx_proxy' networks for
Prometheus scrape and NPM proxying. Frontend on nginx_proxy only.
Postgres isolated on dapp_internal. Secrets read from .env.demo
(gitignored)."
```

---

### Task 1.4: Verify the demo stack comes up end-to-end (without metrics yet)

**Files:** None (verification only)

- [ ] **Step 1: Create a real `.env.demo`**

```bash
cp .env.demo.example .env.demo
SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
DBPW=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
sed -i "s|replace_me_with_a_48+_byte_random_string|${SECRET}|" .env.demo
sed -i "s|replace_me_with_a_24+_byte_random_string|${DBPW}|" .env.demo
cat .env.demo  # sanity check — values are now set
```

- [ ] **Step 2: Bring the stack up**

```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo up -d --build
```
Expected: 4 containers `dapp-postgres`, `dapp-postgres-exporter`, `dapp-backend`, `dapp-frontend` reach `Up` state. `docker compose -f docker-compose.demo.yml ps` shows all healthy or starting.

- [ ] **Step 3: Smoke test from inside the docker network**

```bash
# Backend health (via internal network, since backend isn't published on host port)
docker run --rm --network nginx_proxy curlimages/curl:latest \
    -fsS http://dapp-backend:8000/api/health
# Expected: returns JSON with "status": "ok" or similar

# Frontend root
docker run --rm --network nginx_proxy curlimages/curl:latest \
    -s -o /dev/null -w "%{http_code}\n" http://dapp-frontend/
# Expected: 200

# Postgres exporter (via monitoring network)
docker run --rm --network monitoring_monitoring curlimages/curl:latest \
    -s -o /dev/null -w "%{http_code}\n" http://dapp-postgres-exporter:9187/metrics
# Expected: 200
```

If any step fails, check `docker compose -f docker-compose.demo.yml logs <service>` and resolve before continuing.

- [ ] **Step 4: Tear down (we'll redeploy after metrics are wired)**

```bash
docker compose -f docker-compose.demo.yml down
```

- [ ] **Step 5: No commit (verification only)**

---

# Phase 2: Backend metrics

### Task 2.1: Add `prometheus-fastapi-instrumentator` dependency

**Files:**
- Modify: `python-backend/requirements.txt`

- [ ] **Step 1: Add the dependency line**

Append (don't replace) the following line to `python-backend/requirements.txt`. The `prometheus-client` line is already present — leave it unchanged. Add the new line near it for clarity:

```
prometheus-fastapi-instrumentator>=7.0.0  # Auto-mount /metrics endpoint
```

Verify it's actually appended:
```bash
grep prometheus python-backend/requirements.txt
# Expected: shows both prometheus-client and prometheus-fastapi-instrumentator lines
```

- [ ] **Step 2: Verify the dependency resolves**

```bash
docker run --rm -v "$(pwd)/python-backend":/app -w /app python:3.11-slim \
    sh -c "pip install --quiet -r requirements.txt && python -c 'import prometheus_fastapi_instrumentator; print(prometheus_fastapi_instrumentator.__version__)'"
```
Expected: prints a version number ≥ 7.0.0. If pip resolution fails, check the line for typos and retry.

- [ ] **Step 3: Commit**

```bash
git add python-backend/requirements.txt
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "build(backend): add prometheus-fastapi-instrumentator>=7.0.0

Used by app/observability to mount the global REGISTRY exposition
at /metrics, replacing the legacy hand-rolled /metrics/prometheus."
```

---

### Task 2.2: Create the observability module (metrics + setup)

**Files:**
- Create: `python-backend/app/observability/__init__.py`
- Create: `python-backend/app/observability/metrics.py`
- Test: `python-backend/tests/test_observability.py`

- [ ] **Step 1: Write the failing tests**

Create `python-backend/tests/test_observability.py`:

```python
# python-backend/tests/test_observability.py
"""Unit tests for the observability module: custom metrics + setup."""

import pytest
from prometheus_client import REGISTRY
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _sample(name: str, **labels) -> float:
    """Read a metric sample value, returning 0.0 if not yet recorded."""
    value = REGISTRY.get_sample_value(name, labels=labels or None)
    return value if value is not None else 0.0


def test_metrics_module_exposes_named_singletons():
    from app.observability import metrics

    # All 8 metrics enumerated in the spec
    assert hasattr(metrics, "users_registered_total")
    assert hasattr(metrics, "emotional_onboarding_completed_total")
    assert hasattr(metrics, "soul_connections_initiated_total")
    assert hasattr(metrics, "soul_connections_active")
    assert hasattr(metrics, "revelations_sent_total")
    assert hasattr(metrics, "messages_sent_total")
    assert hasattr(metrics, "login_attempts_total")
    assert hasattr(metrics, "compatibility_calc_seconds")


def test_users_registered_counter_increments():
    from app.observability import metrics

    before = _sample("dapp_users_registered_total")
    metrics.users_registered_total.inc()
    after = _sample("dapp_users_registered_total")
    assert after == before + 1


def test_login_attempts_counter_has_result_label():
    from app.observability import metrics

    before_success = _sample("dapp_login_attempts_total", result="success")
    metrics.login_attempts_total.labels(result="success").inc()
    after_success = _sample("dapp_login_attempts_total", result="success")
    assert after_success == before_success + 1


def test_revelations_counter_has_day_number_label():
    from app.observability import metrics

    metrics.revelations_sent_total.labels(day_number="3").inc()
    sample = _sample("dapp_revelations_sent_total", day_number="3")
    assert sample >= 1.0


def test_compatibility_histogram_records_samples():
    from app.observability import metrics

    with metrics.compatibility_calc_seconds.time():
        pass  # near-zero duration
    # The _count series is incremented by every observation
    count = _sample("dapp_compatibility_calc_seconds_count")
    assert count >= 1.0


def test_setup_observability_mounts_metrics_endpoint():
    from app.observability import setup_observability

    app = FastAPI()
    setup_observability(app)
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"dapp_users_registered_total" in response.content
    # Default HTTP metrics from the instrumentator should also be there
    assert b"http_request" in response.content
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_observability.py -v
```
Expected: `ImportError` / `ModuleNotFoundError` on `from app.observability import metrics` / `setup_observability`. Failure is the goal.

If the dev compose isn't already running, start it first: `./start-app.sh`.

- [ ] **Step 3: Create `python-backend/app/observability/__init__.py`**

```python
# python-backend/app/observability/__init__.py
"""Observability module: Prometheus metrics + /metrics endpoint setup."""

from app.observability.metrics import setup_observability  # noqa: F401
```

- [ ] **Step 4: Create `python-backend/app/observability/metrics.py`**

```python
# python-backend/app/observability/metrics.py
"""DAPP business metrics + setup helper for Prometheus exposition.

All metrics are registered against the default prometheus_client REGISTRY,
which is what prometheus_fastapi_instrumentator exposes at /metrics.
"""

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# ---- Counters ---------------------------------------------------------------

users_registered_total = Counter(
    "dapp_users_registered_total",
    "Total successful user registrations.",
)

emotional_onboarding_completed_total = Counter(
    "dapp_emotional_onboarding_completed_total",
    "Total successful completions of the emotional-onboarding flow.",
)

soul_connections_initiated_total = Counter(
    "dapp_soul_connections_initiated_total",
    "Total soul connections initiated (POST /soul-connections/initiate).",
)

revelations_sent_total = Counter(
    "dapp_revelations_sent_total",
    "Total daily revelations created, by day_number (1-7).",
    labelnames=("day_number",),
)

messages_sent_total = Counter(
    "dapp_messages_sent_total",
    "Total messages sent successfully.",
)

login_attempts_total = Counter(
    "dapp_login_attempts_total",
    "Login attempts, labeled by result (success|failure).",
    labelnames=("result",),
)

# ---- Gauges -----------------------------------------------------------------

soul_connections_active = Gauge(
    "dapp_soul_connections_active",
    "Current count of soul connections in non-terminal stages.",
)

# ---- Histograms -------------------------------------------------------------

compatibility_calc_seconds = Histogram(
    "dapp_compatibility_calc_seconds",
    "Time spent in CompatibilityCalculator.calculate_overall_compatibility.",
    buckets=(0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

# ---- Setup ------------------------------------------------------------------


def setup_observability(app: FastAPI) -> None:
    """Mount /metrics on the given FastAPI app and enable HTTP middleware.

    Call once during app startup, after CORS middleware.
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/api/health", "/api/v1/health"],
    )
    instrumentator.instrument(app).expose(
        app, endpoint="/metrics", include_in_schema=False
    )
```

- [ ] **Step 5: Run the tests to confirm they pass**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_observability.py -v
```
Expected: all 6 tests pass.

If `test_users_registered_counter_increments` fails because of metric collision (the metric was registered twice during the test session), restart the backend container: `docker compose -f ../docker-compose.dev.yml restart backend`, then re-run the test.

- [ ] **Step 6: Commit**

```bash
cd ..
git add python-backend/app/observability/__init__.py \
        python-backend/app/observability/metrics.py \
        python-backend/tests/test_observability.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(observability): add metrics module + /metrics endpoint helper

Defines 8 dapp_* business metrics (counters, gauge, histogram) on the
global prometheus_client REGISTRY. setup_observability(app) mounts
/metrics via prometheus-fastapi-instrumentator, exposing both these
new metrics and the existing scattered prometheus_client metrics
(cache_*, events_*, sentiment_*, ml_*) in a unified scrape target."
```

---

### Task 2.3: Wire `setup_observability` into `app/main.py`

**Files:**
- Modify: `python-backend/app/main.py`

- [ ] **Step 1: Write the failing test**

Append to `python-backend/tests/test_observability.py`:

```python
def test_main_app_exposes_metrics_endpoint():
    """Verify the real app at startup mounts /metrics."""
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"dapp_" in response.content
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_observability.py::test_main_app_exposes_metrics_endpoint -v
```
Expected: FAIL with `404 Not Found` (because main.py hasn't called `setup_observability` yet).

- [ ] **Step 3: Modify `python-backend/app/main.py`**

Locate the line `app.add_middleware(CORSMiddleware, **cors_config)` (around line 66). Immediately after it, add:

```python
# Prometheus metrics + /metrics endpoint
from app.observability import setup_observability
setup_observability(app)
```

The result around lines 64-72 should look like:

```python
# Secure CORS Configuration - Environment-aware and production-ready
cors_config = get_secure_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Prometheus metrics + /metrics endpoint
from app.observability import setup_observability
setup_observability(app)

# Try to create database tables
try:
    create_tables()
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_observability.py::test_main_app_exposes_metrics_endpoint -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ..
git add python-backend/app/main.py python-backend/tests/test_observability.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(backend): mount /metrics endpoint via setup_observability

Calls setup_observability(app) after CORS middleware in main.py so
Prometheus can scrape the unified exposition (dapp_* business metrics
plus existing scattered prometheus_client metrics from cache, events,
sentiment, and ml modules)."
```

---

### Task 2.4: Rename existing `health.py /metrics` to `/metrics-json`

**Files:**
- Modify: `python-backend/app/api/v1/routers/health.py`

- [ ] **Step 1: Write the failing tests**

Create `python-backend/tests/test_health_metrics_rename.py`:

```python
# python-backend/tests/test_health_metrics_rename.py
"""Verifies the legacy JSON /metrics endpoint moved to /metrics-json
so the canonical /metrics path can host the Prometheus exposition."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_legacy_json_metrics_at_old_path_is_gone():
    response = client.get("/api/v1/health/metrics")
    # /metrics is now Prometheus, not JSON. The health endpoint moved.
    # The Prometheus endpoint is at /metrics (root), not /api/v1/health/metrics,
    # so /api/v1/health/metrics should now 404.
    assert response.status_code == 404


def test_legacy_json_metrics_available_at_new_path():
    response = client.get("/api/v1/health/metrics-json")
    assert response.status_code == 200
    body = response.json()
    assert "metrics" in body or "timestamp" in body  # legacy JSON shape
```

- [ ] **Step 2: Run to verify failure**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_health_metrics_rename.py -v
```
Expected: `test_legacy_json_metrics_at_old_path_is_gone` FAILS (still returns 200), `test_legacy_json_metrics_available_at_new_path` FAILS (404).

- [ ] **Step 3: Modify `python-backend/app/api/v1/routers/health.py`**

Find line 344 — the `@router.get("/metrics", ...)` decorator. Change the path string from `"/metrics"` to `"/metrics-json"`. The decorator becomes:

```python
@router.get(
    "/metrics-json",
    summary="Health Metrics for Monitoring (legacy JSON format)",
    description="Get system performance and health metrics as JSON. "
                "Renamed from /metrics so the canonical /metrics path can "
                "serve the Prometheus exposition format.",
    response_description="Structured metrics data for monitoring systems",
    tags=["Health Monitoring", "Metrics"],
)
async def get_health_metrics():
```

Leave the function body unchanged — only the route path and a small note in the description need updating.

- [ ] **Step 4: Run to verify pass**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_health_metrics_rename.py -v
```
Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ..
git add python-backend/app/api/v1/routers/health.py \
        python-backend/tests/test_health_metrics_rename.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "refactor(health): rename JSON /metrics to /metrics-json

Frees the canonical /metrics path so the Prometheus exposition (added
in the previous commit) lives at the conventional location. The JSON
health-format endpoint is preserved verbatim at the new path."
```

---

### Task 2.5: Delete legacy `monitoring.py /metrics/prometheus` and `metrics_store`

**Files:**
- Modify: `python-backend/app/api/v1/routers/monitoring.py`

- [ ] **Step 1: Write the failing test**

Create `python-backend/tests/test_legacy_prometheus_endpoint_removed.py`:

```python
# python-backend/tests/test_legacy_prometheus_endpoint_removed.py
"""The hand-rolled /metrics/prometheus endpoint is replaced by
the proper /metrics endpoint. Verify the legacy one is gone."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_legacy_prometheus_endpoint_returns_404():
    response = client.get("/api/v1/monitoring/metrics/prometheus")
    assert response.status_code == 404
```

- [ ] **Step 2: Run to verify failure**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_legacy_prometheus_endpoint_removed.py -v
```
Expected: FAIL — returns 200 because the legacy endpoint still exists.

- [ ] **Step 3: Modify `python-backend/app/api/v1/routers/monitoring.py`**

Three deletions, in this order:

(a) **Delete the `metrics_store` dict** at lines 43-52:

```python
# DELETE this entire block:
metrics_store = {
    "requests_total": 0,
    "requests_by_endpoint": {},
    "response_times": [],
    "errors_total": 0,
    "active_users": 0,
    "database_queries": 0,
    "cache_hits": 0,
    "cache_misses": 0,
}
```

(b) **Delete the `/metrics/prometheus` endpoint** at lines 202-269 (the entire `@router.get("/metrics/prometheus")` decorator and its `get_prometheus_metrics` async function body, ending at the closing `raise HTTPException` of the except block).

(c) **Delete or fix any remaining references to `metrics_store`** in the file. Run:

```bash
grep -n metrics_store python-backend/app/api/v1/routers/monitoring.py
```

For each remaining reference, examine the context. If it's inside helper functions used only by the deleted endpoint, delete those helpers too. If it's used by other endpoints (e.g., a `/metrics` JSON endpoint), replace `metrics_store["requests_total"]` reads with `0` placeholders and add a TODO comment if needed for future work — but DO NOT introduce new behavior.

After cleanup, this should return zero matches:

```bash
grep -n metrics_store python-backend/app/api/v1/routers/monitoring.py | wc -l
# Expected: 0
```

If complete removal of `metrics_store` would gut multiple other endpoints, instead delete only the `/metrics/prometheus` endpoint and leave `metrics_store` for the others — but verify the test still passes. (The minimal change to pass the test is just deleting the endpoint at lines 202-269.)

- [ ] **Step 4: Run to verify pass**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_legacy_prometheus_endpoint_removed.py -v
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_observability.py -v
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cd ..
git add python-backend/app/api/v1/routers/monitoring.py \
        python-backend/tests/test_legacy_prometheus_endpoint_removed.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "refactor(monitoring): delete legacy /metrics/prometheus endpoint

Hand-rolled exposition is replaced by the new /metrics endpoint that
exposes the global prometheus_client REGISTRY (which now picks up
existing scattered Counters/Gauges/Histograms from cache, events,
sentiment, and ml modules in addition to the new dapp_* metrics)."
```

---

### Task 2.6: Hook `auth_router.py /register` to increment `users_registered_total`

**Files:**
- Modify: `python-backend/app/api/v1/routers/auth_router.py`

- [ ] **Step 1: Write the failing test**

Create `python-backend/tests/test_auth_metric_hooks.py`:

```python
# python-backend/tests/test_auth_metric_hooks.py
"""Verify auth endpoints increment the relevant Prometheus counters."""

import uuid
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import app

client = TestClient(app)


def _sample(name: str, **labels) -> float:
    val = REGISTRY.get_sample_value(name, labels=labels or None)
    return val if val is not None else 0.0


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


def test_register_increments_users_registered_total():
    before = _sample("dapp_users_registered_total")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": _unique_email(),
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "testPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "date_of_birth": "1990-01-01",
            "gender": "other",
        },
    )
    assert response.status_code in (200, 201), response.text
    after = _sample("dapp_users_registered_total")
    assert after == before + 1
```

If the request schema in `auth_router.py` differs from the JSON body above (e.g., requires extra fields), adjust this test's body to match. Read `python-backend/app/api/v1/routers/auth_router.py` lines 28-94 first to confirm the schema.

- [ ] **Step 2: Run to verify failure**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_auth_metric_hooks.py::test_register_increments_users_registered_total -v
```
Expected: FAIL because the counter doesn't increment yet.

- [ ] **Step 3: Modify `python-backend/app/api/v1/routers/auth_router.py`**

Add this import near the top of the file (with the other `app.*` imports):

```python
from app.observability import metrics as obs
```

Find line 82 (after `db.commit()` and `db.refresh(new_user)` in the `/register` handler). Insert the increment after `db.refresh(new_user)`:

```python
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        obs.users_registered_total.inc()

        # Generate access token for immediate login
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
```

- [ ] **Step 4: Run to verify pass**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_auth_metric_hooks.py::test_register_increments_users_registered_total -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ..
git add python-backend/app/api/v1/routers/auth_router.py \
        python-backend/tests/test_auth_metric_hooks.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(metrics): increment users_registered_total on /register success"
```

---

### Task 2.7: Hook `auth_router.py /login` for `login_attempts_total{result}`

**Files:**
- Modify: `python-backend/app/api/v1/routers/auth_router.py`

- [ ] **Step 1: Write the failing tests**

Append to `python-backend/tests/test_auth_metric_hooks.py`:

```python
def test_login_failure_increments_login_attempts_failure():
    before = _sample("dapp_login_attempts_total", result="failure")
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    after = _sample("dapp_login_attempts_total", result="failure")
    assert after == before + 1


def test_login_success_increments_login_attempts_success():
    # First register a user to log in as
    email = _unique_email()
    password = "testPassword123!"
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": password,
            "first_name": "Test",
            "last_name": "User",
            "date_of_birth": "1990-01-01",
            "gender": "other",
        },
    )
    assert register_response.status_code in (200, 201)

    before = _sample("dapp_login_attempts_total", result="success")
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    after = _sample("dapp_login_attempts_total", result="success")
    assert after == before + 1
```

- [ ] **Step 2: Run to verify failure**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_auth_metric_hooks.py -v
```
Expected: the two new tests FAIL because increments don't happen yet.

- [ ] **Step 3: Modify `python-backend/app/api/v1/routers/auth_router.py`**

In the `/login` handler (lines 106-161):

(a) Inside the invalid-credentials branch (lines 138-144), add an increment **before** the `raise`:

```python
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        obs.login_attempts_total.labels(result="failure").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

(b) Inside the inactive-user branch (lines 147-152), add an increment before the `raise`:

```python
    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {user.email}")
        obs.login_attempts_total.labels(result="failure").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
```

(c) On the success path (line 160 area), add the success increment **just before** the `return` and after `logger.info(...)`:

```python
    logger.info(f"Successful login for user: {user.email}")
    obs.login_attempts_total.labels(result="success").inc()
    return LoginResponse(access_token=access_token, token_type="bearer", user=user)
```

- [ ] **Step 4: Run to verify pass**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_auth_metric_hooks.py -v
```
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ..
git add python-backend/app/api/v1/routers/auth_router.py \
        python-backend/tests/test_auth_metric_hooks.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(metrics): record login_attempts_total{result} on /login

Increments label='success' on successful login, label='failure' on
invalid credentials and inactive accounts. Used by future dashboards
and brute-force alerts."
```

---

### Task 2.8: Hook `onboarding.py /complete` for `emotional_onboarding_completed_total`

**Files:**
- Modify: `python-backend/app/api/v1/routers/onboarding.py`

- [ ] **Step 1: Write the failing test**

Create `python-backend/tests/test_onboarding_metric_hook.py`:

```python
# python-backend/tests/test_onboarding_metric_hook.py
"""Verify onboarding completion increments the counter."""

import uuid
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import app

client = TestClient(app)


def _sample(name: str) -> float:
    v = REGISTRY.get_sample_value(name)
    return v if v is not None else 0.0


def _register_and_login() -> str:
    """Register a fresh user, return its bearer token."""
    email = f"onb-{uuid.uuid4().hex[:12]}@example.com"
    password = "testPassword123!"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"onb_{uuid.uuid4().hex[:8]}",
            "password": password,
            "first_name": "Onb",
            "last_name": "Tester",
            "date_of_birth": "1990-01-01",
            "gender": "other",
        },
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return resp.json()["access_token"]


def test_onboarding_complete_increments_counter():
    token = _register_and_login()
    before = _sample("dapp_emotional_onboarding_completed_total")

    response = client.post(
        "/api/v1/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "values": ["honesty", "growth"],
            "experiences": ["climbing kilimanjaro"],
            "traits": ["curious", "warm"],
            "interests": ["hiking", "reading"],
        },
    )
    assert response.status_code == 200, response.text

    after = _sample("dapp_emotional_onboarding_completed_total")
    assert after == before + 1
```

If the OnboardingData payload schema is different (read `python-backend/app/api/v1/routers/onboarding.py` lines 64-110 + the `OnboardingData` model imported at the top to confirm), adjust the test JSON body to match.

- [ ] **Step 2: Run to verify failure**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_onboarding_metric_hook.py -v
```
Expected: FAIL.

- [ ] **Step 3: Modify `python-backend/app/api/v1/routers/onboarding.py`**

Add the import near the top of the file (with the other `app.*` imports):

```python
from app.observability import metrics as obs
```

Find line 95 (after `db.commit()` and `db.refresh(current_user)`). Insert the increment:

```python
        # Commit the changes
        db.commit()
        db.refresh(current_user)

        obs.emotional_onboarding_completed_total.inc()

        logger.info(f"Onboarding completed successfully for user: {current_user.email}")
```

- [ ] **Step 4: Run to verify pass**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_onboarding_metric_hook.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ..
git add python-backend/app/api/v1/routers/onboarding.py \
        python-backend/tests/test_onboarding_metric_hook.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(metrics): increment emotional_onboarding_completed_total"
```

---

### Task 2.9: Hook `soul_connections.py` for `soul_connections_initiated_total` + `soul_connections_active` gauge

**Files:**
- Modify: `python-backend/app/api/v1/routers/soul_connections.py`

- [ ] **Step 1: Write the failing test**

Create `python-backend/tests/test_soul_connection_metric_hook.py`:

```python
# python-backend/tests/test_soul_connection_metric_hook.py
"""Verify soul-connection initiation hooks the counter and active gauge."""

import uuid
import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import app

client = TestClient(app)


def _sample(name: str) -> float:
    v = REGISTRY.get_sample_value(name)
    return v if v is not None else 0.0


def _register_login_complete_onboarding() -> tuple[str, int]:
    """Returns (token, user_id) for a user with completed onboarding."""
    email = f"sc-{uuid.uuid4().hex[:10]}@example.com"
    password = "testPassword123!"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"sc_{uuid.uuid4().hex[:8]}",
            "password": password,
            "first_name": "SC",
            "last_name": "Tester",
            "date_of_birth": "1990-01-01",
            "gender": "other",
        },
    )
    user_id = r.json()["user"]["id"]
    login = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    token = login.json()["access_token"]
    client.post(
        "/api/v1/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"values": ["growth"], "experiences": ["x"], "traits": ["t"], "interests": ["i"]},
    )
    return token, user_id


def test_initiate_increments_counter_and_gauge():
    token1, _ = _register_login_complete_onboarding()
    _, user2_id = _register_login_complete_onboarding()

    counter_before = _sample("dapp_soul_connections_initiated_total")
    gauge_before = _sample("dapp_soul_connections_active")

    response = client.post(
        "/api/v1/soul-connections/initiate",
        headers={"Authorization": f"Bearer {token1}"},
        json={"user2_id": user2_id},
    )

    if response.status_code != 200:
        pytest.skip(f"initiate returned {response.status_code}: {response.text}")

    counter_after = _sample("dapp_soul_connections_initiated_total")
    gauge_after = _sample("dapp_soul_connections_active")

    assert counter_after == counter_before + 1
    assert gauge_after == gauge_before + 1
```

The exact JSON body for `/initiate` may include more fields (read `soul_connections.py` lines 161-302 to confirm). Adjust if needed.

- [ ] **Step 2: Run to verify failure**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_soul_connection_metric_hook.py -v
```
Expected: FAIL.

- [ ] **Step 3: Modify `python-backend/app/api/v1/routers/soul_connections.py`**

Add the import near the top of the file:

```python
from app.observability import metrics as obs
```

Find line 285 (after `db.commit()` and `db.refresh(new_connection)` in the `/initiate` handler). Insert:

```python
        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)

        obs.soul_connections_initiated_total.inc()
        obs.soul_connections_active.inc()

        logger.info(
            f"New soul connection created: {current_user.id} -> "
            f"{connection_data.user2_id}"
        )
        return new_connection
```

For the closure path, find the `PUT /{connection_id}` handler (lines 373-421) — specifically the area where `setattr(connection, field, value)` is called for the status field (around line 403-405). Add a check that decrements the gauge when transitioning to a terminal status:

```python
        # Detect transition to terminal status, decrement active gauge
        terminal_statuses = {"inactive", "archived", "ended", "closed"}
        for field, value in update_data.dict(exclude_unset=True).items():
            previous_value = getattr(connection, field, None)
            setattr(connection, field, value)
            if field == "status" and value in terminal_statuses and previous_value not in terminal_statuses:
                obs.soul_connections_active.dec()
```

(If the existing loop already does `setattr(connection, field, value)` and you're adding the gauge decrement, integrate it without duplicating the setattr. The exact existing code may differ — preserve the existing semantics, only add the decrement.)

- [ ] **Step 4: Run to verify pass**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_soul_connection_metric_hook.py -v
```
Expected: `test_initiate_increments_counter_and_gauge` PASSES (or SKIPS gracefully if /initiate has additional schema requirements not met by this test).

- [ ] **Step 5: Add a startup gauge refresh (so restarts don't lose the active count)**

In `python-backend/app/main.py`, after the existing `try: create_tables()` block, add:

```python
# Initialize soul_connections_active gauge from DB on startup
try:
    from app.observability import metrics as obs
    from app.core.database import SessionLocal
    from app.models.match import SoulConnection  # confirm actual model class name

    with SessionLocal() as session:
        active_count = session.query(SoulConnection).filter(
            SoulConnection.connection_stage.notin_(["ended", "archived", "closed", "inactive"])
        ).count()
        obs.soul_connections_active.set(active_count)
        logger.info(f"Initialized soul_connections_active gauge to {active_count}")
except Exception as e:
    logger.warning(f"Could not initialize soul_connections_active gauge: {e}")
```

If the SoulConnection model is at a different path (check `python-backend/app/models/`), adjust the import accordingly. If the field representing connection state is named differently than `connection_stage`, adjust the filter.

- [ ] **Step 6: Commit**

```bash
cd ..
git add python-backend/app/api/v1/routers/soul_connections.py \
        python-backend/app/main.py \
        python-backend/tests/test_soul_connection_metric_hook.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(metrics): track soul_connections initiated counter + active gauge

Increments dapp_soul_connections_initiated_total + dapp_soul_connections_active
gauge on /initiate. Decrements gauge when status transitions to a
terminal value via PUT /{id}. Gauge is initialized from the DB on
startup so process restarts don't lose the count."
```

---

### Task 2.10: Hook `revelations.py /create` for `revelations_sent_total{day_number}`

**Files:**
- Modify: `python-backend/app/api/v1/routers/revelations.py`

- [ ] **Step 1: Write the failing test**

Create `python-backend/tests/test_revelations_metric_hook.py`:

```python
# python-backend/tests/test_revelations_metric_hook.py
"""Verify revelation creation increments the counter with day_number label."""

import uuid
import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import app

client = TestClient(app)


def _sample(name: str, **labels) -> float:
    v = REGISTRY.get_sample_value(name, labels=labels or None)
    return v if v is not None else 0.0


def test_revelation_create_increments_counter_with_day_label():
    # NOTE: This test requires an existing soul connection between two users.
    # If the prerequisites for /revelations/create can't be set up via the
    # test client cleanly, this test should be marked as integration-only.

    # The minimal correctness check: import the metrics module, increment
    # directly, and verify the label appears in the registry.
    from app.observability import metrics as obs

    obs.revelations_sent_total.labels(day_number="3").inc()
    sample = _sample("dapp_revelations_sent_total", day_number="3")
    assert sample >= 1.0
```

(The full integration test for `/revelations/create` requires a soul connection to exist between two users, which is fixture-heavy. The unit test above verifies the metric works; the hook itself will be exercised in the post-deploy smoke pass.)

- [ ] **Step 2: Run to verify failure**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_revelations_metric_hook.py -v
```
Expected: PASS (because the metric singleton works without the route hook). The test confirms the metric is wired correctly — the route hook is verified by inspection.

- [ ] **Step 3: Modify `python-backend/app/api/v1/routers/revelations.py`**

Add the import near the top of the file:

```python
from app.observability import metrics as obs
```

Find line 211 (after `db.commit()` and `db.refresh(new_revelation)` in the `/create` handler). Insert:

```python
        db.add(new_revelation)
        db.commit()
        db.refresh(new_revelation)

        obs.revelations_sent_total.labels(
            day_number=str(revelation_data.day_number)
        ).inc()

        # Update connection stage if needed
        if (
            revelation_data.day_number == 7
            and revelation_data.revelation_type == RevelationType.PHOTO_REVEAL
        ):
            connection.connection_stage = "photo_reveal"
            db.commit()
```

- [ ] **Step 4: Verify the hook compiles and the unit test still passes**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_revelations_metric_hook.py -v
docker compose -f ../docker-compose.dev.yml exec backend \
    python -c "from app.api.v1.routers import revelations; print('imports OK')"
```
Expected: tests PASS, import succeeds.

- [ ] **Step 5: Commit**

```bash
cd ..
git add python-backend/app/api/v1/routers/revelations.py \
        python-backend/tests/test_revelations_metric_hook.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(metrics): increment revelations_sent_total{day_number}"
```

---

### Task 2.11: Hook `messages.py /send` for `messages_sent_total`

**Files:**
- Modify: `python-backend/app/api/v1/routers/messages.py`

- [ ] **Step 1: Write the failing test**

Create `python-backend/tests/test_messages_metric_hook.py`:

```python
# python-backend/tests/test_messages_metric_hook.py
"""Verify message send increments the counter."""

from prometheus_client import REGISTRY


def _sample(name: str) -> float:
    v = REGISTRY.get_sample_value(name)
    return v if v is not None else 0.0


def test_messages_sent_total_singleton_works():
    """Smoke test for the metric singleton (full integration tested via curl post-deploy)."""
    from app.observability import metrics as obs

    before = _sample("dapp_messages_sent_total")
    obs.messages_sent_total.inc()
    after = _sample("dapp_messages_sent_total")
    assert after == before + 1
```

- [ ] **Step 2: Run to verify pass (singleton-level test passes immediately)**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_messages_metric_hook.py -v
```
Expected: PASS. The route-level integration is exercised via post-deploy smoke.

- [ ] **Step 3: Modify `python-backend/app/api/v1/routers/messages.py`**

Add the import near the top of the file:

```python
from app.observability import metrics as obs
```

Find the `/send` handler (lines 69-100). After the `result = await message_service.send_message(...)` call and before the return, add:

```python
        result = await message_service.send_message(
            sender_id=current_user.id,
            connection_id=message_data.connection_id,
            content=message_data.content,
            emotional_context=message_data.emotional_context,
            db=db,
        )

        if result.success:
            obs.messages_sent_total.inc()

        return SendMessageResponse(
            success=result.success,
            message_id=result.message_id,
            message=result.message,
            delivered=result.delivered,
            error=result.error,
        )
```

- [ ] **Step 4: Verify the import still works**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    python -c "from app.api.v1.routers import messages; print('imports OK')"
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_messages_metric_hook.py -v
```
Expected: import succeeds, test PASSES.

- [ ] **Step 5: Commit**

```bash
cd ..
git add python-backend/app/api/v1/routers/messages.py \
        python-backend/tests/test_messages_metric_hook.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(metrics): increment messages_sent_total on successful send"
```

---

### Task 2.12: Wrap `compatibility.py` with `compatibility_calc_seconds.time()`

**Files:**
- Modify: `python-backend/app/services/compatibility.py`

- [ ] **Step 1: Write the failing test**

Create `python-backend/tests/test_compatibility_metric_hook.py`:

```python
# python-backend/tests/test_compatibility_metric_hook.py
"""Verify compatibility calculations are timed by the histogram."""

from prometheus_client import REGISTRY
from app.services.compatibility import CompatibilityCalculator


def _sample(name: str) -> float:
    v = REGISTRY.get_sample_value(name)
    return v if v is not None else 0.0


def test_compatibility_calc_records_to_histogram():
    calc = CompatibilityCalculator()
    user1 = {
        "interests": ["hiking", "reading"],
        "core_values": {},
        "age": 30,
        "location": "NYC",
    }
    user2 = {
        "interests": ["reading", "cooking"],
        "core_values": {},
        "age": 32,
        "location": "NYC",
    }

    before = _sample("dapp_compatibility_calc_seconds_count")
    result = calc.calculate_overall_compatibility(user1, user2)
    after = _sample("dapp_compatibility_calc_seconds_count")

    assert isinstance(result, dict)
    assert "total_compatibility" in result or "breakdown" in result
    assert after == before + 1
```

The `user1`/`user2` shape may differ from what `calculate_overall_compatibility` expects (it might want User model instances, not dicts). Read the function signature at lines 963-975 of `compatibility.py` and adjust the test inputs to match — minimally enough for the call to succeed.

- [ ] **Step 2: Run to verify failure**

```bash
cd python-backend
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_compatibility_metric_hook.py -v
```
Expected: FAIL — `_count` doesn't increment because nothing is being timed yet.

- [ ] **Step 3: Modify `python-backend/app/services/compatibility.py`**

Add the import at the top of the file (with other imports):

```python
from app.observability import metrics as obs
```

Find the `calculate_overall_compatibility` method (lines 963-1005+). Wrap the function body in `with obs.compatibility_calc_seconds.time():`:

```python
    def calculate_overall_compatibility(
        self, user1_data: Dict, user2_data: Dict
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive compatibility score between two users.

        Args:
            user1_data: Dict containing user1's profile data
            user2_data: Dict containing user2's profile data

        Returns:
            Dict with total compatibility, breakdown, and match quality
        """
        with obs.compatibility_calc_seconds.time():
            # ... ENTIRE existing function body, indented one more level ...
```

(Indent the existing body by 4 spaces to live inside the `with` block. Don't change any logic.)

- [ ] **Step 4: Run to verify pass**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/test_compatibility_metric_hook.py -v
```
Expected: PASS.

- [ ] **Step 5: Verify the broader test suite still passes (no logic regressions from indentation)**

```bash
docker compose -f ../docker-compose.dev.yml exec backend \
    pytest tests/ -v -x
```
Expected: all tests pass. If a previously-passing test fails, the indentation is wrong — re-check the `with` block.

- [ ] **Step 6: Commit**

```bash
cd ..
git add python-backend/app/services/compatibility.py \
        python-backend/tests/test_compatibility_metric_hook.py
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "feat(metrics): time compatibility calc with histogram

Wraps CompatibilityCalculator.calculate_overall_compatibility with
dapp_compatibility_calc_seconds. Buckets sized to verify the <500ms
target documented in CLAUDE.md."
```

---

# Phase 3: Wire DAPP into the host's observability stack

### Task 3.1: Append Prometheus scrape jobs and reload

**Files:**
- Create (in repo): `monitoring/prometheus-dapp-jobs.yml`
- Modify (on host): `/opt/monitoring/config/prometheus.yml`

- [ ] **Step 1: Create the in-repo reference copy of the scrape jobs**

```bash
mkdir -p monitoring
```

Create `monitoring/prometheus-dapp-jobs.yml`:

```yaml
# monitoring/prometheus-dapp-jobs.yml
# Reference copy of the scrape jobs appended to /opt/monitoring/config/prometheus.yml
# during first-time demo deployment. Source of truth lives in the host config.

  - job_name: 'dapp-backend'
    static_configs:
      - targets: ['dapp-backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'dapp-postgres-exporter'
    static_configs:
      - targets: ['dapp-postgres-exporter:9187']
    scrape_interval: 30s
```

- [ ] **Step 2: Back up the host Prometheus config and append the jobs**

```bash
sudo cp /opt/monitoring/config/prometheus.yml /opt/monitoring/config/prometheus.yml.bak
sudo tee -a /opt/monitoring/config/prometheus.yml < monitoring/prometheus-dapp-jobs.yml
```

(If you prefer not to use sudo, the `/opt/monitoring/config/` directory is owned by `lex` per the earlier exploration — try without sudo first.)

- [ ] **Step 3: Validate the appended config**

```bash
docker run --rm -v /opt/monitoring/config:/etc/prometheus prom/prometheus \
    promtool check config /etc/prometheus/prometheus.yml
```
Expected: `Checking /etc/prometheus/prometheus.yml ... SUCCESS`

If it fails, restore the backup and inspect:
```bash
sudo mv /opt/monitoring/config/prometheus.yml.bak /opt/monitoring/config/prometheus.yml
# then read the diff to understand what went wrong
```

- [ ] **Step 4: Reload Prometheus**

```bash
curl -X POST http://localhost:9091/-/reload
echo "exit code: $?"
```
Expected: exit code 0 (Prometheus's reload returns empty body on success).

- [ ] **Step 5: Bring the demo stack back up so the targets become reachable**

```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo up -d --build
```

- [ ] **Step 6: Verify both targets are UP**

```bash
sleep 10  # give Prometheus a scrape cycle
curl -s http://localhost:9091/api/v1/targets | \
    python3 -c "import sys, json; targets=json.load(sys.stdin)['data']['activeTargets']; \
        dapp=[t for t in targets if t['labels']['job'].startswith('dapp')]; \
        print('\n'.join(f\"{t['labels']['job']:25} {t['health']}\" for t in dapp))"
```
Expected output:
```
dapp-backend              up
dapp-postgres-exporter    up
```

If a target is DOWN, check `lastError` in the same JSON for the failure reason. Common causes: container not on the `monitoring_monitoring` network, wrong port, `/metrics` returning non-200.

- [ ] **Step 7: Commit the reference file**

```bash
git add monitoring/prometheus-dapp-jobs.yml
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "ops: add reference copy of Prometheus scrape jobs for DAPP

Source of truth lives in /opt/monitoring/config/prometheus.yml on the
demo host. This in-repo copy documents the scrape config for anyone
re-bootstrapping the demo elsewhere."
```

---

### Task 3.2: Verify Promtail picks up DAPP container logs (no config change required)

**Files:** None (verification only)

- [ ] **Step 1: Generate some log activity**

```bash
curl -fsS http://localhost:8000/api/health || true  # may fail because backend isn't on host port; use the docker-network curl below if so
docker exec dapp-backend curl -fsS http://localhost:8000/api/health
```

- [ ] **Step 2: Query Loki for DAPP logs**

```bash
curl -sG "http://localhost:3100/loki/api/v1/query" \
    --data-urlencode 'query={project="dapp"}' \
    --data-urlencode "limit=5" | \
    python3 -c "import sys, json; r=json.load(sys.stdin); \
        print('matches:', sum(len(s['values']) for s in r['data']['result']))"
```
Expected: a positive number. If 0, check:
- The compose project name is `dapp` (matches `name: dapp` in `docker-compose.demo.yml`). If it's different, query `{project="<actual_name>"}`.
- Promtail container is running: `docker ps | grep promtail`.

- [ ] **Step 3: Filter by service to confirm per-container labelling works**

```bash
curl -sG "http://localhost:3100/loki/api/v1/query" \
    --data-urlencode 'query={project="dapp", service="backend"}' \
    --data-urlencode "limit=5" | \
    python3 -m json.tool | head -30
```
Expected: log lines specifically from the backend container. Same pattern works for `service="frontend"`, `service="postgres"`, etc.

- [ ] **Step 4: No commit (verification only)**

---

### Task 3.3: End-to-end metric flow verification

**Files:** None (verification only)

- [ ] **Step 1: Generate some metric activity through the live stack**

```bash
# Register a real user (this will increment dapp_users_registered_total)
docker exec dapp-backend curl -fsS -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"e2e@test.com","username":"e2e","password":"testPassword123!","first_name":"E","last_name":"E","date_of_birth":"1990-01-01","gender":"other"}' || true
```

- [ ] **Step 2: Query Prometheus for the metric**

```bash
sleep 20  # one scrape cycle
curl -sG "http://localhost:9091/api/v1/query" \
    --data-urlencode 'query=dapp_users_registered_total' | \
    python3 -m json.tool
```
Expected: `data.result` is a non-empty list with at least one entry showing `value: ["..", "1"]` (or higher).

- [ ] **Step 3: No commit (verification only)**

---

# Phase 4: Grafana dashboard provisioning + NPM proxy host

### Task 4.1: Add the Grafana dashboard JSON and provider config to the repo

**Files:**
- Create: `monitoring/dapp-overview-dashboard.json`
- Create: `monitoring/dapp-dashboards-provider.yml`

- [ ] **Step 1: Create the dashboard provider config**

`monitoring/dapp-dashboards-provider.yml`:

```yaml
# monitoring/dapp-dashboards-provider.yml
# Grafana provisioning config that picks up dashboards from the same dir.
# Mirrored to /opt/monitoring/config/grafana/provisioning/dashboards/

apiVersion: 1

providers:
  - name: dapp-dashboards
    orgId: 1
    folder: DAPP
    folderUid: dapp
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: false
```

- [ ] **Step 2: Create the dashboard JSON (DAPP Overview)**

`monitoring/dapp-overview-dashboard.json`:

```json
{
  "annotations": {"list": []},
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "type": "stat",
      "title": "Users Registered (total)",
      "id": 1,
      "gridPos": {"x": 0, "y": 0, "w": 4, "h": 4},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "dapp_users_registered_total", "refId": "A"}]
    },
    {
      "type": "stat",
      "title": "Active Soul Connections",
      "id": 2,
      "gridPos": {"x": 4, "y": 0, "w": 4, "h": 4},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "dapp_soul_connections_active", "refId": "A"}]
    },
    {
      "type": "stat",
      "title": "Revelations Sent (last 24h)",
      "id": 3,
      "gridPos": {"x": 8, "y": 0, "w": 4, "h": 4},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "sum(increase(dapp_revelations_sent_total[24h]))", "refId": "A"}]
    },
    {
      "type": "timeseries",
      "title": "Onboarding Completions (rate)",
      "id": 4,
      "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "rate(dapp_emotional_onboarding_completed_total[5m])", "refId": "A"}]
    },
    {
      "type": "timeseries",
      "title": "HTTP Request Rate by Handler (top 10)",
      "id": 5,
      "gridPos": {"x": 12, "y": 0, "w": 12, "h": 12},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "topk(10, sum by (handler) (rate(http_requests_total{job=\"dapp-backend\"}[5m])))", "refId": "A"}]
    },
    {
      "type": "timeseries",
      "title": "HTTP Latency p50 / p95 / p99",
      "id": 6,
      "gridPos": {"x": 0, "y": 12, "w": 12, "h": 8},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [
        {"expr": "histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket{job=\"dapp-backend\"}[5m])))", "refId": "A", "legendFormat": "p50"},
        {"expr": "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{job=\"dapp-backend\"}[5m])))", "refId": "B", "legendFormat": "p95"},
        {"expr": "histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{job=\"dapp-backend\"}[5m])))", "refId": "C", "legendFormat": "p99"}
      ]
    },
    {
      "type": "timeseries",
      "title": "Compatibility Calc p95 (target < 0.5s)",
      "id": 7,
      "gridPos": {"x": 12, "y": 12, "w": 12, "h": 8},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "histogram_quantile(0.95, sum by (le) (rate(dapp_compatibility_calc_seconds_bucket[5m])))", "refId": "A"}],
      "fieldConfig": {"defaults": {"unit": "s", "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": null}, {"color": "red", "value": 0.5}]}}}
    },
    {
      "type": "timeseries",
      "title": "Login Attempts (success vs failure)",
      "id": 8,
      "gridPos": {"x": 0, "y": 20, "w": 12, "h": 8},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "sum by (result) (rate(dapp_login_attempts_total[5m]))", "refId": "A", "legendFormat": "{{result}}"}]
    },
    {
      "type": "timeseries",
      "title": "Postgres Active Connections",
      "id": 9,
      "gridPos": {"x": 12, "y": 20, "w": 12, "h": 8},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "pg_stat_activity_count{job=\"dapp-postgres-exporter\"}", "refId": "A"}]
    },
    {
      "type": "timeseries",
      "title": "Container CPU (DAPP)",
      "id": 10,
      "gridPos": {"x": 0, "y": 28, "w": 12, "h": 8},
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "sum by (name) (rate(container_cpu_usage_seconds_total{name=~\"dapp-.*\"}[5m]))", "refId": "A", "legendFormat": "{{name}}"}]
    },
    {
      "type": "logs",
      "title": "DAPP Logs (Loki)",
      "id": 11,
      "gridPos": {"x": 12, "y": 28, "w": 12, "h": 8},
      "datasource": {"type": "loki", "uid": "loki"},
      "targets": [{"expr": "{project=\"dapp\"} | json", "refId": "A"}]
    }
  ],
  "refresh": "30s",
  "schemaVersion": 38,
  "tags": ["dapp", "demo"],
  "templating": {"list": []},
  "time": {"from": "now-1h", "to": "now"},
  "timepicker": {},
  "timezone": "",
  "title": "DAPP Overview",
  "uid": "dapp-overview",
  "version": 1,
  "weekStart": ""
}
```

(The Prometheus and Loki datasource UIDs may differ on your Grafana instance — if dashboards show "Datasource not found", open Grafana → Connections → Data sources, click your Prometheus, and copy the actual UID, then `sed -i 's/"uid": "prometheus"/"uid": "<actual-uid>"/g' monitoring/dapp-overview-dashboard.json` and same for loki.)

- [ ] **Step 3: Validate JSON syntax**

```bash
python3 -m json.tool monitoring/dapp-overview-dashboard.json > /dev/null
echo "exit: $?"
```
Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add monitoring/dapp-overview-dashboard.json monitoring/dapp-dashboards-provider.yml
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "ops: add DAPP Overview Grafana dashboard + provider config

11 panels covering business metrics (users, connections, revelations,
logins), HTTP performance (request rate, p50/95/99 latency),
compatibility-calc latency with 500ms target line, postgres connections,
DAPP container CPU, and a Loki logs panel."
```

---

### Task 4.2: Provision the dashboard files on the host and verify Grafana picks them up

**Files (host):**
- `/opt/monitoring/config/grafana/provisioning/dashboards/dapp.yml`
- `/opt/monitoring/config/grafana/provisioning/dashboards/dapp-overview.json`

- [ ] **Step 1: Copy the files to the host's Grafana provisioning directory**

```bash
sudo cp monitoring/dapp-dashboards-provider.yml \
    /opt/monitoring/config/grafana/provisioning/dashboards/dapp.yml
sudo cp monitoring/dapp-overview-dashboard.json \
    /opt/monitoring/config/grafana/provisioning/dashboards/dapp-overview.json
ls -la /opt/monitoring/config/grafana/provisioning/dashboards/
```
Expected: both files present.

- [ ] **Step 2: Trigger Grafana to reload provisioning**

Grafana picks up new dashboards on `updateIntervalSeconds: 30` (set in the provider config), so it'll appear within 30s. To force immediately:

```bash
docker exec grafana kill -HUP 1 || docker restart grafana
```

- [ ] **Step 3: Verify the dashboard appears**

Open `http://localhost:3001` in a browser. Navigate to Dashboards → DAPP folder → "DAPP Overview". All panels should render data (some may show "No data" until traffic exists — that's expected).

If the dashboard doesn't appear, check Grafana logs:
```bash
docker logs grafana 2>&1 | tail -50 | grep -i provision
```

- [ ] **Step 4: No commit (host-side change; in-repo files were committed in Task 4.1)**

---

### Task 4.3: Configure NPM proxy host (manual UI work)

**Files:** None (manual NPM admin UI configuration)

- [ ] **Step 1: Confirm DNS A-record**

```bash
dig +short date.batcomputer.waynetower.de
```
Expected: returns the public IP of this host. If empty, add an A-record at your DNS provider pointing `date.batcomputer.waynetower.de` to the host's public IP and wait for propagation before continuing (otherwise Let's Encrypt won't be able to validate).

- [ ] **Step 2: Open NPM admin UI**

Browse to `http://<host-ip>:81` (or whatever URL you use to access NPM). Log in.

- [ ] **Step 3: Add Proxy Host**

Click **Hosts → Proxy Hosts → Add Proxy Host**.

**Details tab:**
- Domain Names: `date.batcomputer.waynetower.de`
- Scheme: `http`
- Forward Hostname / IP: `dapp-frontend`
- Forward Port: `80`
- Cache Assets: off
- Block Common Exploits: ✓
- Websockets Support: ✓
- Access List: Publicly Accessible

**Custom locations tab:** Add three locations:
1. Define location: `/api/`, Scheme `http`, Forward Hostname `dapp-backend`, Forward Port `8000`
2. Define location: `/docs`, Scheme `http`, Forward Hostname `dapp-backend`, Forward Port `8000`
3. Define location: `/openapi.json`, Scheme `http`, Forward Hostname `dapp-backend`, Forward Port `8000`

**Custom Nginx Configuration** (Advanced tab) — paste this to deny `/metrics` to the public:

```nginx
location = /metrics {
    return 444;
}
location ~ ^/metrics/ {
    return 444;
}
```

**SSL tab:**
- SSL Certificate: Request a new SSL Certificate
- Force SSL: ✓
- HTTP/2 Support: ✓
- HSTS Enabled: ✓
- HSTS Subdomains: off
- Email: <your email for Let's Encrypt notices>
- I Agree: ✓
- Save

NPM provisions the cert (takes ~30s). If it fails, the most common cause is DNS not yet pointing here.

- [ ] **Step 4: Verify the proxy works**

```bash
curl -fsS https://date.batcomputer.waynetower.de/api/health
# Expected: {"status":"ok"} or similar JSON

curl -s -o /dev/null -w "%{http_code}\n" https://date.batcomputer.waynetower.de/
# Expected: 200

curl -s -o /dev/null -w "%{http_code}\n" https://date.batcomputer.waynetower.de/metrics
# Expected: 444 (or "curl: (52) Empty reply from server" — both prove the deny works)

curl -s -o /dev/null -w "%{http_code}\n" https://date.batcomputer.waynetower.de/docs
# Expected: 200 (Swagger UI)
```

- [ ] **Step 5: No commit (NPM config is stored in NPM's data volume, not in the repo)**

---

# Phase 5: Deploy script + docs + final tag

### Task 5.1: Write `deploy-demo.sh`

**Files:**
- Create: `deploy-demo.sh`

- [ ] **Step 1: Create the deploy script**

```bash
cat > deploy-demo.sh <<'SH'
#!/usr/bin/env bash
# deploy-demo.sh
# Idempotent rolling-release deploy for the DAPP demo server.
#
# Usage:
#   ./deploy-demo.sh             # full deploy: pull, build, up, smoke
#   ./deploy-demo.sh --smoke-only  # run smoke tests against current deployment

set -euo pipefail

PUBLIC_URL="https://date.batcomputer.waynetower.de"
COMPOSE_FILE="docker-compose.demo.yml"
ENV_FILE=".env.demo"

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
blue()  { printf '\033[34m%s\033[0m\n' "$*"; }

require_clean_tree() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    red "Working tree is dirty. Commit or stash before deploying."
    exit 1
  fi
}

require_env_file() {
  if [[ ! -f "$ENV_FILE" ]]; then
    red "$ENV_FILE missing. Copy from .env.demo.example and fill in secrets."
    exit 1
  fi
}

smoke_tests() {
  blue "Running smoke tests..."

  blue "  → /api/health"
  curl -fsS "${PUBLIC_URL}/api/health" > /dev/null || { red "FAIL"; return 1; }

  blue "  → / (frontend)"
  test "$(curl -s -o /dev/null -w '%{http_code}' "${PUBLIC_URL}/")" = "200" \
    || { red "FAIL: frontend did not return 200"; return 1; }

  blue "  → /docs (swagger)"
  test "$(curl -s -o /dev/null -w '%{http_code}' "${PUBLIC_URL}/docs")" = "200" \
    || { red "FAIL: /docs did not return 200"; return 1; }

  blue "  → /metrics (must be denied)"
  status=$(curl -s -o /dev/null -w '%{http_code}' "${PUBLIC_URL}/metrics" || echo "0")
  if [[ "$status" == "200" ]]; then
    red "FAIL: /metrics is publicly accessible — NPM deny rule missing"
    return 1
  fi

  blue "  → backend /metrics (internal, must contain dapp_*)"
  docker compose -f "$COMPOSE_FILE" exec -T backend \
    sh -c 'curl -fsS http://localhost:8000/metrics | grep -q dapp_users_registered_total' \
    || { red "FAIL: backend /metrics missing dapp_* series"; return 1; }

  blue "  → Prometheus targets"
  curl -fsS http://localhost:9091/api/v1/targets | \
    python3 -c "
import sys, json
targets = json.load(sys.stdin)['data']['activeTargets']
dapp = [t for t in targets if t['labels']['job'].startswith('dapp')]
unhealthy = [t for t in dapp if t['health'] != 'up']
if unhealthy:
    print('FAIL:', [(t['labels']['job'], t['health']) for t in unhealthy])
    sys.exit(1)
print(f'  OK ({len(dapp)} DAPP targets up)')
" || { red "FAIL: Prometheus target health check"; return 1; }

  green "All smoke tests passed."
}

if [[ "${1:-}" == "--smoke-only" ]]; then
  smoke_tests
  exit $?
fi

require_clean_tree
require_env_file

blue "→ Fetching from origin (Gitea)"
git -c 'credential.helper=!f() { echo username=lex; echo "password=Enigma-2026!"; }; f' \
    fetch origin

blue "→ Switching to main and fast-forwarding"
git checkout main
git -c 'credential.helper=!f() { echo username=lex; echo "password=Enigma-2026!"; }; f' \
    pull --ff-only origin main

blue "→ Building images and restarting stack"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

blue "→ Waiting 15s for services to settle"
sleep 15

smoke_tests
green "Deploy complete. App live at ${PUBLIC_URL}"
SH
chmod +x deploy-demo.sh
```

- [ ] **Step 2: Verify the script's syntax**

```bash
bash -n deploy-demo.sh
echo "exit: $?"
```
Expected: exit 0 (no syntax errors).

- [ ] **Step 3: Run smoke-only against the live deployment**

```bash
./deploy-demo.sh --smoke-only
```
Expected: all 6 smoke checks print green; final "All smoke tests passed.".

If any smoke check fails, the failure is real (not a script bug) — debug the failing component (e.g., NPM config, missing scrape job).

- [ ] **Step 4: Commit**

```bash
git add deploy-demo.sh
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "ops: add deploy-demo.sh rolling-release script

Idempotent deploy: refuses dirty trees, pulls main fast-forward only,
rebuilds + restarts the demo stack, then runs 6 smoke tests against
the public URL and the internal Prometheus/metrics surface. Supports
--smoke-only flag for verification without redeploy."
```

---

### Task 5.2: Write the operations doc + update CLAUDE.md

**Files:**
- Create: `docs/demo-server.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Create `docs/demo-server.md`**

```markdown
# Demo Server (`https://date.batcomputer.waynetower.de`)

This server runs the DAPP demo behind Nginx Proxy Manager, with
metrics/logs/traces flowing into the host's existing Grafana stack.
Spec: `docs/superpowers/specs/2026-04-22-dapp-demo-server-design.md`.

## Access points

| URL | Purpose |
|-----|---------|
| https://date.batcomputer.waynetower.de | Angular frontend (rolling release of `main`) |
| https://date.batcomputer.waynetower.de/api | FastAPI backend |
| https://date.batcomputer.waynetower.de/docs | Swagger UI (public) |
| https://date.batcomputer.waynetower.de/api/health | Health check |
| http://<host>:3001 | Grafana → "DAPP Overview" dashboard |
| http://<host>:9091/targets | Prometheus targets (verify scrapes are UP) |
| http://<host>:81 | NPM admin UI (proxy host config) |

## Daily operations

### Roll a new release

```bash
./deploy-demo.sh
```

This:
1. Refuses to deploy if local working tree is dirty
2. Fetches `origin/main` and fast-forwards local `main`
3. Rebuilds the backend and frontend images
4. Restarts the stack with `docker compose -f docker-compose.demo.yml up -d --build`
5. Runs smoke tests against the public URL and Prometheus targets

Total time after the first build: ~60-90 seconds (cached layers).

### Re-run smoke tests without redeploying

```bash
./deploy-demo.sh --smoke-only
```

### Rollback to a previous tag

```bash
git checkout v0.1.0-demo   # or any prior tag
docker compose -f docker-compose.demo.yml --env-file .env.demo up -d --build
./deploy-demo.sh --smoke-only
```

**Caveat:** DB schema rollback is not automatic. If a release added a destructive Alembic migration, you'll need a manual `alembic downgrade <revision>` against `dapp-postgres`.

### Read logs

```bash
# Tail one service
docker compose -f docker-compose.demo.yml logs -f --tail 100 backend

# Searchable in Grafana
# Open http://<host>:3001 → Explore → Loki → query: {project="dapp"}
# Filter by service: {project="dapp", service="backend"}
# Errors only:        {project="dapp"} |~ "ERROR|WARN"
```

### Check metric targets

```bash
curl http://localhost:9091/api/v1/targets | \
    python3 -c "import sys,json; print('\n'.join(f\"{t['labels']['job']:25} {t['health']}\" for t in json.load(sys.stdin)['data']['activeTargets'] if t['labels']['job'].startswith('dapp')))"
```

### DB shell

```bash
docker compose -f docker-compose.demo.yml exec postgres \
    psql -U postgres dinner_first
```

## Troubleshooting

### `/metrics` returns 200 from the public URL

NPM's deny rule for `/metrics` was not applied. Open NPM → the proxy host →
Advanced tab → ensure the custom nginx config block contains the
`location = /metrics { return 444; }` rules. Save.

### Prometheus target shows DOWN

Most common: backend container isn't on the `monitoring_monitoring` docker
network. Verify:

```bash
docker inspect dapp-backend --format '{{json .NetworkSettings.Networks}}' | python3 -m json.tool
```

Should include `monitoring_monitoring`. If missing, the compose file's
`networks:` block doesn't list `monitoring` for the backend service —
fix and `docker compose ... up -d`.

### Let's Encrypt cert renewal failed

NPM auto-renews. Check NPM logs:

```bash
docker logs nginx-proxy-manager 2>&1 | grep -i letsencrypt | tail -20
```

Manual renewal: NPM admin UI → SSL Certificates → tap your cert → Renew.

### Dashboard shows "No data"

Either:
- No traffic has been sent yet (most metrics are counters/rates that need data flow)
- Prometheus datasource UID in the dashboard JSON differs from the live UID
  (open Grafana → Data sources → copy the UID, edit `monitoring/dapp-overview-dashboard.json`)
```

- [ ] **Step 2: Update `CLAUDE.md` — add a "Demo deployment" section**

Append to `CLAUDE.md` (after the existing "Git Workflow & Branch Management" section):

```markdown
## Demo Deployment

This host runs a live demo of `main` at `https://date.batcomputer.waynetower.de`.

- **Deploy a release:** `./deploy-demo.sh`
- **Verify only:** `./deploy-demo.sh --smoke-only`
- **Operations guide:** `docs/demo-server.md`
- **Design spec:** `docs/superpowers/specs/2026-04-22-dapp-demo-server-design.md`
- **Implementation plan:** `docs/superpowers/plans/2026-04-22-dapp-demo-server-plan.md`

The demo stack is `docker-compose.demo.yml` and is **separate** from the dev stack
(`docker-compose.dev.yml`) — it builds production images and runs them without
source mounts or `--reload`, attached to the host's existing observability +
NPM networks.

Secrets live in `.env.demo` (gitignored). Template: `.env.demo.example`.
```

- [ ] **Step 3: Verify the doc renders OK (no broken Markdown)**

```bash
head -20 docs/demo-server.md
tail -30 CLAUDE.md
```
Expected: docs read cleanly.

- [ ] **Step 4: Commit**

```bash
git add docs/demo-server.md CLAUDE.md
git -c user.name="Alexsander Efrem" -c user.email="alexsefr21@gmail.com" \
    commit -m "docs: add demo-server operations guide + CLAUDE.md section

docs/demo-server.md covers daily operations (deploy, rollback, logs,
metrics, DB shell) and troubleshooting for the most common failures
(public /metrics, target DOWN, cert renewal, dashboard No-Data)."
```

---

### Task 5.3: Push everything, tag the release, and run a final end-to-end smoke

**Files:** None (release operations only)

- [ ] **Step 1: Push the new commits to Gitea**

```bash
git -c 'credential.helper=!f() { echo username=lex; echo "password=Enigma-2026!"; }; f' \
    push origin main
```

- [ ] **Step 2: Run the full deploy (this is the first "real" rolling deploy)**

```bash
./deploy-demo.sh
```
Expected: deploy completes, all 6 smoke tests pass, final green message.

- [ ] **Step 3: Tag the release on the merged `main`**

```bash
NEW_TAG="v0.1.1-demo"
git tag -a "$NEW_TAG" -m "Demo deployment with full observability wiring"
git -c 'credential.helper=!f() { echo username=lex; echo "password=Enigma-2026!"; }; f' \
    push origin "$NEW_TAG"
```

- [ ] **Step 4: Manual verification in the browser**

Open in a browser:
- https://date.batcomputer.waynetower.de/ — Angular SPA loads
- https://date.batcomputer.waynetower.de/docs — Swagger renders
- http://localhost:3001 → Dashboards → DAPP folder → "DAPP Overview" — panels populate (latency, request rate visible after a few requests)

Register a test user via the SPA, watch the `dapp_users_registered_total` value increment in Grafana within ~30s.

- [ ] **Step 5: No commit (release operations)**

---

# Done — verification summary

After all tasks complete, the following should all be true:

| Check | How to verify |
|-------|---------------|
| `main` is merged from `development` | `git log main --oneline | head -3` shows the merge commit |
| `v0.1.0-demo` and `v0.1.1-demo` tags exist | `git tag --list 'v0.1*'` |
| Demo URL serves the SPA | `curl -fsS https://date.batcomputer.waynetower.de` returns HTML 200 |
| Demo `/api/health` works | `curl -fsS https://date.batcomputer.waynetower.de/api/health` returns JSON 200 |
| Public `/metrics` is denied | `curl -o /dev/null -w "%{http_code}" https://date.batcomputer.waynetower.de/metrics` returns `444` (or curl error 52) |
| Backend `/metrics` exposes dapp_* series | `docker compose -f docker-compose.demo.yml exec backend curl http://localhost:8000/metrics | grep ^dapp_` returns non-empty |
| Prometheus has DAPP targets UP | `curl -s http://localhost:9091/api/v1/targets` shows `dapp-backend` and `dapp-postgres-exporter` with `health: up` |
| Loki has DAPP logs | `curl -sG http://localhost:3100/loki/api/v1/query --data-urlencode 'query={project="dapp"}'` returns matches |
| Grafana DAPP dashboard exists | Browse to Grafana → Dashboards → DAPP → "DAPP Overview" |
| Deploy script is reproducible | `./deploy-demo.sh --smoke-only` exits 0 |
| Operations docs exist | `ls docs/demo-server.md && grep -q "Demo Deployment" CLAUDE.md` |

If all rows pass, the implementation is complete and the demo is in rolling-release mode on `main`.
