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

# One compiled binary per analysis, $(OUTDIR)/cclyzer-<analysis>. The
# analysis is chosen with a Soufflé macro (see master.project), so building
# or running one analysis never touches the source tree.
# Build only some of them with e.g. `make ANALYSES=context-insensitive`.
ANALYSES ?= context-insensitive \
            1-call-site-sensitive+heap \
            2-call-site-sensitive+heap \
            2-call-site-sensitive+2-heap

macro.context-insensitive          := CONTEXT_INSENSITIVE
macro.1-call-site-sensitive+heap   := ONE_CALL_SITE_SENSITIVE_HEAP
macro.2-call-site-sensitive+heap   := TWO_CALL_SITE_SENSITIVE_HEAP
macro.2-call-site-sensitive+2-heap := TWO_CALL_SITE_SENSITIVE_TWO_HEAP

LOGIC_BINARIES := $(ANALYSES:%=$(OUTDIR)/cclyzer-%)

# -j: Soufflé emits parallel code only when compiling with -j; without it
# the binary ignores its own -j option and runs on one thread.
$(OUTDIR)/cclyzer-%: $(LOGIC_FILES) $(HEADER_FILES) | $(OUTDIR)
	$(if $(macro.$*),,$(error Unknown analysis '$*'. Known: $(subst macro.,,$(filter macro.%,$(.VARIABLES)))))
	souffle -j auto --macro=$(macro.$*)=1 -o $@ master.project

all: $(LOGIC_BINARIES)


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

#OUTPUT_LOGIC := export/generate-output.dl
#OUTPUT_EXTRA := export/more-output-predicates.txt
#
#ll: $(OUTPUT_LOGIC)
#
#$(OUTPUT_LOGIC): $(filter-out %/$(OUTPUT_LOGIC), $(LOGIC_FILES)) $(OUTPUT_EXTRA)
#	$(SCRIPTDIR)/codegen-export-logic.py . -o $@ --extra-output-preds $(OUTPUT_EXTRA)
