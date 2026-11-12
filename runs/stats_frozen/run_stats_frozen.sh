#!/usr/bin/env bash
# Frozen confirmatory statistics step (PREREG_v4 18 step 7; strict at the FROZEN commit). Lead, 2026-11-12.
# Inputs: the Design R2 grid (5 folds x m 8/16/32), Test C and S2, the downgrade rows (lab_indicator, retain_all,
# random_subset draws 0-2, lab_indicator_C), NC-2 (m32_nc2), the C-rate rows (m32_crate), PC-1 (G0 run pc1_g0_synth, D045),
# the item (f) file and its hash, and the SCORED ledger.
set -euo pipefail
cd "$(dirname "$0")/../.."
r=runs
B=$(printf "$r/conf_samsung_B_f%d_m8,$r/conf_samsung_B_f%d_m16,$r/conf_samsung_B_f%d_m32," 0 0 0 1 1 1 2 2 2 3 3 3 4 4 4); B=${B%,}
S2=$(printf "$r/conf_samsung_S2_f%d," 0 1 2 3 4); S2=${S2%,}
LAB=$(printf "$r/row_labind_B_f%d_g1,$r/row_labind_B_f%d_g4," 0 0 1 1 2 2 3 3 4 4); LAB=${LAB%,}
RET=$(printf "$r/row_retain_B_f%d_g1,$r/row_retain_B_f%d_g4," 0 0 1 1 2 2 3 3 4 4); RET=${RET%,}
RS=""; for d in 0 1 2; do x=$(printf "$r/row_randsub_B_f%d_d${d}_g1," 0 1 2 3 4); RS="$RS${x%,};"; done; RS=${RS%;}
NEG=(); CR=(); for f in 0 1 2 3 4; do NEG+=(--negative-run "$r/conf_samsung_B_f${f}_m32_nc2"); CR+=(--crate-run "$r/conf_samsung_B_f${f}_m32_crate"); done
[ "${1:-}" = "--check" ] && { echo "B $(echo "$B" | tr , '\n' | wc -l) S2 $(echo "$S2" | tr , '\n' | wc -l) lab $(echo "$LAB" | tr , '\n' | wc -l) retain $(echo "$RET" | tr , '\n' | wc -l) draws $(echo "$RS" | tr ';' '\n' | wc -l) neg ${#NEG[@]} crate ${#CR[@]}"; for x in $(echo "$B,$S2,$LAB,$RET,${RS//;/,},$r/conf_samsung_C_f0,$r/row_labind_C_f0,$r/pc1_g0_synth,runs/item_f" | tr , ' ') "${NEG[@]}" "${CR[@]}"; do case $x in --*) ;; *) [ -d "$x" ] || echo "MISSING $x";; esac; done; echo checked; exit 0; }
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=-1
exec .venv/Scripts/python.exe -P code/run_pinnkan_stats.py --analysis-dir runs/stats_frozen/analysis \
  --runs "B=$B" --runs "C=$r/conf_samsung_C_f0" --runs "S2=$S2" \
  --row "lab_indicator=$LAB" --row "retain_all=$RET" --row "random_subset=$RS" --row "lab_indicator_C=$r/row_labind_C_f0" \
  "${NEG[@]}" "${CR[@]}" --h7-run "$r/pc1_g0_synth" \
  --item-f-dir runs/item_f --item-f-sha256 2823abd22e521d404ac6725f1483986e98e70ba0f59a55485c12f4a33159f1cd --ledger-root . \
  </dev/null
