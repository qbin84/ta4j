"""Dependency cycles touching the active areas of artifact-1-territory.md.

usage: python3 context/map/scripts/jdeps_cycles.py OUT_DIR
Run from the repo root after `mvn -pl ta4j-core,ta4j-examples -am compile`.

All edges come from `jdeps -verbose:class -filter:none`. An edge is "runtime" when the
bytecode of the source class really uses the target (inheritance, new, method call, field
access, cast/instanceof, class literal, catch, method handle); everything else jdeps reports
(signatures, generics, annotations, throws) is "type-only". Classes are folded to source files.
"""
import collections, json, os, re, subprocess, sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
MODULES = [("ta4j-core", "ta4j-core/target/classes", []),
           ("ta4j-examples", "ta4j-examples/target/classes", ["ta4j-core/target/classes"])]
OWN = re.compile(r"^(org\.ta4j\.|ta4jexamples\.)")
AREAS = [  # (label, package regex) — top Java areas of artifact-1-territory.md
    ("analysis/elliott", r"^org\.ta4j\.core\.analysis\.elliott(\.|$)"),
    ("indicators (główny)", r"^org\.ta4j\.core\.indicators$"),
    ("core (główny)", r"^org\.ta4j\.core$"),
    ("indicators/statistics", r"^org\.ta4j\.core\.indicators\.statistics(\.|$)"),
    ("examples/elliottwave", r"^ta4jexamples\.analysis\.elliottwave(\.|$)"),
    ("backtest", r"^org\.ta4j\.core\.backtest(\.|$)"),
    ("criteria", r"^org\.ta4j\.core\.criteria(\.|$)"),
    ("analysis (główny)", r"^org\.ta4j\.core\.analysis$"),
    ("indicators/forecast", r"^org\.ta4j\.core\.indicators\.forecast(\.|$)"),
]
def area_of(pkg):
    for label, rx in AREAS:
        if re.search(rx, pkg): return label
    return None

# ---- 1. class -> source file, runtime edges (javap) ------------------------------------
cls_file, runtime = {}, collections.defaultdict(lambda: collections.defaultdict(set))
INSN = re.compile(r"^\s+\d+: (\w+)\s+#\d+.*?// (class|Method|InterfaceMethod|Field) (.+)$")
REF = re.compile(r"// REF_\w+ ([\w/$]+)\.")
CATCH = re.compile(r"^\s+\d+\s+\d+\s+\d+\s+Class (\S+)")
def owner(s):
    s = s.split(":")[0].replace('"', "")
    if s.startswith("["): s = s.lstrip("[").lstrip("L").rstrip(";")
    else:
        if "." in s: s = s.rsplit(".", 1)[0] if "/" in s.rsplit(".", 1)[0] else ""
        elif "/" not in s: s = ""
    return s.replace("/", ".") if "/" in s else None
def strip_generics(s):
    while "<" in s: s = re.sub(r"<[^<>]*>", "", s)
    return s
module_of = {}
for mod, cdir, cp in MODULES:
    names = []
    for root, _, files in os.walk(cdir):
        for f in files:
            if f.endswith(".class") and f not in ("module-info.class", "package-info.class"):
                names.append(os.path.relpath(os.path.join(root, f), cdir)[:-6].replace(os.sep, "."))
    for i in range(0, len(names), 150):
        out = subprocess.run(["javap", "-c", "-p", "-v", "-cp", ":".join([cdir] + cp)] + names[i:i + 150],
                             capture_output=True, text=True).stdout.splitlines()
        cur = prev = None
        for line in out:
            if line.startswith("Classfile "):
                cur = None
            elif line.startswith("  minor version") and prev is not None:
                decl = strip_generics(prev)
                m = re.search(r"(?:class|interface) ([\w.$]+)(.*)$", decl)
                cur = m.group(1); module_of[cur] = mod
                for kw in ("extends", "implements"):
                    mm = re.search(kw + r" ([\w.$, ]+?)(?: implements|$)", m.group(2))
                    if mm:
                        for t in mm.group(1).split(","):
                            runtime[cur][t.strip()].add("dziedziczy")
            elif cur:
                if line.startswith("SourceFile:"):
                    cls_file[cur] = line.split('"')[1]
                elif (m := INSN.match(line)):
                    o = owner(m.group(3))
                    if o: runtime[cur][o].add({"new": "new", "checkcast": "rzutuje", "instanceof": "instanceof"}
                                              .get(m.group(1), "woła" if m.group(2) != "Field" else "pole"))
                elif (m := REF.search(line)):
                    runtime[cur][m.group(1).replace("/", ".")].add("referencja metody")
                elif (m := CATCH.match(line)):
                    runtime[cur][m.group(1).replace("/", ".")].add("catch")
            prev = line
