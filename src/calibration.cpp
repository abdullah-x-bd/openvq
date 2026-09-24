#include "openvq/openvq.h"

#include <fstream>
#include <stdexcept>
#include <string>

namespace openvq {

Calibration LoadCalibration(const std::string& path) {
  std::ifstream in(path);
  if (!in) throw std::runtime_error("cannot open calibration: " + path);

  Calibration c;
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty() || line[0] == '#') continue;
    const auto pos = line.find('=');
    if (pos == std::string::npos) continue;

    const std::string key = line.substr(0, pos);
    const double value = std::stod(line.substr(pos + 1));

    if (key == "bias") c.bias = value;
    else if (key == "missing_weight") c.missing_weight = value;
    else if (key == "added_weight") c.added_weight = value;
    else if (key == "coloration_weight") c.coloration_weight = value;
    else if (key == "noisiness_weight") c.noisiness_weight = value;
    else if (key == "discontinuity_weight") c.discontinuity_weight = value;
    else if (key == "loudness_weight") c.loudness_weight = value;
    else if (key == "clipping_weight") c.clipping_weight = value;
    else if (key == "bad_section_weight") c.bad_section_weight = value;
    else if (key == "visqol_penalty_weight" || key == "visqol_weight") c.visqol_weight = value;
  }
  return c;
}

}  // namespace openvq
