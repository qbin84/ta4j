"""Layer-boundary check on top of jdeps_cycles.py (same runtime vs type-only split).

usage: python3 context/map/scripts/jdeps_layers.py OUT_DIR
Layers are inferred from package-info.java and indicators/AGENTS.md (the repo declares no
explicit layering). A violation is a runtime edge from a lower layer to a higher one.
Type-only edges and edges into registries / configuration-as-code are counted separately.
"""
import collections, io, contextlib, json, os, re, runpy, sys

OUT = sys.argv[1]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(os.path.dirname(__file__), "jdeps_cycles.py"), run_name="jdeps_cycles")
F_all, F_rt, evidence, pkg_of, short, area_of = (g[k] for k in
    ("F_all", "F_rt", "evidence", "pkg_of_file", "short", "area_of"))

C = "org.ta4j.core"
LAYERS = [  # (rank, name, package regex) — first match wins
    (0, "L0 fundament (num, utils)", rf"^{C}\.(num|utils)(\.|$)"),
    (1, "L1 model domeny (core, bars, aggregator)", rf"^{C}(\.bars|\.aggregator)?$"),
    (2, "L2 obliczenia sygnałów (indicators, swing, montecarlo, event)",
        rf"^{C}\.(indicators|analysis\.elliott\.swing|analysis\.montecarlo|analysis\.event|acceleration)(\.|$)"),
    (3, "L3 decyzje i wyniki (rules, analysis, cost, frequency)",
        rf"^{C}\.(rules|analysis|analysis\.cost|analysis\.frequency)(\.|$)"),
    (4, "L4 ocena (criteria)", rf"^{C}\.criteria(\.|$)"),
    (5, "L5 orkiestracja (backtest, walkforward, reports, portfolio, strategy)",
        rf"^{C}\.(backtest|walkforward|reports|portfolio|strategy)(\.|$)"),
    (6, "L6 badania (analysis.elliott, research)", rf"^{C}\.(analysis\.elliott|research)(\.|$)"),
    (7, "L7 przykłady (ta4j-examples)", r"^ta4jexamples(\.|$)"),
]
CROSS = rf"^{C}\.(serialization|named)(\.|$)"  # codec + registry: may depend on everything
REGISTRY_OR_CONFIG = re.compile(r"(Registry|Registries|Catalog|Config|Configuration|Settings|Profiles?)\.java$")
def layer(p):
    if re.search(CROSS, p): return (None, "X kodek/rejestr (serialization, named)")
    for r, n, rx in LAYERS:
        if re.search(rx, p): return (r, n)
    return (None, "?")
def is_registry(f):
    return pkg_of(f).startswith(f"{C}.named") or bool(REGISTRY_OR_CONFIG.search(f))

viol, typeonly, regcfg, into_cross = [], collections.Counter(), collections.Counter(), []
for a, bs in F_all.items():
    for b in bs:
        (ra, na), (rb, nb) = layer(pkg_of(a)), layer(pkg_of(b))
        if pkg_of(a) == pkg_of(b): continue
        upward = ra is not None and rb is not None and ra < rb
        to_cross = rb is None and nb.startswith("X") and ra is not None
        if not (upward or to_cross): continue
        key = (na, nb)
        if b not in F_rt.get(a, ()):
            typeonly[key] += 1; continue
        if is_registry(b):
            regcfg[key] += 1; continue
        rec = {"from": short(a), "to": short(b), "from_layer": na, "to_layer": nb,
               "from_area": area_of(pkg_of(a)), "to_area": area_of(pkg_of(b)),
               "uses": {k: sorted(v) for k, v in evidence[(a, b)].items()}}
        (into_cross if to_cross else viol).append(rec)

# declared rule (indicators/AGENTS.md): no top-level non-indicator API types in indicators namespace
FORBIDDEN = re.compile(r"(Detector|Config|Result|Filter|Runner|Facade)\.java$")
placement = sorted(short(f) for f in set(F_all) | {b for v in F_all.values() for b in v}
                   if pkg_of(f).startswith(f"{C}.indicators") and FORBIDDEN.search(f))

report = {"violations": viol, "into_codec": into_cross,
          "type_only_skipped": {f"{a} -> {b}": n for (a, b), n in typeonly.items()},
          "registry_or_config_skipped": {f"{a} -> {b}": n for (a, b), n in regcfg.items()},
          "indicators_placement": placement}
json.dump(report, open(os.path.join(OUT, "jdeps_layers.json"), "w"), indent=1, ensure_ascii=False)

by = collections.defaultdict(list)
for v in viol: by[(v["from_layer"], v["to_layer"])].append(v)
print(f"runtime upward violations: {len(viol)} file edges; into codec: {len(into_cross)}; "
      f"skipped type-only: {sum(typeonly.values())}; skipped registry/config: {sum(regcfg.values())}")
for (a, b), vs in sorted(by.items(), key=lambda x: -len(x[1])):
    print(f"\n[{len(vs)}] {a}  ->  {b}")
    for v in vs[:12]:
        print(f"    {v['from']} -> {v['to']}   {v['uses']}   areas: {v['from_area']} -> {v['to_area']}")
cb = collections.Counter((v["from_layer"]) for v in into_cross)
print("\ninto codec by source layer:", dict(cb))
for v in into_cross[:12]: print(f"    {v['from']} -> {v['to']}  {v['uses']}")
print("\ntype-only skipped:", dict(typeonly))
print("registry/config skipped:", dict(regcfg))
print("\nindicators namespace placement (declared rule):", len(placement))
for p in placement: print("   ", p)
