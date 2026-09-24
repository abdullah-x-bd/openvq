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


struct TelecomDiagnostics {
  double echo = 0.0;
  double residual = 0.0;
  double temporal_edit = 0.0;
  double clipping_plateau = 0.0;
  double inactive_noise = 0.0;
};

double VectorRms(const std::vector<double>& x) {
  if (x.empty()) return 0.0;
  double s = 0.0;
  for (double v : x) s += v * v;
  return std::sqrt(s / x.size());
}

double Median(std::vector<double> x) {
  if (x.empty()) return 0.0;
  const size_t m = x.size() / 2;
  std::nth_element(x.begin(), x.begin() + m, x.end());
  double v = x[m];
  if (x.size() % 2 == 0) {
    std::nth_element(x.begin(), x.begin() + m - 1, x.end());
    v = 0.5 * (v + x[m - 1]);
  }
  return v;
}

double CorrAtShift(const std::vector<double>& a,
                   const std::vector<double>& b,
                   int shift,
                   size_t begin,
                   size_t end) {
  double aa = 0.0, bb = 0.0, ab = 0.0;
  size_t n = 0;
  end = std::min(end, a.size());
  for (size_t i = begin; i < end; ++i) {
    const long j = static_cast<long>(i) + shift;
    if (j < 0 || j >= static_cast<long>(b.size())) continue;
    const double x = a[i];
    const double y = b[static_cast<size_t>(j)];
    aa += x * x;
    bb += y * y;
    ab += x * y;
    ++n;
  }
  if (n < 12 || aa < kEps || bb < kEps) return -1.0;
  return ab / std::sqrt(aa * bb);
}

