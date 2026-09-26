#include "openvq/phase4.h"

#include "phase4_model.inc"

#include <algorithm>
#include <array>
#include <cmath>
#include <vector>

namespace openvq {
namespace {

double Clamp01(double x) { return std::max(0.0, std::min(1.0, x)); }

std::array<double, 19> NativeFeatures(const AdvancedAnalysisResult& r) {
  const auto& b = r.base;
  const auto& q = r.advanced;
  return {{
      Clamp01((5.0 - b.mos) / 4.0),
      Clamp01(b.missing_disturbance),
      Clamp01(b.added_disturbance),
      Clamp01((5.0 - b.dimensions.coloration) / 4.0),
      Clamp01((5.0 - b.dimensions.noisiness) / 4.0),
      Clamp01((5.0 - b.dimensions.discontinuity) / 4.0),
      Clamp01((5.0 - b.dimensions.loudness) / 4.0),
      Clamp01(b.clipping_ratio * 40.0),
      Clamp01(b.bad_section_fraction),
      Clamp01(1.0 - q.multi_resolution_similarity),
      Clamp01(1.0 - q.temporal_envelope_similarity),
      Clamp01(1.0 - q.modulation_similarity),
      Clamp01(q.asymmetric_disturbance),
      Clamp01(q.spectral_tilt_error),
      Clamp01(q.active_level_delta_db / 18.0),
      Clamp01(q.bad_interval_severity),
      Clamp01(q.echo_score),
      Clamp01(q.choppiness_score),
      Clamp01(q.residual_intrusion),
  }};
}

std::array<double, 209> Basis(const std::array<double, 19>& x) {
  std::array<double, 209> out{};
  std::size_t k = 0;
  for (double v : x) out[k++] = v;
  for (std::size_t i = 0; i < x.size(); ++i) {
    for (std::size_t j = i; j < x.size(); ++j) {
      out[k++] = x[i] * x[j];
    }
  }
  return out;
}

double NativeQuality(const AdvancedAnalysisResult& r) {
  const auto z = Basis(NativeFeatures(r));
  double q = phase4_model::kIntercept;
  for (std::size_t i = 0; i < z.size(); ++i) {
    q += phase4_model::kWeights[i] *
         ((z[i] - phase4_model::kMean[i]) / phase4_model::kScale[i]);
  }
  return Clamp01(q);
}

double Median3(double a, double b, double c) {
  return a + b + c - std::min({a, b, c}) - std::max({a, b, c});
}

}  // namespace

Phase4Prediction EvaluatePhase4(
    const AdvancedAnalysisResult& result,
    const std::optional<double>& visqol_speech_mos,
    const std::optional<double>& visqol_audio_mos) {
  Phase4Prediction out;
  const double native_quality = NativeQuality(result);
  out.native_mos = 1.0 + 4.0 * native_quality;
  out.mos = out.native_mos;

  if (visqol_speech_mos.has_value() && visqol_audio_mos.has_value()) {
    const double speech_quality =
        Clamp01((*visqol_speech_mos - 1.0) / 4.0);
    const double audio_quality =
        Clamp01((*visqol_audio_mos - 1.0) / 4.0);
    const double consensus =
        Median3(native_quality, speech_quality, audio_quality);
    const double final_quality =
        (1.0 - phase4_model::kExpertBlend) * native_quality +
        phase4_model::kExpertBlend * consensus;
    out.mos = 1.0 + 4.0 * Clamp01(final_quality);
    out.experts_applied = true;
    out.expert_disagreement = std::abs(speech_quality - audio_quality);
  }
  return out;
}

const char* Phase4ModelId() { return phase4_model::kModelId; }

}  // namespace openvq
