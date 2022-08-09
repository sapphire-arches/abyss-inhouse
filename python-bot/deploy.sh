#!/usr/bin/env bash

set -exuo pipefail

docker build . -t registry.registry.cakesoft.local:5000/abyss/discord-bot:latest
docker push registry.registry.cakesoft.local:5000/abyss/discord-bot:latest
kubectl -n abyss rollout restart deployment/abyss-bot
