#if LLVM_VERSION_MAJOR >= 7
#include <llvm/IR/Constants.h>
#endif
#include "DebugInfoProcessorImpl.hpp"
#include "debuginfo_predicate_groups.hpp"


using cclyzer::DebugInfoProcessor;
using cclyzer::refmode_t;
namespace pred = cclyzer::predicates;

//----------------------------------------------------------------------------
// Process Debug Info Subranges
//----------------------------------------------------------------------------

void
DebugInfoProcessor::Impl::write_di_subrange::write(
    const llvm::DISubrange& disubrange, const refmode_t& nodeId, DIProc& proc)
{
    proc.writeFact(pred::di_subrange::id, nodeId);

    int64_t count = 0;
#if LLVM_VERSION_MAJOR < 7
    count = disubrange.getCount();
#else
    // getCount does not return a constant for VLAs,
    // so set it to -1 (as it was before LLVM 7).
    auto *CI = disubrange.getCount().dyn_cast<llvm::ConstantInt *>();
    count = CI ? CI->getSExtValue() : -1;
#endif
    // Since LLVM 11 the lower bound is absent when it's the language default
    // (0 for C/C++/Rust), so default it to 0.
    auto *LB = disubrange.getLowerBound().dyn_cast<llvm::ConstantInt *>();
    const int64_t lowerBound = LB ? LB->getSExtValue() : 0;

    proc.writeFact(pred::di_subrange::count, nodeId, count);

    if (lowerBound)
        proc.writeFact(pred::di_subrange::lower_bound, nodeId, lowerBound);

}
