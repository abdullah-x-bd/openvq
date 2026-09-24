#include "openvq/openvq.h"
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
  if (argc < 3) {
    std::cerr << "usage: openvq_cli reference.wav degraded.wav [--visqol-score N]\n";
    return 2;
  }
  try {
    openvq::AnalysisOptions options;
    for (int i = 3; i + 1 < argc; ++i) {
      if (std::string(argv[i]) == "--visqol-score") options.visqol_mos = std::atof(argv[++i]);
    }
    openvq::Analyzer analyzer;
    auto result = analyzer.Analyze(openvq::LoadWav(argv[1]), openvq::LoadWav(argv[2]), options);
    std::cout << openvq::ToJson(result) << "\n";
  } catch (const std::exception& e) {
    std::cerr << "openvq: " << e.what() << "\n";
    return 1;
  }
  return 0;
}
