"""Phase 6.3 feature schema bound to the versioned transport-padding frontend."""
from phase51_feature_schema import RICH_V2, from_result as from_phase51

FRONTEND_ID = "openvq-frontend-phase63b-2026-09-29-v1"
SCHEMA_ID = "openvq-rich-v4-2026-09-29-v1"
RICH_V4 = list(RICH_V2) + ["input_clipping_ratio_raw"]

def from_result(obj):
    out=dict(from_phase51(obj))
    out["input_clipping_ratio_raw"]=float(
        obj.get("input_clipping_ratio",obj.get("clipping_ratio",0.0)))
    return out
