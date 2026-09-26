#include "openvq/advanced.h"
#include "test_support.h"

#include <algorithm>
#include <cmath>
#include <vector>

namespace {
constexpr double kPi = 3.14159265358979323846;

openvq::AudioBuffer SpeechLike(double seconds, double f0 = 173.0,
                               int sr = 48000) {
  openvq::AudioBuffer a;
  a.sample_rate = sr;
  a.samples.resize(static_cast<std::size_t>(seconds * sr));
  for (std::size_t i = 0; i < a.samples.size(); ++i) {
    const double t = static_cast<double>(i) / sr;
    const double syll =
        0.20 + 0.80 * std::pow(std::max(0.0, std::sin(2 * kPi * 2.13 * t)),
                               0.65);
    const double phrase =
        (std::fmod(t, 1.17) < 0.91) ? 1.0 : 0.035;
    const double s =
        0.23 * std::sin(2 * kPi * f0 * t + 0.13 * std::sin(2*kPi*.7*t)) +
        0.13 * std::sin(2 * kPi * (f0 * 3.11) * t) +
        0.07 * std::sin(2 * kPi * (f0 * 8.37) * t) +
        0.035 * std::sin(2 * kPi * 3670.0 * t);
    a.samples[i] = static_cast<float>(syll * phrase * s);
  }
  return a;
}

}  // namespace

int main() {
  openvq::AdvancedAnalyzer analyzer;
  const auto ref = SpeechLike(5.0);
  const auto clean = analyzer.Analyze(ref, ref);
  OPENVQ_REQUIRE(clean.mos > 4.4);
  OPENVQ_REQUIRE(std::abs(clean.base.delay_ms) <= 5.0);
  OPENVQ_REQUIRE(clean.base.active_coverage_fraction > 0.99);

  // Internal mute inside active speech must remain visible.
  auto muted = ref;
  const std::size_t mb = static_cast<std::size_t>(2.05 * ref.sample_rate);
  const std::size_t me = mb + static_cast<std::size_t>(0.24 * ref.sample_rate);
  std::fill(muted.samples.begin() + mb, muted.samples.begin() + me, 0.0f);
  const auto mute = analyzer.Analyze(ref, muted);
  OPENVQ_REQUIRE(mute.mos < clean.mos);
  OPENVQ_REQUIRE(
      mute.base.missing_disturbance > clean.base.missing_disturbance + 0.005 ||
      mute.advanced.choppiness_score > clean.advanced.choppiness_score + 0.005 ||
      mute.base.bad_section_fraction > clean.base.bad_section_fraction + 0.005);

  // Delete active material entirely. Bounded alignment must not warp the
  // deletion into a clean match.
  auto deleted = ref;
  const std::size_t db = static_cast<std::size_t>(2.00 * ref.sample_rate);
  const std::size_t de = db + static_cast<std::size_t>(0.14 * ref.sample_rate);
  deleted.samples.erase(deleted.samples.begin() + db,
                        deleted.samples.begin() + de);
  const auto deletion = analyzer.Analyze(ref, deleted);
  OPENVQ_REQUIRE(deletion.mos < clean.mos - 0.03);
  OPENVQ_REQUIRE(
      deletion.base.missing_disturbance > clean.base.missing_disturbance ||
      deletion.base.bad_section_fraction > clean.base.bad_section_fraction);

  // A different reference must not be treated as clean identity.
  const auto wrong = SpeechLike(5.0, 229.0);
  const auto mismatch = analyzer.Analyze(ref, wrong);
  OPENVQ_REQUIRE(mismatch.mos < clean.mos - 0.10);
  OPENVQ_REQUIRE(
      mismatch.advanced.multi_resolution_similarity <
      clean.advanced.multi_resolution_similarity - 0.01);

  return 0;
}
