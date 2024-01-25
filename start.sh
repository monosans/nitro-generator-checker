#!/bin/sh

set -eu

python3 -m venv --upgrade-deps .venv
.venv/bin/python3 -m pip install -U --disable-pip-version-check -r requirements.txt
.venv/bin/python3 -m nitro_generator_checker
