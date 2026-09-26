#pragma once

#include "openvq/advanced.h"

namespace openvq {

struct Phase4Prediction {
  double native_mos = 1.0;
  double mos = 1.0;
  bool experts_applied = false;
  double expert_disagreement = 0.0;
};

Phase4Prediction EvaluatePhase4(
    const AdvancedAnalysisResult& result,
    const std::optional<double>& visqol_speech_mos = std::nullopt,
    const std::optional<double>& visqol_audio_mos = std::nullopt);

const char* Phase4ModelId();

}  // namespace openvq
