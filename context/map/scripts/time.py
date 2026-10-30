import pickle,collections,re,sys
kept=pickle.load(open(sys.argv[1],"rb"))
areas={"analysis/elliott":r"ta4j-core/src/\w+/java/org/ta4j/core/analysis/elliott/",
"indicators (root)":r"ta4j-core/src/\w+/java/org/ta4j/core/indicators/[^/]+$",
"core (root)":r"ta4j-core/src/\w+/java/org/ta4j/core/[^/]+$",
"indicators/statistics":r"ta4j-core/src/\w+/java/org/ta4j/core/indicators/statistics/",
"examples elliottwave":r"ta4j-examples/src/\w+/java/ta4jexamples/analysis/elliottwave/",
"scripts":r"^scripts/",
"backtest":r"ta4j-core/src/\w+/java/org/ta4j/core/backtest/",
"criteria":r"ta4j-core/src/\w+/java/org/ta4j/core/criteria/",
"analysis (root)":r"ta4j-core/src/\w+/java/org/ta4j/core/analysis/[^/]+$",
"indicators/forecast":r"ta4j-core/src/\w+/java/org/ta4j/core/indicators/forecast/"}
months=sorted({c["dt"][:7] for *_,c in kept})
tot=collections.Counter(c["dt"][:7] for *_,c in kept)
print("months"," ".join(m[2:] for m in months))
print(f"{'ALL':24}"+"".join(f"{tot[m]:5}" for m in months))
for k,rx in areas.items():
    r=re.compile(rx); M=collections.Counter()
    for h,ai,fs,c in kept:
        if any(r.search(f) for f in fs): M[c["dt"][:7]]+=1
    print(f"{k:24}"+"".join(f"{M[m]:5}" for m in months))
