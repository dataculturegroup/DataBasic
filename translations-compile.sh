#!/bin/bash

# CD NOTE - For some reason I have to run each of these two lines manually on my local machine for en_GB language
# or else I get a strange locale error. 

LANG=$1
JSONFILE=databasic/translations/${LANG}/LC_MESSAGES/messages.json

pybabel compile -d databasic/translations
pojson databasic/translations/${LANG}/LC_MESSAGES/messages.po > "${JSONFILE}"

echo "compiled '${LANG}' translation"
