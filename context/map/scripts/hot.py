import subprocess, re, sys, collections, os
SINCE = "12 months ago"
raw = subprocess.run(["git","log","--no-merges","--since",SINCE,"--reverse","-M","--numstat",
    "--format=@@%x1f%H%x1f%as%x1f%an%x1f%ae%x1f%s%x1f%(trailers:key=Co-authored-by,valueonly,separator=;)"],
    capture_output=True,text=True,check=True).stdout
BOTS = re.compile(r"github-actions|dependabot|renovate", re.I)
AI = re.compile(r"^Claude$|jules|copilot|codex|cursor|devin|anthropic", re.I)
FMT = re.compile(r"^(style\b|.*\b(spotless|formatter|formatting|reformat|whitespace|line endings)\b)", re.I)
MOVE = re.compile(r"\b(move|moved|relocate|organize .*packages|restructure)\b", re.I)
WHITELIST = {"d0ef59e7c"}  # unstable-count semantic change across all indicators
def expand(p):
    m = re.match(r"(.*)\{(.*) => (.*)\}(.*)", p)
    if m:
        a,o,n,b = m.groups()
        f = lambda x: re.sub("//+","/",a+x+b)
        return f(o), f(n)
    if " => " in p:
        o,n = p.split(" => "); return o,n
    return None,p
commits=[]; cur=None
for line in raw.splitlines():
    if line.startswith("@@\x1f"):
        _,h,dt,an,ae,s,tr = line.split("\x1f"); cur=dict(h=h,dt=dt,an=an,ae=ae,s=s,tr=tr,files=[]); commits.append(cur)
    elif line.strip() and cur:
        ad,de,p = line.split("\t",2)
        old,new = expand(p)
        ad = int(ad) if ad!="-" else 0; de=int(de) if de!="-" else 0
        cur["files"].append((old,new,ad,de))
alias={}
for c in commits:
    for old,new,_,_ in c["files"]:
        if old and old!=new: alias[old]=new
def final(p, seen=0):
    while p in alias and seen<50: p=alias[p]; seen+=1
    return p
NOISE_EXT = re.compile(r"\.(md|xml|ya?ml|json|csv|tsv|properties|txt|png|jpe?g|gif|svg|ico|lock|snap|html|css|cfg|ini|toml|iml|bin|gz|zip|jar)$", re.I)
NOISE_PATH = re.compile(r"(^|/)(\.github|\.jules|\.githooks|config|docs|release|\.mvn|target|generated)/|(^|/)(\.env.*|\.gitignore|\.gitattributes|mvnw(\.cmd)?|Doxyfile|CNAME|AUTHORS|package-lock\.json|pnpm-lock\.yaml|yarn\.lock)$|/src/(test|main)/resources/")
def noise(p): return bool(NOISE_EXT.search(p) or NOISE_PATH.search(p))
excluded=collections.Counter(); kept=[]
seen=set()
for c in commits:
    short=c["h"][:9]
    files=c["files"]; n=len(files); churn=sum(a+d for _,_,a,d in files)
    renames=sum(1 for o,nw,a,d in files if o and o!=nw)
    key=(c["an"],c["s"],tuple(sorted(f[1] for f in files)))
    if BOTS.search(c["an"]+c["ae"]): excluded["bot"]+=1; continue
    if key in seen: excluded["duplicate (rebased copy)"]+=1; continue
    seen.add(key)
    if short not in WHITELIST:
        if FMT.search(c["s"]): excluded["formatting"]+=1; continue
        if n>=100 and churn/n<15: excluded["mass mechanical (>=100 files, <15 lines/file)"]+=1; continue
        if n and renames/n>=0.5 and (MOVE.search(c["s"]) or churn/n<20): excluded["move/rename"]+=1; continue
        if n>=50 and churn>0 and sum(d for *_,d in files)/churn>0.9 and MOVE.search(c["s"]): excluded["move/rename"]+=1; continue
    ai = bool(AI.search(c["an"]) or AI.search(c["tr"]))
    fs={final(nw) for _,nw,_,_ in files}
    fs={f for f in fs if not noise(f)}
    if not fs: excluded["only noise files"]+=1; continue
    kept.append((short,ai,fs,c))
print("total",len(commits),"kept",len(kept),"ai",sum(k[1] for k in kept),dict(excluded),file=sys.stderr)
import pickle; pickle.dump(kept,open(sys.argv[1],"wb"))
