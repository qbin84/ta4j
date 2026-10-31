# Human contributors per contact area (agents/bots excluded, identities merged by shared name/email).
# usage: python3 context/map/scripts/contributors.py kept.pkl out.json   (kept.pkl from hot.py)
import pickle,re,collections,sys,json
kept=pickle.load(open(sys.argv[1],"rb"))
AGENT=re.compile(r"^(Claude|Codex|Copilot)$|copilot|jules|codex|\[bot\]|github-actions|dependabot",re.I)
# union-find over names and emails -> one person per connected component
par={}
def f(x):
    par.setdefault(x,x)
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
def u(a,b): par[f(a)]=f(b)
for *_,c in kept:
    if AGENT.search(c["an"]) or AGENT.search(c["ae"]): continue
    u("n:"+c["an"],"e:"+c["ae"].lower())
    m=re.match(r"\d+\+([^@]+)@users\.noreply\.github\.com",c["ae"])
    if m: u("n:"+c["an"],"n:"+m.group(1))
groups=collections.defaultdict(set)
for k in list(par): groups[f(k)].add(k)
names={}
for g,ks in groups.items():
    ns=sorted(k[2:] for k in ks if k.startswith("n:"))
    for k in ks: names[k]=ns
AREAS={
"1 mutacje barow i serii":r"/org/ta4j/core/(BaseBar|BaseBarSeries|ConcurrentBarSeries|BarSeries|Bar|BaseRealtimeBar)\w*\.java$|/org/ta4j/core/bars/",
"2 silnik cache wskaznikow":r"/org/ta4j/core/indicators/(\w*Cache\w*|AbstractIndicator|IndicatorUtils)\w*\.java$",
"3 badania Elliotta":r"/analysis/elliott/|/indicators/elliott/|/rules/elliott/|ta4jexamples/analysis/elliottwave/",
"4 krzywa kapitalu i zwroty":r"/org/ta4j/core/analysis/[A-Z]\w*\.java$|/org/ta4j/core/criteria/",
"5 publiczne API kontraktow core":r"/org/ta4j/core/(Rule|Indicator|Strategy|AnalysisCriterion|BaseStrategy|Trade|BaseTrade|TradingRecord|BaseTradingRecord|Position)(Test)?\.java$|/analysis/cost/|/rules/(And|Or|Not|Xor|Abstract)Rule|/rules/RuleCopies|/org/ta4j/core/serialization/",
}
out={}
for area,rx in AREAS.items():
    r=re.compile(rx)
    per=collections.defaultdict(list); agent=0
    for h,ai,fs,c in kept:
        if not any(r.search(x) for x in fs): continue
        if AGENT.search(c["an"]) or AGENT.search(c["ae"]): agent+=1; continue
        key=" / ".join(names["n:"+c["an"]])
        coai=bool(re.search(r"claude|codex|copilot|jules|cursor",c["tr"],re.I))
        per[key].append(dict(h=h,dt=c["dt"],s=c["s"],an=c["an"],coai=coai))
    out[area]={"agent_authored_skipped":agent,"people":{k:v for k,v in per.items()}}
    tot=sum(len(v) for v in per.values())
    print(f"\n== {area}: human commits {tot}, agent-authored skipped {agent}")
    for k,v in sorted(per.items(),key=lambda x:-len(x[1])):
        byname=collections.Counter(x["an"] for x in v)
        print(f"   {len(v):4} ({100*len(v)/tot:.0f}%) {k}  names={dict(byname)}  AI-coauthored={sum(x['coai'] for x in v)}  {min(x['dt'] for x in v)}..{max(x['dt'] for x in v)}")
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False)
