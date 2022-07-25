#!/usr/bin/env bash

set -ex
export OTEL_EXPORTER_JAEGER_AGENT_HOST=$(kubectl get svc -o json jaeger-collector | jq -r '.spec.clusterIP')
export OTEL_SERVICE_NAME=discord-bot
export DISCORD_TOKEN=$(pulumi -C ../pulumi config get discord-token)
export APP_ID=1000819756472999998
export PUBLIC_KEY=9e5ad0f3403ba24b0651d6902bf35200dba07f47bcc1600aaa84cd7a5f86c9d6
npm run start:mon
