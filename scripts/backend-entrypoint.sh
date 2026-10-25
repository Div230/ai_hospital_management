#!/bin/sh
set -eu
if [ "${1:-}" = "serve" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
fi
exec "$@"
