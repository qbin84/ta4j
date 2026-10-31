import pickle,collections,re,sys,json
kept=pickle.load(open(sys.argv[1],"rb"))
areas={"analysis/elliott":r"ta4j-core/src/\w+/java/org/ta4j/core/analysis/elliott/",
"indicators (root)":r"ta4j-core/src/\w+/java/org/ta4j/core/indicators/[^/]+$",
"core (root)":r"ta4j-core/src/\w+/java/org/ta4j/core/[^/]+$",
"indicators/statistics":r"ta4j-core/src/\w+/java/org/ta4j/core/indicators/statistics/",
"examples elliottwave":r"ta4j-examples/src/\w+/java/ta4jexamples/analysis/elliottwave/"}
R={k:re.compile(v) for k,v in areas.items()}
FIX=re.compile(r"^(fix|hotfix|bugfix)\b|\b(fix|fixes|fixed|hotfix|bugfix)\b",re.I)
REV=re.compile(r"\brevert",re.I)
def primary(c):
    ch=collections.Counter()
    for o,n,a,d in c["files"]:
        for k,r in R.items():
            if r.search(n) or (o and r.search(o)): ch[k]+=a+d
    return ch.most_common(1)[0][0] if ch else None
out={}
for k,r in R.items():
    cs=[c for h,ai,fs,c in kept if any(r.search(f) for f in fs)]
    fx=[c for c in cs if FIX.search(c["s"]) and not REV.search(c["s"])]
    rv=[c for h,ai,fs,c in kept if REV.search(c["s"]) and primary(c)==k]
    out[k]=dict(n=len(cs),fix=[(c["h"][:9],c["dt"],c["s"]) for c in fx],rev=[(c["h"][:9],c["dt"],c["s"]) for c in rv])
    print(f"{k:24} n={len(cs):4} fix={len(fx):4} ({100*len(fx)/len(cs):.0f}%) revert={len(rv)}")
allrev=[(c["h"][:9],c["dt"],c["s"],primary(c)) for h,ai,fs,c in kept if REV.search(c["s"])]
print("all reverts in kept:",len(allrev))
for r in allrev: print("  ",r)
json.dump(out,open(sys.argv[2],"w"),indent=0)
