#!/usr/bin/bash
. env.sh

python -m cwoi_problems.crawler ${CWOI_NAME} ${CWOI_PASSWORD} ${CWOI_HOST} --sleep 0 > data/contests.json
python -m cwoi_problems.build data/contests.json dist ${CWOI_HOST}

pnpx wrangler pages deploy dist