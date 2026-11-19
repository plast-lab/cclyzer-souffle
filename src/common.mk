# For debugging
QUIET       := @


# Unix tools
INSTALL     := install
MKDIR       := mkdir -p
SED         := sed
RM          := rm -f
MV          := mv
M4          := m4
CXX         := g++
PROTOC      := /usr/bin/protoc

#--------------------
# Directory Tree
#--------------------

BINDIR    = $(LEVEL)/bin
LIBDIR    = $(LEVEL)/lib
BUILDDIR  = $(LEVEL)/build
SCRIPTDIR = $(LEVEL)/scripts
OUTDIR    = $(BUILDDIR)/$(notdir $(CURDIR))


# Create build directory

$(OUTDIR): | $(BUILDDIR)
	$(MKDIR) $@

# Create build root-directory

$(BUILDDIR):
	$(MKDIR) $@

# Create other directories

$(LIBDIR):
	$(MKDIR) $@

$(BINDIR):
	$(MKDIR) $@

#--------------------
# LLVM
#--------------------

# Oldest supported LLVM major version. Keep version-specific API differences
# in tools/fact-generator/include/llvm_compat.hpp, not in #ifs across the code.
LLVM_MIN_MAJOR := 20

# Unless LLVM_CONFIG is given, use the newest versioned llvm-config on PATH
# (Debian/Ubuntu and apt.llvm.org naming), else plain llvm-config (Nix, Homebrew).
ifndef LLVM_CONFIG
LLVM_CONFIG := $(shell for d in $$(echo "$$PATH" | tr ':' ' '); do ls "$$d"/llvm-config-[0-9]* 2>/dev/null; done \
                 | awk -F- '{ print $$NF, $$0 }' | sort -n | tail -n 1 | cut -d' ' -f2)
ifeq ($(LLVM_CONFIG),)
LLVM_CONFIG := llvm-config
endif
endif

LLVM_VERSION_MAJOR := $(shell $(LLVM_CONFIG) --version 2>/dev/null | cut -d. -f1)

# Sanity checks, skipped when only cleaning
ifneq ($(filter-out clean %.clean,$(or $(MAKECMDGOALS),all)),)
ifeq ($(LLVM_VERSION_MAJOR),)
$(error Cannot run '$(LLVM_CONFIG)'. Install LLVM $(LLVM_MIN_MAJOR) or newer, or set LLVM_CONFIG=/path/to/llvm-config)
endif
ifneq ($(shell [ $(LLVM_VERSION_MAJOR) -ge $(LLVM_MIN_MAJOR) ] && echo ok),ok)
$(error '$(LLVM_CONFIG)' is LLVM $(LLVM_VERSION_MAJOR), but cclyzer needs LLVM $(LLVM_MIN_MAJOR) or newer. Set LLVM_CONFIG, e.g. LLVM_CONFIG=llvm-config-22)
endif
endif

