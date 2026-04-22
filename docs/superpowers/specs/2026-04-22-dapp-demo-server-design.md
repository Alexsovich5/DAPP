# DAPP Demo Server — Rolling Release with Observability

**Status:** Approved (design)
**Date:** 2026-04-22
**Owner:** lex
**Scope:** One spec → one implementation plan → one merge to `main`

---

## 1. Goal

Turn this host into a public demo server for the Dinner First app, with `main` as a rolling-release branch. Wire the running app into the host's existing observability stack (Grafana, Prometheus, Loki/Promtail, Alertmanager, cAdvisor, node-exporter, postgres-exporter) and expose it to the internet via the host's existing Nginx Proxy Manager (NPM) at `https://date.batcomputer.waynetower.de`.

Non-goals for this iteration: real alert routes, frontend nginx-exporter, automated Gitea↔GitHub mirroring, rate limiting / WAF, automated DB backups.

---

## 2. Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Merge strategy | PR-based on Gitea, `development → main`, merge commit (`--no-ff`), tag `v0.1.0-demo` |
| 2 | Source of truth | Gitea canonical (`git.batcomputer.waynetower.de/lex/DAPP`); GitHub mirrored downstream |
| 3 | Demo runtime | New `docker-compose.demo.yml` with built images, no source mounts, no hot-reload |
| 4 | Public hostname | `https://date.batcomputer.waynetower.de` via NPM |
| 5 | Origin layout | **Single-origin**: `/` → frontend, `/api` → backend, `/docs` → Swagger |
| 6 | TLS | Let's Encrypt via NPM, force HTTPS, HSTS, HTTP/2 |
| 7 | Alerting | None for this iteration (Alertmanager exists but no DAPP rules added) |
| 8 | Business metrics | Default set: registrations, onboarding, soul connections, revelations, messages, login attempts, compatibility-calc histogram |
| 9 | Metrics library | `prometheus-fastapi-instrumentator` for HTTP defaults + `prometheus-client` (already in `requirements.txt`) for custom counters/gauges/histograms |
| 10 | DB scope | DAPP keeps its own `dapp-postgres` (isolated from `batman-bi-prod-postgres`). Own postgres-exporter inside the DAPP compose so it's lifecycled with the app |
| 11 | Smoke tests | Run as part of `deploy-demo.sh`; print to terminal; non-zero exit on failure |
| 12 | `/docs` (Swagger) | Public for demo convenience |
| 13 | `/metrics` | Internet-blocked at NPM (return 444); only reachable from docker network |

---

## 3. Architecture

### 3.1 Topology

```
                    Internet
                       │
                       ▼  443 TLS (Let's Encrypt via NPM)
        ┌──────────────────────────────┐
        │  nginx-proxy-manager         │  (already running, host network: nginx_proxy)
        │  proxy_host:                 │
        │   date.batcomputer.waynetower.de
        │     /         → dapp-frontend:80
        │     /api/     → dapp-backend:8000
        │     /docs     → dapp-backend:8000
        │     /openapi.json → dapp-backend:8000
        │     /metrics  → 444 (deny)
        └──────────────┬───────────────┘
                       │
   ┌─── docker-compose.demo.yml ──────────────────────────────────────────┐
   │                                                                      │
   │  dapp-frontend (nginx + built Angular bundle)                        │
   │    networks: nginx_proxy                                             │
   │                                                                      │
   │  dapp-backend  (FastAPI + uvicorn, no --reload, /metrics enabled)    │
   │    networks: nginx_proxy, monitoring_monitoring, dapp_internal       │
   │                                                                      │
   │  dapp-postgres (own data volume, isolated from batman-bi postgres)   │
   │    networks: dapp_internal                                           │
   │                                                                      │
   │  dapp-postgres-exporter                                              │
   │    networks: dapp_internal, monitoring_monitoring                    │
   │                                                                      │
   └──────────────────────────────────────────────────────────────────────┘

       Reuses (no config change for these except scrape file):
       prometheus  ─── scrape ───  dapp-backend, dapp-postgres-exporter
                  ─── reuses  ───  cadvisor (container metrics, free)
                  ─── reuses  ───  node-exporter (host metrics, free)
       loki  ◀─── promtail (Docker SD picks up DAPP containers, no config change)
       grafana (provisioned dashboards from /opt/monitoring/config/grafana/provisioning)
       alertmanager (running, idle for DAPP)
```

