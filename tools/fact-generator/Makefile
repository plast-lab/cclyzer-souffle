# Directory depth
LEVEL := ../..

# Placeholder
all:

# Import common Makefile routines
include $(LEVEL)/src/common.mk

# Set warnings and other compilation options
CXXFLAGS += -fvisibility-inlines-hidden -Wall -W -Wno-unused-parameter    \
            -Wwrite-strings -Wcast-qual -Wmissing-field-initializers      \
            -pedantic -Wno-long-long -ffunction-sections -fdata-sections  \
            -O1  
# Linux supports -O3 but macOS for some reason does not


#-----------------------------------
# Configure paths
#-----------------------------------

srcdir       := src
outdir       := $(OUTDIR)
sources      := $(wildcard $(srcdir)/*.cpp)
objects      := $(patsubst $(srcdir)/%.cpp,$(outdir)/%.o,$(sources))
dependencies := $(patsubst $(srcdir)/%.cpp,$(outdir)/%.d,$(sources))
program      := $(BINDIR)/fact-generator
include_dirs := include


#-----------------------------------
# Search in directories
#-----------------------------------

vpath %.cpp $(srcdir)
vpath %.h $(include_dirs)


#-----------------------------------
# LLVM specific flags
#-----------------------------------

CPPFLAGS += $(shell $(LLVM_CONFIG) --cppflags)
LDFLAGS  += $(shell $(LLVM_CONFIG) --ldflags)
LDLIBS   += $(shell $(LLVM_CONFIG) --libs core irreader transformutils)
LDLIBS   += $(filter-out -lz,$(shell $(LLVM_CONFIG) --system-libs))
LDLIBS   += -lboost_filesystem -lboost_program_options


#-----------------------------------
# Basic Rules
#-----------------------------------

CPPFLAGS += $(addprefix -I ,$(include_dirs))
CXXFLAGS += -fPIC -g -std=c++17

$(outdir)/%.o: %.cpp | $(outdir)
	$(COMPILE.cpp) -o $@ $<

$(program): $(objects) | $(BINDIR)
	$(LINK.cpp) -o $@ $^ $(LDLIBS)


#-----------------------------------
# Phony targets
#-----------------------------------

.PHONY: all
all: $(program)

.PHONY: clean
clean:
	$(RM) -r $(outdir)

.PHONY: check-syntax
check-syntax: CXXFLAGS += -Wall -Wextra -pedantic
check-syntax: COMPILE.cpp := $(CXX) $(CXXFLAGS) $(CPPFLAGS) $(TARGET_ARCH) # -fsyntax-only
check-syntax:
	$(COMPILE.cpp) -o /dev/null -S $(CHK_SOURCES)


#-----------------------------------
# Automatic Dependency Generation
#-----------------------------------

ifneq "$(MAKECMDGOALS)" "clean"
  ifneq "$(MAKECMDGOALS)" "check-syntax"
    -include $(dependencies)
  endif
endif

$(outdir)/%.d: %.cpp | $(outdir)
	$(QUIET) $(CXX) $(CXXFLAGS) $(CPPFLAGS) $(TARGET_ARCH) -M $< |  \
	$(SED) 's,\($*.o\) *:,$(@D)/\1 $@: ,' > $@.tmp
	$(QUIET) $(MV) $@.tmp $@
	$(info Created dependency file: $@)
