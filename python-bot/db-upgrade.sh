#!/usr/bin/env bash

set -euo pipefail

namespace=${1:-abyss-dev}

stale_job=$(kubectl -n ${namespace} get job upgrade-schema --no-headers 2>/dev/null || true)

if [[ ! -z "${stale_job}" ]]; then
  while true; do
    read -r -p "[-] Stale job, do you want to delete it? [y/n] " input

    case $input in
      [yY]*)
        kubectl -n ${namespace} delete job upgrade-schema
        break;
        ;;
      [nN]*)
        echo '[-] Please run:'
        echo '  kubectl -n abyss delete job upgrade-schema'
        echo '[-] and rerun this script'
        exit 1
        ;;
      *)
        echo '[-] Please enter yes or no'
    esac
  done
fi

set -x

docker build . -f Dockerfile.dbmigrate -t registry.registry.cakesoft.local:5000/abyss/db-migrate:latest
docker push registry.registry.cakesoft.local:5000/abyss/db-migrate:latest
kubectl create -n ${namespace} -f ./kubernetes/upgrade-alembic.yaml
