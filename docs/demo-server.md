# DAPP Demo Server

Reference for running the public demo of "Dinner First" at
`https://date.batcomputer.waynetower.de`. This is a single-host rolling
release wired into the host's existing Grafana/Prometheus/Loki/NPM stack.

## What's deployed

| Container               | Image                                          | Purpose                                   |
| ----------------------- | ---------------------------------------------- | ----------------------------------------- |
| `dapp-postgres`         | `postgres:15-alpine`                           | App database                              |
| `dapp-postgres-exporter`| `prometheuscommunity/postgres-exporter`        | DB metrics for Prometheus                 |
| `dapp-backend`          | `dapp-backend:demo` (built from `python-backend/`) | FastAPI app + `/metrics` endpoint     |
| `dapp-frontend`         | `dapp-frontend:demo` (built from `angular-frontend/`) | Nginx serving Angular SPA + `/api/` proxy |

All four are described in `docker-compose.demo.yml`.

## Topology

```
Browser ─https─▶ NPM (date.batcomputer…) ─http─▶ dapp-frontend (nginx)
                                                  │       │
                                                  │       └─/api/, /docs, /openapi.json─▶ dapp-backend
                                                  └─/, /assets/, SPA fallback───────────▶ /usr/share/nginx/html

Prometheus ──scrape──▶ dapp-backend:8000/metrics
Prometheus ──scrape──▶ dapp-postgres-exporter:9187
Promtail (Docker SD) ──tail──▶ all dapp-* container stdout ──▶ Loki (project=dapp label)
Grafana ──datasource──▶ Prometheus + Loki  →  folder "DAPP" → "DAPP Overview"
```

The frontend is the only DAPP container on `nginx_proxy`; the backend
is reached only through it. This keeps `/metrics` off the public
internet without any extra firewall rules.

## Networks

The compose file attaches to two pre-existing external networks:

- `monitoring_monitoring` — shared with Prometheus/Loki/Grafana so
  scrapes and log forwarding work without exposing ports
- `nginx_proxy` — shared with Nginx Proxy Manager so it can reach
  `dapp-frontend:80`

A third network, `dapp_internal`, is created locally and isolates
postgres ↔ exporter ↔ backend traffic.

## URLs

| Endpoint                                              | What you get                              |
| ----------------------------------------------------- | ----------------------------------------- |
| `https://date.batcomputer.waynetower.de/`             | Angular SPA                               |
| `https://date.batcomputer.waynetower.de/api/v1/health/` | Backend health JSON                     |
| `https://date.batcomputer.waynetower.de/api/v1/docs`  | Swagger UI for v1 API (147 routes)        |
| `https://date.batcomputer.waynetower.de/api/v1/openapi.json` | Full OpenAPI schema                |
| `https://date.batcomputer.waynetower.de/docs`         | Swagger for the parent app shell (small)  |
| `https://grafana.batcomputer.waynetower.de/dashboards` → DAPP | "DAPP Overview" dashboard         |

`/metrics` is intentionally NOT proxied through nginx — it's only
reachable inside the `monitoring_monitoring` docker network where
Prometheus lives.

## DNS

`date.batcomputer.waynetower.de` resolves via the household Pi-hole to
the Tailscale IP `100.96.45.92`. The entry is in
`/opt/pihole/etc-pihole/pihole.toml` under `dns.hosts`. To add another
hostname, append to that list and reload pihole. See `dns.hosts` in
the pihole config for the established `100.96.45.92 *.batcomputer…`
pattern.

## Secrets

`.env.demo` (not committed) holds two values, both required:

```bash
SECRET_KEY=...        # 48-byte random; signs JWTs
POSTGRES_PASSWORD=... # 24-byte random
```

A safe template lives in `.env.demo.example`. Generate fresh values
with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

## Deploying a new release

```bash
./scripts/deploy-demo.sh
```

This is the only command you should ever need. It:

1. Verifies prerequisites (docker, networks, `.env.demo`)
2. Syncs Grafana provisioning + Prometheus scrape jobs into
   `/opt/monitoring/config/` only if they have drifted
3. Builds images (Docker layer cache makes re-deploys fast)
4. Recreates DAPP containers via `docker compose up -d`
5. Polls `/health` until backend is ready (90 s timeout)
6. Reloads Prometheus/Grafana when monitoring configs changed

