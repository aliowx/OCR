#!/bin/sh -e

set -x

ruff app --fix
isort app
black app
