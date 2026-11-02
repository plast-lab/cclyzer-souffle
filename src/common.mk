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

PYTHON_VERSION_NODOT := $(shell python3 -c 'import sys; print("%d%d" % sys.version_info[:2])')
LIBBOOST_PYTHON ?= -lboost_python$(PYTHON_VERSION_NODOT)
