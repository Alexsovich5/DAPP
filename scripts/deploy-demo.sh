#!/usr/bin/env bash
# scripts/deploy-demo.sh
#
# Idempotent rolling-release deploy for the demo server at
# https://date.batcomputer.waynetower.de.
#
# What it does (in order):
#   1. Verifies prerequisites: docker, required external networks, .env.demo
#   2. Syncs monitoring configs into /opt/monitoring/ if they have drifted
#      from the in-repo source of truth (Prometheus scrape jobs, Grafana
#      provisioning + dashboard JSON)
#   3. Builds docker images (cache-aware)
#   4. Stops any old DAPP containers and starts the new ones
#   5. Waits for backend /health to return 200
#   6. Reloads Prometheus + Grafana so new scrape jobs / dashboards are
#      picked up without a full restart
#
# Re-run this script after every commit you want live on the demo.
# It is intentionally chatty — every step prints what it changed.
#
# Usage:
#   ./scripts/deploy-demo.sh         # full deploy
#   ./scripts/deploy-demo.sh --check # validate environment, do not deploy

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CHECK_ONLY="${1:-}"

# --- ANSI colors (only if stdout is a terminal) -------------------------------
if [[ -t 1 ]]; then
  C_OK=$'\033[32m'; C_INFO=$'\033[36m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_RST=$'\033[0m'
else
  C_OK=""; C_INFO=""; C_WARN=""; C_ERR=""; C_RST=""
fi
ok()   { echo "${C_OK}✓${C_RST} $*"; }
info() { echo "${C_INFO}→${C_RST} $*"; }
warn() { echo "${C_WARN}!${C_RST} $*" >&2; }
fail() { echo "${C_ERR}✗${C_RST} $*" >&2; exit 1; }

# --- 1. Preflight -------------------------------------------------------------
info "Preflight checks"

command -v docker >/dev/null || fail "docker not on PATH"
docker info >/dev/null 2>&1 || fail "docker daemon not reachable"

[[ -f .env.demo ]] || fail "missing .env.demo (copy .env.demo.example and fill in secrets)"

for net in monitoring_monitoring nginx_proxy; do
  docker network inspect "$net" >/dev/null 2>&1 \
    || fail "external docker network '$net' is missing — bring up monitoring/NPM stacks first"
done
ok "docker, .env.demo, external networks present"

[[ -d /opt/monitoring/config ]] \
  || warn "/opt/monitoring/config not found — monitoring sync will be skipped"

if [[ "$CHECK_ONLY" == "--check" ]]; then
  ok "preflight only — exiting"
  exit 0
fi

# --- 2. Sync monitoring configs ----------------------------------------------
# Idempotent: only writes when the destination differs from the source. This
# keeps re-deploys fast and avoids touching files that haven't changed.
sync_if_changed() {
  local src="$1" dst="$2"
  if [[ ! -f "$src" ]]; then return; fi
  if [[ ! -f "$dst" ]] || ! cmp -s "$src" "$dst"; then
    sudo install -D -m 0644 "$src" "$dst"
    ok "synced $(basename "$dst")"
    return 0
  fi
  return 1
}

if [[ -d /opt/monitoring/config ]]; then
  info "Sync monitoring configs"

  changed_grafana=false
  if sync_if_changed monitoring/dapp-dashboards-provider.yml \
       /opt/monitoring/config/grafana/provisioning/dashboards/dapp.yml; then
    changed_grafana=true
  fi
  if sync_if_changed monitoring/dapp-overview-dashboard.json \
       /opt/monitoring/config/grafana/provisioning/dashboards/dapp/dapp-overview.json; then
    changed_grafana=true
  fi

  # Prometheus scrape jobs: append once. We detect by grepping for the
  # job_name; duplicates would break the reload.
  changed_prometheus=false
  if [[ -f /opt/monitoring/config/prometheus.yml ]]; then
    if ! grep -q "job_name: 'dapp-backend'" /opt/monitoring/config/prometheus.yml; then
      sudo tee -a /opt/monitoring/config/prometheus.yml < monitoring/prometheus-dapp-jobs.yml >/dev/null
      changed_prometheus=true
      ok "appended dapp scrape jobs to prometheus.yml"
    fi
  fi
fi

# --- 3. Build images ----------------------------------------------------------
info "Build images (cache-aware)"
docker compose -f docker-compose.demo.yml --env-file .env.demo build
ok "images built"

# --- 4. Recreate containers ---------------------------------------------------
info "Recreate DAPP containers"
docker compose -f docker-compose.demo.yml --env-file .env.demo up -d --remove-orphans
ok "containers up"

# --- 5. Wait for backend health ----------------------------------------------
info "Wait for backend /health (timeout 90s)"
deadline=$(( $(date +%s) + 90 ))
while (( $(date +%s) < deadline )); do
  if docker exec dapp-backend curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    ok "backend healthy"
    break
  fi
  sleep 2
done
if ! docker exec dapp-backend curl -sf http://localhost:8000/health >/dev/null 2>&1; then
  fail "backend never became healthy — check 'docker logs dapp-backend'"
fi

# --- 6. Reload observability stack -------------------------------------------
# Prometheus on this host runs WITHOUT --web.enable-lifecycle, so we have
# to send SIGHUP to the master process. Grafana similarly picks up new
# dashboards on a SIGHUP, but provisioning poll interval is 30s so we just
# wait if nothing changed.
if [[ "${changed_prometheus:-false}" == true ]]; then
  if docker ps --format '{{.Names}}' | grep -q '^prometheus$'; then
    docker kill --signal=SIGHUP prometheus >/dev/null
    ok "prometheus reloaded"
  fi
fi

if [[ "${changed_grafana:-false}" == true ]]; then
  if docker ps --format '{{.Names}}' | grep -q '^grafana$'; then
    # Grafana must be restarted (not SIGHUP'd) for new provider files to be
    # picked up. Dashboard JSON inside an already-known provider IS picked
    # up via the 30s file poll, so we only restart when the .yml changed.
    if [[ -f /opt/monitoring/config/grafana/provisioning/dashboards/dapp.yml ]] \
       && [[ /opt/monitoring/config/grafana/provisioning/dashboards/dapp.yml \
             -nt /var/lib/docker/containers/$(docker inspect grafana --format '{{.Id}}')/config.v2.json ]]; then
      docker restart grafana >/dev/null
      ok "grafana restarted (new provider config)"
    else
      ok "grafana provider unchanged — dashboard JSON will be polled"
    fi
  fi
fi

# --- 7. Summary ---------------------------------------------------------------
echo
ok "Demo deploy complete."
echo
echo "  Public URL : https://date.batcomputer.waynetower.de/"
echo "  API health : https://date.batcomputer.waynetower.de/api/v1/health/"
echo "  API docs   : https://date.batcomputer.waynetower.de/api/v1/docs"
echo "  Metrics    : http://localhost:9091  (Prometheus, query dapp_*)"
echo "  Dashboards : https://grafana.batcomputer.waynetower.de/  → folder 'DAPP'"
echo