### 3.2 Networks

| Network | Purpose | DAPP attaches? |
|---------|---------|----------------|
| `dapp_internal` (NEW) | Backend ↔ DB ↔ exporter, isolated | yes |
| `nginx_proxy` (existing, external) | NPM → frontend/backend | yes |
| `monitoring_monitoring` (existing, external) | Prometheus scrape, exporter scrape | yes (backend + postgres-exporter) |

DAPP frontend joins only `nginx_proxy` (it serves static files; Prometheus does not scrape it in this iteration).

### 3.3 Single-origin URL plan

| URL | Routed to | Notes |
|-----|-----------|-------|
| `https://date.batcomputer.waynetower.de/` | `dapp-frontend:80` | Angular SPA |
| `https://date.batcomputer.waynetower.de/api/v1/...` | `dapp-backend:8000` | FastAPI |
| `https://date.batcomputer.waynetower.de/docs` | `dapp-backend:8000` | Swagger UI (public) |
| `https://date.batcomputer.waynetower.de/openapi.json` | `dapp-backend:8000` | OpenAPI schema |
| `https://date.batcomputer.waynetower.de/metrics` | NPM returns **444** | Internet-blocked |
| `https://date.batcomputer.waynetower.de/health` | `dapp-backend:8000/health` | Public health check |

Angular's `environment.demo.ts` sets `apiUrl: '/api'` so it makes relative calls — no CORS preflight needed in browsers.

---

## 4. What changes (file inventory)

### 4.1 New files

| Path | Purpose |
|------|---------|
| `python-backend/Dockerfile` | Multi-stage prod image (builder installs deps; runtime runs `uvicorn` without `--reload`) |
| `angular-frontend/Dockerfile` | Multi-stage: Node 20 builder runs `ng build --configuration=demo`; nginx alpine serves the bundle |
| `angular-frontend/nginx.conf` | SPA fallback (`try_files $uri $uri/ /index.html`), gzip, cache headers, no `/api` proxy (NPM does that) |
| `angular-frontend/src/environments/environment.demo.ts` | `production: true, apiUrl: '/api'` |
| `docker-compose.demo.yml` | Services: `dapp-postgres`, `dapp-postgres-exporter`, `dapp-backend`, `dapp-frontend`. Networks: `dapp_internal` (new) + external `nginx_proxy`, `monitoring_monitoring`. Read env from `.env.demo`. |
| `.env.demo.example` | Template: `SECRET_KEY`, `POSTGRES_PASSWORD`, `CORS_ORIGINS=https://date.batcomputer.waynetower.de`, `ENVIRONMENT=demo`, `DEBUG=false` |
| `python-backend/app/observability/__init__.py` | Module init |
| `python-backend/app/observability/metrics.py` | Defines all custom metrics + `setup_observability(app)` helper that mounts the instrumentator and `/metrics` endpoint |
| `deploy-demo.sh` | Idempotent deploy script (fetch → checkout main → pull --ff-only → build → up -d → smoke tests → tag if new). Refuses to deploy a dirty working tree. |
| `docs/demo-server.md` | Operations guide: how to access, redeploy, roll back, read logs/dashboards, common troubleshooting |
| `monitoring/dapp-overview-dashboard.json` (in repo) | Grafana dashboard JSON. Symlinked / copied to `/opt/monitoring/config/grafana/provisioning/dashboards/dapp-overview.json` during deploy |
| `monitoring/dapp-dashboards-provider.yml` (in repo) | Grafana dashboard provider config. Copied to `/opt/monitoring/config/grafana/provisioning/dashboards/dapp.yml` |
| `monitoring/prometheus-dapp-jobs.yml` (in repo, reference copy) | Source-of-truth copy of the scrape jobs we appended to `/opt/monitoring/config/prometheus.yml` |

### 4.2 Modified files

