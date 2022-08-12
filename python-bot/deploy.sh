#!/usr/bin/env bash

set -exuo pipefail

namespace=${1:-abyss-dev}

docker build . -t registry.registry.cakesoft.local:5000/abyss/discord-bot:latest
docker push registry.registry.cakesoft.local:5000/abyss/discord-bot:latest
kubectl -n ${namespace} rollout restart deployment/abyss-bot
