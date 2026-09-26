"""Phase 5.1 feature schemas shared by extraction and engineering tests."""

LEGACY19 = [
    "base","missing","added","coloration","noisiness","discontinuity","loudness",
    "clipping","bad_section","multi_resolution","temporal","modulation","asymmetry",
    "tilt","level","bad_interval","echo","choppiness","residual",
]

RICH_EXTRA = [
    "lost_active_speech",
    "active_coverage",
    "alignment_uncertainty",
    "active_level_delta_db_raw",
    "similarity_p10_loss",
    "similarity_p50_loss",
    "discontinuity_p90",
    "longest_bad_interval_ms",
    "severe_frame_fraction",
    "clock_drift_abs_ppm",
    "clipping_ratio_raw",
    "confidence_deficit",
]

RICH_V2 = LEGACY19 + RICH_EXTRA

def clamp(x,lo=0.0,hi=1.0):
    return max(lo,min(hi,float(x)))

def from_result(obj):
    d=obj["dimensions"]
    q=obj["advanced"]
    legacy={
        "base":clamp((5-float(obj["base_mos"]))/4),
        "missing":clamp(obj["missing_disturbance"]),
        "added":clamp(obj["added_disturbance"]),
        "coloration":clamp((5-float(d["coloration"]))/4),
        "noisiness":clamp((5-float(d["noisiness"]))/4),
        "discontinuity":clamp((5-float(d["discontinuity"]))/4),
        "loudness":clamp((5-float(d["loudness"]))/4),
        "clipping":clamp(float(obj["clipping_ratio"])*40),
        "bad_section":clamp(obj["bad_section_fraction"]),
        "multi_resolution":clamp(1-float(q["multi_resolution_similarity"])),
        "temporal":clamp(1-float(q["temporal_envelope_similarity"])),
        "modulation":clamp(1-float(q["modulation_similarity"])),
        "asymmetry":clamp(q["asymmetric_disturbance"]),
        "tilt":clamp(q["spectral_tilt_error"]),
        "level":clamp(float(q["active_level_delta_db"])/18),
        "bad_interval":clamp(q["bad_interval_severity"]),
        "echo":clamp(q.get("echo_score",0)),
        "choppiness":clamp(q.get("choppiness_score",0)),
        "residual":clamp(q.get("residual_intrusion",0)),
    }
    rich={
        "lost_active_speech":float(obj.get("lost_active_speech_fraction",0.0)),
        "active_coverage":float(obj.get("active_coverage_fraction",1.0)),
        "alignment_uncertainty":1.0-float(obj.get("alignment_confidence",1.0)),
        "active_level_delta_db_raw":float(q.get("active_level_delta_db",0.0)),
        "similarity_p10_loss":1.0-float(q.get("similarity_p10",1.0)),
        "similarity_p50_loss":1.0-float(q.get("similarity_p50",1.0)),
        "discontinuity_p90":float(q.get("discontinuity_p90",0.0)),
        "longest_bad_interval_ms":float(q.get("longest_bad_interval_ms",0.0)),
        "severe_frame_fraction":float(q.get("severe_frame_fraction",0.0)),
        "clock_drift_abs_ppm":abs(float(obj.get("clock_drift_ppm",0.0))),
        "clipping_ratio_raw":float(obj.get("clipping_ratio",0.0)),
        "confidence_deficit":1.0-float(obj.get("confidence",1.0)),
    }
    return {**legacy,**rich}
