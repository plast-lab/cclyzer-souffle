#!/usr/bin/env python3
"""Check that the fact generator still produces the same facts for tests/.

  scripts/test-facts.py            compare with tests/facts.sha256
  scripts/test-facts.py --update   rewrite tests/facts.sha256

Facts are generated for every tests/*/*.bc. Each relation's lines are
normalised (input paths made relative, renames between supported LLVM
versions undone), sorted and hashed, and the hashes are compared with the
reference file: one line per relation (over all programs) and one per
program. Run it before and after changing the fact generator or the LLVM
version; a difference names the relations and programs to look at.
"""
import argparse, concurrent.futures as cf, hashlib, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(ROOT, "tests", "facts.sha256")

# Spelling differences between the supported LLVM versions (20+), and
# relations that only hash other facts.
NORMALISE = [
    (re.compile(r"(llvm\.va_(?:start|end|copy))\.p0(?:\.p0)?"), r"\1"),
    (re.compile(r"captures\(none\)"), "nocapture"),
]
SKIP = {"constant_hashes_to.csv"}


def facts_for(bc, workdir):
    out = os.path.join(workdir, os.path.relpath(bc, ROOT).replace("/", "%"))
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([os.path.join(ROOT, "bin", "fact-generator"), "-o", out + "/", bc],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        return bc, None, r.stderr.strip().splitlines()[-1:] or ["exit %d" % r.returncode]
    prefix = os.path.dirname(os.path.realpath(bc)) + "/"
    rels = {}
    for d, _, files in os.walk(out):
        for f in files:
            rel = os.path.relpath(os.path.join(d, f), out)
            if not f.endswith(".csv") or rel in SKIP:
                continue
            with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                lines = []
                for line in fh:
                    line = line.replace(prefix, "")
                    for rx, s in NORMALISE:
                        line = rx.sub(s, line)
                    lines.append(line)
            lines.sort()
            rels[rel] = hashlib.sha256("".join(lines).encode()).hexdigest()
    shutil.rmtree(out)   # keep only a few programs' facts on disk at a time
    return bc, rels, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true")
    ap.add_argument("-j", type=int, default=os.cpu_count() or 4)
    args = ap.parse_args()

    bcs = sorted(os.path.join(d, f) for d, _, fs in os.walk(os.path.join(ROOT, "tests"))
                 for f in fs if f.endswith(".bc"))
    by_rel, by_prog, failed = {}, {}, []
    with tempfile.TemporaryDirectory(prefix="cclyzer-test-facts-") as work, \
         cf.ThreadPoolExecutor(args.j) as pool:
        for bc, rels, err in pool.map(lambda b: facts_for(b, work), bcs):
            name = os.path.relpath(bc, os.path.join(ROOT, "tests"))
            if rels is None:
                failed.append(f"{name}: {err[0]}")
                continue
            by_prog[name] = hashlib.sha256("".join(f"{r} {h}\n" for r, h in sorted(rels.items())).encode()).hexdigest()
            for r, h in rels.items():
                by_rel.setdefault(r, hashlib.sha256())
                by_rel[r].update(f"{name} {h}\n".encode())
    current = {f"relation {r}": h.hexdigest() for r, h in by_rel.items()}
    current.update({f"program {p}": h for p, h in by_prog.items()})

    for f in failed:
        print(f"fact generation FAILED: {f}")
    if args.update:
        with open(REFERENCE, "w") as fh:
            fh.write("# scripts/test-facts.py --update; one hash per relation and per program\n")
            for k in sorted(current):
                fh.write(f"{current[k]}  {k}\n")
        print(f"wrote {len(current)} hashes for {len(by_prog)} programs to {os.path.relpath(REFERENCE, ROOT)}")
        return 1 if failed else 0

    reference = {}
    with open(REFERENCE) as fh:
        for line in fh:
            if line.strip() and not line.startswith("#"):
                h, k = line.rstrip("\n").split("  ", 1)
                reference[k] = h
    changed = sorted(k for k in set(reference) | set(current) if reference.get(k) != current.get(k))
    for k in changed:
        state = "missing" if k not in current else "new" if k not in reference else "changed"
        print(f"{state:8s} {k}")
    print(f"{len(by_prog)} programs, {len(by_rel)} relations: "
          f"{'no differences' if not changed else f'{len(changed)} differences'}"
          f"{f', {len(failed)} failed' if failed else ''}")
    return 1 if changed or failed else 0


if __name__ == "__main__":
    sys.exit(main())
