#!/usr/bin/env python3
"""Summary statistics of a cclyzer run, like Doop's end-of-run statistics.

  stats.py <results dir> [--facts <facts dir>] [--json]

--facts adds call sites, library calls, dereference precision and casts;
--json prints one JSON object instead of the table.

Counts come from the output relations, including the ones computed by
points-to/points-to-statistics.dl. "Without contexts" numbers use the
context-stripped projections, so they are comparable across analyses.
"""
import json, os, sys

# (key, label, relation, how): how = "rows" (row count) or "value" (single number)
STATS = [
    ("reachable_functions",      "reachable functions",                    "reachable_function",      "rows"),
    ("reachable_instructions",   "reachable instructions",                 "reachable_instruction",   "rows"),
    ("reachable_contexts",       "reachable function contexts",            "reachable_context4",      "rows"),
    ("callgraph_edges",          "call-graph edges (without contexts)",    "stripctx_callgraph_edge", "rows"),
    ("callgraph_edges_ctx",      "call-graph edges (with contexts)",       "callgraph_edge",          "rows"),
    ("callgraph_invalid_edges",  "invalid call-graph edges",               "callgraph_invalid_edge",  "rows"),
    ("allocations",              "abstract objects (incl. subobjects)",   "allocation",              "rows"),
    ("heap_allocations",         "heap allocation sites",                  "heap_allocation",         "rows"),
    ("stack_allocations",        "stack allocation sites",                 "stack_allocation",        "rows"),
    ("global_allocations",       "global allocation sites",                "global_allocation",       "rows"),
    ("reachable_vars",           "variables in reachable functions",       "reachable_vars",          "value"),
    ("nonempty_vars",            "variables with points-to (all functions)",    "nonempty_vars",           "value"),
    ("empty_vars",               "variables without points-to (all functions)", "empty_vars",              "value"),
    ("var_points_to",            "var points-to (without contexts)",       "stripctx_var_points_to",  "rows"),
    ("var_points_to_ctx",        "var points-to (with contexts)",          "var_points_to",           "rows"),
    ("nonempty_ptrs",            "abstract objects with points-to",          "nonempty_ptrs",           "value"),
    ("empty_ptrs",               "abstract objects without points-to",       "empty_ptrs",              "value"),
    ("ptr_points_to",            "object points-to (without contexts)",    "stripctx_ptr_points_to",  "rows"),
    ("ptr_points_to_ctx",        "object points-to (with contexts)",       "ptr_points_to",           "rows"),
]


