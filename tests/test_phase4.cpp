#include "openvq/phase4.h"
#include "test_support.h"

#include <cmath>
#include <iostream>

int main() {
  openvq::AdvancedAnalysisResult r;
  r.base.mos = 5.0 - 4.0 * 0.08379399999999992;
  r.base.missing_disturbance = 0.005692;
  r.base.added_disturbance = 0.193986;
  r.base.dimensions.coloration = 5.0 - 4.0 * 0.26143724999999995;
  r.base.dimensions.noisiness = 5.0 - 4.0 * 0.06789525000000007;
  r.base.dimensions.discontinuity = 5.0;
  r.base.dimensions.loudness = 5.0 - 4.0 * 0.0637144999999999;
  r.base.clipping_ratio = 0.0;
  r.base.bad_section_fraction = 0.0;
  r.advanced.multi_resolution_similarity = 1.0 - 0.03292200000000001;
  r.advanced.temporal_envelope_similarity = 1.0 - 0.004693999999999976;
  r.advanced.modulation_similarity = 1.0 - 0.0023330000000000295;
  r.advanced.asymmetric_disturbance = 0.193278;
  r.advanced.spectral_tilt_error = 0.067636;
  r.advanced.active_level_delta_db = 18.0 * 0.010526;
  r.advanced.bad_interval_severity = 0.120493;
  r.advanced.echo_score = 0.289701;
  r.advanced.choppiness_score = 0.041833;
  r.advanced.residual_intrusion = 0.083021;

  const auto native = openvq::EvaluatePhase4(r);
  OPENVQ_REQUIRE(!native.experts_applied);
  OPENVQ_REQUIRE(std::abs(native.native_mos - 1.3854801113025141) < 1e-10);
  OPENVQ_REQUIRE(std::abs(native.mos - native.native_mos) < 1e-12);

  const double speech_mos = 5.0 - 4.0 * 0.9013108025000001;
  const double audio_mos = 5.0 - 4.0 * 0.25548963;
  const auto hybrid =
      openvq::EvaluatePhase4(r, speech_mos, audio_mos);
  OPENVQ_REQUIRE(hybrid.experts_applied);
  OPENVQ_REQUIRE(std::abs(hybrid.mos - 1.3891907827815084) < 1e-10);
  OPENVQ_REQUIRE(std::abs(hybrid.expert_disagreement - 0.6458211725) < 1e-10);
  OPENVQ_REQUIRE(std::string(openvq::Phase4ModelId()) ==
         "phase4-native-poly2-constrained-2026-09-25-v3");

  std::cout << "Phase-4 candidate tests passed\n";
}
