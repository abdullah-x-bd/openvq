#!/usr/bin/env python3
"""Phase 6.2G padding-safe model with a separate clipping-order property constraint."""
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from phase6_train_sequence import SeqDataset,collate,groupsplit,weights,seed_all
from phase62_padding_safe import PaddingSafeLearnedBands,predict_padding_safe

MODE_LABEL="learned_bands_padding_safe_clipreg"
PROPERTY_LAMBDA=0.25
PROPERTY_MARGIN_RAW=0.03
PROPERTY_INTERVAL=4

def property_batch(rows):
    loader=DataLoader(SeqDataset(rows),batch_size=len(rows),shuffle=False,collate_fn=collate)
    return next(iter(loader))

def clipping_property_loss(model,batch,device):
    (ref,deg,ext,mask,glob,y),meta=batch
    ref,deg,ext,mask,glob=[x.to(device) for x in (ref,deg,ext,mask,glob)]
    pred=model(ref,deg,ext,mask,glob)
    by={}
    for i,r in enumerate(meta):
        by.setdefault(r["canonical_source_id"],[]).append((float(r["level"]),i))
    losses=[]
    for items in by.values():
        items=sorted(items)
        for (_,i),(_,j) in zip(items,items[1:]):
            losses.append(torch.relu(pred[j]-pred[i]+PROPERTY_MARGIN_RAW))
    if not losses:
        raise RuntimeError("no clipping property pairs")
    return torch.stack(losses).mean()

def run_epoch_with_property(model,loader,opt,device,row_weights,constraint_batch):
    model.train(True)
    huber=nn.SmoothL1Loss(reduction="none",beta=.1)
    total=0.0;den=0
    for step,((ref,deg,ext,mask,glob,y),meta) in enumerate(loader):
        ref,deg,ext,mask,glob,y=[x.to(device) for x in (ref,deg,ext,mask,glob,y)]
        pred=model(ref,deg,ext,mask,glob)
        loss=huber(pred,y)
        ww=torch.tensor([row_weights[id(m)] for m in meta],device=device)
        human=(loss*ww).sum()/ww.sum()
        total_loss=human
        if step%PROPERTY_INTERVAL==0:
            total_loss=total_loss+PROPERTY_LAMBDA*clipping_property_loss(
                model,constraint_batch,device)
        opt.zero_grad();total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),5)
        opt.step()
        total+=float(human.detach())*len(y);den+=len(y)
    return total/max(1,den)

@torch.no_grad()
def property_report(model,rows,device):
    pred=predict_padding_safe(model,rows,device,batch=len(rows))
    by={}
    for r,p in zip(rows,pred):
        by.setdefault(r["canonical_source_id"],[]).append((float(r["level"]),float(p),r["label"]))
    pairs=[];violations=0
    for source,items in sorted(by.items()):
        items=sorted(items)
        for (la,pa,aa),(lb,pb,bb) in zip(items,items[1:]):
            hinge=max(0.0,pb-pa+PROPERTY_MARGIN_RAW)
            if hinge>1e-8:violations+=1
            pairs.append({"source":source,"mild":aa,"severe":bb,
                          "mild_prediction":pa,"severe_prediction":pb,
                          "margin_hinge":hinge})
    return {"margin_raw":PROPERTY_MARGIN_RAW,"pairs":len(pairs),
            "margin_violations":violations,
            "max_margin_hinge":max((x["margin_hinge"] for x in pairs),default=0.0)}

def fit_clipping_regularized(rows,constraint_rows,seed,device,max_epochs=80):
    seed_all(seed)
    tr,va=groupsplit(rows,seed)
    train=[rows[i] for i in tr];valid=[rows[i] for i in va]
    gd=np.load(rows[0]["trace_path"])["global_features"].shape[0]
    model=PaddingSafeLearnedBands(gd).to(device)
    n=sum(p.numel() for p in model.parameters())
    if n>=1_000_000:raise RuntimeError(f"parameter budget exceeded: {n}")
    cb=property_batch(constraint_rows)
    opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(train);wm={id(r):float(w) for r,w in zip(train,wr)}
    loader=DataLoader(SeqDataset(train),batch_size=16,shuffle=True,collate_fn=collate)
    best_rmse=1e9;bad=0;best_epoch=1
    for epoch in range(1,max_epochs+1):
        run_epoch_with_property(model,loader,opt,device,wm,cb)
        pv=predict_padding_safe(model,valid,device)
        yy=np.asarray([float(r["target_normalized"]) for r in valid])
        vw=weights(valid)
        rmse=float(np.sqrt(np.average((pv-yy)**2,weights=vw)))
        if rmse<best_rmse-1e-5:
            best_rmse=rmse;best_epoch=epoch;bad=0
        else:
            bad+=1
            if bad>=12:break
    seed_all(seed)
    final=PaddingSafeLearnedBands(gd).to(device)
    opt=torch.optim.AdamW(final.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(rows);wm={id(r):float(w) for r,w in zip(rows,wr)}
    loader=DataLoader(SeqDataset(rows),batch_size=16,shuffle=True,collate_fn=collate)
    for _ in range(best_epoch):
        run_epoch_with_property(final,loader,opt,device,wm,cb)
    return final,{
      "best_epoch":best_epoch,
      "parameters":n,
      "normalization":"per_frame_channel_layernorm",
      "padding_mask":"after_every_encoder_and_tcn_stage",
      "property":"clipping_order_only",
      "property_lambda":PROPERTY_LAMBDA,
      "property_margin_raw":PROPERTY_MARGIN_RAW,
      "property_margin_mos":PROPERTY_MARGIN_RAW*4,
      "property_interval_human_batches":PROPERTY_INTERVAL,
      "property_fixture_rows":len(constraint_rows),
      "property_report":property_report(final,constraint_rows,device),
      "early_stopping_metric":"human_only_corpus_balanced_validation_rmse",
    }
