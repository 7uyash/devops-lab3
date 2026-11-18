#!/usr/bin/env bash
# Generates mixed traffic against ShopLite: normal pages, 404s, slow calls and errors.
# usage: scripts/traffic.sh BASE_URL SECONDS
BASE=${1:-http://localhost:8000}
END=$(( $(date +%s) + ${2:-60} ))
n=0
while [ "$(date +%s)" -lt "$END" ]; do
  u="user$(( RANDOM % 40 ))"
  r=$(( RANDOM % 100 ))
  if   [ $r -lt 30 ]; then p="/api/products"
  elif [ $r -lt 50 ]; then p="/"
  elif [ $r -lt 62 ]; then p="/api/products/$(( RANDOM % 6 + 1 ))"
  elif [ $r -lt 77 ]; then p="/checkout"
  elif [ $r -lt 85 ]; then p="/health"
  elif [ $r -lt 92 ]; then p="/api/slow"
  elif [ $r -lt 96 ]; then p="/flags"
  else p="/api/error"; fi
  curl -s -o /dev/null "$BASE$p?user=$u" &
  n=$((n+1))
  [ $((n % 8)) -eq 0 ] && wait
  sleep 0.05
done
wait
echo "sent $n requests"
