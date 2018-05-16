#include <string>
#include <llvm/IR/Type.h>
#include "predicate_groups.hpp"
#include "FactGenerator.hpp"

using cclyzer::FactGenerator;
namespace pred = cclyzer::predicates;


void
FactGenerator::writeLocalVariables()
{
    typedef type_cache_t::iterator operand_iterator;
    const llvm::Function *containingFunction = functionContext();
    const std::string funcname = "@" + containingFunction->getName().str();

    // Record every variable encountered so far
    for (operand_iterator
             it = variableTypes.begin(), end = variableTypes.end();
         it != end; ++it)
    {
        refmode_t varId = it->first;
        const llvm::Type *type = it->second;

        // Record variable entity with its type and containing function
        writeFact(pred::variable::id, varId);
        writeFact(pred::variable::type, varId, recordType(type));
        writeFact(pred::variable::in_function, varId, funcname);
    }

    variableTypes.clear();
}
