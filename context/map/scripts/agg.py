import pickle,sys,re,collections
kept=pickle.load(open(sys.argv[1],"rb")); depth=int(sys.argv[2])
def area(p,d):
    m=re.match(r"([^/]+)/src/(main|test|jmh)/java/(?:org/ta4j/core|ta4jexamples|org/ta4j/[^/]+)/(.*)",p)
    if m:
        mod,_,rest=m.groups(); parts=rest.split("/")[:-1]
        return mod+":"+("/".join(parts[:d]) or "(root)")
    parts=p.split("/")
    return "/".join(parts[:min(d,len(parts)-1)]) or p
A=collections.Counter(); AA=collections.Counter(); F=collections.Counter(); FA=collections.Counter()
for h,ai,fs,c in kept:
    for a in {area(f,depth) for f in fs}:
        A[a]+=1; AA[a]+=ai
    if depth==1:
        for f in fs: F[f]+=1; FA[f]+=ai
for a,n in A.most_common(25): print(f"{n:5} {AA[a]:4} {a}")
if depth==1:
    print("--- files")
    for f,n in F.most_common(30): print(f"{n:5} {FA[f]:4} {f}")
