#!/usr/bin/env python3
"""Phase 6.2E padding-safe learned-bands ablation.

This keeps the corrected Trace V2 data, training objective, optimizer, source
groups, early-stopping procedure, and seed set unchanged. The only model
change is padding-safe temporal processing:

- every convolutional stage masks padded frames before they can feed the next
  stage;
- BatchNorm1d is replaced with per-frame channel LayerNorm so normalization
  does not depend on batch composition or padded sequence length.
"""
import copy
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from phase6_train_sequence import (
    SeqDataset,collate,groupsplit,weights,run_epoch,predict,seed_all
)

MODE_LABEL="learned_bands_padding_safe"

class MaskedSharedEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.convs=nn.ModuleList([
            nn.Conv1d(64,32,3,padding=1),
            nn.Conv1d(32,64,3,padding=1),
            nn.Conv1d(64,128,3,padding=1),
        ])

    def forward(self,x,mask):
        z=x.transpose(1,2)
        m=mask[:,None,:]
        for conv in self.convs:
            z=torch.relu(conv(z))*m
        return z

class PaddingSafeTCN(nn.Module):
    def __init__(self,in_ch):
        super().__init__()
        self.inp=nn.Conv1d(in_ch,128,1)
        self.blocks=nn.ModuleList([
            nn.Conv1d(128,128,3,padding=d,dilation=d) for d in (1,2,4)
        ])
        self.norms=nn.ModuleList([nn.LayerNorm(128) for _ in range(3)])

    def forward(self,x,mask):
        m=mask[:,None,:]
        z=torch.relu(self.inp(x))*m
        for conv,norm in zip(self.blocks,self.norms):
            y=conv(z)
            y=norm(y.transpose(1,2)).transpose(1,2)
            z=torch.relu(y+z)*m
        return z

class PaddingSafeLearnedBands(nn.Module):
    def __init__(self,global_dim):
        super().__init__()
        self.enc=MaskedSharedEncoder()
        self.tcn=PaddingSafeTCN(128*4+8)
        self.head=nn.Sequential(
            nn.Linear(128+4,64),nn.ReLU(),nn.Linear(64,1)
        )

    def forward(self,ref,deg,ext,mask,glob):
        a=self.enc(ref,mask)
        b=self.enc(deg,mask)
        z=torch.cat([a,b,torch.abs(a-b),a*b,ext.transpose(1,2)],dim=1)
        z=self.tcn(z,mask)
        m=mask[:,None,:]
        pooled=(z*m).sum(-1)/m.sum(-1).clamp_min(1)

        active=ext[:,:,0]*mask
        unmatched=ext[:,:,2]*mask
        sim=ext[:,:,4]*mask
        denom=mask.sum(1).clamp_min(1)
        stats=torch.stack([
            active.sum(1)/denom,
            unmatched.sum(1)/denom,
            ((1-sim)*active).sum(1)/active.sum(1).clamp_min(1),
            (ext[:,:,3]*mask).sum(1)/denom,
        ],1)
        return self.head(torch.cat([pooled,stats],1)).squeeze(1)

@torch.no_grad()
def predict_padding_safe(model,rows,device,batch=16):
    loader=DataLoader(SeqDataset(rows),batch_size=batch,shuffle=False,collate_fn=collate)
    model.eval();out=[]
    for (ref,deg,ext,mask,glob,y),meta in loader:
        ref,deg,ext,mask,glob=[x.to(device) for x in (ref,deg,ext,mask,glob)]
        out.extend(model(ref,deg,ext,mask,glob).cpu().numpy().tolist())
    return np.asarray(out)

def fit_padding_safe(rows,seed,device,max_epochs=80):
    seed_all(seed)
    tr,va=groupsplit(rows,seed)
    train=[rows[i] for i in tr]
    valid=[rows[i] for i in va]
    gd=np.load(rows[0]["trace_path"])["global_features"].shape[0]

    model=PaddingSafeLearnedBands(gd).to(device)
    n=sum(p.numel() for p in model.parameters())
    if n>=1_000_000:
        raise RuntimeError(f"parameter budget exceeded: {n}")

    opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(train);wm={id(r):float(w) for r,w in zip(train,wr)}
    loader=DataLoader(SeqDataset(train),batch_size=16,shuffle=True,collate_fn=collate)

    best_rmse=1e9
    bad=0
    best_epoch=1
    for epoch in range(1,max_epochs+1):
        run_epoch(model,loader,opt,device,wm)
        pv=predict_padding_safe(model,valid,device)
        yy=np.asarray([float(r["target_normalized"]) for r in valid])
        vw=weights(valid)
        rmse=float(np.sqrt(np.average((pv-yy)**2,weights=vw)))
        if rmse<best_rmse-1e-5:
            best_rmse=rmse
            best_epoch=epoch
            bad=0
        else:
            bad+=1
            if bad>=12:
                break

    seed_all(seed)
    final=PaddingSafeLearnedBands(gd).to(device)
    opt=torch.optim.AdamW(final.parameters(),lr=1e-3,weight_decay=1e-4)
    wr=weights(rows);wm={id(r):float(w) for r,w in zip(rows,wr)}
    loader=DataLoader(SeqDataset(rows),batch_size=16,shuffle=True,collate_fn=collate)
    for _ in range(best_epoch):
        run_epoch(final,loader,opt,device,wm)

    return final,{
        "best_epoch":best_epoch,
        "parameters":n,
        "normalization":"per_frame_channel_layernorm",
        "padding_mask":"after_every_encoder_and_tcn_stage",
    }
