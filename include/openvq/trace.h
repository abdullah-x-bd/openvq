#pragma once

#include "openvq/openvq.h"
#include <array>
#include <string>
#include <vector>

namespace openvq {

inline constexpr const char* kTraceSchemaId =
    "openvq-trace-v1-2026-09-26";

struct TraceFrame {
  double start_ms = 0.0;
  double mapped_start_ms = 0.0;
  bool reference_active = false;
  bool valid = false;
  bool unmatched = false;
  double alignment_confidence = 0.0;
  double local_similarity = 0.0;
  double reference_rms_db = -120.0;
  double degraded_rms_db = -120.0;
  std::array<double,64> reference_bands_db{};
  std::array<double,64> degraded_bands_db{};
};

struct TraceResult {
  std::string frontend_id;
  std::string trace_schema_id;
  int sample_rate = 0;
  int frame_ms = 20;
  int hop_ms = 10;
  double global_delay_ms = 0.0;
  double clock_drift_ppm = 0.0;
  double alignment_confidence = 0.0;
  double input_clipping_ratio = 0.0;
  std::vector<TraceFrame> frames;
};

class TraceAnalyzer {
 public:
  TraceResult Analyze(const AudioBuffer& reference,
                      const AudioBuffer& degraded,
                      const AnalysisOptions& options = {}) const;
};

std::string TraceToJson(const TraceResult& result);

}  // namespace openvq
