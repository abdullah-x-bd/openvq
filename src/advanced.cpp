#include "openvq/advanced.h"
#include "openvq/preprocessing.h"
#include "openvq/hybrid.h"
#include "openvq/phase4.h"

#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <numeric>
#include <sstream>
#include <vector>

namespace openvq {
namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr double kEps = 1e-12;

double Clamp(double x, double lo, double hi) {
  return std::max(lo, std::min(hi, x));
}

double Rms(const std::vector<float>& x, size_t b, size_t e) {
  if (b >= e || b >= x.size()) return 0.0;
  e = std::min(e, x.size());
  double s = 0.0;
  for (size_t i = b; i < e; ++i) s += static_cast<double>(x[i]) * x[i];
  return std::sqrt(s / std::max<size_t>(1, e - b));
}

std::vector<float> ResampleLinear(const AudioBuffer& a, int out_sr) {
  if (a.sample_rate == out_sr) return a.samples;
  if (a.sample_rate <= 0 || a.samples.empty()) return {};
  const double ratio = static_cast<double>(out_sr) / a.sample_rate;
  const size_t n = static_cast<size_t>(std::llround(a.samples.size() * ratio));
  std::vector<float> out(n);
  for (size_t i = 0; i < n; ++i) {
    const double p = i / ratio;
    const size_t j = std::min(static_cast<size_t>(p), a.samples.size() - 1);
    const size_t k = std::min(j + 1, a.samples.size() - 1);
    const double f = p - j;
    out[i] = static_cast<float>((1 - f) * a.samples[j] + f * a.samples[k]);
  }
  return out;
}

size_t NextPow2(size_t n) {
  size_t p = 1;
  while (p < n) p <<= 1;
  return p;
}

void Fft(std::vector<std::complex<double>>& x) {
  const size_t n = x.size();
  for (size_t i = 1, j = 0; i < n; ++i) {
    size_t bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) std::swap(x[i], x[j]);
  }
  for (size_t len = 2; len <= n; len <<= 1) {
    const double a = -2 * kPi / len;
    const std::complex<double> wl(std::cos(a), std::sin(a));
    for (size_t i = 0; i < n; i += len) {
      std::complex<double> w(1, 0);
      for (size_t j = 0; j < len / 2; ++j) {
        auto u = x[i + j];
        auto v = x[i + j + len / 2] * w;
        x[i + j] = u + v;
        x[i + j + len / 2] = u - v;
        w *= wl;
      }
    }
  }
}

double HzToErb(double f) {
  return 21.4 * std::log10(1.0 + 0.00437 * f);
}

double ErbToHz(double e) {
  return (std::pow(10.0, e / 21.4) - 1.0) / 0.00437;
}

std::vector<double> ErbLoudness(
    const std::vector<float>& x, size_t b, size_t n, int sr, int bands = 32) {
  const size_t nfft = NextPow2(n);
  std::vector<std::complex<double>> z(nfft, {0, 0});
  for (size_t i = 0; i < n; ++i) {
    const double w = 0.5 - 0.5 * std::cos(2 * kPi * i / std::max<size_t>(1, n - 1));
    z[i] = (b + i < x.size() ? x[b + i] : 0.0) * w;
  }
  Fft(z);

  const double elo = HzToErb(50);
  const double ehi = HzToErb(std::min(20000.0, sr * 0.48));
  std::vector<double> out(bands, 0.0);

  for (int q = 0; q < bands; ++q) {
    const double f0 = ErbToHz(elo + (ehi - elo) * q / bands);
    const double f1 = ErbToHz(elo + (ehi - elo) * (q + 1) / bands);
    size_t k0 = std::min(nfft / 2, static_cast<size_t>(f0 * nfft / sr));
    size_t k1 = std::min(nfft / 2 + 1, static_cast<size_t>(std::ceil(f1 * nfft / sr)));
    k1 = std::max(k1, k0 + 1);

    double p = 0.0;
    for (size_t k = k0; k < k1; ++k) p += std::norm(z[k]);
    out[q] = std::pow(p / std::max<size_t>(1, k1 - k0) + 1e-15, 0.23);
  }
  return out;
}

double Cosine(const std::vector<double>& a, const std::vector<double>& b) {
  double aa = 0, bb = 0, ab = 0;
  for (size_t i = 0; i < std::min(a.size(), b.size()); ++i) {
    aa += a[i] * a[i];
    bb += b[i] * b[i];
    ab += a[i] * b[i];
  }
  return aa > kEps && bb > kEps ? Clamp(ab / std::sqrt(aa * bb), 0.0, 1.0) : 0.0;
}

