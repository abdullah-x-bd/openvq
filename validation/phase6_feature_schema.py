"""Phase 6 feature schema.

rich_v2 remains frozen for Phase 5.1 reproduction. Phase 6 adds raw input
clipping as a new field and therefore uses a new schema ID rather than silently
changing rich_v2 semantics.
"""
from phase51_feature_schema import LEGACY19, RICH_V2, from_result as from_phase51

FRONTEND_ID = "openvq-frontend-phase6a-2026-09-26-v1"
SCHEMA_ID = "openvq-rich-v3-2026-09-26-v1"
RICH_V3 = list(RICH_V2) + ["input_clipping_ratio_raw"]

def from_result(obj):
    out = dict(from_phase51(obj))
    out["input_clipping_ratio_raw"] = float(
        obj.get("input_clipping_ratio", obj.get("clipping_ratio", 0.0))
    )
    return out
