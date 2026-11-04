import numpy as np, zipfile, csv, io, re, collections
exec(open('isu_profile.py').read().split("z=zipfile.ZipFile")[0])
z=zipfile.ZipFile(r'C:\Users\Shlok\Downloads\PINN KAN battery paper\data\raw\isu_ilcc_small\capacity_fade.zip')
cells={}
for n in z.namelist():
    if not n.endswith('.csv'): continue
    m=re.search(r'G(\d+)C(\d+)',n)
    r=list(csv.reader(io.StringIO(z.read(n).decode())))[1:]
    t=np.array([float(a[0]) for a in r]); q=np.array([float(a[1]) for a in r])
    cells[(int(m.group(1)),int(m.group(2)))]=(t,q/q[0])
def t80(t,x):
    i=np.where(x<=0.8)[0][0]
    return t[i-1]+(x[i-1]-0.8)/(x[i-1]-x[i])*(t[i]-t[i-1])
T80={k:t80(*v) for k,v in cells.items()}
# 1) leave-one-replicate-out condition median in log t80
err=[]
for (g,c),v in T80.items():
    others=[T80[(g,c2)] for (g2,c2) in T80 if g2==g and c2!=c]
    err.append(abs(np.log(v)-np.log(np.median(others))))
print('LORO condition-median |log err| median %.3f mean %.3f'%(np.median(err),np.mean(err)))
# 2) per-cell power-law on first W weeks
for W in [2,4,6]:
    e=[];n=0;skipped=0
    for k,(t,x) in cells.items():
        m=(t<=W)&(t>0)
        if m.sum()<2 or T80[k]<=W: skipped+=1; continue
        y=1-x[m]; ok=y>0
        if ok.sum()<2: skipped+=1; continue
        b,a=np.polyfit(np.log(t[m][ok]),np.log(y[ok]),1)
        b=min(max(b,0.2),3.0)
        a=np.mean(np.log(y[ok])-b*np.log(t[m][ok]))
        t80h=np.exp((np.log(0.2)-a)/b)
        e.append(abs(np.log(t80h)-np.log(T80[k])))
    print('W=%d powerlaw per-cell: n=%d skipped=%d median |log err| %.3f'%(W,len(e),skipped,np.median(e)))
# 3) shape: curvature of late fade; fraction with accelerating rate (rate in last third > first third)
acc=0;tot=0
for k,(t,x) in cells.items():
    if len(t)<10: continue
    d=np.diff(1-x)/np.diff(t); n=len(d)
    tot+=1; acc+= d[-n//3:].mean()>d[:n//3].mean()
print('cells>=10pts',tot,'frac with later 3rd mean rate > first 3rd',acc/tot)
# points available in first W weeks
for W in [2,4,6]:
    print('W',W,'median #pts incl t=0',np.median([(t<=W).sum() for t,x in cells.values()]))
print('frac cells with t80<=4w',np.mean([v<=4 for v in T80.values()]),'<=2w',np.mean([v<=2 for v in T80.values()]))
