#include "openvq/hybrid.h"
#include "test_support.h"

#include <algorithm>
#include <cmath>
#include <iostream>

int main() {
  openvq::HybridFeatures f;
  f.base=0.08379399999999992; f.missing=0.005692; f.added=0.193986;
  f.coloration=0.26143724999999995; f.noisiness=0.06789525000000007;
  f.discontinuity=0.0; f.loudness=0.0637144999999999; f.clipping=0.0;
  f.bad_section=0.0; f.multi_resolution=0.03292200000000001;
  f.temporal=0.004693999999999976; f.modulation=0.0023330000000000295;
  f.asymmetry=0.193278; f.tilt=0.067636; f.level=0.010526;
  f.bad_interval=0.120493; f.echo=0.289701; f.choppiness=0.041833;
  f.residual=0.083021; f.visqol_speech=0.9013108025000001;
  f.visqol_audio=0.25548963;
  const double expected=1.6350263119881987;
  const double got=openvq::EvaluateFrozenPhase3(f);
  OPENVQ_REQUIRE(std::abs(got-expected)<1e-12);
  auto worse=f; worse.echo=std::min(1.0,f.echo+0.10);
  OPENVQ_REQUIRE(openvq::EvaluateFrozenPhase3(worse)<=got+1e-12);
  std::cout << "Frozen Phase-3 hybrid tests passed\n";
}