def file_of(c):
    if c not in cls_file: return None
    pkg = c.rsplit(".", 1)[0]
    root = "ta4j-core" if module_of[c] == "ta4j-core" else "ta4j-examples"
    return f"{root}/src/main/java/{pkg.replace('.', '/')}/{cls_file[c]}"
def pkg_of_file(f):
    return f.split("/src/main/java/")[1].rsplit("/", 1)[0].replace("/", ".")

# ---- 2. all edges (jdeps) ------------------------------------------------------------
all_e = collections.defaultdict(set)
LINE = re.compile(r"^\s+(\S+)\s+->\s+(\S+)\s")
for mod, cdir, cp in MODULES:
    cmd = ["jdeps", "-verbose:class", "-filter:none", "-q"] + (["-cp", ":".join(cp)] if cp else []) + [cdir]
    for line in subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines():
        m = LINE.match(line)
        if m and OWN.match(m.group(2)):
            all_e[m.group(1)].add(m.group(2))

# ---- 3. fold to files -----------------------------------------------------------------
F_all, F_rt = collections.defaultdict(set), collections.defaultdict(set)
evidence = collections.defaultdict(lambda: collections.defaultdict(set))  # (fa,fb) -> {"A->B": kinds}
for a, targets in all_e.items():
    fa = file_of(a)
    for b in targets:
        fb = file_of(b)
        if not fa or not fb or fa == fb: continue
        F_all[fa].add(fb)
        kinds = runtime.get(a, {}).get(b)
        if kinds:
            F_rt[fa].add(fb)
            evidence[(fa, fb)][f"{a.rsplit('.', 1)[1]} -> {b.rsplit('.', 1)[1]}"] |= kinds
nodes = set(F_all) | {b for v in F_all.values() for b in v}

def sccs(graph, nodes):
    index, low, stack, on, res, i = {}, {}, [], set(), [], [0]
    for root in sorted(nodes):
        if root in index: continue
        work = [(root, iter(sorted(graph.get(root, ()))))]
        index[root] = low[root] = i[0]; i[0] += 1; stack.append(root); on.add(root)
        while work:
            v, it = work[-1]
            for w in it:
                if w not in index:
                    index[w] = low[w] = i[0]; i[0] += 1; stack.append(w); on.add(w)
                    work.append((w, iter(sorted(graph.get(w, ()))))); break
                elif w in on: low[v] = min(low[v], index[w])
            else:
                work.pop()
                if work: low[work[-1][0]] = min(low[work[-1][0]], low[v])
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = stack.pop(); on.discard(w); comp.append(w)
                        if w == v: break
                    if len(comp) > 1: res.append(sorted(comp))
    return res
def shortest_cycle_through(graph, start, allowed):
    prev, q, seen = {start: None}, collections.deque([start]), {start}
    while q:
        v = q.popleft()
        for w in sorted(graph.get(v, ())):
            if w not in allowed: continue
            if w == start:
                path = [v]
                while prev[path[-1]] is not None: path.append(prev[path[-1]])
                return path[::-1]
            if w not in seen:
                seen.add(w); prev[w] = v; q.append(w)
    return None
def canon(c):
    i = c.index(min(c)); return tuple(c[i:] + c[:i])

# ---- 4. report ------------------------------------------------------------------------
short = lambda f: f.split("/src/main/java/")[1].replace("org/ta4j/core/", "core/").replace("ta4jexamples/", "examples/")
report = {"nodes": len(nodes), "edges_all": sum(map(len, F_all.values())), "edges_runtime": sum(map(len, F_rt.values())),
          "components": []}