TelecomDiagnostics AnalyzeTelecomImpairments(
    const std::vector<float>& reference,
    const std::vector<float>& degraded,
    int sr,
    long delay) {
  TelecomDiagnostics out;

  const size_t rb =
      delay < 0 ? static_cast<size_t>(std::min<long>(-delay, reference.size())) : 0;
  const size_t db =
      delay > 0 ? static_cast<size_t>(std::min<long>(delay, degraded.size())) : 0;
  if (rb >= reference.size() || db >= degraded.size()) return out;

  const size_t n = std::min(reference.size() - rb, degraded.size() - db);
  if (n < static_cast<size_t>(sr / 2)) return out;

  // Estimate the direct-path gain before studying the unexplained residual.
  double rr = 0.0, rd = 0.0;
  for (size_t i = 0; i < n; ++i) {
    const double r = reference[rb + i];
    const double d = degraded[db + i];
    rr += r * r;
    rd += r * d;
  }
  const double gain = Clamp(rd / (rr + kEps), 0.05, 8.0);

  std::vector<double> residual(n);
  double ref_energy = 0.0, residual_energy = 0.0;
  for (size_t i = 0; i < n; ++i) {
    const double direct = gain * reference[rb + i];
    const double e = degraded[db + i] - direct;
    residual[i] = e;
    ref_energy += direct * direct;
    residual_energy += e * e;
  }
  const double residual_ratio =
      std::sqrt(residual_energy / (ref_energy + kEps));
  out.residual = Clamp(
      residual_ratio / (residual_ratio + 0.18), 0.0, 1.0);

  // Echo is a delayed copy of the reference remaining after direct-path
  // subtraction. Decimation makes the search inexpensive while keeping
  // telecom echo delays well resolved.
  const int decim = std::max(1, sr / 2000);
  std::vector<double> ref_ds;
  std::vector<double> res_ds;
  ref_ds.reserve(n / decim + 1);
  res_ds.reserve(n / decim + 1);
  for (size_t i = 0; i < n; i += decim) {
    ref_ds.push_back(reference[rb + i]);
    res_ds.push_back(residual[i]);
  }

  const double fs_ds = static_cast<double>(sr) / decim;
  const int min_lag = std::max(1, static_cast<int>(0.018 * fs_ds));
  const int max_lag = std::min(
      static_cast<int>(0.400 * fs_ds),
      static_cast<int>(ref_ds.size() / 3));
  const int lag_step = std::max(1, static_cast<int>(0.002 * fs_ds));
  double best_echo_corr = 0.0;
  for (int lag = min_lag; lag <= max_lag; lag += lag_step) {
    double aa = 0.0, bb = 0.0, ab = 0.0;
    size_t count = 0;
    for (size_t i = static_cast<size_t>(lag); i < ref_ds.size(); ++i) {
      const double x = ref_ds[i - lag];
      const double y = res_ds[i];
      aa += x * x;
      bb += y * y;
      ab += x * y;
      ++count;
    }
    if (count > 100 && aa > kEps && bb > kEps) {
      best_echo_corr = std::max(
          best_echo_corr, std::abs(ab / std::sqrt(aa * bb)));
    }
  }
  const double residual_presence =
      residual_ratio / (residual_ratio + 0.08);
  out.echo = Clamp(
      1.45 * best_echo_corr * residual_presence, 0.0, 1.0);

  // Reference-silent regions expose additive background noise without
  // confusing it with legitimate speech energy.
  const size_t block = static_cast<size_t>(std::max(1, sr / 50));  // 20 ms
  double peak_ref_rms = 0.0;
  for (size_t i = 0; i + block <= n; i += block) {
    peak_ref_rms = std::max(
        peak_ref_rms,
        Rms(reference, rb + i, rb + i + block));
  }
  double inactive_e = 0.0;
  size_t inactive_n = 0;
  for (size_t i = 0; i + block <= n; i += block) {
    const double frame_ref = Rms(reference, rb + i, rb + i + block);
    if (frame_ref <= peak_ref_rms * 0.08) {
      for (size_t j = i; j < i + block; ++j) {
        inactive_e += residual[j] * residual[j];
        ++inactive_n;
      }
    }
  }
  if (inactive_n > 0 && peak_ref_rms > 1e-7) {
    const double inactive_rms = std::sqrt(inactive_e / inactive_n);
    const double q = inactive_rms / (gain * peak_ref_rms + kEps);
    out.inactive_noise = Clamp(q / (q + 0.035), 0.0, 1.0);
  }

  // Detect saturation even when a clipped file has later been normalized.
  // The relevant signal is excess occupancy very close to the waveform peak.
  double peak_d = 0.0, peak_r = 0.0;
  for (size_t i = 0; i < n; ++i) {
    peak_d = std::max(peak_d, std::abs(static_cast<double>(degraded[db + i])));
    peak_r = std::max(peak_r, std::abs(static_cast<double>(reference[rb + i])));
  }
  auto peak_occupancy = [&](const std::vector<float>& x,
                            size_t begin,
                            double peak) {
    if (peak < 1e-6) return 0.0;
    const double tol = std::max(2.5 / 32768.0, peak * 0.0025);
    size_t count = 0;
    for (size_t i = 0; i < n; ++i) {
      if (std::abs(std::abs(static_cast<double>(x[begin + i])) - peak) <= tol) {
        ++count;
      }
    }
    return static_cast<double>(count) / n;
  };
  const double occ_d = peak_occupancy(degraded, db, peak_d);
  const double occ_r = peak_occupancy(reference, rb, peak_r);
  out.clipping_plateau = Clamp((occ_d - occ_r) * 45.0, 0.0, 1.0);

  // Track local envelope delay around an already globally aligned pair.
  // Insertions, deletions and time edits manifest as local path excursions.
  const size_t env_block = static_cast<size_t>(std::max(1, sr / 100));  // 10 ms
  std::vector<double> er, ed;
  for (size_t i = 0; i + env_block <= n; i += env_block) {
    er.push_back(Rms(reference, rb + i, rb + i + env_block));
    ed.push_back(Rms(degraded, db + i, db + i + env_block));
  }
  const double max_er =
      er.empty() ? 0.0 : *std::max_element(er.begin(), er.end());
  const double max_ed =
      ed.empty() ? 0.0 : *std::max_element(ed.begin(), ed.end());
  if (max_er > kEps && max_ed > kEps) {
    for (double& v : er) v /= max_er;
    for (double& v : ed) v /= max_ed;

    const size_t window = 40;  // 400 ms
    const size_t hop = 10;     // 100 ms
    const int radius = 40;     // +/- 400 ms
    std::vector<double> shifts;
    int weak = 0, total = 0;
    for (size_t begin = 0; begin + window <= er.size(); begin += hop) {
      double activity = 0.0;
      for (size_t i = begin; i < begin + window; ++i) activity += er[i];
      if (activity / window < 0.08) continue;

      double best = -2.0;
      int best_shift = 0;
      for (int s = -radius; s <= radius; ++s) {
        const double corr =
            CorrAtShift(er, ed, s, begin, begin + window);
        if (corr > best) {
          best = corr;
          best_shift = s;
        }
      }
      shifts.push_back(best_shift);
      if (best < 0.70) ++weak;
      ++total;
    }
    if (!shifts.empty()) {
      std::vector<double> abs_shifts;
      abs_shifts.reserve(shifts.size());
      for (double s : shifts) abs_shifts.push_back(std::abs(s));
      const double shift_pen = Clamp(Median(abs_shifts) / 18.0, 0.0, 1.0);

      double variation = 0.0;
      for (size_t i = 1; i < shifts.size(); ++i) {
        variation += std::abs(shifts[i] - shifts[i - 1]);
      }
      variation = shifts.size() > 1
                      ? Clamp(variation / ((shifts.size() - 1) * 10.0), 0.0, 1.0)
                      : 0.0;
      const double weak_fraction =
          total ? static_cast<double>(weak) / total : 0.0;

      out.temporal_edit = Clamp(
          0.50 * shift_pen +
          0.32 * variation +
          0.18 * weak_fraction,
          0.0,
          1.0);
    }
  }

  return out;
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

  const TelecomDiagnostics telecom =
      AnalyzeTelecomImpairments(r, d, sr, delay);
  out.advanced.echo_likelihood = telecom.echo;
  out.advanced.residual_energy = telecom.residual;
  out.advanced.temporal_edit = telecom.temporal_edit;
  out.advanced.clipping_plateau = telecom.clipping_plateau;
  out.advanced.inactive_noise = telecom.inactive_noise;

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
      out.advanced.echo_likelihood;
  final_penalty +=
      std::max(0.0, c.advanced_residual_weight) *
      out.advanced.residual_energy;
  final_penalty +=
      std::max(0.0, c.advanced_temporal_edit_weight) *
      out.advanced.temporal_edit;
  final_penalty +=
      std::max(0.0, c.advanced_clip_plateau_weight) *
      out.advanced.clipping_plateau;
  final_penalty +=
      std::max(0.0, c.advanced_inactive_noise_weight) *
      out.advanced.inactive_noise;

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
    << r.advanced.bad_interval_severity
    << ",\"echo_likelihood\":" << r.advanced.echo_likelihood
    << ",\"residual_energy\":" << r.advanced.residual_energy
    << ",\"temporal_edit\":" << r.advanced.temporal_edit
    << ",\"clipping_plateau\":" << r.advanced.clipping_plateau
    << ",\"inactive_noise\":" << r.advanced.inactive_noise << "}}";
  return o.str();
}

}  // namespace openvq
