#!/bin/bash
# Resumable fetch of the eight CALCE PL pouch SOC-window zips (notes/data/NASA_CALCE_feasibility.md).
# In-progress data always lives in <name>.part; it is renamed to <name> only when its size equals the byte count
# below. 40 KB/s cap. The CALCE server refuses connections for hours at a time, so the whole queue is retried in
# rounds (sleep 5 min between rounds, up to 200 rounds). Stop: create data/STOP_CALCE. Log: data/logs/fetch_calce.log
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
D="$ROOT/data/raw/calce_pl_pouch"; B=https://web.calce.umd.edu/batteries/data/pl
LOG="$ROOT/data/logs/fetch_calce.log"; mkdir -p "$ROOT/data/logs"
LIST="SOC_20-80_2C.zip:74575680 SOC_0-100_HalfC.zip:67460712 SOC_0-100_2C.zip:57559175 SOC_40-60_2C.zip:57740595
SOC_40-60_HalfC.zip:72818135 SOC_0-60_HalfC.zip:89357014 SOC_40-100_HalfC.zip:106626746 SOC_20-80_HalfC.zip:132710443"
cd "$D" || exit 1
# normalise: an incomplete file with the final name goes back to .part (keep the larger one)
for e in $LIST; do f=${e%%:*}; s=${e##*:}
  if [ -f "$f" ] && [ "$(stat -c %s "$f")" != "$s" ]; then
    if [ ! -f "$f.part" ] || [ "$(stat -c %s "$f")" -gt "$(stat -c %s "$f.part")" ]; then mv -f "$f" "$f.part"; else rm -f "$f"; fi
  fi
done
for round in $(seq 1 200); do
  left=0
  for e in $LIST; do f=${e%%:*}; s=${e##*:}
    [ -f "$ROOT/data/STOP_CALCE" ] && { echo "$(date +%F\ %T) stop file" >> "$LOG"; exit 0; }
    [ -f "$f" ] && [ "$(stat -c %s "$f")" = "$s" ] && continue
    left=1
    curl -L -C - -sS --connect-timeout 30 --limit-rate 40k -m 1800 -A "Mozilla/5.0" -o "$f.part" "$B/$f" 2>>"$LOG" || true
    if [ "$(stat -c %s "$f.part" 2>/dev/null)" = "$s" ]; then mv "$f.part" "$f"; echo "$(date +%F\ %T) done $f" >> "$LOG"; fi
  done
  [ $left = 0 ] && { echo "$(date +%F\ %T) ALLDONE" >> "$LOG"; exit 0; }
  sleep 300
done
