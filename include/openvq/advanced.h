#pragma once

#include "openvq/openvq.h"

namespace openvq {

struct AdvancedDiagnostics {
  double erb_similarity = 0.0;
  double multi_resolution_similarity = 0.0;
  double temporal_envelope_similarity = 0.0;
  double modulation_similarity = 0.0;
  double asymmetric_disturbance = 0.0;
  double spectral_tilt_error = 0.0;
  double active_level_delta_db = 0.0;
  double bad_interval_severity = 0.0;
  // Correlated delayed residual after subtracting the direct path.
  double echo_score = 0.0;
  // Short gain-normalized speech holes and abrupt local envelope changes.
  double choppiness_score = 0.0;
  // Residual energy not explained by the direct path or detected echo.
  double residual_intrusion = 0.0;

  // Phase 5.1 richer evidence. These preserve temporal/event information that
  // the original 19-feature mapper discarded.
  double similarity_p10 = 0.0;
  double similarity_p50 = 0.0;
  double discontinuity_p90 = 0.0;
  double longest_bad_interval_ms = 0.0;
  double severe_frame_fraction = 0.0;
  double alignment_coverage = 0.0;
  double alignment_confidence = 0.0;
};

struct AdvancedAnalysisResult {
  AnalysisResult base;
  AdvancedDiagnostics advanced;
  double mos = 1.0;
  double confidence = 0.0;
  bool hybrid_applied = false;
  bool phase4_applied = false;
  bool phase4_experts_applied = false;
  std::optional<double> phase4_native_mos;
  std::optional<double> phase4_expert_disagreement;
  std::optional<double> visqol_speech_mos;
  std::optional<double> visqol_audio_mos;
};

class AdvancedAnalyzer {
 public:
  AdvancedAnalysisResult Analyze(const AudioBuffer& reference,
                                 const AudioBuffer& degraded,
                                 const AnalysisOptions& options = {}) const;
};

std::string ToJson(const AdvancedAnalysisResult& result);

}  // namespace openvq
