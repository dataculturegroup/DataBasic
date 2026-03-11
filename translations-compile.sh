#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <language_code|all>"
  exit 1
fi

LANG=$1

if [ "$LANG" = "all" ]; then
  pybabel compile -d databasic/translations

  for POFILE in databasic/translations/*/LC_MESSAGES/messages.po; do
    JSONFILE="${POFILE%.po}.json"
    pojson "$POFILE" > "$JSONFILE"
  done

  echo "compiled all translations"

else
  JSONFILE=databasic/translations/${LANG}/LC_MESSAGES/messages.json

  pybabel compile -d databasic/translations -l "${LANG}"
  pojson "databasic/translations/${LANG}/LC_MESSAGES/messages.po" > "${JSONFILE}"

  echo "compiled '${LANG}' translation"
fi