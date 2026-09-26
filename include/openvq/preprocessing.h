#pragma once

#include "openvq/openvq.h"

#include <cstddef>
#include <vector>

namespace openvq {

struct AlignmentKnot {
  double reference_sample = 0.0;
  double degraded_sample = 0.0;
  double confidence = 0.0;
};

struct AlignmentMap {
  int sample_rate = 0;
  double global_delay_samples = 0.0;
  double clock_drift_ppm = 0.0;
  double mean_confidence = 0.0;
  std::vector<AlignmentKnot> knots;

  double MapReferenceSample(double reference_sample) const;
  bool Covers(double reference_sample, std::size_t frame_samples,
              std::size_t degraded_size) const;
};

struct PreparedPair {
  int sample_rate = 0;
  std::vector<float> reference;
  std::vector<float> degraded;
  AlignmentMap alignment;
};

struct ActiveLevelStats {
  double reference_db = -120.0;
  double degraded_db = -120.0;
  double delta_db = 0.0;
  double active_coverage_fraction = 0.0;
  double lost_active_speech_fraction = 0.0;
  std::size_t active_frames = 0;
  std::size_t covered_active_frames = 0;
};

PreparedPair PreparePair(const AudioBuffer& reference,
                         const AudioBuffer& degraded,
                         const AnalysisOptions& options);

ActiveLevelStats MeasureMatchedActiveLevel(
    const PreparedPair& pair,
    int frame_ms,
    int hop_ms,
    double vad_relative_db);

float SampleAlignedDegraded(const PreparedPair& pair,
                            double reference_sample);

}  // namespace openvq
