import json,subprocess,sys
# usage: fixpr.py fix.json merges.txt > fixpr.txt
# merges.txt: git rev-list --first-parent master --merges --since='13 months ago' --format='%H %s' | grep -v '^commit'
d=json.load(open(sys.argv[1]))
fp=[l.split(" ",1) for l in open(sys.argv[2]).read().splitlines()][::-1]  # oldest first
hs=sorted({h for v in d.values() for h,_,_ in v["fix"]})
def pr(h):
    for m,s in fp:
        if subprocess.run(["git","merge-base","--is-ancestor",h,m]).returncode==0:
            if subprocess.run(["git","merge-base","--is-ancestor",h,m+"^1"]).returncode==0: return "DIRECT(before "+s[:60]+")"
            return s
    return "DIRECT/unmerged"
for h in hs: print(h, pr(h))
