#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace openvq {

enum class BandwidthClass {
  kNarrowband,
  kWideband,
  kSuperWideband,
  kFullband,
  kUnknown,
};

enum class EventType {
  kDropout,
  kClipping,
  kNoiseBurst,
  kTimeWarp,
};

struct AudioBuffer {
  int sample_rate = 0;
  std::vector<float> samples;
};

struct QualityDimensions {
  double coloration = 1.0;
  double noisiness = 1.0;
  double discontinuity = 1.0;
  double loudness = 1.0;
};

struct QualityEvent {
  EventType type = EventType::kDropout;
  double start_ms = 0.0;
  double duration_ms = 0.0;
  double severity = 0.0;
};

struct FrameQuality {
  double start_ms = 0.0;
  double similarity = 0.0;
  double missing_disturbance = 0.0;
  double added_disturbance = 0.0;
  double discontinuity = 0.0;
};

struct Calibration {
  double bias = 0.02;
  double missing_weight = 1.05;
  double added_weight = 0.68;
  double coloration_weight = 0.45;
  double noisiness_weight = 0.55;
  double discontinuity_weight = 0.95;
  double loudness_weight = 0.35;
  double clipping_weight = 0.65;
  double bad_section_weight = 0.80;
  // Penalty in MOS points for normalized ViSQOL degradation (5 - MOS) / 4.
  double visqol_penalty_weight = 1.00;

  // Final advanced fusion. These defaults reproduce the bootstrap 58/42
  // base-to-advanced blend, but every value can be fitted to human MOS.
  double final_bias = 0.0;
  double base_penalty_weight = 0.58;
  double advanced_multi_resolution_weight = 0.3864;
  double advanced_temporal_weight = 0.2688;
  double advanced_modulation_weight = 0.1680;
  double advanced_asymmetry_weight = 0.3192;
  double advanced_tilt_weight = 0.1344;
  double advanced_level_weight = 0.1680;
  double advanced_bad_interval_weight = 0.2352;
  double advanced_echo_weight = 0.0;
  double advanced_residual_weight = 0.0;
  double advanced_temporal_edit_weight = 0.0;
  double advanced_clip_plateau_weight = 0.0;
  double advanced_inactive_noise_weight = 0.0;
};

struct AnalysisOptions {
  int target_sample_rate = 48000;
  int frame_ms = 20;
  int hop_ms = 10;
  int max_delay_ms = 1500;
  double vad_relative_db = -36.0;
  bool enable_local_alignment = true;
  std::optional<double> visqol_mos;
  Calibration calibration;
};

struct AnalysisResult {
  double mos = 1.0;
  double confidence = 0.0;
  BandwidthClass bandwidth = BandwidthClass::kUnknown;
  double delay_ms = 0.0;
  double clock_drift_ppm = 0.0;
  double active_speech_seconds = 0.0;
  double clipping_ratio = 0.0;
  double missing_disturbance = 0.0;
  double added_disturbance = 0.0;
  double bad_section_fraction = 0.0;
  QualityDimensions dimensions;
  std::vector<QualityEvent> events;
  std::vector<FrameQuality> frames;
};

class Analyzer {
 public:
  AnalysisResult Analyze(const AudioBuffer& reference,
                         const AudioBuffer& degraded,
                         const AnalysisOptions& options = {}) const;
};

AudioBuffer LoadWav(const std::string& path);
Calibration LoadCalibration(const std::string& path);
std::string ToString(BandwidthClass bandwidth);
std::string ToString(EventType type);
std::string ToJson(const AnalysisResult& result);

}  // namespace openvq
