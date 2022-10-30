#include <llvm/Config/llvm-config.h>
#include <llvm/IR/Attributes.h>
#include <llvm/IR/Constants.h>
#include <llvm/IR/Function.h>
#include "debuginfo_predicate_groups.hpp"
#include "predicate_groups.hpp"
#include "FactGenerator.hpp"

using cclyzer::FactGenerator;
namespace pred = cclyzer::predicates;


//------------------------------------------------------------------------------
// Record Function (but not the function body)
//------------------------------------------------------------------------------

void
FactGenerator::writeFunction(
    const llvm::Function& func,
    const refmode_t& funcref)
{
    // Serialize function properties
    refmode_t visibility = refmode(func.getVisibility());
    refmode_t linkage = refmode(func.getLinkage());
    refmode_t typeSignature = recordType(func.getFunctionType());

    // Record function subprogram
    if (const llvm::DISubprogram *subprogram = func.getSubprogram()) {
        refmode_t subprogramId = refmode<llvm::DINode>(*subprogram);
        writeFact(pred::di_subprogram::function, subprogramId, funcref);
    }

    // Record function type signature
    writeFact(pred::function::type, funcref, typeSignature);

    // Record function signature (name plus type signature) after
    // unmangling
    writeFact(pred::function::signature, funcref, demangle(func.getName().data()));

    // Record function linkage, visibility, alignment, and GC
    if (!linkage.empty())
        writeFact(pred::function::linkage, funcref, linkage);

    if (!visibility.empty())
        writeFact(pred::function::visibility, funcref, visibility);

    if (func.getAlignment())
        writeFact(pred::function::alignment, funcref, func.getAlignment());

    if (func.hasGC())
        writeFact(pred::function::gc, funcref, func.getGC());

    if (func.hasPersonalityFn()) {
        llvm::Constant *pers_fn = func.getPersonalityFn();
        refmode_t pers_fn_ref = writeConstant(*pers_fn);

        writeFact(pred::function::pers_fn, funcref, pers_fn_ref);
    }

    // Record calling convection if it not defaults to C
    if (func.getCallingConv() != llvm::CallingConv::C) {
        refmode_t cconv = refmode(func.getCallingConv());
        writeFact(pred::function::calling_conv, funcref, cconv);
    }

    // Record function name
    const std::string funcname = "@" + func.getName().str();
    writeFact(pred::function::name, funcref, funcname);

    // Address not significant
    
#if LLVM_VERSION_MAJOR > 3 || (LLVM_VERSION_MAJOR == 3 && LLVM_VERSION_MINOR >= 9)
    // NB: for macOS LLVM-3.9.0svn this does not work, i.e. the test should be
    //#if LLVM_VERSION_MAJOR > 3 or equivalent to force else case
    if (func.hasGlobalUnnamedAddr()) {
        writeFact(pred::function::unnamed_addr, funcref);
    }

    // TODO Record appropriately
    if (func.hasAtLeastLocalUnnamedAddr()) {
    }
#else
    if (func.hasUnnamedAddr()) {
        writeFact(pred::function::unnamed_addr, funcref);
    }
#endif

    // Record function attributes TODO
    const Attributes &Attrs = func.getAttributes();


     if(Attrs.hasAttributesAtIndex(Attributes::ReturnIndex)){ 
        writeFact(pred::function::ret_attr, funcref,Attrs.getAsString(Attributes::ReturnIndex));
    }

    writeFnAttributes<pred::function>(funcref, Attrs);

    if (func.isDeclaration()) {
        // Record as a function declaration entity
        writeFact(pred::function::id_decl, funcref);

        // Nothing more to do for function declarations
        return;
    }

    // Record function definition entity
    writeFact(pred::function::id_defn, funcref);

    // Record section
    if (func.hasSection()) {
#if LLVM_VERSION_MAJOR > 3 || (LLVM_VERSION_MAJOR == 3 && LLVM_VERSION_MINOR >= 9)
        llvm::StringRef secStr = func.getSection();
        writeFact(pred::function::section, funcref, secStr.str());
#else
        writeFact(pred::function::section, funcref, func.getSection());
#endif
    }

    // Record function parameters
    int index = 0;

    for (llvm::Function::const_arg_iterator
             arg = func.arg_begin(), arg_end = func.arg_end();
         arg != arg_end; arg++)
    {
        refmode_t varId = refmode<llvm::Value>(*arg);

        writeFact(pred::function::param, funcref, index++, varId);
        recordVariable(varId, arg->getType());
    }
}


//------------------------------------------------------------------------------
// Record Function Attributes
//------------------------------------------------------------------------------

template<typename PredGroup>
void FactGenerator::writeFnAttributes(
    const refmode_t &refmode,
    const Attributes allAttrs)
{
    //TODO VALIDATE THESE LOOPS ITERATE OVER EVERYTHING THEY NEED TO

    //write out function attributes 
    for(auto attrib : allAttrs.getFnAttrs()){
        std::string attr = attrib.getAsString();
        attr.erase (std::remove(attr.begin(), attr.end(), '"'), attr.end());
        writeFact(PredGroup::fn_attr, refmode, attr);
        if(attrib.isStringAttribute()){
            writeFact(pred::attribute::target_dependent , attr);
        }
    }

    //write out ret attrs
    for(auto attrib : allAttrs.getRetAttrs()){
        std::string attr = attrib.getAsString();
        attr.erase (std::remove(attr.begin(), attr.end(), '"'), attr.end());
        writeFact(PredGroup::ret_attr, refmode, attr);
        if(attrib.isStringAttribute()){
            writeFact(pred::attribute::target_dependent , attr);
        }
    }


    //TODO test if this works
    for(unsigned int i=0 ; i < allAttrs.getNumAttrSets();i++){
        //write out param attrs
        for(auto attrib : allAttrs.getParamAttrs(i)){
            std::string attr = attrib.getAsString();
            attr.erase (std::remove(attr.begin(), attr.end(), '"'), attr.end());
            writeFact(PredGroup::param_attr, refmode, i-1, attr);
            if(attrib.isStringAttribute()){
                writeFact(pred::attribute::target_dependent , attr);
            }       
        }
    }
}

// Instantiate template method

template void FactGenerator::writeFnAttributes<pred::function>(
    const refmode_t &refmode,
    const Attributes Attrs);

template void FactGenerator::writeFnAttributes<pred::call>(
    const refmode_t &refmode,
    const Attributes Attrs);

template void FactGenerator::writeFnAttributes<pred::invoke>(
    const refmode_t &refmode,
    const Attributes Attrs);
