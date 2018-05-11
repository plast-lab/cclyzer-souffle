# Directory depth
LEVEL := ../..

# Placeholder
all:

# Import common Makefile routines
include $(LEVEL)/src/common.mk


#-----------------------------------
# Phony targets
#-----------------------------------

all:

force:

clean:
	$(RM) -r $(OUTDIR)

.PHONY: all clean force


#-----------------------------------
# Souffle Compilation
#-----------------------------------

LOGIC_FILES  := $(shell find ./ -type f -name '*.dl')
HEADER_FILES := $(shell find ./ -type f -name '*.project')
MODULES      := $(patsubst ./%/,%,$(dir $(HEADER_FILES)))

LOGIC_CXX_OUT := cclyzer-analyze


$(LOGIC_CXX_OUT): $(LOGIC_FILES) $(HEADER_FILES) | $(OUTDIR)
	souffle -c master.project


all: $(LOGIC_CXX_OUT)


#-----------------------------------
# Transform to python package
#-----------------------------------

all: $(OUTDIR)/__init__.py

$(OUTDIR)/__init__.py:
	touch $@

#-----------------------------------
# Predicate Lists
#-----------------------------------

ALL_PREDS   := all-predicates.txt~
INPUT_PREDS := input-predicates.txt~

$(ALL_PREDS):
	grep -Rhe '^\.decl' | sed 's/.decl \(.*\)(.*)/\1/' | sort -u > $@

$(INPUT_PREDS):
	grep -Rhe '^\.input' | sed 's/.input \(.*\)(.*)/\1/' | sort -u > $@

generate-output.dl: $(ALL_PREDS) $(INPUT_PREDS)
	comm -3 $(ALL_PREDS) $(INPUT_PREDS) | sed -e 's/^/.output /' > $@
