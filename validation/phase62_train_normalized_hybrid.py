#!/usr/bin/env python3
"""Phase 6.2D fold-fitted global normalization ablation for hybrid only."""
import copy
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader

from phase6_train_sequence import (
    Model,SeqDataset,collate,groupsplit,weights,run_epoch,seed_all,metrics,
    validate_trace_rows
)

MODE_LABEL="hybrid_global_zscore"
BASE_MODE="hybrid"

class NormalizedSeqDataset(SeqDataset):
    def __init__(self,rows,mean,std):
        super().__init__(rows)
        self.mean=np.asarray(mean,np.float32)
        self.std=np.asarray(std,np.float32)
    def __getitem__(self,i):
        ref,deg,ext,glob,y,r=super().__getitem__(i)
        glob=(glob-self.mean)/self.std
        return ref,deg,ext,glob,y,r

def fit_global_normalizer(rows):
    g=np.stack([np.load(r["trace_path"])["global_features"].astype(np.float64) for r in rows])
    mean=g.mean(axis=0)
    std=g.std(axis=0)
    std=np.where(std<1e-6,1.0,std)
    return mean.astype(np.float32),std.astype(np.float32)

@torch.no_grad()
def predict_normalized(model,rows,device,mean,std,batch=16):
    loader=DataLoader(NormalizedSeqDataset(rows,mean,std),batch_size=batch,shuffle=False,collate_fn=collate)
    model.eval();out=[]
    for (ref,deg,ext,mask,glob,y),meta in loader:
        ref,deg,ext,mask,glob=[x.to(device) for x in (ref,deg,ext,mask,glob)]
        out.extend(model(ref,deg,ext,mask,glob).cpu().numpy().tolist())
    return np.asarray(out)

def run_epoch_normalized(model,loader,opt,device,row_weights=None):
    train=opt is not None
    model.train(train);tot=0;den=0
    huber=torch.nn.SmoothL1Loss(reduction="none",beta=.1)
    for (ref,deg,ext,mask,glob,y),meta in loader:
        ref,deg,ext,mask,glob,y=[x.to(device) for x in (ref,deg,ext,mask,glob,y)]
        pred=model(ref,deg,ext,mask,glob);loss=huber(pred,y)
        if row_weights is not None:
            ww=torch.tensor([row_weights[id(m)] for m in meta],device=device)
            loss=(loss*ww).sum()/ww.sum()
        else:
            loss=loss.mean()
        if train:
            opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
        tot+=float(loss.detach())*len(y);den+=len(y)
    return tot/max(1,den)

def fit_normalized_hybrid(rows,seed,device,max_epochs=80):
    seed_all(seed)
    tr,va=groupsplit(rows,seed)
    train=[rows[i] for i in tr];valid=[rows[i] for i in va]

    # Internal early-stopping preprocessing is fitted on the internal training
    # groups only. Validation rows do not contribute to the normalizer.
    mean,std=fit_global_normalizer(train)
    gd=len(mean)
    model=Model(BASE_MODE,gd).to(device)
    n=sum(p.numel() for p in model.parameters())
    if n>=1_000_000:raise RuntimeError(f"parameter budget exceeded: {n}")
    opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(train);wm={id(r):float(w) for r,w in zip(train,wr)}
    loader=DataLoader(NormalizedSeqDataset(train,mean,std),batch_size=16,shuffle=True,collate_fn=collate)

    best_rmse=1e9;bad=0;best_epoch=1
    for epoch in range(1,max_epochs+1):
        run_epoch_normalized(model,loader,opt,device,wm)
        pv=predict_normalized(model,valid,device,mean,std)
        yy=np.asarray([float(r["target_normalized"]) for r in valid])
        vw=weights(valid)
        rmse=float(np.sqrt(np.average((pv-yy)**2,weights=vw)))
        if rmse<best_rmse-1e-5:
            best_rmse=rmse;best_epoch=epoch;bad=0
        else:
            bad+=1
            if bad>=12:break

    # Final outer-fold fit uses every allowed outer-training row. The held
    # corpus never contributes to these statistics.
    final_mean,final_std=fit_global_normalizer(rows)
    seed_all(seed)
    final=Model(BASE_MODE,gd).to(device)
    opt=torch.optim.AdamW(final.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(rows);wm={id(r):float(w) for r,w in zip(rows,wr)}
    loader=DataLoader(NormalizedSeqDataset(rows,final_mean,final_std),batch_size=16,shuffle=True,collate_fn=collate)
    for _ in range(best_epoch):
        run_epoch_normalized(final,loader,opt,device,wm)

    info={
      "best_epoch":best_epoch,
      "parameters":n,
      "normalization":"fold_fitted_zscore",
      "early_normalizer_fit_rows":len(train),
      "final_normalizer_fit_rows":len(rows),
      "global_mean":[float(x) for x in final_mean],
      "global_std":[float(x) for x in final_std],
    }
    return final,info,final_mean,final_std