rt_sccs = sccs(F_rt, nodes)
rt_member = {f: i for i, c in enumerate(rt_sccs) for f in c}
for comp in sccs(F_all, nodes):
    touched = sorted({area_of(pkg_of_file(f)) for f in comp} - {None})
    if not touched: continue
    cs = set(comp)
    inner_rt = [c for c in rt_sccs if set(c) <= cs]
    entry = {"size_all": len(comp), "areas": touched,
             "packages": sorted(collections.Counter(pkg_of_file(f) for f in comp).items(), key=lambda x: -x[1]),
             "runtime_components": [], "type_only_files": len(comp) - sum(map(len, inner_rt))}
    for rc in sorted(inner_rt, key=len, reverse=True):
        rcs = set(rc)
        cyc = {}
        for f in rc:
            c = shortest_cycle_through(F_rt, f, rcs)
            if c: cyc[canon(c)] = c
        loops = sorted(cyc.values(), key=lambda c: (len(c), c))
        cross = [c for c in loops if len({pkg_of_file(f) for f in c}) > 1]
        def ev(c): return [{"edge": f"{short(c[k])} -> {short(c[(k + 1) % len(c)])}",
                            "uses": {k2: sorted(v) for k2, v in list(evidence[(c[k], c[(k + 1) % len(c)])].items())[:3]}}
                           for k in range(len(c))]
        entry["runtime_components"].append({
            "size": len(rc), "areas": sorted({area_of(pkg_of_file(f)) for f in rc} - {None}),
            "packages": sorted(collections.Counter(pkg_of_file(f) for f in rc).items(), key=lambda x: -x[1]),
            "min_len": len(loops[0]) if loops else None,
            "two_file_loops": sum(1 for c in loops if len(c) == 2),
            "min_loop": [short(f) for f in loops[0]], "min_loop_evidence": ev(loops[0]),
            "min_cross_package_loop": [short(f) for f in cross[0]] if cross else None,
            "min_cross_package_evidence": ev(cross[0]) if cross else None,
            "cross_package_loops": [[short(f) for f in c] for c in cross[:15]]})
    if not inner_rt:  # type-only cycle: report its smallest loop on all edges
        c = min((shortest_cycle_through(F_all, f, cs) for f in comp), key=lambda c: len(c) if c else 1e9)
        entry["type_only_min_loop"] = [short(f) for f in c]
    report["components"].append(entry)
# package-level runtime graph between packages of active areas
P = collections.defaultdict(set); Pev = collections.defaultdict(set)
for a, bs in F_rt.items():
    for b in bs:
        pa, pb = pkg_of_file(a), pkg_of_file(b)
        if pa != pb: P[pa].add(pb); Pev[(pa, pb)].add(f"{short(a)} -> {short(b)}")
report["package_runtime_sccs"] = []
for comp in sccs(P, set(P) | {b for v in P.values() for b in v}):
    if not any(area_of(p) for p in comp): continue
    cs = set(comp); loops = {}
    for p in comp:
        c = shortest_cycle_through(P, p, cs)
        if c: loops[canon(c)] = c
    two = sorted(c for c in loops.values() if len(c) == 2)
    report["package_runtime_sccs"].append({
        "size": len(comp), "packages": comp,
        "two_package_loops": [{"loop": c, "a_to_b": sorted(Pev[(c[0], c[1])])[:4], "a_to_b_count": len(Pev[(c[0], c[1])]),
                               "b_to_a": sorted(Pev[(c[1], c[0])])[:4], "b_to_a_count": len(Pev[(c[1], c[0])])} for c in two]})
json.dump(report, open(os.path.join(OUT, "jdeps_cycles.json"), "w"), indent=1, ensure_ascii=False)
print(f"files {report['nodes']}, edges all {report['edges_all']}, runtime {report['edges_runtime']}")
for e in report["components"]:
    print(f"\nSCC(all) size={e['size_all']} areas={e['areas']} type-only files outside runtime cycles={e['type_only_files']}")
    print("   packages:", e["packages"][:8])
    for r in e["runtime_components"]:
        print(f"   runtime SCC size={r['size']} min={r['min_len']} 2-file loops={r['two_file_loops']} areas={r['areas']}")
        print(f"      packages: {r['packages'][:8]}")
        print(f"      min loop: {r['min_loop']}")
        print(f"      min cross-package: {r['min_cross_package_loop']}")
    if "type_only_min_loop" in e: print("   TYPE-ONLY min loop:", e["type_only_min_loop"])
print("\n== package-level runtime SCCs touching active areas")
for s in report["package_runtime_sccs"]:
    print(f" size={s['size']} {s['packages'][:12]}")
    for t in s["two_package_loops"]:
        print(f"   {t['loop'][0]} <-> {t['loop'][1]}  ({t['a_to_b_count']} / {t['b_to_a_count']} file edges)")
