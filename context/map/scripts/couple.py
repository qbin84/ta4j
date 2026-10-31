import pickle,collections,re,sys,itertools,statistics
kept=pickle.load(open(sys.argv[1],"rb"))
def area(p):
    m=re.match(r"([^/]+)/src/(?:main|test|jmh)/java/(?:org/ta4j/core|ta4jexamples|org/ta4j/[^/]+)/(.*)",p)
    if m:
        mod,rest=m.groups(); parts=rest.split("/")[:-1]
        short={"ta4j-core":"core","ta4j-examples":"examples","ta4j-cli":"cli"}.get(mod,mod)
        return short+":"+("/".join(parts[:2]) or "(root)")
    parts=p.split("/"); return parts[0] if len(parts)>1 else "(repo root)"
rows=[(h,{area(f) for f in fs},len(fs),c) for h,ai,fs,c in kept]
na=[len(a) for _,a,_,_ in rows]; nf=[n for _,_,n,_ in rows]
qs=lambda v:[sorted(v)[int(len(v)*q)] for q in (.5,.75,.9,.95,.99)]
print("areas/commit p50,75,90,95,99:",qs(na),"files/commit:",qs(nf),file=sys.stderr)
MAXA=int(sys.argv[2]); MAXF=int(sys.argv[3])
use=[r for r in rows if len(r[1])<=MAXA and r[2]<=MAXF]
print("used",len(use),"of",len(rows),"dropped",len(rows)-len(use),file=sys.stderr)
A=collections.Counter(a for _,s,_,_ in use for a in s)
P=collections.Counter(); T=collections.Counter()
for _,s,_,_ in use:
    s=sorted(s)
    for p in itertools.combinations(s,2): P[p]+=1
    for t in itertools.combinations(s,3): T[t]+=1
top3=["core:analysis/elliott","core:indicators","core:(root)"]
print("area totals:",{a:A[a] for a in top3})
def fmt(p,n): m=min(A[x] for x in p); return f"{n:4}  {100*n/m:5.1f}% of {m:4}  "+" + ".join(p)
print("== top pairs"); [print(fmt(p,n)) for p,n in P.most_common(20)]
print("== top triples"); [print(fmt(t,n)) for t,n in T.most_common(12)]
for a in top3:
    print("==",a,A[a])
    cand=[(p,n) for p,n in P.items() if a in p]
    cand.sort(key=lambda x:-x[1])
    for p,n in cand[:8]:
        o=[x for x in p if x!=a][0]
        print(f"   {n:4} {100*n/A[a]:5.1f}% of {a.split(':')[-1]}  {100*n/A[o]:5.1f}% of other({A[o]})  {o}")
    tc=sorted([(t,n) for t,n in T.items() if a in t],key=lambda x:-x[1])[:4]
    for t,n in tc: print("   T",fmt(t,n))
