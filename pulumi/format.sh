#!/usr/bin/env bash
set -ex

isort --force-single-line-imports --thirdparty pulumi --virtual-env ./venv *.py dev/**.py common/**.py aws/**.py
yapf -i --recursive *.py dev/ aws/
