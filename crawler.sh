#!/usr/bin/bash
. .dev.vars

python scripts/crawler.py ${CWOI_NAME} ${CWOI_PASSWORD} ${CWOI_HOST} --sleep 0 > src/data/contests.json