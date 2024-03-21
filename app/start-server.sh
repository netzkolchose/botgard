#!/usr/bin/env bash

./manage.py migrate || exit 1
./manage.py botgard_update_config || exit 1

# ./manage.py cms delete-orphaned-plugins --noinput || exit 1
# ./manage.py compilemessages || exit 1
./manage.py collectstatic --no-input || exit 1

# check for existence of special env variable to run unittest
if [[ -z "${BOTGARD_RUN_TESTS}" ]]; then
  # or run server
  gunicorn -b 127.0.0.1:8000 BotGard.wsgi || exit 1
else
  ./manage.py test || exit 1
fi
