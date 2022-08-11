#!/usr/bin/env bash

set -euo pipefail

stale_job=$(kubectl -n abyss get job upgrade-schema --no-headers 2>/dev/null || true)

if [[ ! -z "${stale_job}" ]]; then
  echo '[-] Stale job, please run:'
  echo '  kubectl -n abyss delete job upgrade-schema'
  echo '[-] and rerun this script'

  exit 1
fi

set -x

docker build . -f Dockerfile.dbmigrate -t registry.registry.cakesoft.local:5000/abyss/db-migrate:latest
docker push registry.registry.cakesoft.local:5000/abyss/db-migrate:latest
kubectl create -f ./kubernetes/upgrade-alembic.yaml
