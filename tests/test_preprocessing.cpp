#include "openvq/preprocessing.h"

#include <cmath>
#include <cstdlib>
#include <iostream>

namespace {

openvq::AudioBuffer MakeSpeechLike(int sr, double seconds) {
  openvq::AudioBuffer a;
  a.sample_rate = sr;
  const std::size_t n = static_cast<std::size_t>(sr * seconds);
  a.samples.resize(n);
  for (std::size_t i = 0; i < n; ++i) {
    const double t = static_cast<double>(i) / sr;
    const double env =
        (std::fmod(t, 0.8) < 0.62) ? (0.45 + 0.35 * std::sin(2 * M_PI * 2.1 * t)) : 0.02;
    a.samples[i] = static_cast<float>(
        env * (0.55 * std::sin(2 * M_PI * 180 * t) +
               0.25 * std::sin(2 * M_PI * 370 * t) +
               0.12 * std::sin(2 * M_PI * 920 * t)));
  }
  return a;
}

openvq::AudioBuffer MakePeriodicIdentity(int sr = 48000, double seconds = 4.0) {
  openvq::AudioBuffer a;
  a.sample_rate = sr;
  a.samples.resize(static_cast<std::size_t>(sr * seconds));
  for (std::size_t i = 0; i < a.samples.size(); ++i) {
    const double t = static_cast<double>(i) / sr;
    a.samples[i] = static_cast<float>(
        0.25 * std::sin(2 * M_PI * 190 * t) +
        0.12 * std::sin(2 * M_PI * 900 * t) +
        0.06 * std::sin(2 * M_PI * 4200 * t));
  }
  return a;
}

openvq::AudioBuffer Delay(const openvq::AudioBuffer& a, int delay_ms) {
  openvq::AudioBuffer d;
  d.sample_rate = a.sample_rate;
  const std::size_t delay =
      static_cast<std::size_t>(a.sample_rate * delay_ms / 1000);
  d.samples.assign(delay, 0.0f);
  d.samples.insert(d.samples.end(), a.samples.begin(), a.samples.end());
  return d;
}

void Require(bool ok, const char* msg) {
  if (!ok) {
    std::cerr << msg << "\n";
    std::exit(1);
  }
}

}  // namespace

int main() {
  const auto ref = MakeSpeechLike(16000, 5.5);
  const auto deg = Delay(ref, 120);

  openvq::AnalysisOptions options;
  options.target_sample_rate = 48000;
  options.max_delay_ms = 500;
  const auto pair = openvq::PreparePair(ref, deg, options);

  Require(pair.sample_rate == 48000, "shared target sample rate not applied");
  Require(!pair.alignment.knots.empty(), "alignment map has no knots");
  const double delay_ms =
      pair.alignment.global_delay_samples * 1000.0 / pair.sample_rate;
  Require(std::abs(delay_ms - 120.0) < 15.0, "known delay not recovered");
  Require(pair.alignment.mean_confidence > 0.4, "alignment confidence too low");

  const auto levels = openvq::MeasureMatchedActiveLevel(
      pair, options.frame_ms, options.hop_ms, options.vad_relative_db);
  Require(levels.active_frames > 0, "no active frames measured");
  Require(levels.active_coverage_fraction > 0.95,
          "delay-only pair should retain active coverage");
  Require(levels.delta_db < 0.75, "matched active level changed under pure delay");

  // Remove the tail from the degraded recording. Coverage must now expose
  // missing active reference material instead of silently dropping it.
  auto truncated = deg;
  truncated.samples.resize(
      truncated.samples.size() - static_cast<std::size_t>(0.9 * truncated.sample_rate));
  const auto truncated_pair = openvq::PreparePair(ref, truncated, options);
  const auto truncated_levels = openvq::MeasureMatchedActiveLevel(
      truncated_pair, options.frame_ms, options.hop_ms, options.vad_relative_db);
  Require(truncated_levels.lost_active_speech_fraction > 0.03,
          "truncation did not create explicit lost active speech");

  // Regression for the Phase 5.1 audit finding: the old correlation search
  // selected -1500 ms for this identical periodic signal.
  {
    const auto periodic = MakePeriodicIdentity();
    openvq::AnalysisOptions p;
    p.target_sample_rate = 48000;
    p.max_delay_ms = 1500;
    const auto identity = openvq::PreparePair(periodic, periodic, p);
    const double identity_delay =
        identity.alignment.global_delay_samples * 1000.0 / identity.sample_rate;
    const auto identity_levels = openvq::MeasureMatchedActiveLevel(
        identity, p.frame_ms, p.hop_ms, p.vad_relative_db);
    Require(std::abs(identity_delay) <= 5.0,
            "periodic identity selected an unsupported non-zero global delay");
    Require(identity_levels.active_coverage_fraction > 0.99,
            "periodic identity lost active coverage");
    Require(identity_levels.lost_active_speech_fraction < 0.01,
            "periodic identity created false lost speech");
  }

  // Phase 6A controlled delay contract: one 200-Hz envelope bin tolerance.
  for (const int expected_ms : {40, 120, 250, 500}) {
    openvq::AnalysisOptions dopt;
    dopt.target_sample_rate = 48000;
    dopt.max_delay_ms = 600;
    const auto speech = MakeSpeechLike(48000, 5.5);
    const auto delayed = Delay(speech, expected_ms);
    const auto p = openvq::PreparePair(speech, delayed, dopt);
    const double got_ms =
        p.alignment.global_delay_samples * 1000.0 / p.sample_rate;
    Require(std::abs(got_ms - expected_ms) <= 5.0,
            "controlled delay exceeded one envelope-bin tolerance");
  }

  return 0;
}
