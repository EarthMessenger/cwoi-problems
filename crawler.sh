#!/usr/bin/bash
. .env.local

python scripts/crawler.py ${CWOI_NAME} ${CWOI_PASSWORD} ${CWOI_HOST} --sleep 0 > ./latest_crawl.json
python scripts/merge.py ./src/data/contests.json ./latest_crawl.json > ./merged.json
cp ./merged.json ./src/data/contests.json
rm ./latest_crawl.json ./merged.json
