#!/usr/bin/env python3
"""Phase 6.3B-R1 model: Phase 6.2G architecture plus identity/invariance constraints."""
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from phase6_train_sequence import SeqDataset,collate,groupsplit,weights,seed_all
from phase62_padding_safe import PaddingSafeLearnedBands,predict_padding_safe

MODE_LABEL="learned_bands_padding_safe_clipreg_identityinv_v3"
CLIP_LAMBDA=0.25
CLIP_MARGIN_RAW=0.03
IDENTITY_LAMBDA=0.50
IDENTITY_FLOOR_RAW=0.85
INVARIANCE_LAMBDA=0.25
INVARIANCE_MARGIN_RAW=0.05
PROPERTY_INTERVAL=4

def batch_all(rows):
    if not rows:return None
    return next(iter(DataLoader(SeqDataset(rows),batch_size=len(rows),shuffle=False,collate_fn=collate)))

def _pred(model,batch,device):
    (ref,deg,ext,mask,glob,y),meta=batch
    ref,deg,ext,mask,glob=[x.to(device) for x in (ref,deg,ext,mask,glob)]
    return model(ref,deg,ext,mask,glob),meta

def clipping_loss(model,batch,device):
    pred,meta=_pred(model,batch,device);by={}
    for i,r in enumerate(meta):by.setdefault(r["canonical_source_id"],[]).append((float(r["level"]),i))
    losses=[]
    for items in by.values():
        items=sorted(items)
        for (_,i),(_,j) in zip(items,items[1:]):losses.append(torch.relu(pred[j]-pred[i]+CLIP_MARGIN_RAW))
    if not losses:raise RuntimeError("no clipping pairs")
    return torch.stack(losses).mean()

def identity_invariance_loss(model,batch,device):
    pred,meta=_pred(model,batch,device);by={}
    for i,r in enumerate(meta):by.setdefault(r["canonical_source_id"],[]).append((r,i))
    ids=[];invs=[]
    for source,items in by.items():
        ii=[i for r,i in items if r.get("property_kind")=="identity"]
        if len(ii)!=1:raise RuntimeError(f"{source}: expected one identity row")
        qi=pred[ii[0]];ids.append(torch.relu(torch.as_tensor(IDENTITY_FLOOR_RAW,device=device)-qi))
        for r,i in items:
            if r.get("property_kind")=="invariance":invs.append(torch.relu(torch.abs(pred[i]-qi)-INVARIANCE_MARGIN_RAW))
    if not ids or not invs:raise RuntimeError("missing identity/invariance constraints")
    return torch.stack(ids).mean(),torch.stack(invs).mean()

def run_epoch(model,loader,opt,device,row_weights,clip_batch,inv_batch):
    model.train(True);huber=nn.SmoothL1Loss(reduction="none",beta=.1);total=0.;den=0
    for step,((ref,deg,ext,mask,glob,y),meta) in enumerate(loader):
        ref,deg,ext,mask,glob,y=[x.to(device) for x in (ref,deg,ext,mask,glob,y)]
        pred=model(ref,deg,ext,mask,glob);loss=huber(pred,y)
        ww=torch.tensor([row_weights[id(m)] for m in meta],device=device);human=(loss*ww).sum()/ww.sum();objective=human
        if step%PROPERTY_INTERVAL==0:
            objective=objective+CLIP_LAMBDA*clipping_loss(model,clip_batch,device)
            li,lv=identity_invariance_loss(model,inv_batch,device)
            objective=objective+IDENTITY_LAMBDA*li+INVARIANCE_LAMBDA*lv
        opt.zero_grad();objective.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
        total+=float(human.detach())*len(y);den+=len(y)
    return total/max(1,den)

