#!/usr/bin/bash
. .env.local

python scripts/crawler.py ${CWOI_NAME} ${CWOI_PASSWORD} ${CWOI_HOST} --sleep 0 > ./latest_crawl.json
python scripts/merge.py ./latest_crawl.json ./src/data/contests.json > ./merged.json
cp ./merged.json ./src/data/contests.json
rm ./latest_crawl.json ./merged.json
