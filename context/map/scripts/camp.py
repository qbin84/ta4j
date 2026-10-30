import pickle,collections,re,sys
kept=pickle.load(open(sys.argv[1],"rb"))
spikes=[("examples elliottwave",r"ta4j-examples/src/\w+/java/ta4jexamples/analysis/elliottwave/",["2026-03"]),
("statistics",r"core/indicators/statistics/",["2026-08"]),
("forecast",r"core/indicators/forecast/",["2026-07","2026-08"]),
("analysis/elliott",r"core/analysis/elliott/",["2026-07","2026-08","2026-09","2026-10"]),
("backtest",r"core/backtest/",["2026-08","2026-09"]),
("criteria",r"core/criteria/",["2026-08","2026-09"]),
("analysis root",r"core/analysis/[^/]+$",["2026-08","2026-09"]),
("scripts",r"^scripts/",["2026-05","2026-06","2026-07","2026-08"]),
("core root",r"org/ta4j/core/[^/]+$",["2026-08","2026-09","2026-10"]),
("indicators root",r"core/indicators/[^/]+$",["2025-11","2026-07","2026-08","2026-10"])]
for name,rx,ms in spikes:
    r=re.compile(rx)
    for m in ms:
        cs=[c for h,ai,fs,c in kept if c["dt"].startswith(m) and any(r.search(f) for f in fs)]
        tk=collections.Counter(t for c in cs for t in set(re.findall(r"CF-\d+|#\d{4}",c["s"])))
        words=collections.Counter(w.lower() for c in cs for w in re.findall(r"[A-Z][a-zA-Z]{4,}",c["s"]))
        print(f"\n## {name} {m} n={len(cs)} tickets={tk.most_common(6)}")
        print("   words:",[w for w,_ in words.most_common(10)])
        for c in cs[:: max(1,len(cs)//6)][:6]: print("   -",c["s"][:110])