double Pearson(const std::vector<double>& a, const std::vector<double>& b) {
  if (a.size() != b.size() || a.size() < 2) return 0;
  const double ma = std::accumulate(a.begin(), a.end(), 0.0) / a.size();
  const double mb = std::accumulate(b.begin(), b.end(), 0.0) / b.size();

  double aa = 0, bb = 0, ab = 0;
  for (size_t i = 0; i < a.size(); ++i) {
    const double x = a[i] - ma;
    const double y = b[i] - mb;
    aa += x * x;
    bb += y * y;
    ab += x * y;
  }
  return aa > kEps && bb > kEps
             ? Clamp(ab / std::sqrt(aa * bb), -1.0, 1.0)
             : 0.0;
}

double Quantile(std::vector<double> v, double q) {
  if (v.empty()) return 0;
  const size_t i = static_cast<size_t>(Clamp(q, 0, 1) * (v.size() - 1));
  std::nth_element(v.begin(), v.begin() + i, v.end());
  return v[i];
}

struct ResolutionStats {
  double sim = 0;
  double asym = 0;
  double tilt = 0;
  double bad = 0;
  int frames = 0;
};

ResolutionStats CompareResolution(
    const std::vector<float>& r,
    const std::vector<float>& d,
    int sr,
    const AlignmentMap& alignment,
    int frame_ms,
    int hop_ms) {
  const size_t frame = static_cast<size_t>(frame_ms * sr / 1000);
  const size_t hop = static_cast<size_t>(hop_ms * sr / 1000);

  double peak = 0;
  for (size_t b = 0; b + frame <= r.size(); b += hop) {
    peak = std::max(peak, Rms(r, b, b + frame));
  }
  const double vad = peak * 0.035;

  std::vector<double> sims, asym, tilts;
  for (size_t rb = 0; rb + frame <= r.size(); rb += hop) {
    const long db = static_cast<long>(
        std::llround(alignment.MapReferenceSample(rb)));
    if (!alignment.Covers(rb, frame, d.size()) ||
        db < 0 || static_cast<size_t>(db) + frame > d.size() ||
        Rms(r, rb, rb + frame) < vad) {
      continue;
    }

    auto a = ErbLoudness(r, rb, frame, sr);
    auto b = ErbLoudness(d, static_cast<size_t>(db), frame, sr);
    const double sa = std::accumulate(a.begin(), a.end(), 0.0) + kEps;
    const double sb = std::accumulate(b.begin(), b.end(), 0.0) + kEps;
    for (double& x : a) x /= sa;
    for (double& x : b) x /= sb;

    sims.push_back(Cosine(a, b));

    double miss = 0, add = 0;
    for (size_t i = 0; i < a.size(); ++i) {
      miss += std::max(0.0, a[i] - b[i]);
      add += std::max(0.0, b[i] - a[i]);
    }
    asym.push_back(Clamp(0.75 * miss + 1.25 * add, 0.0, 1.0));

    auto slope = [](const std::vector<double>& v) {
      double mx = 0, my = 0;
      for (size_t i = 0; i < v.size(); ++i) {
        mx += std::log1p(i);
        my += std::log(v[i] + 1e-12);
      }
      mx /= v.size();
      my /= v.size();

      double num = 0, den = 0;
      for (size_t i = 0; i < v.size(); ++i) {
        const double x = std::log1p(i) - mx;
        const double y = std::log(v[i] + 1e-12) - my;
        num += x * y;
        den += x * x;
      }
      return den > 0 ? num / den : 0.0;
    };
    tilts.push_back(Clamp(std::abs(slope(a) - slope(b)) / 2.0, 0.0, 1.0));
  }

  ResolutionStats s;
  s.frames = static_cast<int>(sims.size());
  if (sims.empty()) return s;
  s.sim = std::accumulate(sims.begin(), sims.end(), 0.0) / sims.size();
  s.asym = std::accumulate(asym.begin(), asym.end(), 0.0) / asym.size();
  s.tilt = std::accumulate(tilts.begin(), tilts.end(), 0.0) / tilts.size();
  s.bad = 1.0 - Quantile(sims, 0.10);
  return s;
}

