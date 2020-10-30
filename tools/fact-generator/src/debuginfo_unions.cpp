#include <llvm/ADT/SmallVector.h>
#include "DebugInfoProcessorImpl.hpp"
#include "debuginfo_predicate_groups.hpp"

using cclyzer::DebugInfoProcessor;
using cclyzer::refmode_t;
using llvm::cast;
using llvm::dyn_cast;
using llvm::SmallVector;
using std::string;
namespace pred = cclyzer::predicates;
namespace dwarf = llvm::dwarf;



//------------------------------------------------------------------------------
// Helper method to record union attributes
//------------------------------------------------------------------------------

template<typename P, typename W, typename T> void
DebugInfoProcessor::Impl::recordUnionAttribute(
#if LLVM_VERSION_MAJOR >= 9
    const refmode_t& nodeId, const T* attribute)
#else
    const refmode_t& nodeId, const llvm::TypedDINodeRef<T>& attribute)
#endif
{
    typedef P pred;
    typedef di_recorder<T, W> recorder;

    if (attribute) {
        using llvm::MDString;
        const llvm::Metadata& meta = *attribute;

        if (const MDString *mds = dyn_cast<MDString>(&meta)) {
            std::string attribStr = mds->getString();
            writeFact(pred::raw, nodeId, attribStr);
        }
        else {
            refmode_t attribId = recorder::record(cast<T>(*attribute), *this);
            writeFact(pred::node, nodeId, attribId);
        }
    }
}

//------------------------------------------------------------------------------
// Helper method to record bit flags
//------------------------------------------------------------------------------

void
DebugInfoProcessor::Impl::recordFlags(
    const Predicate& pred, const refmode_t& nodeId, unsigned flags)
{
#if LLVM_VERSION_MAJOR < 4  // unsigned -> llvm::DINode::DIFlags
    typedef unsigned Flags;
#else
    typedef llvm::DINode::DIFlags Flags;
#endif
    if (flags) {
        // Split flags inside vector
        typedef SmallVector<Flags,8> FlagVectorT;
        FlagVectorT flagsVector;
        llvm::DINode::splitFlags((Flags)flags, flagsVector);

        for (FlagVectorT::iterator it = flagsVector.begin(),
                 end = flagsVector.end(); it != end; ++it )
        {
#if LLVM_VERSION_MAJOR < 4  // const char * -> StringRef
            const char *flag = llvm::DINode::getFlagString(*it);
            writeFact(pred, nodeId, flag);
#else
            llvm::StringRef flag = llvm::DINode::getFlagString(*it);
            writeFact(pred, nodeId, flag.str());
#endif
        }
    }
}

//------------------------------------------------------------------------------
// Explicit template instantiations
//------------------------------------------------------------------------------

    template void
    DebugInfoProcessor::Impl
    ::recordUnionAttribute<pred::di_subprogram::containing_type,
                        DebugInfoProcessor::Impl::write_di_type >(
#if LLVM_VERSION_MAJOR >= 9
        const refmode_t &, const llvm::DIType *);
#else
        const refmode_t &, const llvm::DITypeRef &);
#endif

    template void
    DebugInfoProcessor::Impl
    ::recordUnionAttribute<pred::di_subprogram::scope,
                        DebugInfoProcessor::Impl::write_di_scope >(
#if LLVM_VERSION_MAJOR >= 9
        const refmode_t &, const llvm::DIScope *);
#else
        const refmode_t &, const llvm::DIScopeRef &);
#endif

    template void
    DebugInfoProcessor::Impl
    ::recordUnionAttribute<pred::di_template_param::type,
                        DebugInfoProcessor::Impl::write_di_type >(
#if LLVM_VERSION_MAJOR >= 9
        const refmode_t &, const llvm::DIType *);
#else
        const refmode_t &, const llvm::DITypeRef &);
#endif


    template void
    DebugInfoProcessor::Impl
    ::recordUnionAttribute<pred::di_variable::type,
                        DebugInfoProcessor::Impl::write_di_type >(
#if LLVM_VERSION_MAJOR >= 9
        const refmode_t &, const llvm::DIType *);
#else
        const refmode_t &, const llvm::DITypeRef &);
#endif

    template void
    DebugInfoProcessor::Impl
    ::recordUnionAttribute<pred::di_composite_type::basetype,
                        DebugInfoProcessor::Impl::write_di_type >(
#if LLVM_VERSION_MAJOR >= 9
        const refmode_t &, const llvm::DIType *);
#else
        const refmode_t &, const llvm::DITypeRef &);
#endif

    template void
    DebugInfoProcessor::Impl
    ::recordUnionAttribute<pred::di_composite_type::vtable,
                        DebugInfoProcessor::Impl::write_di_type >(
#if LLVM_VERSION_MAJOR >= 9
        const refmode_t &, const llvm::DIType *);
#else
        const refmode_t &, const llvm::DITypeRef &);
#endif

    template void
    DebugInfoProcessor::Impl
    ::recordUnionAttribute<pred::di_derived_type::basetype,
                        DebugInfoProcessor::Impl::write_di_type >(
#if LLVM_VERSION_MAJOR >= 9
        const refmode_t &, const llvm::DIType *);
#else
        const refmode_t &, const llvm::DITypeRef &);
#endif

    template void
    DebugInfoProcessor::Impl
    ::recordUnionAttribute<pred::di_type::scope,
                        DebugInfoProcessor::Impl::write_di_scope>(
#if LLVM_VERSION_MAJOR >= 9
        const refmode_t &, const llvm::DIScope *);
#else
        const refmode_t &, const llvm::DIScopeRef &);
#endif
