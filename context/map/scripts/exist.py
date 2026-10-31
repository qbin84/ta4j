import pickle,re,collections,itertools,os,subprocess,sys
# usage: exist.py kept.pkl > exist.txt
# Lists files behind coupled area pairs (>=10 co-commits) that no longer exist at HEAD, with their fate,
# then recomputes the top pairs using only files that still exist.
kept=pickle.load(open(sys.argv[1],"rb"))
def area(p):
    m=re.match(r"([^/]+)/src/(?:main|test|jmh)/java/(?:org/ta4j/core|ta4jexamples|org/ta4j/[^/]+)/(.*)",p)
    if m:
        mod,rest=m.groups(); parts=rest.split("/")[:-1]
        short={"ta4j-core":"core","ta4j-examples":"examples","ta4j-cli":"cli"}.get(mod,mod)
        return short+":"+("/".join(parts[:2]) or "(root)")
    parts=p.split("/"); return parts[0] if len(parts)>1 else "(repo root)"
use=[fs for h,ai,fs,c in kept if len(fs)<=40 and len({area(f) for f in fs})<=6]
P=collections.Counter()
for fs in use:
    for p in itertools.combinations(sorted({area(f) for f in fs}),2): P[p]+=1
pairs=[p for p,n in P.items() if n>=10]
F=collections.Counter(); FP=collections.defaultdict(set)
for fs in use:
    ar={area(f) for f in fs}
    for p in pairs:
        if set(p)<=ar:
            for f in fs:
                if area(f) in p: F[f]+=1; FP[f].add(" + ".join(p))
cand=[f for f,n in F.items() if n>=3]
gone=[f for f in cand if not os.path.exists(f)]
print("pairs>=10:",len(pairs),"files with >=3 coupled co-commits:",len(cand),"gone:",len(gone))
for f in sorted(gone,key=lambda f:-F[f]):
    r=subprocess.run(["git","log","--full-history","-M","--format=%h %as %an|%s","--name-status","-1","--diff-filter=DR","--",f],capture_output=True,text=True).stdout.strip().splitlines()
    print(f"{F[f]:3} {f}\n      pairs: {sorted(FP[f])[:3]}\n      fate: {' / '.join(x[:150] for x in r[:3])}")
def counts(live):
    A=collections.Counter(); C=collections.Counter()
    for fs in use:
        s=sorted({area(f) for f in fs if (os.path.exists(f) or not live)})
        for a in s: A[a]+=1
        for p in itertools.combinations(s,2): C[p]+=1
    return A,C
A0,P0=counts(False); A1,P1=counts(True)
print("\n== pairs: all files -> existing files only")
for p,n in P0.most_common(14):
    m=P1[p]; mn=min(A1[x] for x in p)
    print(f"{n:4} -> {m:4} live ({100*m/mn:4.0f}% of {mn})  {' + '.join(p)}")
