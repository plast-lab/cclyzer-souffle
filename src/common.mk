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


#--------------------
# Python and Boost.Python
#--------------------

# The Python bindings must use the Python that Boost.Python was built for.
# Override PYTHON3 when the first python3 on PATH is a different one, e.g.
# PYTHON3=/usr/bin/python3 when a Homebrew python3 shadows the system one.
PYTHON3        ?= python3
PYTHON3_CONFIG ?= $(PYTHON3)-config
PYTHON_VERSION_NODOT := $(shell $(PYTHON3) -c 'import sys; print("%d%d" % sys.version_info[:2])')
LIBBOOST_PYTHON ?= -lboost_python$(PYTHON_VERSION_NODOT)

# Fail at the start rather than at the final link step: link an empty
# program against Boost.Python with the same compiler and LDFLAGS as the
# real link. (Not -print-file-name: it ignores -L, so it misses libraries
# outside the compiler's default search path, e.g. Boost on Nix.)
ifneq ($(filter-out clean %.clean,$(or $(MAKECMDGOALS),all)),)
BOOST_PYTHON_LIB := libboost_python$(PYTHON_VERSION_NODOT)
ifneq ($(shell printf 'int main(){}\n' | $(CXX) -x c++ - $(LDFLAGS) $(LIBBOOST_PYTHON) -o /dev/null 2>/dev/null && echo ok),ok)
ifeq ($(origin LIBBOOST_PYTHON),file)
$(error No $(BOOST_PYTHON_LIB) found for '$(shell command -v $(PYTHON3))'. Install Boost.Python for that Python, or set PYTHON3 to the Python Boost.Python was built for, e.g. PYTHON3=/usr/bin/python3)
endif
endif
endif
