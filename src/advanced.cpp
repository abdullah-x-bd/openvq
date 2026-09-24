#include "openvq/advanced.h"

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
    long delay,
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
    const long db = static_cast<long>(rb) + delay;
    if (db < 0 || static_cast<size_t>(db) + frame > d.size() ||
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

std::vector<double> Envelope10ms(
    const std::vector<float>& x, int sr, long offset, size_t nref) {
  const size_t hop = static_cast<size_t>(sr / 100);
  std::vector<double> out;

  for (size_t rb = 0; rb + hop <= nref; rb += hop) {
    const long b = static_cast<long>(rb) + offset;
    if (b < 0 || static_cast<size_t>(b) + hop > x.size()) {
      out.push_back(0.0);
    } else {
      out.push_back(Rms(x, static_cast<size_t>(b), static_cast<size_t>(b) + hop));
    }
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

}  // namespace

AdvancedAnalysisResult AdvancedAnalyzer::Analyze(
    const AudioBuffer& reference,
    const AudioBuffer& degraded,
    const AnalysisOptions& options) const {
  AdvancedAnalysisResult out;
  out.base = Analyzer().Analyze(reference, degraded, options);

  const int sr = 48000;
  auto r = ResampleLinear(reference, sr);
  auto d = ResampleLinear(degraded, sr);
  if (r.empty() || d.empty()) {
    out.mos = out.base.mos;
    out.confidence = out.base.confidence;
    return out;
  }

  const long delay =
      static_cast<long>(std::llround(out.base.delay_ms * sr / 1000.0));

  const auto s20 = CompareResolution(r, d, sr, delay, 20, 10);
  const auto s80 = CompareResolution(r, d, sr, delay, 80, 40);
  const auto s200 = CompareResolution(r, d, sr, delay, 200, 100);
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

  auto er = Envelope10ms(r, sr, 0, r.size());
  auto ed = Envelope10ms(d, sr, delay, r.size());
  out.advanced.temporal_envelope_similarity =
      Clamp((Pearson(er, ed) + 1.0) * 0.5, 0.0, 1.0);
  out.advanced.modulation_similarity = ModulationSimilarity(er, ed);

  const double rr = Rms(r, 0, r.size());
  const double dr =
      Rms(d, delay > 0 ? static_cast<size_t>(delay) : 0, d.size());
  out.advanced.active_level_delta_db =
      std::abs(20 * std::log10((dr + 1e-9) / (rr + 1e-9)));

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

  out.mos = Clamp(5.0 - final_penalty, 1.0, 5.0);
  out.confidence = Clamp(
      0.65 * out.base.confidence +
          0.35 * Clamp(count / 3.0, 0.0, 1.0),
      0.0,
      1.0);
  return out;
}

std::string ToJson(const AdvancedAnalysisResult& r) {
  const std::string base = ToJson(r.base);
  const size_t comma = base.find(',');

  std::ostringstream o;
  o << std::fixed << std::setprecision(6);
  o << "{\"mos\":" << r.mos;
  if (comma != std::string::npos) {
    o << base.substr(comma, base.size() - comma - 1);
  }
  o << ",\"base_mos\":" << r.base.mos
    << ",\"advanced\":{\"erb_similarity\":" << r.advanced.erb_similarity
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
    << r.advanced.bad_interval_severity << "}}";
  return o.str();
}

}  // namespace openvq
