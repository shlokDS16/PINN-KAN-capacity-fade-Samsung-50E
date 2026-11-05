import os,sys,importlib.util,numpy as np,torch
sys.path.insert(0,r"C:\Users\Shlok\Downloads\PINN KAN battery paper\code\prereg"); sys.path.insert(0,r"C:\Users\Shlok\Downloads\PINN KAN battery paper\code")
import d022_kan_study as K
from pinnkan import synth, data as D, arms as A, symbolic
from pinnkan.law import batch_from_cells
from pinnkan.hard import make_law
from pinnkan.pinn import fit_pinn
S=K.SPEC
for init in (-4.0,-2.0,-1.0,0.0):
  tot=[]
  for seed in (0,1):
    S0=synth.make_synthetic("G0",n_cyc_cond=40,n_sto_cond=8,reps=2,seed=seed)
    tr,te=synth.split_conditions(S0.cells,0.2,seed)
    b=batch_from_cells(S,tr); cyc=(b.is_cyc>0.5).numpy(); s_cyc=np.unique(b.s.numpy()[cyc],axis=0)
    geos=symbolic.stress_geos(S,s_cyc)
    raw=K.probe_rows(tr,seed=seed); ty=np.asarray(S0.log_rate_cyc(raw),float).ravel(); r=float(np.ptp(ty))
    hp={**A.default_hp("G15"),"sparsity":0.0}; hpm=dict(hp,map="gam")
    torch.manual_seed(seed); law=make_law(S,b,hpm,"self_limiting")
    vm=K.VariantMap(S.d,None,int(hp["grid"]),True,False,geos,s_cyc,hp["l2"])
    with torch.no_grad():
        for i in range(S.d):
            if float(vm.layers[0].signs[i])!=0:
                vm.layers[0].base_w[:,i]=init; vm.layers[0].spline_w[:,i,:]=init
    law.cyc=vm
    m=fit_pinn(b,S,hpm,"self_limiting",seed,steps=2000,law=law)
    tot.append(K.law_err(m.law.cyc,raw,ty,r))
  print("init",init,"E_par G0 m32 GAM-mono",np.round(tot,3),flush=True)
