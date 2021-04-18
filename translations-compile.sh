#!/bin/bash

LANG=$1
JSONFILE=databasic/translations/${LANG}/LC_MESSAGES/messages.json

pybabel compile -d databasic/translations
pojson databasic/translations/${LANG}/LC_MESSAGES/messages.po > "${JSONFILE}"

echo "compiled '${LANG}' translation"
