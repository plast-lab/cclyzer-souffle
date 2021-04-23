#!/bin/bash

ANALYSIS_CONFIG="src/logic/analysis.config"

if [ -f "$ANALYSIS_CONFIG" ]; then
    rm $ANALYSIS_CONFIG
fi

usage() {
    echo "Usage: $0 PARAMETERS [OPTIONS]"
    echo "PARAMETERS:"
    echo "  -i <input bitcode file>"
    echo "  -a <analysis>
            
     available analysis options:           context-insensitive
                                           1-call-site-sensitive+heap
                                           2-call-site-sensitive+heap"
    exit 1;
}

while getopts "i:a::" o; do
    case "${o}" in
        i)
            INPUT_FILE=${OPTARG}
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

rm -rf ./facts/
mkdir facts
bin/fact-generator -o facts/ "$INPUT_FILE"
python3 cti.py facts/
mkdir -p results

if [ "$ANALYSIS" = "context-insensitive" ]; then
    echo "#define CONTEXT_INSENSITIVE" >> "$ANALYSIS_CONFIG"
elif [ "$ANALYSIS" = "1-call-site-sensitive+heap" ]; then
    echo "#define ONE_CALL_SITE_SENSITIVE_HEAP" >> "$ANALYSIS_CONFIG"
elif [ "$ANALYSIS" = "2-call-site-sensitive+heap" ]; then
    echo "#define TWO_CALL_SITE_SENSITIVE_HEAP" >> "$ANALYSIS_CONFIG"
else
    echo "#define CONTEXT_INSENSITIVE" >> "$ANALYSIS_CONFIG"
fi

souffle --profile=cclyzer.log -F facts/ -D results/ src/logic/master.project
rm "$ANALYSIS_CONFIG"
touch "$ANALYSIS_CONFIG"
