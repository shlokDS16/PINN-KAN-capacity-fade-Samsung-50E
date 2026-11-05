#!/bin/bash
# Resumable fetch of the CALCE PL pouch SOC-window zips (the only CALCE subset kept for the NASA/CALCE
# feasibility work, notes/data/NASA_CALCE_feasibility.md). One file at a time, 40 KB/s cap, 12 tries per file.
# Stop: create data/STOP_CALCE. A file is complete only when its size equals the size below; in-progress
# files carry the final name until then (compare sizes; zipfile cannot open them).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
D="$ROOT/data/raw/calce_pl_pouch"; B=https://web.calce.umd.edu/batteries/data/pl
get() { f="$1"; size="$2"; cd "$D" || exit 1
  [ -f "$f" ] && [ "$(stat -c %s "$f")" = "$size" ] && return 0
  [ -f "$f.part" ] && mv "$f.part" "$f"
  for i in $(seq 1 12); do
    [ -f "$ROOT/data/STOP_CALCE" ] && exit 0
    curl -L -C - -sS --limit-rate 40k -m 3000 -A "Mozilla/5.0" -o "$f" "$B/$f" || true
    [ "$(stat -c %s "$f" 2>/dev/null)" = "$size" ] && { echo "$(date +%T) done $f"; return 0; }
    sleep 20
  done
  [ -f "$f" ] && mv "$f" "$f.part"; }
get SOC_20-80_2C.zip 74575680
get SOC_0-100_HalfC.zip 67460712
get SOC_0-100_2C.zip 57559175
get SOC_40-60_2C.zip 57740595
get SOC_40-60_HalfC.zip 72818135
get SOC_0-60_HalfC.zip 89357014
get SOC_40-100_HalfC.zip 106626746
get SOC_20-80_HalfC.zip 132710443
echo ALLDONE
