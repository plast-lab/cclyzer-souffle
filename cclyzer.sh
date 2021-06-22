#!/bin/bash

CCLYZER_DIR=$(dirname $(readlink -f "$0"))
ANALYSIS_CONFIG="$CCLYZER_DIR/src/logic/analysis.config"

if [ -f "$ANALYSIS_CONFIG" ]; then
    rm $ANALYSIS_CONFIG
fi

usage() {
    echo "Usage: $0 PARAMETERS [OPTIONS]"
    echo "PARAMETERS:"
    echo "  -i <input bitcode file>"
    echo "  -o <output directory>"
    echo "  -a <analysis>

     available analysis options:           context-insensitive
                                           1-call-site-sensitive+heap
                                           2-call-site-sensitive+heap"
    exit 1;
}

OUTPUT_DIR=$(pwd)

while getopts "i:o:a::" o; do
    case "${o}" in
        i)
            INPUT_FILE=${OPTARG}
            ;;
        o)
            OUTPUT_DIR=${OPTARG}
            ;;
        a)
            ANALYSIS=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

if ((OPTIND == 1)); then
    usage
fi

shift $((OPTIND-1))
if [ ! -f "$INPUT_FILE" ]; then
    echo Input file "$INPUT_FILE" not found!
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo Output directory "$OUTPUT_DIR" not found!
    exit 1
fi

rm -rf $OUTPUT_DIR/facts/
mkdir $OUTPUT_DIR/facts
$CCLYZER_DIR/bin/fact-generator -o $OUTPUT_DIR/facts/ "$INPUT_FILE"
python3 $CCLYZER_DIR/cti.py $OUTPUT_DIR/facts/
mkdir -p $OUTPUT_DIR/results

if [ "$ANALYSIS" = "context-insensitive" ]; then
    echo "#define CONTEXT_INSENSITIVE" >> "$ANALYSIS_CONFIG"
elif [ "$ANALYSIS" = "1-call-site-sensitive+heap" ]; then
    echo "#define ONE_CALL_SITE_SENSITIVE_HEAP" >> "$ANALYSIS_CONFIG"
elif [ "$ANALYSIS" = "2-call-site-sensitive+heap" ]; then
    echo "#define TWO_CALL_SITE_SENSITIVE_HEAP" >> "$ANALYSIS_CONFIG"
else
    echo "#define CONTEXT_INSENSITIVE" >> "$ANALYSIS_CONFIG"
fi

souffle --profile=cclyzer.log -F $OUTPUT_DIR/facts/ -D $OUTPUT_DIR/results/ $CCLYZER_DIR/src/logic/master.project
rm "$ANALYSIS_CONFIG"
touch "$ANALYSIS_CONFIG"
