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
# Output Logic
#-----------------------------------

OUTPUT_LOGIC := export/generate-output.dl

all: $(OUTPUT_LOGIC)

$(OUTPUT_LOGIC): $(filter-out %/$(OUTPUT_LOGIC), $(LOGIC_FILES))
	$(SCRIPTDIR)/codegen-export-logic.py . -o $@
