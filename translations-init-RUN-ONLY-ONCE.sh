#!/bin/bash

pybabel extract -F config/babel.cfg databasic/ -o databasic/messages.pot
pybabel init -i databasic/messages.pot -d databasic/translations -l es