#!/usr/bin/env python3
"""Why do dereferenced pointers have empty points-to sets?

  empty-derefs.py <results dir> <facts dir>

Takes every reachable load or store whose address has an empty points-to set
(context-stripped), follows the empty values back through copies, GEPs,
phis, parameters and call results, and counts the root causes, e.g.

  "call, unresolved/external: @foo"   a library function without a model
                                      (see unmodelled.py, library-models.dl)
  "load from non-empty address: contents never written"
  "gep on non-empty base: no field object"
  "param of function with no callers"

with one example variable each. A sound analysis has an empty set only where
the pointer is null or never points anywhere at runtime, so every other root
is a missing fact. Needs the full results (cclyzer-benchmarks: KEEP_RESULTS=1).
"""
import csv, sys, collections, re, glob, os
csv.field_size_limit(1 << 30)
if len(sys.argv) != 3:
    sys.exit(__doc__)
A, F = sys.argv[1], sys.argv[2]
for d, f in ((A, "stripctx_var_points_to.csv"), (F, "instruction_in_function.csv")):
    if not os.path.exists(os.path.join(d, f)):
        sys.exit(f"{d}/{f} not found")
def R(f):
  try: return csv.reader(open(f),delimiter='\t')
  except FileNotFoundError: return []
pts=collections.defaultdict(int)
for r in R(f"{A}/stripctx_var_points_to.csv"): pts[r[1]]+=1
reach={r[0] for r in R(f"{A}/reachable_function.csv")}
inf={r[0]:r[1] for r in R(f"{F}/instruction_in_function.csv")}
def2={r[1]:r[0] for r in R(f"{F}/instruction_assigns_to.csv")}
kind={}
for f in glob.glob(f"{F}/*_instruction.csv"):
  k=os.path.basename(f)[:-len("_instruction.csv")]
  if k in ("next","reachable","schema_invalid"): continue
  for r in R(f): kind.setdefault(r[0],k)
ins=collections.defaultdict(list)
for f in ["load_instruction_address","getelementptr_instruction_base","select_instruction_first_operand","select_instruction_second_operand","bitcast_instruction_from_operand","inttoptr_instruction_from_operand","extractvalue_instruction_base","freeze_instruction_operand"]:
  for r in R(f"{F}/{f}.csv"): ins[r[0]].append(r[-1])
for r in R(f"{F}/phi_instruction_pair_value.csv"): ins[r[0]].append(r[-1])
fnop={r[0]:r[1] for r in R(f"{F}/call_instruction_fn_operand.csv")}
body={r[0] for r in R(f"{F}/function.csv")}
params={}
for r in R(f"{F}/function_param.csv"): params[r[2]]=(r[0],int(r[1]))
callers=collections.defaultdict(list)   # callee -> call instrs
for r in R(f"{A}/stripctx_callgraph_edge.csv"): callers[r[0]].append(r[1])
args={}
for r in R(f"{F}/call_instruction_arg.csv"): args[(r[0],int(r[1]))]=r[2]
rets=collections.defaultdict(list)
for r in R(f"{F}/ret_instruction_value.csv"): rets[inf.get(r[0])].append(r[1])
cg=collections.defaultdict(list)
for r in R(f"{A}/stripctx_callgraph_edge.csv"): cg[r[1]].append(r[0])
isvar=lambda v: ":%" in v
def inputs(v):
  if v in params:
    f,i=params[v]; return [args.get((c,i)) for c in callers.get(f,[]) if args.get((c,i))]
  i=def2.get(v)
  if i is None: return []
  if kind.get(i)=="call":
    out=[]
    for c in cg.get(i,[]): out+=rets.get(c,[])
    return out
  return ins.get(i,[])
def label(v):
  if v in params:
    f,i=params[v]
    return "param of function with no callers" if not callers.get(f) else "param (all actuals empty)"
  i=def2.get(v); k=kind.get(i,"?")
  if k=="call":
    op=fnop.get(i,"")
    if not cg.get(i): return "call, unresolved/external: "+op.rsplit(":",1)[-1]
    return "call (callee returns nothing)"
  if k=="load": return "load (memory empty)"
  return k
memo={}
def root(v,depth=0,seen=None):
  if seen is None: seen=set()
  if v in memo: return memo[v]
  if v in seen or depth>60: return ["cycle"]
  seen.add(v)
  xs=[x for x in inputs(v) if isvar(x)]
  empt=[x for x in xs if pts.get(x,0)==0]
  nonvar=[x for x in inputs(v) if not isvar(x)]
  k=kind.get(def2.get(v))
  # a load whose address is non-empty is itself a root (memory never written)
  if k=="load" and xs and not empt: res=["load from non-empty address: contents never written"]
  elif k=="getelementptr" and xs and not empt: res=["gep on non-empty base: no field object"]
  elif not xs and not nonvar: res=[label(v)]
  elif not empt: res=[label(v)+(" (constant input)" if nonvar else "")]
  else:
    res=[]
    for x in empt[:3]: res+=root(x,depth+1,seen)
  memo[v]=res; return res
deref=set()
for f in ["load_instruction_address","store_instruction_address"]:
  for r in R(f"{F}/{f}.csv"):
    if inf.get(r[0]) in reach and isvar(r[1]) and pts.get(r[1],0)==0: deref.add(r[1])
c=collections.Counter(); ex={}
for v in deref:
  for x in set(root(v)): c[x]+=1; ex.setdefault(x,v)
print(len(deref),"empty dereferenced pointers; root causes:")
P=re.compile(r"</[^>]*>:")
for k,n in c.most_common(40): print(f"{n:6d}  {k}   e.g. {P.sub('',ex[k])}")
