#include "DebugInfoProcessorImpl.hpp"
#include "debuginfo_predicate_groups.hpp"


using cclyzer::DebugInfoProcessor;
using cclyzer::refmode_t;
namespace pred = cclyzer::predicates;

//----------------------------------------------------------------------------
// Process Debug Info Enumerators
//----------------------------------------------------------------------------

void
DebugInfoProcessor::Impl::write_di_enumerator::write(
    const llvm::DIEnumerator& dienum, const refmode_t& nodeId, DIProc& proc)
{
    proc.writeFact(pred::di_enumerator::id, nodeId);

    const std::string name = dienum.getName().str();
    
    //TODO Might need to check bit-width of APint returned by dienum.getValue to ensure that its <= 64 bits
    const int64_t value = dienum.getValue().getSExtValue();


    proc.writeFact(pred::di_enumerator::name, nodeId, name);
    proc.writeFact(pred::di_enumerator::value, nodeId, value);
}
