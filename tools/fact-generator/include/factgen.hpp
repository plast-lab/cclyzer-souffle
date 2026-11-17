#ifndef FACT_GENERATOR_HPP__
#define FACT_GENERATOR_HPP__

#include <string>
#include <boost/filesystem.hpp>

namespace cclyzer
{
    // Main fact-generation routines

    template<typename FileIt> void
    factgen(FileIt firstFile, FileIt endFile, boost::filesystem::path outputDir)
    {
        return factgen(firstFile, endFile, outputDir, "\t");
    }

    // promoteLocals: promote local variables whose address is never taken
    // from stack slots to SSA values (LLVM's mem2reg) before generating
    // facts; see promoteLocals() in main.cpp.
    template<typename FileIt> void
    factgen(FileIt firstFile, FileIt endFile, boost::filesystem::path outputDir,
            std::string delim, bool promoteLocals = true);
}

#endif /* FACT_GENERATOR_HPP__ */
