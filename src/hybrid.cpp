#include "openvq/hybrid.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <functional>

namespace openvq {
namespace {

double Clamp01(double x) { return std::max(0.0, std::min(1.0, x)); }

struct Term { std::size_t feature; double knot; double weight; };
constexpr double kBias = 0.5326278543380228;
constexpr std::array<Term, 70> kTerms = {{
    {0, 0.45, 0.02480238598130599},
    {0, 0.6, 0.017059258090025623},
    {0, 0.75, 0.017059258090025623},
    {1, 0.3, 0.035387642252867176},
    {1, 0.45, 0.01763777437821818},
    {1, 0.6, 0.017059258090025623},
    {1, 0.75, 0.017059258090025623},
    {2, 0.75, 0.017083379508742114},
    {5, 0.6, 0.013856938059651935},
    {5, 0.75, 0.017059258090025623},
    {6, 0.6, 0.014189521111631355},
    {6, 0.75, 0.13274592731218304},
    {7, 0, 0.017059258090025623},
    {7, 0.15, 0.017059258090025623},
    {7, 0.3, 0.017059258090025623},
    {7, 0.45, 0.017059258090025623},
    {7, 0.6, 0.017059258090025623},
    {7, 0.75, 0.017059258090025623},
    {8, 0.15, 0.005492562271632836},
    {8, 0.3, 0.013767355025200547},
    {8, 0.45, 0.017059258090025623},
    {8, 0.6, 0.017059258090025623},
    {8, 0.75, 0.017059258090025623},
    {9, 0.45, 0.017059258090025623},
    {9, 0.6, 0.017059258090025623},
    {9, 0.75, 0.017059258090025623},
    {10, 0.45, 0.017059258090025623},
    {10, 0.6, 0.017059258090025623},
    {10, 0.75, 0.017059258090025623},
    {11, 0.3, 0.017059258090025623},
    {11, 0.45, 0.017059258090025623},
    {11, 0.6, 0.017059258090025623},
    {11, 0.75, 0.017059258090025623},
    {12, 0.75, 0.013145693128172993},
    {13, 0.45, 0.017059258090025623},
    {13, 0.6, 0.017059258090025623},
    {13, 0.75, 0.017059258090025623},
    {15, 0.6, 0.014663449735516018},
    {15, 0.75, 0.017059258090025623},
    {16, 0, 1.3777553446812958},
    {17, 0.3, 0.1650553953987244},
    {17, 0.45, 0.092858293549331},
    {17, 0.6, 0.027310951711285853},
    {17, 0.75, 0.017059258090025623},
    {18, 0, 0.21996814385977154},
    {19, 0, 1.519440424439323},
    {19, 0.15, 1.265923728647842},
    {20, 0, 0.3636430453066157},
    {20, 0.6, 0.022247608993292367},
    {20, 0.75, 0.017059258090025623},
    {23, 0, 0.0597106958891576},
    {23, 0.15, 0.017059258090025623},
    {23, 0.3, 0.017059258090025623},
    {23, 0.45, 0.017059258090025623},
    {23, 0.6, 0.017059258090025623},
    {23, 0.75, 0.017059258090025623},
    {24, 0.15, 0.09401772247293266},
    {24, 0.3, 0.018471737439116814},
    {24, 0.45, 0.017059258090025623},
    {24, 0.6, 0.017059258090025623},
    {24, 0.75, 0.017059258090025623},
    {26, 0, 0.017059258090025623},
    {26, 0.15, 0.017059258090025623},
    {26, 0.3, 0.017059258090025623},
    {26, 0.45, 0.017059258090025623},
    {26, 0.6, 0.017059258090025623},
    {26, 0.75, 0.017059258090025623},
    {27, 0.45, 0.017059258090025623},
    {27, 0.6, 0.017059258090025623},
    {27, 0.75, 0.017059258090025623}
}};

std::array<double, 28> Values(const HybridFeatures& f) {
  std::array<double, 28> v{};
  v[0]=f.base; v[1]=f.missing; v[2]=f.added; v[3]=f.coloration;
  v[4]=f.noisiness; v[5]=f.discontinuity; v[6]=f.loudness;
  v[7]=f.clipping; v[8]=f.bad_section; v[9]=f.multi_resolution;
  v[10]=f.temporal; v[11]=f.modulation; v[12]=f.asymmetry;
  v[13]=f.tilt; v[14]=f.level; v[15]=f.bad_interval; v[16]=f.echo;
  v[17]=f.choppiness; v[18]=f.residual; v[19]=f.visqol_speech;
  v[20]=f.visqol_audio;
  std::array<double, 21> base{};
  for (std::size_t i=0;i<base.size();++i) base[i]=v[i];
  auto sorted=base;
  std::sort(sorted.begin(),sorted.end(),std::greater<double>());
  v[21]=sorted.front();
  v[22]=(sorted[0]+sorted[1]+sorted[2])/3.0;
  v[23]=f.echo*f.base;
  v[24]=f.choppiness*f.bad_interval;
  v[25]=f.residual*f.noisiness;
  v[26]=f.clipping*f.bad_interval;
  v[27]=f.visqol_speech*f.base;
  return v;
}

}  // namespace

HybridFeatures BuildHybridFeatures(
    const AdvancedAnalysisResult& result,
    const HybridExpertScores& experts) {
  HybridFeatures f;
  f.base=Clamp01((5.0-result.base.mos)/4.0);
  f.missing=Clamp01(result.base.missing_disturbance);
  f.added=Clamp01(result.base.added_disturbance);
  f.coloration=Clamp01((5.0-result.base.dimensions.coloration)/4.0);
  f.noisiness=Clamp01((5.0-result.base.dimensions.noisiness)/4.0);
  f.discontinuity=Clamp01((5.0-result.base.dimensions.discontinuity)/4.0);
  f.loudness=Clamp01((5.0-result.base.dimensions.loudness)/4.0);
  f.clipping=Clamp01(result.base.clipping_ratio*40.0);
  f.bad_section=Clamp01(result.base.bad_section_fraction);
  f.multi_resolution=Clamp01(1.0-result.advanced.multi_resolution_similarity);
  f.temporal=Clamp01(1.0-result.advanced.temporal_envelope_similarity);
  f.modulation=Clamp01(1.0-result.advanced.modulation_similarity);
  f.asymmetry=Clamp01(result.advanced.asymmetric_disturbance);
  f.tilt=Clamp01(result.advanced.spectral_tilt_error);
  f.level=Clamp01(result.advanced.active_level_delta_db/18.0);
  f.bad_interval=Clamp01(result.advanced.bad_interval_severity);
  f.echo=Clamp01(result.advanced.echo_score);
  f.choppiness=Clamp01(result.advanced.choppiness_score);
  f.residual=Clamp01(result.advanced.residual_intrusion);
  f.visqol_speech=Clamp01((5.0-experts.visqol_speech_mos)/4.0);
  f.visqol_audio=Clamp01((5.0-experts.visqol_audio_mos)/4.0);
  return f;
}

double EvaluateFrozenPhase3(const HybridFeatures& f) {
  const auto v=Values(f);
  double penalty=kBias;
  for (const auto& term:kTerms)
    penalty += term.weight*std::max(0.0,v[term.feature]-term.knot);
  return std::max(1.0,std::min(5.0,5.0-penalty));
}

}  // namespace openvq
