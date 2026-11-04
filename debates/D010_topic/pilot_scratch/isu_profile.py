import zipfile,csv,io,statistics,re,numpy as np,json
groups_all=list(range(1,15))+list(range(16,65))
chg1=[0.5,0.5,0.5,1,1,2,2,2,2,2.5,2.5,3,3,3,0.5,1,2.5,2.5,0.8,1.2,1.4,1.6,1.8,1.8,1.4,0.6,2.4,1.6,0.8,1.2,1.0,2.0,2.2,1.825,2.075,0.725,1.875,1.475,1.825,2.075]
dis1=[0.5]*23+[0.6,2.2,2.4,1.6,1.8,0.8,1.0,1.4,1.2,2.0,0.5,0.5,0.5,0.5,0.5,1.025,1.775]
dod1=[25.90,46.11,67.77,47.27,97.54,27.23,46.86,67.24,96.93,47.21,95.98,28.60,47.26,66.32,97.62,67.53,27.53,65.70,98.16,97.98,97.88,97.61,97.51,51.43,4.16,57.85,80.99,52.48,77.59,61.43,38.86,40.65,27.60,97.02,97.06,98.08,95.83,97.14,31.94,67.02]
print(len(chg1),len(dis1),len(dod1))
chg2=[0.725,1.875,0.775,1.125,1.225,2.325,2.375,0.975,2.425,2.275,1.425,2.025,0.925,1.025,2.175,1.775,2.475,1.325,0.675,2.125,1.575,1.975,1.175]
dis2=[2.375,2.325,1.275,1.725,2.025,1.925,2.225,0.675,1.625,1.875,0.875,0.825,1.125,2.475,0.975,1.175,0.575,1.825,1.325,1.975,2.425,1.675,1.425]
dod2=[36.32,38.00,37.12,80.26,75.36,48.27,58.57,18.82,20.10,53.64,83.55,91.54,27.05,61.44,53.81,17.42,42.03,31.64,83.63,54.07,64.19,80.57,91.44]
print(len(chg2),len(dis2),len(dod2))
G=groups_all
C=chg1+chg2; D=dis1+dis2; O=dod1+dod2
assert len(G)==len(C)==len(D)==len(O)==63
cond={g:(c,d,o) for g,c,d,o in zip(G,C,D,O)}
z=zipfile.ZipFile(r'C:\Users\Shlok\Downloads\PINN KAN battery paper\data\raw\isu_ilcc_small\capacity_fade.zip')
rows=[]
for n in z.namelist():
    if not n.endswith('.csv'): continue
    m=re.search(r'G(\d+)C(\d+)',n); g=int(m.group(1)); c=int(m.group(2))
    r=list(csv.reader(io.StringIO(z.read(n).decode())))[1:]
    t=np.array([float(a[0]) for a in r]); q=np.array([float(a[1]) for a in r])
    rel=q/q[0]
    # time to 80%
    idx=np.where(rel<=0.8)[0]
    if len(idx): 
        i=idx[0]; 
        t80=t[i-1]+(rel[i-1]-0.8)/(rel[i-1]-rel[i])*(t[i]-t[i-1]) if i>0 else t[0]
    else: t80=np.nan
    rows.append((g,c,len(t),t[-1],rel[-1],t80,q[0]))
rows.sort()
import collections
n=len(rows); reach=[r for r in rows if not np.isnan(r[5])]
print('cells',n,'reach80',len(reach))
print('npts quartiles',np.percentile([r[2] for r in rows],[0,10,25,50,75,90,100]))
print('t80 weeks quartiles',np.percentile([r[5] for r in reach],[0,10,25,50,75,90,100]))
print('Q0 range',min(r[6] for r in rows),max(r[6] for r in rows))
# points within first 25% of t80
k=[]
for r in reach:
    pass
# group sizes
gs=collections.Counter(r[0] for r in rows); print('cells/group',collections.Counter(gs.values()))
# within-group t80 spread (log) for groups with >=3 reaching cells
spreads=[]
for g in gs:
    tt=[r[5] for r in reach if r[0]==g]
    if len(tt)>=3: spreads.append(np.std(np.log(tt),ddof=1))
print('within-condition sd log t80: n groups',len(spreads),'median',np.median(spreads),'p90',np.percentile(spreads,90))
tt_all=np.array([np.log(r[5]) for r in reach]); print('between all sd log t80',tt_all.std(ddof=1))
# how many cells with >=4 RPT points before 25% of their t80 ... weeks
cnt=0
for r in reach: pass
# example group shapes
import sys
for g in [1,5,9,12,26,45]:
    for r in rows:
        if r[0]==g and r[1]==1:
            print('G',g,'cond',cond[g],'npts',r[2],'last t',round(r[3],1),'ret',round(r[4],3),'t80',None if np.isnan(r[5]) else round(r[5],2))
