#!/usr/bin/env bash

gunicorn databasic:app --workers $WORKERS --timeout 120 --log-file=-