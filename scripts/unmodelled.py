#!/usr/bin/env python3
"""Library functions a program calls that have no body and no model.

  unmodelled.py <facts dir> [--results <results dir>] [--all] [--top N]

A function without a body in the bitcode (a libc or other library function)
produces no points-to facts unless the logic models it. This lists every such
function that is called directly, takes or returns a pointer, and is not named
in any rule of src/logic (library-models.dl, allocations.dl, memcpy, ...),
ranked by number of call sites.

--results restricts the count to call sites in reachable functions.
--all also lists functions without pointer parameters or result.
"""
import argparse, collections, csv, glob, os, re, sys

csv.field_size_limit(1 << 30)
HERE = os.path.dirname(os.path.abspath(__file__))
LOGIC = os.path.join(HERE, "..", "src", "logic")


def rows(path):
    try:
        with open(path) as f:
            yield from csv.reader(f, delimiter="\t")
    except FileNotFoundError:
        return


def modelled_names():
    """Every "@name" string literal in the Datalog sources."""
    names = set()
    for dl in glob.glob(os.path.join(LOGIC, "**", "*.dl"), recursive=True):
        with open(dl) as f:
            names.update(re.findall(r'"(@[A-Za-z_][A-Za-z0-9_.$]*)"', f.read()))
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("facts")
    ap.add_argument("--results")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--top", type=int, default=50)
    a = ap.parse_args()
    F = a.facts
    if not os.path.exists(f"{F}/function.csv"):
        sys.exit(f"{F}/function.csv not found: not a facts directory")

    with_body = {r[0] for r in rows(f"{F}/function.csv")}
    name = {r[0]: r[1] for r in rows(f"{F}/function_has_name.csv")}
    ftype = {r[0]: r[1] for r in rows(f"{F}/function_has_type.csv")}
    ret = {r[0]: r[1] for r in rows(f"{F}/function_type_return.csv")}
    params = collections.defaultdict(list)
    for r in rows(f"{F}/function_type_param.csv"):
        params[r[0]].append(r[2])

    inst_fn = None
    if a.results:
        if not os.path.exists(f"{a.results}/reachable_function.csv"):
            sys.exit(f"{a.results}/reachable_function.csv not found"
                     " (cclyzer-benchmarks deletes results unless KEEP_RESULTS=1)")
        reach = {r[0] for r in rows(f"{a.results}/reachable_function.csv")}
        inst_fn = {r[0]: r[1] for r in rows(f"{F}/instruction_in_function.csv")}

    by_name = {n: fn for fn, n in name.items() if fn not in with_body}
    callee = {}
    for r in rows(f"{F}/call_instruction_fn_operand.csv"):
        m = re.search(r":(@[^:]+)$", r[1])
        if m and m.group(1) in by_name:
            callee[r[0]] = m.group(1)

    known = modelled_names()
    sites = collections.Counter()
    for call, n in callee.items():
        if n.startswith("@llvm.") or n in known:
            continue
        if inst_fn is not None and inst_fn.get(call) not in reach:
            continue
        sites[n] += 1

    def uses_ptr(n):
        t = ftype.get(by_name[n], "")
        return ret.get(t) == "ptr" or "ptr" in params.get(t, []) or "ptr" in t

    def returns_ptr(n):
        return ret.get(ftype.get(by_name[n], "")) == "ptr"

    where = " (reachable call sites)" if a.results else ""
    groups = [
        ("Return a pointer: almost certainly need a model", lambda n: returns_ptr(n)),
        ("Take pointers: need a model only if they store a pointer into an argument"
         " (out-parameters, like getline) or call a function argument (callbacks);"
         " most (free, strlen, fprintf) need none", lambda n: not returns_ptr(n) and uses_ptr(n)),
    ]
    if a.all:
        groups.append(("No pointers", lambda n: not uses_ptr(n)))
    for title, keep in groups:
        shown = [(n, c) for n, c in sites.most_common() if keep(n)]
        print(f"== {title}\n   {len(shown)} functions{where}, top {min(a.top, len(shown))}:")
        for n, c in shown[: a.top]:
            print(f"{c:>6}  {n}  {ftype.get(by_name[n], '?')}")
        print()


if __name__ == "__main__":
    sys.exit(main())