std::vector<double> Envelope10msReference(
    const std::vector<float>& x, int sr) {
  const size_t hop = static_cast<size_t>(sr / 100);
  std::vector<double> out;
  for (size_t b = 0; b + hop <= x.size(); b += hop) {
    out.push_back(Rms(x, b, b + hop));
  }
  return out;
}

std::vector<double> Envelope10msAlignedDegraded(
    const PreparedPair& pair) {
  const size_t hop = static_cast<size_t>(pair.sample_rate / 100);
  std::vector<double> out;
  for (size_t rb = 0; rb + hop <= pair.reference.size(); rb += hop) {
    if (!pair.alignment.Covers(rb, hop, pair.degraded.size())) {
      out.push_back(0.0);
      continue;
    }
    double s = 0.0;
    for (size_t i = 0; i < hop; ++i) {
      const double v = SampleAlignedDegraded(pair, rb + i);
      s += v * v;
    }
    out.push_back(std::sqrt(s / std::max<size_t>(1, hop)));
  }
  return out;
}

double ModulationSimilarity(
    const std::vector<double>& a, const std::vector<double>& b) {
  if (a.size() != b.size() || a.size() < 16) return 0;

  const int bins = 16;
  std::vector<double> ma(bins), mb(bins);
  for (int k = 1; k <= bins; ++k) {
    double ar = 0, ai = 0, br = 0, bi = 0;
    for (size_t n = 0; n < a.size(); ++n) {
      const double ph = 2 * kPi * k * n / a.size();
      ar += a[n] * std::cos(ph);
      ai -= a[n] * std::sin(ph);
      br += b[n] * std::cos(ph);
      bi -= b[n] * std::sin(ph);
    }
    ma[k - 1] = std::hypot(ar, ai);
    mb[k - 1] = std::hypot(br, bi);
  }
  return Cosine(ma, mb);
}


struct ResidualDiagnostics {
  double echo = 0.0;
  double choppiness = 0.0;
  double intrusion = 0.0;
};

void BuildAlignedSignals(
    const PreparedPair& pair,
    std::vector<float>* ar,
    std::vector<float>* ad) {
  ar->clear();
  ad->clear();
  ar->reserve(pair.reference.size());
  ad->reserve(pair.reference.size());
  for (size_t i = 0; i < pair.reference.size(); ++i) {
    if (!pair.alignment.Covers(i, 1, pair.degraded.size())) continue;
    ar->push_back(pair.reference[i]);
    ad->push_back(SampleAlignedDegraded(pair, i));
  }
}

std::vector<double> BlockAverage(
    const std::vector<float>& x, size_t block) {
  std::vector<double> out;
  if (block == 0) return out;
  out.reserve((x.size() + block - 1) / block);
  for (size_t b = 0; b < x.size(); b += block) {
    const size_t e = std::min(x.size(), b + block);
    double s = 0.0;
    for (size_t i = b; i < e; ++i) s += x[i];
    out.push_back(s / std::max<size_t>(1, e - b));
  }
  return out;
}

double CenteredCorrelationAtLagWindow(
    const std::vector<double>& a,
    const std::vector<double>& b,
    size_t lag,
    size_t begin,
    size_t end) {
  if (a.size() <= lag + 16 || b.size() <= lag + 16) return 0.0;
  end = std::min(end, std::min(a.size(), b.size() - lag));
  begin = std::min(begin, end);
  const size_t n = end - begin;
  if (n < 16) return 0.0;

  double ma = 0.0, mb = 0.0;
  for (size_t i = begin; i < end; ++i) {
    ma += a[i];
    mb += b[i + lag];
  }
  ma /= n;
  mb /= n;

  double aa = 0.0, bb = 0.0, ab = 0.0;
  for (size_t i = begin; i < end; ++i) {
    const double x = a[i] - ma;
    const double y = b[i + lag] - mb;
    aa += x * x;
    bb += y * y;
    ab += x * y;
  }
  if (aa < kEps || bb < kEps) return 0.0;
  return Clamp(ab / std::sqrt(aa * bb), -1.0, 1.0);
}

double CenteredCorrelationAtLag(
    const std::vector<double>& a,
    const std::vector<double>& b,
    size_t lag) {
  return CenteredCorrelationAtLagWindow(
      a, b, lag, 0, std::min(a.size(), b.size()));
}