| Path | Edit |
|------|------|
| `python-backend/requirements.txt` | Add `prometheus-fastapi-instrumentator>=7.0.0` |
| `python-backend/app/main.py` | Call `setup_observability(app)` after app creation |
| `python-backend/app/api/v1/auth.py` | Increment `users_registered_total`, `login_attempts_total{result=...}` |
| `python-backend/app/api/v1/onboarding.py` | Increment `emotional_onboarding_completed_total{step=...}` |
| `python-backend/app/api/v1/connections.py` (or matching file) | Increment `soul_connections_initiated_total`; update `soul_connections_active` gauge |
| `python-backend/app/api/v1/revelations.py` (or matching file) | Increment `revelations_sent_total{day_number=...}` |
| `python-backend/app/api/v1/messages.py` | Increment `messages_sent_total` |
| `python-backend/app/services/compatibility.py` (or matching file) | Wrap `calculate_overall_compatibility` body in `compatibility_calc_seconds.time()` |
| `angular-frontend/angular.json` | Add `demo` build configuration that uses `environment.demo.ts` |
| `CLAUDE.md` | Add "Demo deployment" section pointing at `deploy-demo.sh` and `docs/demo-server.md` |
| `.gitignore` | Add `.env.demo` (the actual file, never the example) |

### 4.3 Host-level changes (outside the repo)

| Path / system | Change |
|---------------|--------|
| `/opt/monitoring/config/prometheus.yml` | Append 2 scrape jobs (`dapp-backend`, `dapp-postgres-exporter`); reload Prometheus via `POST :9091/-/reload` |
| `/opt/monitoring/config/grafana/provisioning/dashboards/dapp.yml` | Add provider entry pointing at the dashboard JSON |
| `/opt/monitoring/config/grafana/provisioning/dashboards/dapp-overview.json` | Copy of the in-repo dashboard JSON |
| NPM admin UI (`:81`) | Create proxy host for `date.batcomputer.waynetower.de` with the location rules above; request Let's Encrypt cert; force SSL + HSTS + HTTP/2 |
| DNS (your provider) | Confirm `date.batcomputer.waynetower.de` A-record points at this host (assumed yes since `git.batcomputer.waynetower.de` does) |

---

## 5. Custom business metrics

All metrics are prefixed `dapp_` (Prometheus convention: app-specific prefix).

| Name | Type | Labels | Where incremented |
|------|------|--------|-------------------|
| `dapp_users_registered_total` | Counter | — | `POST /api/v1/auth/register` success |
| `dapp_emotional_onboarding_completed_total` | Counter | `step` | `POST /api/v1/onboarding/complete` (step = "step_1"/"step_2"/"step_3"/"all") |
| `dapp_soul_connections_initiated_total` | Counter | — | `POST /api/v1/connections/initiate` |
| `dapp_soul_connections_active` | Gauge | — | Set on connection state change (initiate +1, archive/close -1). Periodically refreshed from DB on app startup. |
| `dapp_revelations_sent_total` | Counter | `day_number` (1–7) | `POST /api/v1/revelations/create` |
| `dapp_messages_sent_total` | Counter | — | `POST /api/v1/messages/{connection_id}` |
| `dapp_login_attempts_total` | Counter | `result` ("success"/"failure") | `POST /api/v1/auth/login` outcome |
| `dapp_compatibility_calc_seconds` | Histogram | — | Wraps `CompatibilityCalculator.calculate_overall_compatibility`. Buckets: `0.005, 0.01, 0.05, 0.1, 0.5, 1, 5`. |

Plus all defaults from `prometheus-fastapi-instrumentator`:
- `http_requests_total{method, handler, status}`
- `http_request_duration_seconds_bucket{...}` (histogram)
- `http_request_size_bytes` / `http_response_size_bytes`
- Process metrics (CPU, memory, GC, file descriptors)

---

## 6. Grafana dashboard ("DAPP Overview")

Provisioned via filesystem (no clicks). Panels:

1. **Stat row**: total users registered, active soul connections, revelations sent today
2. **Onboarding completion rate** (timeseries, `rate(dapp_emotional_onboarding_completed_total[5m])` per step)
3. **Active soul connections** (gauge)
4. **Revelations by day_number** (heatmap, 7 columns)
5. **HTTP request rate by endpoint** (timeseries, top 10)
6. **Latency p50/p95/p99** (timeseries, computed from histogram buckets)
7. **Compatibility-calc latency** (timeseries with target line at 500ms — visualizes CLAUDE.md requirement)
8. **Login success vs failure rate** (timeseries)
9. **Postgres**: active connections, tx/sec, slow queries (from `postgres-exporter`)
10. **Container CPU & memory** (from cAdvisor, filtered `compose_project="dapp"`)
11. **Logs** (Loki panel, query `{project="dapp"} |~ "ERROR|WARN"` last 1h)