@torch.no_grad()
def property_report(model,clip_rows,inv_rows,device):
    cp=predict_padding_safe(model,clip_rows,device,batch=len(clip_rows));by={}
    for r,p in zip(clip_rows,cp):by.setdefault(r["canonical_source_id"],[]).append((float(r["level"]),float(p),r["label"]))
    clip_pairs=[];clip_viol=0
    for source,items in sorted(by.items()):
        s=sorted(items)
        for (_,pa,aa),(_,pb,bb) in zip(s,s[1:]):
            h=max(0.,pb-pa+CLIP_MARGIN_RAW);clip_viol+=h>1e-8;clip_pairs.append({"source":source,"mild":aa,"severe":bb,"hinge":h})
    ip=predict_padding_safe(model,inv_rows,device,batch=len(inv_rows));by={}
    for r,p in zip(inv_rows,ip):by.setdefault(r["canonical_source_id"],[]).append((r,float(p)))
    ids=[];invs=[]
    for source,items in sorted(by.items()):
        identity=[p for r,p in items if r.get("property_kind")=="identity"]
        if len(identity)!=1:continue
        qi=identity[0];ids.append({"source":source,"quality_raw":qi,"shortfall":max(0.,IDENTITY_FLOOR_RAW-qi)})
        for r,p in items:
            if r.get("property_kind")=="invariance":
                delta=abs(p-qi);invs.append({"source":source,"label":r["label"],"abs_raw_delta":delta,
                  "excess":max(0.,delta-INVARIANCE_MARGIN_RAW)})
    return {"clipping":{"pairs":len(clip_pairs),"margin_violations":int(clip_viol),"max_hinge":max((x["hinge"] for x in clip_pairs),default=0.)},
      "identity":{"cases":len(ids),"violations":sum(x["shortfall"]>1e-8 for x in ids),"min_quality_raw":min((x["quality_raw"] for x in ids),default=None)},
      "invariance":{"cases":len(invs),"violations":sum(x["excess"]>1e-8 for x in invs),"max_abs_raw_delta":max((x["abs_raw_delta"] for x in invs),default=None)}}

def fit_repaired(rows,clip_rows,inv_rows,seed,device,max_epochs=80):
    if not clip_rows or not inv_rows:raise RuntimeError("property rows required")
    seed_all(seed);tr,va=groupsplit(rows,seed);train=[rows[i] for i in tr];valid=[rows[i] for i in va]
    gd=np.load(rows[0]["trace_path"])["global_features"].shape[0];model=PaddingSafeLearnedBands(gd).to(device)
    n=sum(p.numel() for p in model.parameters())
    if n>=1_000_000:raise RuntimeError(f"parameter budget exceeded {n}")
    cb=batch_all(clip_rows);ib=batch_all(inv_rows);opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(train);wm={id(r):float(w) for r,w in zip(train,wr)}
    loader=DataLoader(SeqDataset(train),batch_size=16,shuffle=True,collate_fn=collate)
    best_rmse=1e9;bad=0;best_epoch=1
    for epoch in range(1,max_epochs+1):
        run_epoch(model,loader,opt,device,wm,cb,ib)
        pv=predict_padding_safe(model,valid,device);yy=np.asarray([float(r["target_normalized"]) for r in valid]);vw=weights(valid)
        rmse=float(np.sqrt(np.average((pv-yy)**2,weights=vw)))
        if rmse<best_rmse-1e-5:best_rmse=rmse;best_epoch=epoch;bad=0
        else:
            bad+=1
            if bad>=12:break
    seed_all(seed);final=PaddingSafeLearnedBands(gd).to(device);opt=torch.optim.AdamW(final.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(rows);wm={id(r):float(w) for r,w in zip(rows,wr)};loader=DataLoader(SeqDataset(rows),batch_size=16,shuffle=True,collate_fn=collate)
    for _ in range(best_epoch):run_epoch(final,loader,opt,device,wm,cb,ib)
    return final,{"best_epoch":best_epoch,"parameters":n,"normalization":"per_frame_channel_layernorm",
      "padding_mask":"after_every_encoder_and_tcn_stage","clip_lambda":CLIP_LAMBDA,"clip_margin_raw":CLIP_MARGIN_RAW,
      "identity_lambda":IDENTITY_LAMBDA,"identity_floor_raw":IDENTITY_FLOOR_RAW,
      "invariance_lambda":INVARIANCE_LAMBDA,"invariance_margin_raw":INVARIANCE_MARGIN_RAW,
      "property_interval_human_batches":PROPERTY_INTERVAL,"property_report":property_report(final,clip_rows,inv_rows,device),
      "early_stopping_metric":"human_only_corpus_balanced_validation_rmse"}