ResidualDiagnostics AnalyzeResidualStructure(
    const PreparedPair& pair) {
  const auto& r = pair.reference;
  const auto& d = pair.degraded;
  const int sr = pair.sample_rate;
  ResidualDiagnostics out;
  std::vector<float> ar, ad;
  BuildAlignedSignals(pair, &ar, &ad);
  if (ar.size() < static_cast<size_t>(sr / 2)) return out;

  // Direct-path least-squares subtraction. Echo is then sought in the residual,
  // not in the already-explained aligned speech.
  double rr = 0.0, rd = 0.0, dd = 0.0;
  for (size_t i = 0; i < ar.size(); ++i) {
    rr += static_cast<double>(ar[i]) * ar[i];
    rd += static_cast<double>(ar[i]) * ad[i];
    dd += static_cast<double>(ad[i]) * ad[i];
  }
  const double gain = rr > kEps ? rd / rr : 0.0;
  std::vector<float> residual(ar.size());
  double residual_energy = 0.0;
  for (size_t i = 0; i < ar.size(); ++i) {
    residual[i] = static_cast<float>(ad[i] - gain * ar[i]);
    residual_energy += static_cast<double>(residual[i]) * residual[i];
  }
  const double residual_ratio =
      std::sqrt(residual_energy / (dd + kEps));

  // Use a signed 1 kHz representation for delayed-copy detection. Searching
  // from 20 to 450 ms covers common perceptually salient talker echo delays
  // while avoiding the direct path.
  const size_t block = static_cast<size_t>(std::max(1, sr / 1000));
  auto ref_ds = BlockAverage(ar, block);
  auto res_ds = BlockAverage(residual, block);
  double best_echo_corr = 0.0;
  size_t best_echo_lag = 0;
  for (size_t lag_ms = 20; lag_ms <= 450; lag_ms += 5) {
    const double corr =
        std::abs(CenteredCorrelationAtLag(ref_ds, res_ds, lag_ms));
    if (corr > best_echo_corr) {
      best_echo_corr = corr;
      best_echo_lag = lag_ms;
    }
  }

  // A true echo is a coherent delayed copy over much of the utterance. PLC,
  // time warps and local jitter can create a large global delayed correlation,
  // but it normally does not persist across independent temporal quarters.
  std::vector<double> echo_quarters;
  if (best_echo_lag > 0) {
    const size_t usable =
        std::min(ref_ds.size(), res_ds.size() > best_echo_lag
                                    ? res_ds.size() - best_echo_lag
                                    : 0);
    for (int q = 0; q < 4; ++q) {
      const size_t begin = usable * q / 4;
      const size_t end = usable * (q + 1) / 4;
      if (end > begin + 20) {
        echo_quarters.push_back(std::abs(CenteredCorrelationAtLagWindow(
            ref_ds, res_ds, best_echo_lag, begin, end)));
      }
    }
  }
  const double echo_consistency =
      echo_quarters.empty() ? 0.0 : Quantile(echo_quarters, 0.25);
  out.echo = Clamp(
      std::sqrt(std::max(0.0, best_echo_corr * echo_consistency)) *
          Clamp(residual_ratio * 1.8, 0.0, 1.0),
      0.0,
      1.0);

  // Detect short speech holes after normalizing out global gain. This keeps a
  // quiet but continuous call from looking "choppy".
  const size_t micro = static_cast<size_t>(std::max(1, sr * 5 / 1000));
  std::vector<double> ratios;
  double peak_ref = 0.0;
  for (size_t b = 0; b + micro <= ar.size(); b += micro) {
    peak_ref = std::max(peak_ref, Rms(ar, b, b + micro));
  }
  const double active_threshold = peak_ref * 0.04;
  for (size_t b = 0; b + micro <= ar.size(); b += micro) {
    const double er = Rms(ar, b, b + micro);
    if (er < active_threshold) continue;
    const double ed = Rms(ad, b, b + micro);
    ratios.push_back(ed / (er + 1e-9));
  }
  double hole_component = 0.0;
  double transition_component = 0.0;
  if (ratios.size() >= 8) {
    const double median_ratio = std::max(1e-6, Quantile(ratios, 0.5));
    std::vector<double> holes;
    std::vector<double> transitions;
    double previous = ratios.front() / median_ratio;
    for (double raw : ratios) {
      const double q = Clamp(raw / median_ratio, 0.0, 2.5);
      holes.push_back(Clamp((0.65 - q) / 0.65, 0.0, 1.0));
      transitions.push_back(Clamp(std::abs(q - previous) / 1.2, 0.0, 1.0));
      previous = q;
    }
    hole_component =
        std::accumulate(holes.begin(), holes.end(), 0.0) / holes.size();
    transition_component = Quantile(transitions, 0.90);
  }

  // Packet-loss concealment often repeats the previous waveform rather than
  // inserting silence. Compare the amount of frame-to-frame change in the
  // degraded stream with the change the clean reference should have had.
  const size_t plc_frame =
      static_cast<size_t>(std::max(1, sr * 20 / 1000));
  std::vector<double> freezes;
  for (size_t b = plc_frame; b + plc_frame <= ar.size(); b += plc_frame) {
    const double active =
        std::max(Rms(ar, b - plc_frame, b), Rms(ar, b, b + plc_frame));
    if (active < active_threshold) continue;

    double ref_delta = 0.0, deg_delta = 0.0;
    double ref_energy = 0.0, deg_energy = 0.0;
    for (size_t i = 0; i < plc_frame; ++i) {
      const double r0 = ar[b - plc_frame + i];
      const double r1 = ar[b + i];
      const double d0 = ad[b - plc_frame + i];
      const double d1 = ad[b + i];
      ref_delta += (r1 - r0) * (r1 - r0);
      deg_delta += (d1 - d0) * (d1 - d0);
      ref_energy += r0 * r0 + r1 * r1;
      deg_energy += d0 * d0 + d1 * d1;
    }
    const double nr =
        std::sqrt(ref_delta / (ref_energy + kEps));
    const double nd =
        std::sqrt(deg_delta / (deg_energy + kEps));
    if (nr > 0.08) {
      const double change_ratio = nd / (nr + 1e-9);
      freezes.push_back(Clamp((0.55 - change_ratio) / 0.55, 0.0, 1.0));
    }
  }
  const double freeze_component =
      freezes.empty() ? 0.0 : Quantile(freezes, 0.90);
  out.choppiness = Clamp(
      0.46 * hole_component +
          0.18 * transition_component +
          0.36 * freeze_component,
      0.0,
      1.0);

  // Residual energy not explained by the direct path or a coherent delayed
  // copy is a generic added-interference signal useful for competing speakers
  // and nonstationary foreground noise.
  out.intrusion =
      Clamp(residual_ratio - 0.65 * out.echo, 0.0, 1.0);
  return out;
}

}  // namespace

