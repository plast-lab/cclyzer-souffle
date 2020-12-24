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

LOGIC_CXX_OUT := $(OUTDIR)/cclyzer-analyze

$(LOGIC_CXX_OUT): $(LOGIC_FILES) $(HEADER_FILES) | $(OUTDIR)
	souffle -o $@ master.project

#$(LOGIC_CXX_OUT): $(LOGIC_FILES) $(HEADER_FILES) | $(OUTDIR)
#	souffle --profile=cclyzer.log master.dl

#$(LOGIC_CXX_OUT): $(LOGIC_FILES) $(HEADER_FILES) | $(OUTDIR)
#	souffle -c -F ../../facts/ -D ../../results/ -o $@ master.project

all: $(LOGIC_CXX_OUT)


#-----------------------------------
# Transform to python package
#-----------------------------------

all: $(OUTDIR)/__init__.py

$(OUTDIR)/__init__.py:
	mkdir -p $(OUTDIR)
	touch $@


#-----------------------------------
# Output Logic
#-----------------------------------

OUTPUT_LOGIC := export/generate-output.dl
OUTPUT_EXTRA := export/more-output-predicates.txt

all: $(OUTPUT_LOGIC)

$(OUTPUT_LOGIC): $(filter-out %/$(OUTPUT_LOGIC), $(LOGIC_FILES)) $(OUTPUT_EXTRA)
	$(SCRIPTDIR)/codegen-export-logic.py . -o $@ --extra-output-preds $(OUTPUT_EXTRA)
