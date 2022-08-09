#!/usr/bin/env bash

POSTGRES_HOST = $(pulumi stack output postgres-host)
POSTGRES_PORT = $(pulumi stack output postgres-port)
POSTGRES_PASS = $(pulumi stack output postgres-password)