AdvancedAnalysisResult AdvancedAnalyzer::Analyze(
    const AudioBuffer& reference,
    const AudioBuffer& degraded,
    const AnalysisOptions& options) const {
  AdvancedAnalysisResult out;
  const PreparedPair pair = PreparePair(reference, degraded, options);
  out.base = Analyzer().AnalyzePrepared(pair, options);
  const int sr = pair.sample_rate;
  const auto& r = pair.reference;
  const auto& d = pair.degraded;
  if (r.empty() || d.empty()) {
    out.mos = out.base.mos;
    out.confidence = out.base.confidence;
    return out;
  }

  const auto s20 = CompareResolution(r, d, sr, pair.alignment, 20, 10);
  const auto s80 = CompareResolution(r, d, sr, pair.alignment, 80, 40);
  const auto s200 = CompareResolution(r, d, sr, pair.alignment, 200, 100);
  const int count =
      (s20.frames > 0) + (s80.frames > 0) + (s200.frames > 0);

  out.advanced.erb_similarity = s20.sim;
  out.advanced.multi_resolution_similarity =
      count ? ((s20.frames ? s20.sim : 0) +
               (s80.frames ? s80.sim : 0) +
               (s200.frames ? s200.sim : 0)) /
                  count
            : 0;
  out.advanced.asymmetric_disturbance =
      count ? ((s20.frames ? s20.asym : 0) +
               (s80.frames ? s80.asym : 0) +
               (s200.frames ? s200.asym : 0)) /
                  count
            : 1;
  out.advanced.spectral_tilt_error =
      count ? ((s20.frames ? s20.tilt : 0) +
               (s80.frames ? s80.tilt : 0) +
               (s200.frames ? s200.tilt : 0)) /
                  count
            : 1;
  out.advanced.bad_interval_severity =
      std::max({s20.bad, s80.bad, s200.bad});

  auto er = Envelope10msReference(r, sr);
  auto ed = Envelope10msAlignedDegraded(pair);
  out.advanced.temporal_envelope_similarity =
      Clamp((Pearson(er, ed) + 1.0) * 0.5, 0.0, 1.0);
  out.advanced.modulation_similarity = ModulationSimilarity(er, ed);

  const auto active_levels = MeasureMatchedActiveLevel(
      pair, options.frame_ms, options.hop_ms, options.vad_relative_db);
  out.advanced.active_level_delta_db = active_levels.delta_db;
  out.advanced.alignment_coverage = active_levels.active_coverage_fraction;
  out.advanced.alignment_confidence = pair.alignment.mean_confidence;

  const auto residual = AnalyzeResidualStructure(pair);
  out.advanced.echo_score = residual.echo;
  out.advanced.choppiness_score = residual.choppiness;
  out.advanced.residual_intrusion = residual.intrusion;

  std::vector<double> frame_sims;
  std::vector<double> frame_disc;
  frame_sims.reserve(out.base.frames.size());
  frame_disc.reserve(out.base.frames.size());
  double longest_bad_ms = 0.0;
  double current_bad_ms = 0.0;
  double previous_start_ms = -1e30;
  int severe_frames = 0;
  for (const auto& fq : out.base.frames) {
    frame_sims.push_back(fq.similarity);
    frame_disc.push_back(fq.discontinuity);
    // out.base.frames contains active-reference frames only. A large timestamp
    // gap therefore represents intervening inactive speech/silence and must
    // break an accumulated bad interval.
    if (fq.start_ms - previous_start_ms > options.hop_ms * 1.5) {
      current_bad_ms = 0.0;
    }
    const bool bad = fq.discontinuity > 0.45 || fq.similarity < 0.55;
    if (bad) {
      current_bad_ms += options.hop_ms;
      longest_bad_ms = std::max(longest_bad_ms, current_bad_ms);
      ++severe_frames;
    } else {
      current_bad_ms = 0.0;
    }
    previous_start_ms = fq.start_ms;
  }
  out.advanced.similarity_p10 = Quantile(frame_sims, 0.10);
  out.advanced.similarity_p50 = Quantile(frame_sims, 0.50);
  out.advanced.discontinuity_p90 = Quantile(frame_disc, 0.90);
  out.advanced.longest_bad_interval_ms = longest_bad_ms;
  out.advanced.severe_frame_fraction =
      out.base.frames.empty()
          ? 0.0
          : static_cast<double>(severe_frames) / out.base.frames.size();

  const auto& c = options.calibration;
  const double base_penalty = Clamp(5.0 - out.base.mos, 0.0, 4.0);
  const double level_penalty =
      Clamp(out.advanced.active_level_delta_db / 18.0, 0.0, 1.0);

  double final_penalty = std::max(0.0, c.final_bias);
  final_penalty +=
      std::max(0.0, c.base_penalty_weight) * base_penalty;
  final_penalty +=
      std::max(0.0, c.advanced_multi_resolution_weight) *
      (1.0 - out.advanced.multi_resolution_similarity);
  final_penalty +=
      std::max(0.0, c.advanced_temporal_weight) *
      (1.0 - out.advanced.temporal_envelope_similarity);
  final_penalty +=
      std::max(0.0, c.advanced_modulation_weight) *
      (1.0 - out.advanced.modulation_similarity);
  final_penalty +=
      std::max(0.0, c.advanced_asymmetry_weight) *
      out.advanced.asymmetric_disturbance;
  final_penalty +=
      std::max(0.0, c.advanced_tilt_weight) *
      out.advanced.spectral_tilt_error;
  final_penalty +=
      std::max(0.0, c.advanced_level_weight) * level_penalty;
  final_penalty +=
      std::max(0.0, c.advanced_bad_interval_weight) *
      out.advanced.bad_interval_severity;
  final_penalty +=
      std::max(0.0, c.advanced_echo_weight) *
      out.advanced.echo_score;
  final_penalty +=
      std::max(0.0, c.advanced_choppiness_weight) *
      out.advanced.choppiness_score;
  final_penalty +=
      std::max(0.0, c.advanced_residual_intrusion_weight) *
      out.advanced.residual_intrusion;

  out.mos = Clamp(5.0 - final_penalty, 1.0, 5.0);
  out.confidence = Clamp(
      0.65 * out.base.confidence +
          0.35 * Clamp(count / 3.0, 0.0, 1.0),
      0.0,
      1.0);

  if (options.enable_phase4_candidate) {
    const auto prediction = EvaluatePhase4(
        out, options.visqol_speech_mos, options.visqol_audio_mos);
    out.mos = prediction.mos;
    out.phase4_applied = true;
    out.phase4_experts_applied = prediction.experts_applied;
    out.phase4_native_mos = prediction.native_mos;
    if (prediction.experts_applied) {
      out.phase4_expert_disagreement = prediction.expert_disagreement;
      out.visqol_speech_mos =
          Clamp(*options.visqol_speech_mos, 1.0, 5.0);
      out.visqol_audio_mos =
          Clamp(*options.visqol_audio_mos, 1.0, 5.0);
    }
  } else if (options.enable_frozen_phase3_hybrid &&
             options.visqol_speech_mos.has_value() &&
             options.visqol_audio_mos.has_value()) {
    HybridExpertScores experts{
        Clamp(*options.visqol_speech_mos, 1.0, 5.0),
        Clamp(*options.visqol_audio_mos, 1.0, 5.0)};
    out.visqol_speech_mos = experts.visqol_speech_mos;
    out.visqol_audio_mos = experts.visqol_audio_mos;
    out.mos = EvaluateFrozenPhase3(BuildHybridFeatures(out, experts));
    out.hybrid_applied = true;
  }
  return out;
}

