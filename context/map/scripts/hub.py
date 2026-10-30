import pickle,re,collections,sys,os
kept=pickle.load(open(sys.argv[1],"rb"))
def area(p):
    m=re.match(r"([^/]+)/src/(?:main|test|jmh)/java/(?:org/ta4j/core|ta4jexamples|org/ta4j/[^/]+)/(.*)",p)
    if m:
        mod,rest=m.groups(); parts=rest.split("/")[:-1]
        short={"ta4j-core":"core","ta4j-examples":"examples","ta4j-cli":"cli"}.get(mod,mod)
        return short+":"+("/".join(parts[:2]) or "(root)")
    return None
# all files of the commit (incl. noise), canonical newest names not stored -> use raw new path
N=collections.Counter(); AR=collections.defaultdict(set); AC=collections.Counter(); CC=collections.Counter()
for h,ai,fs,c in kept:
    allf={n for o,n,a,d in c["files"]}
    code_areas={area(f) for f in allf if area(f)}
    if len(code_areas)>6 or len(allf)>40 or not code_areas: continue
    CC["n"]+=1
    for f in allf:
        N[f]+=1
        others=code_areas-{area(f)}
        AR[f]|=others
        if len(others)>=2: AC[f]+=1
print("commits considered",CC["n"])
for f,_ in sorted(AR.items(),key=lambda x:-len(x[1]))[:15]:
    print(f"{len(AR[f]):4} areas  {N[f]:5} commits  {AC[f]:4} multi-area  {'OK' if os.path.exists(f) else 'GONE'}  {f}")