Dashboard JSON lives at `monitoring/dapp-overview-dashboard.json` in the repo so it's version-controlled, and is mirrored to `/opt/monitoring/config/grafana/provisioning/dashboards/` by `deploy-demo.sh`.

---

## 7. Deploy & rollback

### 7.1 First-time deploy

```bash
# 1. Merge dev → main (PR on Gitea), pull main locally
git checkout main && git pull --ff-only

# 2. Create .env.demo from .env.demo.example, fill secrets
cp .env.demo.example .env.demo  # then edit

# 3. Add scrape jobs to host prometheus, validate, then reload
sudo cp /opt/monitoring/config/prometheus.yml /opt/monitoring/config/prometheus.yml.bak
sudo tee -a /opt/monitoring/config/prometheus.yml < monitoring/prometheus-dapp-jobs.yml
docker run --rm -v /opt/monitoring/config:/etc/prometheus prom/prometheus \
  promtool check config /etc/prometheus/prometheus.yml \
  || { sudo mv /opt/monitoring/config/prometheus.yml.bak /opt/monitoring/config/prometheus.yml; exit 1; }
curl -X POST http://localhost:9091/-/reload

# 4. Provision dashboard
sudo cp monitoring/dapp-dashboards-provider.yml /opt/monitoring/config/grafana/provisioning/dashboards/dapp.yml
sudo cp monitoring/dapp-overview-dashboard.json /opt/monitoring/config/grafana/provisioning/dashboards/

# 5. Bring up the demo
./deploy-demo.sh

# 6. Configure NPM proxy host via UI (one-time)
#    (manual; documented in docs/demo-server.md)
```

### 7.2 Rolling release (every subsequent deploy)

```bash
./deploy-demo.sh
# = git fetch + checkout main + pull --ff-only + docker compose -f docker-compose.demo.yml up -d --build + smoke tests
```

### 7.3 Rollback

```bash
git checkout v0.1.0-demo   # or any prior tag
./deploy-demo.sh
```

DB schema rollback is **not** automatic. If a release adds a destructive Alembic migration, rollback requires a manual `alembic downgrade`. Flagged in `docs/demo-server.md`.

---

## 8. Smoke tests (run by `deploy-demo.sh`)

Exit non-zero on any failure:

1. `curl -fsS https://date.batcomputer.waynetower.de/api/health` → `{"status":"ok"}`
2. `curl -fsS https://date.batcomputer.waynetower.de/` → 200 with `<html`
3. `curl -fsS https://date.batcomputer.waynetower.de/api/v1/onboarding/status` → 401 (proves auth middleware loaded)
4. `docker compose -f docker-compose.demo.yml exec -T dapp-backend curl -fsS http://localhost:8000/metrics | grep -q dapp_users_registered_total` → match
5. `curl -fsS http://localhost:9091/api/v1/targets | jq -e '.data.activeTargets[] | select(.labels.job=="dapp-backend") | select(.health=="up")'` → match

---

## 9. Security posture (single-origin demo on public internet)

| Concern | Mitigation |
|---------|------------|
| `/metrics` exposed publicly | NPM custom location returns **444** for `/metrics`. Backend's `/metrics` only reachable from the docker `monitoring_monitoring` network. |
| Secrets in compose file | All secrets read from `.env.demo` (gitignored). `.env.demo.example` template committed with placeholders. |
| CORS | `CORS_ORIGINS=https://date.batcomputer.waynetower.de` only — no wildcard. Single-origin design means CORS isn't actually triggered by the demo browser flow. |
| HTTPS enforcement | NPM "Force SSL" + HSTS (max-age 1 year) |
| TLS cert | Let's Encrypt via NPM, auto-renew |
| Stack traces leaking via Swagger | `DEBUG=false` in `.env.demo`; FastAPI returns generic 500 in non-debug mode. Swagger remains exposed (per Q5) but doesn't expose internals. |
| DB password | Random, set via `.env.demo`; postgres on `dapp_internal` only (no host port mapping in demo compose) |
| Session token storage | Existing JWT setup unchanged in this PR |
| Rate limiting on `/auth/login` | **Not added in this iteration** — flagged as future work. `dapp_login_attempts_total{result="failure"}` is recorded so we can add it later as a dashboard signal. |
| Backups | **Not added in this iteration** — confirm whether host's existing backup tool covers `/var/lib/docker/volumes/dapp_postgres_*` |

