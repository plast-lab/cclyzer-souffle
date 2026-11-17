#!/usr/bin/env python3
"""Summary statistics of a cclyzer run, like Doop's end-of-run statistics.

  stats.py <results dir>            print the summary
  stats.py <results dir> --json     print it as one JSON object

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


def compute(results):
    s = {}
    for key, _, rel, how in STATS:
        p = os.path.join(results, rel + ".csv")
        s[key] = rows(p) if how == "rows" else value(p)
    if s["nonempty_vars"]:
        s["avg_var_points_to"] = round(s["var_points_to"] / s["nonempty_vars"], 2)
    if s["nonempty_ptrs"]:
        s["avg_ptr_points_to"] = round(s["ptr_points_to"] / s["nonempty_ptrs"], 2)
    reachable = set(column(os.path.join(results, "reachable_instruction.csv"), 0))
    indirect = [i for i in column(os.path.join(results, "indirect_call_instruction.csv"), 0) if i in reachable]
    targets = {}
    for site in column(os.path.join(results, "stripctx_callgraph_edge.csv"), 1):
        targets[site] = targets.get(site, 0) + 1
    resolved = [i for i in indirect if i in targets]
    s["indirect_calls"] = len(indirect)
    s["indirect_calls_resolved"] = len(resolved)
    s["indirect_calls_unresolved"] = len(indirect) - len(resolved)
    if resolved:
        s["avg_indirect_targets"] = round(sum(targets[i] for i in resolved) / len(resolved), 2)
    return s


LABELS = {k: l for k, l, _, _ in STATS}
LABELS.update({
    "avg_var_points_to": "average var points-to set (non-empty)",
    "avg_ptr_points_to": "average object points-to set (non-empty)",
    "indirect_calls": "reachable indirect calls",
    "indirect_calls_resolved": "  with a target",
    "indirect_calls_unresolved": "  without a target",
    "avg_indirect_targets": "average targets per resolved indirect call",
})
ORDER = ["reachable_functions", "reachable_instructions", "reachable_contexts",
         "callgraph_edges", "callgraph_edges_ctx", "callgraph_invalid_edges",
         "indirect_calls", "indirect_calls_resolved", "indirect_calls_unresolved", "avg_indirect_targets",
         "heap_allocations", "stack_allocations", "global_allocations", "allocations",
         "reachable_vars", "nonempty_vars", "empty_vars", "var_points_to", "var_points_to_ctx", "avg_var_points_to",
         "nonempty_ptrs", "empty_ptrs", "ptr_points_to", "ptr_points_to_ctx", "avg_ptr_points_to"]


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    s = compute(sys.argv[1])
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