std::string ToJson(const AdvancedAnalysisResult& r) {
  const std::string base = ToJson(r.base);
  const size_t comma = base.find(',');

  std::ostringstream o;
  o << std::fixed << std::setprecision(6);
  o << "{\"mos\":" << r.mos
    << ",\"frontend_id\":\"" << kFrontendId << "\"";
  if (comma != std::string::npos) {
    o << base.substr(comma, base.size() - comma - 1);
  }
  o << ",\"base_mos\":" << r.base.mos
    << ",\"hybrid_applied\":" << (r.hybrid_applied ? "true" : "false")
    << ",\"phase4_applied\":" << (r.phase4_applied ? "true" : "false");
  if (r.hybrid_applied) {
    o << ",\"hybrid_model\":\"" << kFrozenPhase3ModelId << "\""
      << ",\"visqol_speech_mos\":" << *r.visqol_speech_mos
      << ",\"visqol_audio_mos\":" << *r.visqol_audio_mos;
  }
  if (r.phase4_applied) {
    o << ",\"phase4_model\":\"" << Phase4ModelId() << "\""
      << ",\"phase4_native_mos\":" << *r.phase4_native_mos
      << ",\"phase4_experts_applied\":"
      << (r.phase4_experts_applied ? "true" : "false");
    if (r.phase4_experts_applied) {
      o << ",\"phase4_expert_disagreement\":"
        << *r.phase4_expert_disagreement
        << ",\"visqol_speech_mos\":" << *r.visqol_speech_mos
        << ",\"visqol_audio_mos\":" << *r.visqol_audio_mos;
    }
  }
  o << ",\"advanced\":{\"erb_similarity\":" << r.advanced.erb_similarity
    << ",\"multi_resolution_similarity\":"
    << r.advanced.multi_resolution_similarity
    << ",\"temporal_envelope_similarity\":"
    << r.advanced.temporal_envelope_similarity
    << ",\"modulation_similarity\":" << r.advanced.modulation_similarity
    << ",\"asymmetric_disturbance\":"
    << r.advanced.asymmetric_disturbance
    << ",\"spectral_tilt_error\":" << r.advanced.spectral_tilt_error
    << ",\"active_level_delta_db\":"
    << r.advanced.active_level_delta_db
    << ",\"bad_interval_severity\":"
    << r.advanced.bad_interval_severity
    << ",\"echo_score\":" << r.advanced.echo_score
    << ",\"choppiness_score\":" << r.advanced.choppiness_score
    << ",\"residual_intrusion\":" << r.advanced.residual_intrusion
    << ",\"similarity_p10\":" << r.advanced.similarity_p10
    << ",\"similarity_p50\":" << r.advanced.similarity_p50
    << ",\"discontinuity_p90\":" << r.advanced.discontinuity_p90
    << ",\"longest_bad_interval_ms\":" << r.advanced.longest_bad_interval_ms
    << ",\"severe_frame_fraction\":" << r.advanced.severe_frame_fraction
    << ",\"alignment_coverage\":" << r.advanced.alignment_coverage
    << ",\"alignment_confidence\":" << r.advanced.alignment_confidence
    << "}}";
  return o.str();
}

}  // namespace openvq