It is idempotent — running it again with no changes is a no-op apart
from a fresh container restart.

Use `./scripts/deploy-demo.sh --check` to validate the environment
without deploying.

## Observability

### Metrics (Prometheus)

Eight first-class business metrics are exported on
`dapp-backend:8000/metrics` with the `dapp_` prefix:

| Metric                                   | Type      | Labels        |
| ---------------------------------------- | --------- | ------------- |
| `dapp_users_registered_total`            | Counter   | —             |
| `dapp_emotional_onboarding_completed_total` | Counter | —           |
| `dapp_soul_connections_initiated_total`  | Counter   | —             |
| `dapp_revelations_sent_total`            | Counter   | `day_number`  |
| `dapp_messages_sent_total`               | Counter   | —             |
| `dapp_login_attempts_total`              | Counter   | `result`      |
| `dapp_soul_connections_active`           | Gauge     | —             |
| `dapp_compatibility_calc_seconds`        | Histogram | —             |

HTTP-level metrics (`http_requests_total`, `http_request_duration_seconds_bucket`)
come from `prometheus-fastapi-instrumentator`.

The backend runs with `--workers 1` because `prometheus_client`'s
default `REGISTRY` is per-process. Multi-worker would silently split
counters across workers, breaking every scrape. If demo traffic ever
warrants multiple workers, switch to `MultiProcessCollector` with a
`PROMETHEUS_MULTIPROC_DIR` shared-memory directory.

### Logs (Loki)

Promtail with Docker service discovery is already running on this
host. It picks up every container whose name matches `dapp-*` and
labels the stream `project=dapp` plus `service=<compose-service>`. No
DAPP-side configuration needed — query it in Grafana with:

```logql
{project="dapp"} | json
```

### Dashboards (Grafana)

The single dashboard `DAPP Overview` lives at
`monitoring/dapp-overview-dashboard.json` and is provisioned by
`monitoring/dapp-dashboards-provider.yml`. Both files are synced into
`/opt/monitoring/config/grafana/provisioning/dashboards/` by
`deploy-demo.sh`. The provider is scoped to a `dapp/` subdirectory so
it can't collide with other tenants' dashboard UIDs.

To add a panel: edit the JSON, commit, redeploy. Grafana polls the
provisioning directory every 30 s — no restart needed for content
changes (only for changes to the provider `.yml`).

## How the proxy chain handles HTTPS

NPM terminates TLS, then forwards plain HTTP to `dapp-frontend:80`
inside `nginx_proxy`. `dapp-frontend`'s nginx then either:

- Serves a static file from `/usr/share/nginx/html/`
- Falls back to `index.html` (SPA routes)
- Proxies `/api/` to `dapp-backend:8000`
- Proxies `/docs`, `/redoc`, `/openapi.json` to `dapp-backend:8000`

For the backend to build correct `https://` redirects (FastAPI's
trailing-slash 307 etc.) two things are wired:

1. `dapp-frontend` nginx forwards `X-Forwarded-Proto:
   $http_x_forwarded_proto`, preserving NPM's original `https`
2. uvicorn runs with `--proxy-headers --forwarded-allow-ips="*"`

If you ever see a redirect to `http://...`, one of those two has
regressed.

## Disaster recovery

Database lives in the named volume `dapp_postgres_data`. Back it up
with:

```bash
docker run --rm -v dapp_postgres_data:/data -v "$PWD":/backup \
  alpine tar czf /backup/dapp-pg-$(date +%F).tar.gz -C /data .
```

To wipe and start over:

```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo down -v
./scripts/deploy-demo.sh
```

(`-v` removes the volume; alembic re-creates the schema on next
backend startup.)

## Source-of-truth files

- `docker-compose.demo.yml` — runtime
- `python-backend/Dockerfile` + `entrypoint.sh` — backend image
- `angular-frontend/Dockerfile` + `nginx.conf` — frontend image
- `python-backend/app/observability/` — metric definitions + setup
- `monitoring/prometheus-dapp-jobs.yml` — Prometheus scrape jobs
- `monitoring/dapp-overview-dashboard.json` + `…-provider.yml` — Grafana
- `scripts/deploy-demo.sh` — deploy orchestration
- `docs/superpowers/specs/2026-04-22-dapp-demo-server-design.md` — design rationale
- `docs/superpowers/plans/2026-04-22-dapp-demo-server-plan.md` — original implementation plan
