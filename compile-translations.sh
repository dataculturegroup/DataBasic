#!/bin/bash

JSONFILE=databasic/translations/es/LC_MESSAGES/messages.json
ES_FILE=databasic/static/js/es-locale-data.js

pybabel compile -d databasic/translations
pojson databasic/translations/es/LC_MESSAGES/messages.po > "${JSONFILE}"

LINENUMBER=7
ES=`cat ${JSONFILE}`

awk -v line=${LINENUMBER} -v new_content="${ES}" '{
        if (NR == line) {
                print new_content;
        } else {
                print $0;
        }
}' "${ES_FILE}" > "${ES_FILE}.new"

mv "${ES_FILE}.new" "${ES_FILE}"