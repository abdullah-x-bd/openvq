#!/usr/bin/env python3
"""Export a Phase 6.2F padding-safe learned-bands model to ONNX."""
import argparse,json
import numpy as np
import torch
from phase62_padding_safe import PaddingSafeLearnedBands

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--state",required=True)
    ap.add_argument("--sample-trace",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    z=np.load(a.sample_trace)
    T=max(8,len(z["reference_bands_db"]))
    gdim=len(z["global_features"])
    model=PaddingSafeLearnedBands(gdim)
    model.load_state_dict(torch.load(a.state,map_location="cpu"))
    model.eval()
    ref=torch.zeros(1,T,64);deg=torch.zeros(1,T,64);ext=torch.zeros(1,T,8)
    mask=torch.ones(1,T);glob=torch.zeros(1,gdim)
    torch.onnx.export(
      model,(ref,deg,ext,mask,glob),a.output,
      input_names=["reference_bands","degraded_bands","frame_extras","mask","global_features"],
      output_names=["quality_raw"],opset_version=18,
      dynamic_axes={
        "reference_bands":{1:"time"},
        "degraded_bands":{1:"time"},
        "frame_extras":{1:"time"},
        "mask":{1:"time"},
      },
      do_constant_folding=True,
    )
    print(json.dumps({"mode":"learned_bands_padding_safe","output":a.output,"global_dim":gdim,"sample_frames":T}))
if __name__=="__main__":main()
