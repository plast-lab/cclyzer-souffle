#!/usr/bin/env python3
"""Warn when cclyzer's input does not look like a whole program.

  check-whole-program.py facts <facts dir>      before the analysis
  check-whole-program.py results <facts dir> <results dir>   after it

cclyzer only analyses code that is in its input. A single translation unit,
or a program linked without its own static libraries, leaves calls into the
missing code undefined: the call graph stops there and function-pointer
targets set up in the missing files are lost. These checks only warn; they
never stop the analysis.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_LISTED = 8


def warn(msg):
    print(f"cclyzer: warning: {msg}", file=sys.stderr)


def column(path, col=0):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\n").split("\t")[col] for line in f]
    except FileNotFoundError:
        return []


def known_externals():
    names = set()
    extra = os.environ.get("CCLYZER_KNOWN_EXTERNALS", "")
    for path in [os.path.join(HERE, "known-externals.txt")] + [p for p in extra.split(":") if p]:
        try:
            with open(path) as f:
                names.update(l.strip() for l in f if l.strip() and not l.startswith("#"))
        except FileNotFoundError:
            warn(f"known-externals list {path} not found")
    return names


def check_facts(facts):
    names = dict(zip(column(f"{facts}/function_has_name.csv", 0), column(f"{facts}/function_has_name.csv", 1)))
    defined = {names.get(f, f) for f in column(f"{facts}/function.csv")}
    declared = {names.get(f, f) for f in column(f"{facts}/function_decl.csv")} - defined
    if "@main" not in defined:
        warn("no main function: the input looks like a library or plugin; "
             "only code reachable from its entry points is analysed")
    known = known_externals()
    unknown = sorted(n for n in declared
                     if not n.startswith("@llvm.") and n.lstrip("@") not in known)
    # Programs often link a few third-party libraries on purpose (libselinux,
    # zlib, ...), so only warn when the unknown names are a real share.
    if len(unknown) >= 3 and len(unknown) >= 0.1 * len(declared):
        listed = ", ".join(n.lstrip("@") for n in unknown[:MAX_LISTED])
        more = f" and {len(unknown) - MAX_LISTED} more" if len(unknown) > MAX_LISTED else ""
        warn(f"{len(unknown)} of {len(declared)} external functions are not standard "
             f"C/C++/POSIX library functions ({listed}{more}). If they are defined in "
             f"other files of this program, link all translation units into one bitcode "
             f"file first (llvm-link, or -flto with lld --save-temps); otherwise calls to "
             f"them are not analysed. Add names of libraries you link on purpose to a file "
             f"listed in CCLYZER_KNOWN_EXTERNALS to silence this.")


def check_results(facts, results):
    reachable = set(column(f"{results}/reachable_instruction.csv"))
    indirect = [i for i in column(f"{results}/indirect_call_instruction.csv") if i in reachable]
    resolved = set(column(f"{results}/stripctx_callgraph_edge.csv", 1))
    unresolved = [i for i in indirect if i not in resolved]
    if len(unresolved) >= 5 and len(unresolved) >= 0.2 * len(indirect):
        warn(f"{len(unresolved)} of {len(indirect)} reachable indirect calls have no target. "
             f"This happens when function pointers are set up in code that is not in the "
             f"input (check that it is the whole program), and also where cclyzer cannot yet "
             f"follow a function pointer, e.g. stored in a union or loaded from a global "
             f"array of structs.")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "facts":
        check_facts(sys.argv[2])
    elif len(sys.argv) == 4 and sys.argv[1] == "results":
        check_results(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
