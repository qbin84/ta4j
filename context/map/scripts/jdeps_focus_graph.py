"""Focused package graph: how changes to org.ta4j.core contracts spread upward.

usage: python3 context/map/scripts/jdeps_focus_graph.py KEPT_PKL OUT_DOT
KEPT_PKL comes from hot.py (git activity). Emulates dependency-cruiser style filtering on top
of jdeps data: include-only the packages around the core contracts, collapse rules.** and
criteria.**, keep runtime edges only (type-only and registry/config edges dropped).
"""
import collections, contextlib, io, os, pickle, re, runpy, sys, tempfile

KEPT, OUT = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], tempfile.mkdtemp()]  # jdeps_cycles/jdeps_layers write their JSON here
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(here, "jdeps_layers.py"), run_name="jdeps_layers")
F_rt, pkg_of, layer, is_registry = g["F_rt"], g["pkg_of"], g["layer"], g["is_registry"]

C = "org.ta4j.core"
FOCUS = "core"  # only edges touching this node: who is hit by a contract change, and which edges go back up
NODES = [  # (node, package regex, layer label) — include-only + collapse
    ("backtest", rf"^{C}\.backtest$", "L5"), ("criteria.**", rf"^{C}\.criteria(\.|$)", "L4"),
    ("rules.**", rf"^{C}\.rules(\.|$)", "L3"), ("analysis", rf"^{C}\.analysis$", "L3"),
    ("analysis.cost", rf"^{C}\.analysis\.cost$", "L3"), ("core", rf"^{C}$", "L1"),
    ("bars", rf"^{C}\.bars$", "L1"), ("serialization", rf"^{C}\.serialization$", "X"),
]
RANK = {"L5": 5, "L4": 4, "L3": 3, "L1": 1, "L0": 0}
BY_DESIGN = re.compile(r"(/serialization/|/criteria/ReturnRepresentation|/analysis/cost/"
                       r"|/analysis/(AnalysisWindow|AnalysisContext|OpenPositionHandling)\.java$)")
def node_of(f):
    p = pkg_of(f)
    for n, rx, _ in NODES:
        if re.search(rx, p): return n
    return None
lay = {n: l for n, _, l in NODES}

edges = collections.defaultdict(list)  # (na, nb) -> [(fa, fb)]
for a, bs in F_rt.items():
    na = node_of(a)
    if not na: continue
    for b in bs:
        nb = node_of(b)
        if nb and nb != na and FOCUS in (na, nb) and not is_registry(b): edges[(na, nb)].append((a, b))

kept = pickle.load(open(KEPT, "rb"))
commits = collections.Counter()
for _, _, fs, _ in kept:
    for n in {node_of(f) for f in fs if "/src/main/java/" in f} - {None}: commits[n] += 1
fan_in = collections.Counter(nb for _, nb in edges); fan_out = collections.Counter(na for na, _ in edges)

def name(f): return f.rsplit("/", 1)[1][:-5]
FILL = {"L5": "#e8eaf6", "L4": "#e3f2fd", "L3": "#e0f2f1", "L1": "#fff3e0", "L0": "#f5f5f5", "X": "#fce4ec"}
out = ['digraph core_contracts {',
       '  graph [rankdir=TB, newrank=true, nodesep=0.8, ranksep=1.1, splines=true, fontname="Helvetica", fontsize=12,',
       '         labelloc=t, label="Kogo dotyka zmiana kontraktów org.ta4j.core i które krawędzie wracają w górę'
       ' (tylko krawędzie z/do core; runtime: jdeps + bajtkod)\\n'
       'szare = pakiet zależy od core (liczba plików, które trzeba sprawdzić) · '
       'pomarańczowe przerywane = core sięga w górę z projektu / przez złą lokalizację typu · '
       'czerwone = core sięga w górę po logikę\\n'
       'w węźle: warstwa, commity z 12 mies. (kod produkcyjny) i fan-in/fan-out w tym podgrafie"];',
       '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, margin="0.2,0.1"];',
       '  edge [fontname="Helvetica", fontsize=9];']
rows = [[n for n, _, ll in NODES if ll in group] for group in (("L5",), ("L4",), ("L3", "X"), ("L1",), ("L0",))]
rows = [r for r in rows if r]
for r in rows:
    out.append("  { rank=same; " + " ".join(f'"{n}"' for n in r) + " }")
for upper, lower in zip(rows, rows[1:]):  # keep layers stacked top-down even though edges only touch core
    out.append(f'  "{upper[0]}" -> "{lower[0]}" [style=invis];')
for n, _, l in NODES:
    pen = ', penwidth=2.5, color="#b71c1c"' if n == "core" else ""
    out.append(f'  "{n}" [label="{n}\\n{l} · {commits[n]} commitów\\nfan-in {fan_in[n]} / fan-out {fan_out[n]}", '
               f'fillcolor="{FILL[l]}"{pen}];')
for (na, nb), fe in sorted(edges.items()):
    ra, rb = RANK.get(lay[na]), RANK.get(lay[nb])
    upward = (lay[nb] == "X" and na != "serialization") or (ra is not None and rb is not None and ra < rb)
    if not upward:
        out.append(f'  "{na}" -> "{nb}" [label="{len(fe)}", color="#9e9e9e", fontcolor="#757575"];')
        continue
    logic = [(a, b) for a, b in fe if not BY_DESIGN.search(b)]
    shown = logic or fe
    files = sorted({f"{name(a)} → {name(b)}" for a, b in shown})
    back = len(edges.get((nb, na), []))
    lbl = (f"{len(fe)} (wstecz: {back})\\n" if back else f"{len(fe)}\\n") + \
          "\\n".join(files[:3]) + ("\\n…" if len(files) > 3 else "")
    style = ('color="#c62828", fontcolor="#c62828", penwidth=2.2' if logic
             else 'color="#ef6c00", fontcolor="#ef6c00", style=dashed, penwidth=1.6')
    out.append(f'  "{na}" -> "{nb}" [label="{lbl}", {style}, constraint=false];')
out.append("}")
open(OUT, "w").write("\n".join(out) + "\n")
print(f"nodes {len(NODES)}, edges {len(edges)} -> {OUT}")
