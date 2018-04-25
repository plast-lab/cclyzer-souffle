ALL_PREDS   := all-predicates.txt~
INPUT_PREDS := input-predicates.txt~

all:
	souffle -c src/master.project

$(ALL_PREDS):
	grep -Rhe '^\.decl' | sed 's/.decl \(.*\)(.*)/\1/' | sort -u > $@

$(INPUT_PREDS):
	grep -Rhe '^\.input' | sed 's/.input \(.*\)(.*)/\1/' | sort -u > $@

src/generate-output.dl: $(ALL_PREDS) $(INPUT_PREDS)
	comm -3 $(ALL_PREDS) $(INPUT_PREDS) | sed -e 's/^/.output /' > $@
