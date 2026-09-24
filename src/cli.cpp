#include "openvq/advanced.h"
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
  if (argc < 3) {
    std::cerr << "usage: openvq_cli reference.wav degraded.wav "
                 "[--visqol-score N] [--visqol-speech-score N] "
                 "[--visqol-audio-score N] [--calibration FILE]\n";
    return 2;
  }
  try {
    openvq::AnalysisOptions options;
    for (int i = 3; i < argc; ++i) {
      const std::string arg = argv[i];
      if (arg == "--visqol-score" && i + 1 < argc) {
        options.visqol_mos = std::atof(argv[++i]);
      } else if (arg == "--visqol-speech-score" && i + 1 < argc) {
        options.visqol_speech_mos = std::atof(argv[++i]);
      } else if (arg == "--visqol-audio-score" && i + 1 < argc) {
        options.visqol_audio_mos = std::atof(argv[++i]);
      } else if (arg == "--calibration" && i + 1 < argc) {
        options.calibration = openvq::LoadCalibration(argv[++i]);
      } else {
        throw std::invalid_argument("unknown or incomplete option: " + arg);
      }
    }
    openvq::AdvancedAnalyzer analyzer;
    auto result = analyzer.Analyze(
        openvq::LoadWav(argv[1]),
        openvq::LoadWav(argv[2]),
        options);
    std::cout << openvq::ToJson(result) << "\n";
  } catch (const std::exception& e) {
    std::cerr << "openvq: " << e.what() << "\n";
    return 1;
  }
  return 0;
}