def rows(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return None


def value(path):
    try:
        with open(path) as f:
            line = f.readline().strip()
        return int(line) if line else 0
    except FileNotFoundError:
        return None


def column(path, col):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return [l.rstrip("\n").split("\t")[col] for l in f]
    except FileNotFoundError:
        return []


def pairs(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for l in f:
                p = l.rstrip("\n").split("\t")
                if len(p) >= 2:
                    yield p[0], p[1]
    except FileNotFoundError:
        return


def ratio(a, b):
    return round(a / b, 2) if b else None


def compute(results, facts=None):
    """Statistics from a results directory; the facts directory adds the
    call-site, library, dereference and cast numbers."""
    R = lambda rel: os.path.join(results, rel + ".csv")
    s = {}
    for key, _, rel, how in STATS:
        s[key] = rows(R(rel)) if how == "rows" else value(R(rel))
    s["avg_var_points_to"] = ratio(s["var_points_to"] or 0, s["nonempty_vars"])
    s["avg_ptr_points_to"] = ratio(s["ptr_points_to"] or 0, s["nonempty_ptrs"])

    reachable = set(column(R("reachable_instruction"), 0))
    indirect = [i for i in column(R("indirect_call_instruction"), 0) if i in reachable]
    targets = {}
    for callee, site in pairs(R("stripctx_callgraph_edge")):
        targets.setdefault(site, set()).add(callee)
    s["indirect_calls"] = len(indirect)
    s["indirect_calls_mono"] = sum(1 for i in indirect if len(targets.get(i, ())) == 1)
    s["indirect_calls_poly"] = sum(1 for i in indirect if len(targets.get(i, ())) >= 2)
    s["indirect_calls_unresolved"] = sum(1 for i in indirect if not targets.get(i))
    resolved = [i for i in indirect if targets.get(i)]
    s["avg_indirect_targets"] = ratio(sum(len(targets[i]) for i in resolved), len(resolved))

    if facts:
        F = lambda rel: os.path.join(facts, rel + ".csv")
        name = dict(pairs(F("function_has_name")))
        defined = set(column(F("function"), 0))
        intrinsic = lambda f: name.get(f, "").startswith("@llvm.")
        rfuncs = [f for f in column(R("reachable_function"), 0) if not intrinsic(f)]
        s["reachable_functions_defined"] = sum(1 for f in rfuncs if f in defined)
        s["reachable_functions_external"] = sum(1 for f in rfuncs if f not in defined)

        calls = [c for c in column(F("call_instruction"), 0) + column(F("invoke_instruction"), 0) if c in reachable]
        real = [c for c in calls if not all(intrinsic(t) for t in targets.get(c, {None}) if t)]
        s["call_sites"] = len(real)
        s["call_sites_direct"] = len(real) - len(indirect)
        ext_sites = [c for c in real if targets.get(c) and all(t not in defined for t in targets[c])]
        s["call_sites_external"] = len(ext_sites)
        s["external_callees"] = len({t for c in ext_sites for t in targets[c]})
        s["dynamic_cast_sites"] = sum(1 for c in real if any(name.get(t) == "@__dynamic_cast" for t in targets.get(c, ())))

        pts = {}
        for _, var in pairs(R("stripctx_var_points_to")):
            pts[var] = pts.get(var, 0) + 1
        variables = set(column(F("variable"), 0))
        derefs = [(i, a) for rel in ("load_instruction_address", "store_instruction_address")
                  for i, a in pairs(F(rel)) if i in reachable and a in variables]
        sizes = [pts.get(a, 0) for _, a in derefs]
        s["deref_sites"] = len(sizes)
        s["deref_sites_empty"] = sum(1 for n in sizes if n == 0)
        s["avg_deref_points_to"] = ratio(sum(sizes), sum(1 for n in sizes if n))

        s["inttoptr_casts"] = sum(1 for i in column(F("inttoptr_instruction"), 0) if i in reachable)
        s["ptrtoint_casts"] = sum(1 for i in column(F("ptrtoint_instruction"), 0) if i in reachable)
    return s


LABELS = {k: l for k, l, _, _ in STATS}
LABELS.update({
    "reachable_functions_defined": "  defined in the program",
    "reachable_functions_external": "  external (library)",
    "call_sites": "reachable call sites",
    "call_sites_direct": "  direct",
    "call_sites_external": "  to external functions",
    "external_callees": "distinct external functions called",
    "indirect_calls": "reachable indirect calls",
    "indirect_calls_mono": "  monomorphic (1 target)",
    "indirect_calls_poly": "  polymorphic (2+ targets)",
    "indirect_calls_unresolved": "  unresolved (no target)",
    "avg_indirect_targets": "average targets per resolved indirect call",
    "dynamic_cast_sites": "reachable dynamic_cast calls (C++)",
    "avg_var_points_to": "average var points-to set (non-empty)",
    "avg_ptr_points_to": "average object points-to set (non-empty)",
    "deref_sites": "reachable loads/stores through a variable",
    "deref_sites_empty": "  with an empty points-to set",
    "avg_deref_points_to": "average points-to set at a dereference",
    "inttoptr_casts": "reachable int-to-pointer casts",
    "ptrtoint_casts": "reachable pointer-to-int casts",
})
ORDER = ["reachable_functions", "reachable_functions_defined", "reachable_functions_external",
         "reachable_instructions", "reachable_contexts",
         "callgraph_edges", "callgraph_edges_ctx", "callgraph_invalid_edges",
         "call_sites", "call_sites_direct", "call_sites_external", "external_callees",
         "indirect_calls", "indirect_calls_mono", "indirect_calls_poly", "indirect_calls_unresolved",
         "avg_indirect_targets", "dynamic_cast_sites",
         "heap_allocations", "stack_allocations", "global_allocations", "allocations",
         "reachable_vars", "nonempty_vars", "empty_vars", "var_points_to", "var_points_to_ctx", "avg_var_points_to",
         "deref_sites", "deref_sites_empty", "avg_deref_points_to",
         "nonempty_ptrs", "empty_ptrs", "ptr_points_to", "ptr_points_to_ctx", "avg_ptr_points_to",
         "inttoptr_casts", "ptrtoint_casts"]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    facts = None
    if "--facts" in sys.argv:
        facts = sys.argv[sys.argv.index("--facts") + 1]
        args = [a for a in args if a != facts]
    s = compute(args[0], facts)
    if "--json" in sys.argv[2:]:
        print(json.dumps(s))
        return
    width = max(len(LABELS[k]) for k in ORDER)
    print("Statistics")
    for k in ORDER:
        if s.get(k) is not None:
            v = s[k]
            print(f"  {LABELS[k]:<{width}}  {v:>12,}" if isinstance(v, int) else f"  {LABELS[k]:<{width}}  {v:>12}")


if __name__ == "__main__":
    main()
