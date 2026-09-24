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
};

struct AdvancedAnalysisResult {
  AnalysisResult base;
  AdvancedDiagnostics advanced;
  double mos = 1.0;
  double confidence = 0.0;
};

class AdvancedAnalyzer {
 public:
  AdvancedAnalysisResult Analyze(const AudioBuffer& reference,
                                 const AudioBuffer& degraded,
                                 const AnalysisOptions& options = {}) const;
};

std::string ToJson(const AdvancedAnalysisResult& result);

}  // namespace openvq
