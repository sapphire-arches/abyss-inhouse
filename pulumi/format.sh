#!/usr/bin/env bash
set -ex

isort --force-single-line-imports --thirdparty pulumi --virtual-env ./venv *.py ingress/**.py
yapf -i --recursive *.py ingress/
