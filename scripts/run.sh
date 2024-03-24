#!/bin/sh -e

alembic upgrade head

sh /prestart.sh

sh /start-server.sh
