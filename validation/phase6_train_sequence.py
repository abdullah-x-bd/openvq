#!/usr/bin/env python3
"""Phase 6E compact full-reference sequence experiments."""
import argparse,csv,json,copy,hashlib,math,random
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset,DataLoader

SEEDS=[20260926,20260927,20260928]
MODES=["native_temporal","learned_bands","hybrid"]
TRACE_SCHEMA="openvq-trace-v1-2026-09-26"

def seed_all(s):
    random.seed(s);np.random.seed(s);torch.manual_seed(s)
def ranks(v):
    v=np.asarray(v,float);o=np.argsort(v,kind="mergesort");r=np.empty(len(v));i=0
    while i<len(o):
        j=i+1
        while j<len(o) and v[o[j]]==v[o[i]]:j+=1
        r[o[i:j]]=(i+j-1)/2+1;i=j
    return r
def corr(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if len(a)<2 or np.std(a)<1e-12 or np.std(b)<1e-12:return 0.0
    return float(np.corrcoef(a,b)[0,1])
def metrics(y,p):
    y=np.asarray(y,float);raw=np.asarray(p,float);q=np.clip(raw,0,1);e=q-y
    return {"n":len(y),"pearson":corr(y,q),"spearman":corr(ranks(y),ranks(q)),
      "rmse_normalized":float(np.sqrt(np.mean(e*e))),"mae_normalized":float(np.mean(np.abs(e))),
      "bias_normalized":float(np.mean(e)),"floor_fraction":float(np.mean(q<=1e-6)),
      "ceiling_fraction":float(np.mean(q>=1-1e-6)),"near_floor_fraction":float(np.mean(q<=.05)),
      "near_ceiling_fraction":float(np.mean(q>=.95)),"raw_below_zero_fraction":float(np.mean(raw<0)),
      "raw_above_one_fraction":float(np.mean(raw>1))}
def objective(by):
    vals=[];r=[]
    for m in by.values():vals.extend([m["pearson"],m["spearman"]]);r.append(m["rmse_normalized"])
    return {"worst_correlation":float(min(vals)),"mean_correlation":float(np.mean(vals)),
            "worst_rmse_normalized":float(max(r))}

class SeqDataset(Dataset):
    def __init__(self,rows):self.rows=rows
    def __len__(self):return len(self.rows)
    def __getitem__(self,i):
        r=self.rows[i];z=np.load(r["trace_path"])
        ref=z["reference_bands_db"].astype("float32")
        deg=z["degraded_bands_db"].astype("float32")
        ext=z["frame_extras"].astype("float32")
        glob=z["global_features"].astype("float32")
        # Stable input ranges. Preserve silence/unmatched masks explicitly.
        ref=np.clip((ref+120.0)/140.0,0,1);deg=np.clip((deg+120.0)/140.0,0,1)
        ext=ext.copy()
        ext[:,5]=np.clip((ext[:,5]+120)/140,0,1)
        ext[:,6]=np.clip((ext[:,6]+120)/140,0,1)
        ext[:,7]=np.clip(ext[:,7]/500.0,-4,4)
        return ref,deg,ext,glob,float(r["target_normalized"]),r
def collate(batch):
    B=len(batch);T=max(x[0].shape[0] for x in batch)
    ref=np.zeros((B,T,64),np.float32);deg=np.zeros_like(ref);ext=np.zeros((B,T,8),np.float32)
    mask=np.zeros((B,T),np.float32);glob=np.zeros((B,batch[0][3].shape[0]),np.float32)
    y=np.zeros(B,np.float32);meta=[]
    for i,(r,d,e,g,q,m) in enumerate(batch):
        n=len(r);ref[i,:n]=r;deg[i,:n]=d;ext[i,:n]=e;mask[i,:n]=1;glob[i]=g;y[i]=q;meta.append(m)
    return tuple(torch.from_numpy(x) for x in (ref,deg,ext,mask,glob,y)),meta

class SharedEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(
          nn.Conv1d(64,32,3,padding=1),nn.ReLU(),
          nn.Conv1d(32,64,3,padding=1),nn.ReLU(),
          nn.Conv1d(64,128,3,padding=1),nn.ReLU())
    def forward(self,x):return self.net(x.transpose(1,2))
class TCN(nn.Module):
    def __init__(self,in_ch):
        super().__init__()
        self.inp=nn.Conv1d(in_ch,128,1)
        self.blocks=nn.ModuleList([
          nn.Conv1d(128,128,3,padding=d,dilation=d) for d in (1,2,4)])
        self.norms=nn.ModuleList([nn.BatchNorm1d(128) for _ in range(3)])
    def forward(self,x):
        z=torch.relu(self.inp(x))
        for conv,norm in zip(self.blocks,self.norms):
            z=torch.relu(norm(conv(z))+z)
        return z
class Model(nn.Module):
    def __init__(self,mode,global_dim):
        super().__init__();self.mode=mode
        if mode in ("learned_bands","hybrid"):
            self.enc=SharedEncoder();pair=128*4+8
        else:
            pair=8
        self.tcn=TCN(pair)
        head_in=128+4+(global_dim if mode=="hybrid" else 0)
        self.head=nn.Sequential(nn.Linear(head_in,64),nn.ReLU(),nn.Linear(64,1))
    def forward(self,ref,deg,ext,mask,glob):
        if self.mode in ("learned_bands","hybrid"):
            a=self.enc(ref);b=self.enc(deg)
            z=torch.cat([a,b,torch.abs(a-b),a*b,ext.transpose(1,2)],dim=1)
        else:
            z=ext.transpose(1,2)
        z=self.tcn(z);m=mask[:,None,:]
        pooled=(z*m).sum(-1)/m.sum(-1).clamp_min(1)
        # Explicit duration/tail facts remain visible after temporal pooling.
        active=ext[:,:,0]*mask;unmatched=ext[:,:,2]*mask;sim=ext[:,:,4]*mask
        denom=mask.sum(1).clamp_min(1)
        stats=torch.stack([
          active.sum(1)/denom,
          unmatched.sum(1)/denom,
          ((1-sim)*active).sum(1)/active.sum(1).clamp_min(1),
          (ext[:,:,3]*mask).sum(1)/denom,
        ],1)
        parts=[pooled,stats]
        if self.mode=="hybrid":parts.append(glob)
        return self.head(torch.cat(parts,1)).squeeze(1)

def groupsplit(rows,seed,val_frac=.15):
    tr=[];va=[]
    for d in sorted(set(r["dataset"] for r in rows)):
        groups=sorted(set(r["canonical_source_id"] for r in rows if r["dataset"]==d))
        rng=np.random.default_rng(seed+sum(map(ord,d)));rng.shuffle(groups)
        n=max(1,round(len(groups)*val_frac)) if len(groups)>2 else 1;vg=set(groups[:n])
        for i,r in enumerate(rows):
            if r["dataset"]==d:(va if r["canonical_source_id"] in vg else tr).append(i)
    return tr,va
def weights(rows):
    counts=defaultdict(int)
    for r in rows:counts[r["dataset"]]+=1
    w=np.asarray([1/counts[r["dataset"]] for r in rows],np.float32)
    return w/w.mean()
def run_epoch(model,loader,opt,device,row_weights=None):
    train=opt is not None;model.train(train);tot=0;den=0
    huber=nn.SmoothL1Loss(reduction="none",beta=.1)
    for (ref,deg,ext,mask,glob,y),meta in loader:
        ref,deg,ext,mask,glob,y=[x.to(device) for x in (ref,deg,ext,mask,glob,y)]
        pred=model(ref,deg,ext,mask,glob);loss=huber(pred,y)
        if row_weights is not None:
            ww=torch.tensor([row_weights[id(m)] for m in meta],device=device);loss=(loss*ww).sum()/ww.sum()
        else:loss=loss.mean()
        if train:opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
        tot+=float(loss.detach())*len(y);den+=len(y)
    return tot/max(1,den)
@torch.no_grad()
def predict(model,rows,device,batch=16):
    loader=DataLoader(SeqDataset(rows),batch_size=batch,shuffle=False,collate_fn=collate)
    model.eval();out=[]
    for (ref,deg,ext,mask,glob,y),meta in loader:
        ref,deg,ext,mask,glob=[x.to(device) for x in (ref,deg,ext,mask,glob)]
        out.extend(model(ref,deg,ext,mask,glob).cpu().numpy().tolist())
    return np.asarray(out)
def fit(rows,mode,seed,device,max_epochs=100):
    seed_all(seed);tr,va=groupsplit(rows,seed)
    train=[rows[i] for i in tr];valid=[rows[i] for i in va]
    gd=np.load(rows[0]["trace_path"])["global_features"].shape[0]
    model=Model(mode,gd).to(device)
    n=sum(p.numel() for p in model.parameters())
    if n>=1_000_000:raise RuntimeError(f"parameter budget exceeded: {n}")
    opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(train);wm={id(r):float(w) for r,w in zip(train,wr)}
    loader=DataLoader(SeqDataset(train),batch_size=16,shuffle=True,collate_fn=collate)
    best=None;best_rmse=1e9;bad=0;best_epoch=1
    for epoch in range(1,max_epochs+1):
        run_epoch(model,loader,opt,device,wm)
        pv=predict(model,valid,device);yy=np.asarray([float(r["target_normalized"]) for r in valid])
        # corpus-balanced validation RMSE
        vw=weights(valid);rmse=float(np.sqrt(np.average((pv-yy)**2,weights=vw)))
        if rmse<best_rmse-1e-5:
            best_rmse=rmse;best=copy.deepcopy(model.state_dict());best_epoch=epoch;bad=0
        else:
            bad+=1
            if bad>=12:break
    # Refit from scratch on every allowed row for the selected epoch count.
    # The validation groups select training duration but are not discarded from
    # the final outer-fold fit.
    seed_all(seed)
    final=Model(mode,gd).to(device)
    opt=torch.optim.AdamW(final.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(rows);wm={id(r):float(w) for r,w in zip(rows,wr)}
    loader=DataLoader(SeqDataset(rows),batch_size=16,shuffle=True,collate_fn=collate)
    for _ in range(best_epoch):
        run_epoch(final,loader,opt,device,wm)
    return final,{"best_epoch":best_epoch,"parameters":n}
def evaluate_mode(rows,mode,device):
    by_held={};all_pred=[];all_y=[];all_ds=[]
    for held in sorted(set(r["dataset"] for r in rows)):
        tr=[r for r in rows if r["dataset"]!=held];te=[r for r in rows if r["dataset"]==held]
        pp=[];fitinfo=[]
        for seed in SEEDS:
            m,info=fit(tr,mode,seed,device);pp.append(predict(m,te,device));fitinfo.append(info)
        pred=np.mean(pp,axis=0);yy=np.asarray([float(r["target_normalized"]) for r in te])
        by_held[held]={"test":metrics(yy,pred),"fit_info":fitinfo}
        all_pred.extend(pred);all_y.extend(yy);all_ds.extend([held]*len(te))
    vals=[min(v["test"]["pearson"],v["test"]["spearman"]) for v in by_held.values()]
    return {"by_held_corpus":by_held,"worst_held_corpus_correlation":float(min(vals)),
            "mean_held_corpus_correlation":float(np.mean(vals))}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sequences");ap.add_argument("outdir")
    ap.add_argument("--device",default="cpu");ap.add_argument("--max-epochs",type=int,default=100)
    a=ap.parse_args();rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    if any(r["trace_schema_id"]!=TRACE_SCHEMA for r in rows):raise SystemExit("trace schema mismatch")
    outdir=Path(a.outdir);outdir.mkdir(parents=True,exist_ok=True);device=torch.device(a.device)
    reports={}
    for mode in MODES:
        print("evaluating",mode,flush=True)
        reports[mode]=evaluate_mode(rows,mode,device)
    selected=max(MODES,key=lambda m:(reports[m]["worst_held_corpus_correlation"],
                                    reports[m]["mean_held_corpus_correlation"]))
    # Fit final selected candidate on all development evidence for each seed.
    states=[];infos=[]
    for seed in SEEDS:
        m,info=fit(rows,selected,seed,device,a.max_epochs)
        p=outdir/f"{selected}-seed{seed}.pt";torch.save(m.state_dict(),p);states.append(str(p));infos.append(info)
    result={"experiment_id":"phase6e-sequence-v1","seeds":SEEDS,"modes":reports,
            "selected_mode":selected,"selected_state_files":states,"selected_fit_info":infos,
            "selection_rule":"maximize worst leave-corpus-out Pearson/Spearman, then mean held-corpus correlation",
            "status":"development candidate only; URGENT remains untouched"}
    (outdir/"phase6e-report.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
