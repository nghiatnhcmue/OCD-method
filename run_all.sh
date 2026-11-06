#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
WORKERS=${WORKERS:-4}
TIME_LIMIT=${TIME_LIMIT:-21600}
METHODS=${*:-"danmf infomap slpa clusterone bigclam oslom proposed aslpaw wghac"}
for m in $METHODS; do
  for k in 1 2 3; do
    python3 "methods/$m/run_test$k.py" --workers "$WORKERS" --time-limit "$TIME_LIMIT"
  done
done
python3 common/rescore.py --workers "$WORKERS" --missing-only
python3 common/summarize.py
