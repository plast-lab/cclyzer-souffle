#include "FactGenerator.hpp"
#include "predicate_groups.hpp"
#include "TypeVisitor.hpp"

using cclyzer::TypeVisitor;
namespace pred = cclyzer::predicates;

// Add basic LLVM types to current namespace
using llvm::Type;
using llvm::ArrayType;
using llvm::FunctionType;
using llvm::PointerType;
using llvm::StructType;
using llvm::VectorType;
using llvm::cast;


//-------------------------------------------------------------------
// Methods for recording different kinds of LLVM types.
//-------------------------------------------------------------------

void
TypeVisitor::visitType(const llvm::Type *type)
{
    // Record type sizes while skipping unsized types (e.g.,
    // labels, functions)

    if (type->isSized()) {
        uint64_t allocSize = layout.getTypeAllocSize(const_cast<Type*>(type));
        uint64_t storeSize = layout.getTypeStoreSize(const_cast<Type*>(type));

        // Store size of type in bytes
        refmode_t typeId = gen.refmode<llvm::Type>(*type);

        gen.writeFact(pred::type::alloc_size, typeId, allocSize);
        gen.writeFact(pred::type::store_size, typeId, storeSize);
    }

    refmode_t tref = gen.refmode<llvm::Type>(*type);

    // Record each different kind of type
    switch (type->getTypeID()) { // Fallthrough is intended
      case Type::VoidTyID:
      case Type::LabelTyID:
      case Type::MetadataTyID:
          gen.writeFact(pred::primitive_type::id, tref);
          break;
      case Type::HalfTyID: // Fallthrough to all 6 floating point types
      case Type::FloatTyID:
      case Type::DoubleTyID:
      case Type::X86_FP80TyID:
      case Type::FP128TyID:
      case Type::PPC_FP128TyID:
          assert(type->isFloatingPointTy());
          gen.writeFact(pred::fp_type::id, tref);
          break;
      case llvm::Type::IntegerTyID:
          gen.writeFact(pred::integer_type::id, tref);
          break;
      case llvm::Type::FunctionTyID:
          visitFunctionType(cast<FunctionType>(type));
          break;
      case llvm::Type::StructTyID:
          visitStructType(cast<StructType>(type));
          break;
      case llvm::Type::ArrayTyID:
          visitArrayType(cast<ArrayType>(type));
          break;
      case llvm::Type::PointerTyID:
          visitPointerType(cast<PointerType>(type));
          break;
      //VectorTyID seems to be replaced by the following 2, fallthrough intended
      case llvm::Type::ScalableVectorTyID:
      case llvm::Type::FixedVectorTyID:
          visitVectorType(cast<VectorType>(type));
          break;
      case llvm::Type::X86_MMXTyID: // TODO: handle this type
          break;
    }
}


void
TypeVisitor::visitPointerType(const PointerType *ptrType)
{
    //pointers no longer have element types as of LLVM-17,
    //only thing to record is pointer type entities and their address space

    refmode_t typeId = gen.refmode<llvm::Type>(*ptrType);

    // Record pointer type entity
    gen.writeFact(pred::ptr_type::id, typeId);


    // Record pointer address space
    if (unsigned addressSpace = ptrType->getPointerAddressSpace())
        gen.writeFact(pred::ptr_type::addr_space, typeId, addressSpace);
}


void
TypeVisitor::visitArrayType(const ArrayType *arrayType)
{
    const llvm::Type *elemType = arrayType->getArrayElementType();
    size_t nElements = arrayType->getArrayNumElements();

    refmode_t typeId = gen.refmode<llvm::Type>(*arrayType);
    refmode_t elemTypeId = gen.refmode<llvm::Type>(*elemType);

    gen.writeFact(pred::array_type::id, typeId);
    gen.writeFact(pred::array_type::component_type, typeId, elemTypeId);
    gen.writeFact(pred::array_type::size, typeId, nElements);
}


void
TypeVisitor::visitStructType(const StructType *structType)
{
    using llvm::StructLayout;

    refmode_t tref = gen.refmode<llvm::Type>(*structType);
    size_t nFields = structType->getStructNumElements();

    // Record struct type entity
    gen.writeFact(pred::struct_type::id, tref);

    if (structType->isOpaque()) {
        // Opaque structs carry no info about their internal structure
        gen.writeFact(pred::struct_type::opaque, tref);
    } else {
        // Get struct layout
        const StructLayout *structLayout =
            layout.getStructLayout(const_cast<StructType*>(structType));

        // Record struct field types
        for (size_t i = 0; i < nFields; i++)
        {
            refmode_t fieldType = gen.refmode<llvm::Type>(
                *(structType->getStructElementType(i)));

            refmode_t fieldType2 = gen.refmode<llvm::Type>(
                *(structType->getTypeAtIndex(i)));

            

            uint64_t fieldOffset = structLayout->getElementOffset(i);
            uint64_t fieldBitOffset = structLayout->getElementOffsetInBits(i);

            gen.writeFact(pred::struct_type::field_type, tref, i, fieldType2);
            gen.writeFact(pred::struct_type::field_offset, tref, i, fieldOffset);
            gen.writeFact(pred::struct_type::field_bit_offset, tref, i, fieldBitOffset);
        }

        // Record number of fields
        gen.writeFact(pred::struct_type::nfields, tref, nFields);
    }
}


void
TypeVisitor::visitFunctionType(const FunctionType *functionType)
{
    size_t nParameters = functionType->getFunctionNumParams();
    const llvm::Type *returnType = functionType->getReturnType();

    refmode_t funcId = gen.refmode<llvm::Type>(*functionType);
    refmode_t returnTypeId = gen.refmode<llvm::Type>(*returnType);

    // Record function type entity
    gen.writeFact(pred::func_type::id, funcId);

    // TODO: which predicate/entity do we need to update for varagrs?
    if (functionType->isVarArg())
        gen.writeFact(pred::func_type::varargs, funcId);

    // Record return type
    gen.writeFact(pred::func_type::return_type, funcId, returnTypeId);

    // Record function formal parameters
    for (size_t i = 0; i < nParameters; i++)
    {
        const llvm::Type *paramType = functionType->getFunctionParamType(i);
        refmode_t paramTypeId = gen.refmode<llvm::Type>(*paramType);

        gen.writeFact(pred::func_type::param_type, funcId, i, paramTypeId);
    }

    // Record number of formal parameters
    gen.writeFact(pred::func_type::nparams, funcId, nParameters);
}


void
TypeVisitor::visitVectorType(const VectorType *vectorType)
{
    refmode_t tref = gen.refmode<llvm::Type>(*vectorType);
    size_t nElements = vectorType->getArrayNumElements();//getVectorNumElements();

    Type *componentType = vectorType->getArrayElementType();//getVectorElementType();

    // Record vector type entity
    gen.writeFact(pred::vector_type::id, tref);

    // Record vector component type
    refmode_t compref = gen.refmode<llvm::Type>(*componentType);
    gen.writeFact(pred::vector_type::component_type, tref, compref);

    // Record vector type size
    gen.writeFact(pred::vector_type::size, tref, nElements);
}
