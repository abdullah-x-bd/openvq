#pragma once

#include "openvq/advanced.h"

#include <string_view>

namespace openvq {

struct HybridExpertScores {
  double visqol_speech_mos = 5.0;
  double visqol_audio_mos = 5.0;
};

struct HybridFeatures {
  double base = 0.0;
  double missing = 0.0;
  double added = 0.0;
  double coloration = 0.0;
  double noisiness = 0.0;
  double discontinuity = 0.0;
  double loudness = 0.0;
  double clipping = 0.0;
  double bad_section = 0.0;
  double multi_resolution = 0.0;
  double temporal = 0.0;
  double modulation = 0.0;
  double asymmetry = 0.0;
  double tilt = 0.0;
  double level = 0.0;
  double bad_interval = 0.0;
  double echo = 0.0;
  double choppiness = 0.0;
  double residual = 0.0;
  double visqol_speech = 0.0;
  double visqol_audio = 0.0;
};

inline constexpr std::string_view kFrozenPhase3ModelId =
    "phase3-tcd-only-2026-09-24-f099129";

HybridFeatures BuildHybridFeatures(
    const AdvancedAnalysisResult& result,
    const HybridExpertScores& experts);

double EvaluateFrozenPhase3(const HybridFeatures& features);

}  // namespace openvq
