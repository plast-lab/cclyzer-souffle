#!/usr/bin/env bash
#
# Generate facts for an LLVM bitcode file and run one cclyzer analysis on them.
# Uses the compiled analysis from `make` when there is one, else Soufflé's
# interpreter. Never writes into the source tree, so several runs can share
# one checkout.

set -euo pipefail

CCLYZER_DIR=$(dirname "$(readlink -f "$0")")

declare -A MACRO=(
    [context-insensitive]=CONTEXT_INSENSITIVE
    [1-call-site-sensitive+heap]=ONE_CALL_SITE_SENSITIVE_HEAP
    [2-call-site-sensitive+heap]=TWO_CALL_SITE_SENSITIVE_HEAP
    [2-call-site-sensitive+2-heap]=TWO_CALL_SITE_SENSITIVE_TWO_HEAP
)

usage() {
    cat <<EOF
Usage: $0 -i <input.bc> [-o <output dir>] [-a <analysis>] [-j <threads>]

  -i  input LLVM bitcode file (one whole program: link all translation units first)
  -o  output directory, created if missing (default: current directory).
      Facts go to <dir>/facts, results to <dir>/results.
  -a  analysis (default: context-insensitive):
        context-insensitive
        1-call-site-sensitive+heap
        2-call-site-sensitive+heap
        2-call-site-sensitive+2-heap
  -j  Soufflé threads (default: auto)
EOF
    exit "${1:-1}"
}

INPUT_FILE=
OUTPUT_DIR=$(pwd)
ANALYSIS=context-insensitive
JOBS=auto

while getopts "i:o:a:j:h" o; do
    case "$o" in
        i) INPUT_FILE=$OPTARG ;;
        o) OUTPUT_DIR=$OPTARG ;;
        a) ANALYSIS=$OPTARG ;;
        j) JOBS=$OPTARG ;;
        h) usage 0 ;;
        *) usage ;;
    esac
done

[ -n "$INPUT_FILE" ] || usage
if [ ! -f "$INPUT_FILE" ]; then
    echo "Input file '$INPUT_FILE' not found!" >&2
    exit 1
fi
if [ -z "${MACRO[$ANALYSIS]+x}" ]; then
    echo "Unknown analysis '$ANALYSIS'. Known: ${!MACRO[*]}" >&2
    exit 1
fi

FACTS="$OUTPUT_DIR/facts"
RESULTS="$OUTPUT_DIR/results"
rm -rf -- "$FACTS"
mkdir -p -- "$FACTS" "$RESULTS"

"$CCLYZER_DIR/bin/fact-generator" -o "$FACTS/" "$INPUT_FILE"
python3 "$CCLYZER_DIR/cti.py" "$FACTS/"

# Warn (never fail) when the input does not look like a whole program.
# CCLYZER_NO_CHECKS=1 turns this off.
check() {
    [ "${CCLYZER_NO_CHECKS:-0}" = 1 ] || python3 "$CCLYZER_DIR/scripts/check-whole-program.py" "$@" || true
}
check facts "$FACTS"

COMPILED="$CCLYZER_DIR/build/logic/cclyzer-$ANALYSIS"
if [ -x "$COMPILED" ]; then
    "$COMPILED" -j "$JOBS" -F "$FACTS/" -D "$RESULTS/"
else
    echo "No compiled $ANALYSIS analysis (run make); using the Soufflé interpreter." >&2
    souffle -j "$JOBS" --macro="${MACRO[$ANALYSIS]}=1" -F "$FACTS/" -D "$RESULTS/" \
            "$CCLYZER_DIR/src/logic/master.project"
fi

check results "$FACTS" "$RESULTS"

# Summary statistics, like Doop's end-of-run statistics
python3 "$CCLYZER_DIR/scripts/stats.py" "$RESULTS" | tee "$OUTPUT_DIR/stats.txt"
python3 "$CCLYZER_DIR/scripts/stats.py" "$RESULTS" --json > "$OUTPUT_DIR/stats.json"
