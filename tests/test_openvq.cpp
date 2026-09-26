#include "openvq/openvq.h"
#include "test_support.h"
#include <algorithm>
#include <cmath>
#include <iostream>

namespace {
openvq::AudioBuffer SpeechLike(double seconds, int sr = 48000) {
  openvq::AudioBuffer a; a.sample_rate = sr;
  a.samples.resize(static_cast<size_t>(seconds * sr));
  for (size_t i = 0; i < a.samples.size(); ++i) {
    double t = static_cast<double>(i) / sr;
    double env = 0.45 + 0.45 * std::sin(2.0 * 3.141592653589793 * 2.7 * t);
    double v = 0.28 * std::sin(2.0 * 3.141592653589793 * 180.0 * t)
             + 0.16 * std::sin(2.0 * 3.141592653589793 * 720.0 * t)
             + 0.08 * std::sin(2.0 * 3.141592653589793 * 2100.0 * t)
             + 0.04 * std::sin(2.0 * 3.141592653589793 * 5200.0 * t);
    a.samples[i] = static_cast<float>(env * v);
  }
  return a;
}
}

int main() {
  openvq::Analyzer analyzer;
  auto ref = SpeechLike(4.0);
  auto clean = analyzer.Analyze(ref, ref);
  OPENVQ_REQUIRE(clean.mos > 4.5);
  OPENVQ_REQUIRE(clean.confidence > 0.7);

  auto dropped = ref;
  const int sr = ref.sample_rate;
  std::fill(dropped.samples.begin() + sr, dropped.samples.begin() + sr + sr / 3, 0.0f);
  auto bad = analyzer.Analyze(ref, dropped);
  OPENVQ_REQUIRE(bad.mos < clean.mos);
  OPENVQ_REQUIRE(bad.dimensions.discontinuity < clean.dimensions.discontinuity);
  OPENVQ_REQUIRE(!bad.events.empty());

  auto clipped = ref;
  for (float& v : clipped.samples) v = std::max(-1.0f, std::min(1.0f, v * 9.0f));
  auto clip = analyzer.Analyze(ref, clipped);
  OPENVQ_REQUIRE(clip.clipping_ratio > 0.001);
  OPENVQ_REQUIRE(clip.mos < clean.mos);

  auto delayed = ref;
  delayed.samples.insert(delayed.samples.begin(), sr / 5, 0.0f);
  auto del = analyzer.Analyze(ref, delayed);
  OPENVQ_REQUIRE(std::abs(std::abs(del.delay_ms) - 200.0) < 15.0);

  std::cout << "OpenVQ tests passed\n";
  return 0;
}
