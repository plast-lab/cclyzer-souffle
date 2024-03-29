LEVEL := .
CCLYZER_OPTS ?=
PYTHON = python
PIP    = pip
CCLYZER = ./cclyzer.sh

all:

module.logic   := logic
module.facts   := fact-generator
module.jsonast := json-ast-exporter
modules        := $(module.logic) $(module.facts) $(module.jsonast)
modules.clean  := $(addsuffix .clean,$(modules))

include $(LEVEL)/src/common.mk


# Paths to modules

$(addsuffix _PATH, $(module.logic))   := src/logic
$(addsuffix _PATH, $(module.facts))   := tools/fact-generator
$(addsuffix _PATH, $(module.jsonast)) := tools/json-ast-exporter


# Accumulating Rules

$(modules):
	$(MAKE) --directory=$($@_PATH)

$(modules.clean): %.clean:
	$(MAKE) --directory=$($*_PATH) clean


# Phony targets

.PHONY: all clean $(modules) $(modules.clean)
all: $(modules)

clean: $(modules.clean)
	$(RM) -r $(OUTDIR)/

.PHONY: install
install:
	$(PIP) install -r requirements.txt
	$(PYTHON) setup.py install


#-----------------------------------------
#    _            _   _
#   | |_ ___  ___| |_(_)_ __   __ _
#   | __/ _ \/ __| __| | '_ \ / _` |
#   | ||  __/\__ \ |_| | | | | (_| |
#    \__\___||___/\__|_|_| |_|\__, |
#                             |___/
#
#-----------------------------------------


# Overwrite build directory for tests
OUTDIR = $(BUILDDIR)/tests

# List of our coreutils benchmarks
coreutils_dir    := tests/coreutils-8.24
coreutils_outdir := $(OUTDIR)/coreutils-8.24
coreutils_files  := $(wildcard $(coreutils_dir)/*.bc)
coreutils_tests  := $(coreutils_files:$(coreutils_dir)/%.bc=%)

$(coreutils_outdir): | $(OUTDIR)
	$(MKDIR) $@

# Phony testing targets that apply to all benchmarks
.PHONY: tests.setup tests.run tests.clean


#----------------------------
# Benchmark Template
#----------------------------

define coreutils_template

$1.file   := $(coreutils_dir)/$1.bc
$1.outdir := $(coreutils_outdir)/$1


# Create subdirectories

$$($1.outdir): | $(coreutils_outdir)
	$(MKDIR) $$@


# Run target

test-$1: tests.setup
	@echo Analyzing $1 ...
	@mkdir -p ./$(BUILDDIR)/$(coreutils_dir)/$1
	$(CCLYZER) -o $$($1.outdir) $(CCLYZER_OPTS) -i $$($1.file)


# Cleaning target

.PHONY: test-$1.clean
test-$1-clean:
	$(RM) -r $$($1.outdir)/


# Phony targets dependencies

tests.setup  : $(targets)
tests.run    : test-$1
tests.clean  : test-$1-clean

endef


# !! Generate rules per benchmark !!
$(foreach benchmark,$(coreutils_tests),$(eval $(call coreutils_template,$(benchmark))))