---

## 10. Operations

### Access points (post-deploy)

- **App:** https://date.batcomputer.waynetower.de
- **API docs:** https://date.batcomputer.waynetower.de/docs
- **Health:** https://date.batcomputer.waynetower.de/api/health
- **Grafana:** http://localhost:3001 → "DAPP Overview"
- **Prometheus targets:** http://localhost:9091/targets
- **Logs:** Grafana → Explore → Loki → `{project="dapp"}`
- **NPM admin:** http://localhost:81

### Common operations

```bash
# Tail logs of a single service
docker compose -f docker-compose.demo.yml logs -f --tail 100 dapp-backend

# DB shell
docker compose -f docker-compose.demo.yml exec dapp-postgres psql -U postgres dinner_first

# Re-run smoke tests without redeploying
./deploy-demo.sh --smoke-only
```

---

## 11. Out of scope (deliberate)

Each one is a future PR if/when it becomes worth doing:

- Real alerting routes (Alertmanager rules → email/slack/ntfy)
- `nginx-exporter` for the frontend container
- Automated Gitea → GitHub mirror (Gitea push-mirror feature)
- Rate limiting / WAF rules (NPM has plugin support; or app-level via `slowapi`)
- Automated backups of `dapp-postgres` data volume
- Blue-green deployment (current cutover has ~1s window of 503s during NPM upstream swap)
- E2E tests in CI before deploy (`./deploy-demo.sh` only runs smoke tests post-deploy)
- Per-tenant metric labels (the demo runs as a single-tenant deployment)

---

## 12. Implementation phases (high-level — full plan to be produced by writing-plans skill)

| Phase | Scope | Verifiable outcome |
|-------|-------|--------------------|
| 0 | Open Gitea PR `development → main`, merge with merge commit, tag `v0.1.0-demo` | `main` HEAD == merged dev work; tag exists |
| 1 | Production Dockerfiles (backend + frontend) + `docker-compose.demo.yml` + `.env.demo.example` | `docker compose -f docker-compose.demo.yml up -d --build` succeeds; health/root return 200 from inside docker net |
| 2 | Backend `/metrics` endpoint + custom business metrics + call-site hooks | `curl :8000/metrics` shows `dapp_*` series; values increment on real requests |
| 3 | Append Prometheus scrape jobs + reload; verify Promtail picks up logs (no config change) | `:9091/targets` shows DAPP jobs UP; Loki query `{project="dapp"}` returns lines |
| 4 | NPM proxy host with single-origin layout + Let's Encrypt cert | `https://date.batcomputer.waynetower.de` returns 200 with valid cert; `/metrics` returns 444 |
| 5 | Grafana dashboard provisioned; `deploy-demo.sh` + `docs/demo-server.md` written; CLAUDE.md updated | Dashboard appears with live data; `./deploy-demo.sh` is idempotent and runs smoke tests |

---

## 13. Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| DNS for `date.batcomputer.waynetower.de` not yet pointing at this host | Low | Verify `dig date.batcomputer.waynetower.de` before requesting LE cert in NPM. If wrong, request cert after fixing DNS. |
| `monitoring_monitoring` network name differs (e.g., literal docker network name not `monitoring_monitoring`) | Medium | Verify with `docker network ls | grep monit` before writing compose. Use the actual network name. |
| Existing Promtail labels project name differently than `dapp` | Low | Compose project name defaults to the directory name (`DAPP` lowercased = `dapp`). Confirm after first `up`. Use `--project-name dapp` flag explicitly in the compose command to lock it. |
| New Alembic migration breaks on production data | Low (no prod data on day 1) | Backup volume snapshot before each deploy starting after the first real users. Out of scope for this PR. |
| Prometheus reload fails (config syntax) | Low | First-time setup (§7.1 step 3) runs `docker run --rm -v /opt/monitoring/config:/etc/prometheus prom/prometheus promtool check config /etc/prometheus/prometheus.yml` after appending and before posting `/-/reload`. If validation fails, the appended jobs are reverted with a backup file. |
| Building frontend image OOMs on small host | Medium | Multi-stage build keeps final image small (~30MB) but the `node` builder stage needs ~1.5GB RAM. Builds happen on demo host — verify free RAM before first build. |
