#include "openvq/openvq.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <tuple>

namespace openvq {
namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr double kEps = 1e-12;

double Clamp(double x, double lo, double hi) {
  return std::max(lo, std::min(hi, x));
}

double Db(double x) {
  return 20.0 * std::log10(std::max(x, 1e-9));
}

double Rms(const std::vector<float>& x, size_t begin, size_t end) {
  if (begin >= end || begin >= x.size()) return 0.0;
  end = std::min(end, x.size());
  double sum = 0.0;
  for (size_t i = begin; i < end; ++i) sum += static_cast<double>(x[i]) * x[i];
  return std::sqrt(sum / static_cast<double>(end - begin));
}

void RemoveDc(std::vector<float>* x) {
  if (x->empty()) return;
  const double mean = std::accumulate(x->begin(), x->end(), 0.0) / x->size();
  for (float& v : *x) v = static_cast<float>(v - mean);
}

std::vector<float> ResampleSinc(const std::vector<float>& in, int in_rate, int out_rate) {
  if (in_rate <= 0 || out_rate <= 0) throw std::invalid_argument("sample rate must be positive");
  if (in.empty() || in_rate == out_rate) return in;
  const double ratio = static_cast<double>(out_rate) / in_rate;
  const size_t out_n = static_cast<size_t>(std::llround(in.size() * ratio));
  std::vector<float> out(out_n, 0.0f);
  constexpr int radius = 16;
  const double cutoff = std::min(1.0, ratio) * 0.94;
  for (size_t n = 0; n < out_n; ++n) {
    const double src = static_cast<double>(n) / ratio;
    const int center = static_cast<int>(std::floor(src));
    double acc = 0.0;
    double norm = 0.0;
    for (int k = center - radius + 1; k <= center + radius; ++k) {
      if (k < 0 || k >= static_cast<int>(in.size())) continue;
      const double d = src - k;
      const double z = kPi * d * cutoff;
      const double sinc = std::abs(z) < 1e-9 ? 1.0 : std::sin(z) / z;
      const double wd = d / radius;
      const double window = std::abs(wd) <= 1.0 ? 0.5 * (1.0 + std::cos(kPi * wd)) : 0.0;
      const double w = cutoff * sinc * window;
      acc += w * in[k];
      norm += w;
    }
    out[n] = static_cast<float>(norm == 0.0 ? 0.0 : acc / norm);
  }
  return out;
}

std::vector<double> Envelope(const std::vector<float>& x, int sample_rate, int hz) {
  const int block = std::max(1, sample_rate / hz);
  std::vector<double> env;
  env.reserve((x.size() + block - 1) / block);
  for (size_t i = 0; i < x.size(); i += block) {
    const size_t e = std::min(x.size(), i + static_cast<size_t>(block));
    double s = 0.0;
    for (size_t j = i; j < e; ++j) s += std::abs(x[j]);
    env.push_back(s / std::max<size_t>(1, e - i));
  }
  return env;
}

double NormalizedCorrelation(const std::vector<double>& a,
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
  if (n < 8 || aa < kEps || bb < kEps) return -1.0;
  return ab / std::sqrt(aa * bb);
}

int EstimateDelayBins(const std::vector<double>& ref,
                      const std::vector<double>& deg,
                      int max_shift,
                      size_t begin = 0,
                      size_t end = std::numeric_limits<size_t>::max()) {
  end = std::min(end, ref.size());
  int best = 0;
  double best_corr = -2.0;
  for (int s = -max_shift; s <= max_shift; ++s) {
    const double c = NormalizedCorrelation(ref, deg, s, begin, end);
    if (c > best_corr) {
      best_corr = c;
      best = s;
    }
  }
  return best;
}

std::pair<double, double> EstimateDelayAndDrift(const std::vector<float>& ref,
                                                const std::vector<float>& deg,
                                                int sr,
                                                int max_delay_ms) {
  constexpr int kEnvHz = 200;
  const auto re = Envelope(ref, sr, kEnvHz);
  const auto de = Envelope(deg, sr, kEnvHz);
  const int max_shift = max_delay_ms * kEnvHz / 1000;
  const int global = EstimateDelayBins(re, de, max_shift);

  std::vector<double> times;
  std::vector<double> delays;
  constexpr int segments = 5;
  for (int s = 0; s < segments; ++s) {
    const size_t b = re.size() * s / segments;
    const size_t e = re.size() * (s + 1) / segments;
    if (e <= b + 20) continue;
    const int local_radius = std::max(2, kEnvHz / 20);
    int best = global;
    double best_corr = -2.0;
    for (int d = global - local_radius; d <= global + local_radius; ++d) {
      const double c = NormalizedCorrelation(re, de, d, b, e);
      if (c > best_corr) {
        best_corr = c;
        best = d;
      }
    }
    if (best_corr > 0.15) {
      const double t = (static_cast<double>(b + e) * 0.5) / kEnvHz;
      times.push_back(t);
      delays.push_back(static_cast<double>(best) / kEnvHz);
    }
  }

  double drift_ppm = 0.0;
  if (times.size() >= 3) {
    const double mt = std::accumulate(times.begin(), times.end(), 0.0) / times.size();
    const double md = std::accumulate(delays.begin(), delays.end(), 0.0) / delays.size();
    double num = 0.0, den = 0.0;
    for (size_t i = 0; i < times.size(); ++i) {
      num += (times[i] - mt) * (delays[i] - md);
      den += (times[i] - mt) * (times[i] - mt);
    }
    if (den > kEps) drift_ppm = Clamp((num / den) * 1e6, -5000.0, 5000.0);
  }
  return {static_cast<double>(global) * 1000.0 / kEnvHz, drift_ppm};
}

size_t NextPow2(size_t n) {
  size_t p = 1;
  while (p < n) p <<= 1;
  return p;
}

void Fft(std::vector<std::complex<double>>* a) {
  auto& x = *a;
  const size_t n = x.size();
  for (size_t i = 1, j = 0; i < n; ++i) {
    size_t bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) std::swap(x[i], x[j]);
  }
  for (size_t len = 2; len <= n; len <<= 1) {
    const double ang = -2.0 * kPi / len;
    const std::complex<double> wlen(std::cos(ang), std::sin(ang));
    for (size_t i = 0; i < n; i += len) {
      std::complex<double> w(1.0, 0.0);
      for (size_t j = 0; j < len / 2; ++j) {
        const auto u = x[i + j];
        const auto v = x[i + j + len / 2] * w;
        x[i + j] = u + v;
        x[i + j + len / 2] = u - v;
        w *= wlen;
      }
    }
  }
}

std::vector<double> PowerSpectrum(const std::vector<float>& x, size_t begin, size_t length) {
  const size_t nfft = NextPow2(length);
  std::vector<std::complex<double>> a(nfft, {0.0, 0.0});
  for (size_t i = 0; i < length; ++i) {
    const double w = 0.5 - 0.5 * std::cos(2.0 * kPi * i / std::max<size_t>(1, length - 1));
    const double v = begin + i < x.size() ? x[begin + i] : 0.0;
    a[i] = v * w;
  }
  Fft(&a);
  std::vector<double> p(nfft / 2 + 1);
  for (size_t i = 0; i < p.size(); ++i) p[i] = std::norm(a[i]) + 1e-14;
  return p;
}

std::vector<double> LogBandEnergies(const std::vector<double>& p, int sr, int bands = 32) {
  const double nyq = sr * 0.5;
  const double f_lo = 50.0;
  const double f_hi = std::min(20000.0, nyq * 0.98);
  std::vector<double> out(bands, -120.0);
  const size_t nfft = (p.size() - 1) * 2;
  for (int b = 0; b < bands; ++b) {
    const double t0 = static_cast<double>(b) / bands;
    const double t1 = static_cast<double>(b + 1) / bands;
    const double lo = f_lo * std::pow(f_hi / f_lo, t0);
    const double hi = f_lo * std::pow(f_hi / f_lo, t1);
    size_t k0 = static_cast<size_t>(std::floor(lo * nfft / sr));
    size_t k1 = static_cast<size_t>(std::ceil(hi * nfft / sr));
    k0 = std::min(k0, p.size() - 1);
    k1 = std::min(std::max(k1, k0 + 1), p.size());
    double e = 0.0;
    for (size_t k = k0; k < k1; ++k) e += p[k];
    out[b] = 10.0 * std::log10(e / std::max<size_t>(1, k1 - k0) + 1e-14);
  }
  return out;
}

double Pearson(const std::vector<double>& a, const std::vector<double>& b) {
  if (a.size() != b.size() || a.empty()) return 0.0;
  const double ma = std::accumulate(a.begin(), a.end(), 0.0) / a.size();
  const double mb = std::accumulate(b.begin(), b.end(), 0.0) / b.size();
  double aa = 0.0, bb = 0.0, ab = 0.0;
  for (size_t i = 0; i < a.size(); ++i) {
    const double x = a[i] - ma;
    const double y = b[i] - mb;
    aa += x * x;
    bb += y * y;
    ab += x * y;
  }
  if (aa < kEps || bb < kEps) return 0.0;
  return Clamp(ab / std::sqrt(aa * bb), -1.0, 1.0);
}

BandwidthClass DetectBandwidth(const std::vector<float>& x, int sr) {
  if (x.empty()) return BandwidthClass::kUnknown;
  const size_t len = std::min<size_t>(x.size(), static_cast<size_t>(sr * 4));
  auto p = PowerSpectrum(x, 0, len);
  const size_t nfft = (p.size() - 1) * 2;
  auto band_power = [&](double lo, double hi) {
    size_t a = std::min(p.size() - 1, static_cast<size_t>(lo * nfft / sr));
    size_t b = std::min(p.size(), static_cast<size_t>(std::ceil(hi * nfft / sr)));
    double s = 0.0;
    for (size_t i = a; i < b; ++i) s += p[i];
    return s;
  };
  const double total = band_power(80, std::min(20000.0, sr * 0.49)) + kEps;
  const double above34 = band_power(3400, std::min(20000.0, sr * 0.49)) / total;
  const double above7 = band_power(7000, std::min(20000.0, sr * 0.49)) / total;
  const double above14 = band_power(14000, std::min(20000.0, sr * 0.49)) / total;
  if (above34 < 0.003) return BandwidthClass::kNarrowband;
  if (above7 < 0.003) return BandwidthClass::kWideband;
  if (above14 < 0.002) return BandwidthClass::kSuperWideband;
  return BandwidthClass::kFullband;
}

struct FrameStats {
  double similarity = 0.0;
  double missing = 0.0;
  double added = 0.0;
  double coloration = 0.0;
  double energy_ref = 0.0;
  double energy_deg = 0.0;
  double discontinuity = 0.0;
  bool active = false;
};

FrameStats CompareFrame(const std::vector<float>& ref,
                        const std::vector<float>& deg,
                        size_t rb,
                        long db,
                        size_t frame,
                        int sr,
                        double vad_db) {
  FrameStats fs;
  if (db < 0 || rb + frame > ref.size() || static_cast<size_t>(db) + frame > deg.size()) return fs;
  fs.energy_ref = Rms(ref, rb, rb + frame);
  fs.energy_deg = Rms(deg, static_cast<size_t>(db), static_cast<size_t>(db) + frame);
  fs.active = Db(fs.energy_ref) >= vad_db;
  if (!fs.active) return fs;

  auto rp = PowerSpectrum(ref, rb, frame);
  auto dp = PowerSpectrum(deg, static_cast<size_t>(db), frame);
  auto re = LogBandEnergies(rp, sr);
  auto de = LogBandEnergies(dp, sr);
  const double level_r = std::accumulate(re.begin(), re.end(), 0.0) / re.size();
  const double level_d = std::accumulate(de.begin(), de.end(), 0.0) / de.size();
  double miss = 0.0, add = 0.0, col = 0.0;
  for (size_t i = 0; i < re.size(); ++i) {
    const double spectral_delta = (de[i] - level_d) - (re[i] - level_r);
    col += std::abs(spectral_delta);
    const double level_delta = de[i] - re[i];
    miss += std::max(0.0, -level_delta - 1.5);
    add += std::max(0.0, level_delta - 1.5);
  }
  fs.coloration = Clamp(col / (re.size() * 18.0), 0.0, 1.0);
  fs.missing = Clamp(miss / (re.size() * 22.0), 0.0, 1.0);
  fs.added = Clamp(add / (re.size() * 22.0), 0.0, 1.0);
  const double corr = (Pearson(re, de) + 1.0) * 0.5;
  const double level_penalty = Clamp(std::abs(Db(fs.energy_deg + 1e-9) - Db(fs.energy_ref + 1e-9)) / 24.0, 0.0, 1.0);
  fs.similarity = Clamp(0.75 * corr + 0.25 * (1.0 - level_penalty), 0.0, 1.0);
  const double ratio = fs.energy_deg / (fs.energy_ref + 1e-9);
  const double hole = ratio < 0.22 ? Clamp((0.22 - ratio) / 0.22, 0.0, 1.0) : 0.0;
  fs.discontinuity = Clamp(std::max(hole, (0.45 - fs.similarity) * 1.8), 0.0, 1.0);
  return fs;
}

double Quantile(std::vector<double> v, double q) {
  if (v.empty()) return 0.0;
  q = Clamp(q, 0.0, 1.0);
  const size_t idx = static_cast<size_t>(q * (v.size() - 1));
  std::nth_element(v.begin(), v.begin() + idx, v.end());
  return v[idx];
}

}  // namespace

AnalysisResult Analyzer::Analyze(const AudioBuffer& reference,
                                 const AudioBuffer& degraded,
                                 const AnalysisOptions& options) const {
  if (reference.sample_rate <= 0 || degraded.sample_rate <= 0) {
    throw std::invalid_argument("invalid sample rate");
  }
  if (reference.samples.empty() || degraded.samples.empty()) {
    throw std::invalid_argument("empty audio");
  }

  std::vector<float> ref = ResampleSinc(reference.samples, reference.sample_rate, options.target_sample_rate);
  std::vector<float> deg = ResampleSinc(degraded.samples, degraded.sample_rate, options.target_sample_rate);
  RemoveDc(&ref);
  RemoveDc(&deg);
  const int sr = options.target_sample_rate;

  AnalysisResult out;
  out.bandwidth = DetectBandwidth(deg, sr);
  const auto [delay_ms, drift_ppm] = EstimateDelayAndDrift(ref, deg, sr, options.max_delay_ms);
  out.delay_ms = delay_ms;
  out.clock_drift_ppm = drift_ppm;
  const long global_delay = static_cast<long>(std::llround(delay_ms * sr / 1000.0));

  const size_t frame = static_cast<size_t>(std::max(1, options.frame_ms * sr / 1000));
  const size_t hop = static_cast<size_t>(std::max(1, options.hop_ms * sr / 1000));
  double max_frame_rms = 0.0;
  for (size_t rb = 0; rb + frame <= ref.size(); rb += hop) {
    max_frame_rms = std::max(max_frame_rms, Rms(ref, rb, rb + frame));
  }
  const double vad_db = std::max(-55.0, Db(max_frame_rms + 1e-9) + options.vad_relative_db);

  std::vector<double> misses, adds, cols, discontinuities, similarities, level_diffs;
  bool in_dropout = false;
  double dropout_start = 0.0;
  int dropout_frames = 0;
  int active_frames = 0;

  for (size_t rb = 0; rb + frame <= ref.size(); rb += hop) {
    const double time_s = static_cast<double>(rb) / sr;
    long expected = static_cast<long>(rb) + global_delay;
    expected += static_cast<long>(std::llround(time_s * drift_ppm * 1e-6 * sr));

    long best_db = expected;
    FrameStats best = CompareFrame(ref, deg, rb, best_db, frame, sr, vad_db);
    if (best.active && options.enable_local_alignment && best.energy_deg > 0.20 * best.energy_ref) {
      const int local = std::max(1, sr * 10 / 1000);
      for (int delta = -local; delta <= local; delta += std::max(1, sr / 1000)) {
        const long candidate = expected + delta;
        FrameStats cur = CompareFrame(ref, deg, rb, candidate, frame, sr, vad_db);
        if (cur.active && cur.similarity > best.similarity) {
          best = cur;
          best_db = candidate;
        }
      }
    }
    if (!best.active) continue;
    ++active_frames;
    misses.push_back(best.missing);
    adds.push_back(best.added);
    cols.push_back(best.coloration);
    discontinuities.push_back(best.discontinuity);
    similarities.push_back(best.similarity);
    level_diffs.push_back(std::abs(Db(best.energy_deg + 1e-9) - Db(best.energy_ref + 1e-9)));

    out.frames.push_back(FrameQuality{
        time_s * 1000.0, best.similarity, best.missing, best.added, best.discontinuity});

    const bool is_dropout = best.discontinuity > 0.58;
    if (is_dropout && !in_dropout) {
      in_dropout = true;
      dropout_start = time_s * 1000.0;
      dropout_frames = 1;
    } else if (is_dropout) {
      ++dropout_frames;
    } else if (in_dropout) {
      const double duration = dropout_frames * options.hop_ms + options.frame_ms;
      out.events.push_back({EventType::kDropout, dropout_start, duration,
                            Clamp(Quantile(discontinuities, 0.9), 0.0, 1.0)});
      in_dropout = false;
      dropout_frames = 0;
    }
  }
  if (in_dropout) {
    out.events.push_back({EventType::kDropout, dropout_start,
                          static_cast<double>(dropout_frames * options.hop_ms + options.frame_ms), 1.0});
  }

  out.active_speech_seconds = active_frames * options.hop_ms / 1000.0;
  if (active_frames == 0) {
    out.mos = 1.0;
    out.confidence = 0.0;
    return out;
  }

  auto mean = [](const std::vector<double>& v) {
    return v.empty() ? 0.0 : std::accumulate(v.begin(), v.end(), 0.0) / v.size();
  };
  out.missing_disturbance = mean(misses);
  out.added_disturbance = mean(adds);
  const double col_pen = mean(cols);
  const double disc_pen = mean(discontinuities);
  const double worst_disc = Quantile(discontinuities, 0.90);
  out.bad_section_fraction = static_cast<double>(std::count_if(
      discontinuities.begin(), discontinuities.end(), [](double x) { return x > 0.45; })) / active_frames;

  size_t clipped = 0;
  for (float v : deg) if (std::abs(v) >= 0.995f) ++clipped;
  out.clipping_ratio = deg.empty() ? 0.0 : static_cast<double>(clipped) / deg.size();
  if (out.clipping_ratio > 0.0005) {
    out.events.push_back({EventType::kClipping, 0.0,
                          1000.0 * deg.size() / sr,
                          Clamp(out.clipping_ratio * 80.0, 0.0, 1.0)});
  }

  std::vector<double> deg_frame_db;
  for (size_t i = 0; i + frame <= deg.size(); i += hop) {
    deg_frame_db.push_back(Db(Rms(deg, i, i + frame) + 1e-9));
  }
  const double noise_floor_db = Quantile(deg_frame_db, 0.15);
  const double speech_db = Db(max_frame_rms + 1e-9);
  const double snr_proxy = speech_db - noise_floor_db;
  const double noise_pen = Clamp((28.0 - snr_proxy) / 28.0, 0.0, 1.0) * 0.65
                         + out.added_disturbance * 0.35;
  const double loud_pen = Clamp(mean(level_diffs) / 18.0, 0.0, 1.0);
  const double clip_pen = Clamp(out.clipping_ratio * 40.0, 0.0, 1.0);

  out.dimensions.coloration = Clamp(5.0 - 4.0 * col_pen, 1.0, 5.0);
  out.dimensions.noisiness = Clamp(5.0 - 4.0 * noise_pen, 1.0, 5.0);
  out.dimensions.discontinuity =
      Clamp(5.0 - 4.0 * Clamp(0.55 * disc_pen + 0.45 * worst_disc, 0.0, 1.0), 1.0, 5.0);
  out.dimensions.loudness = Clamp(5.0 - 4.0 * loud_pen, 1.0, 5.0);

  const auto& c = options.calibration;
  double penalty = c.bias;
  penalty += c.missing_weight * out.missing_disturbance;
  penalty += c.added_weight * out.added_disturbance;
  penalty += c.coloration_weight * (5.0 - out.dimensions.coloration) / 4.0;
  penalty += c.noisiness_weight * (5.0 - out.dimensions.noisiness) / 4.0;
  penalty += c.discontinuity_weight * (5.0 - out.dimensions.discontinuity) / 4.0;
  penalty += c.loudness_weight * (5.0 - out.dimensions.loudness) / 4.0;
  penalty += c.clipping_weight * clip_pen;
  penalty += c.bad_section_weight * out.bad_section_fraction;
  if (options.visqol_mos.has_value()) {
    const double visqol_penalty =
        Clamp((5.0 - *options.visqol_mos) / 4.0, 0.0, 1.0);
    penalty +=
        std::max(0.0, c.visqol_penalty_weight) * visqol_penalty;
  }
  out.mos = Clamp(5.0 - penalty, 1.0, 5.0);

  const double active_factor = Clamp(out.active_speech_seconds / 3.0, 0.0, 1.0);
  const double align_factor = Clamp(mean(similarities), 0.0, 1.0);
  out.confidence = Clamp(0.25 + 0.45 * active_factor + 0.30 * align_factor, 0.0, 1.0);
  return out;
}

std::string ToString(BandwidthClass b) {
  switch (b) {
    case BandwidthClass::kNarrowband: return "NB";
    case BandwidthClass::kWideband: return "WB";
    case BandwidthClass::kSuperWideband: return "SWB";
    case BandwidthClass::kFullband: return "FB";
    default: return "UNKNOWN";
  }
}

std::string ToString(EventType t) {
  switch (t) {
    case EventType::kDropout: return "dropout";
    case EventType::kClipping: return "clipping";
    case EventType::kNoiseBurst: return "noise_burst";
    case EventType::kTimeWarp: return "time_warp";
  }
  return "unknown";
}

std::string ToJson(const AnalysisResult& r) {
  std::ostringstream o;
  o << std::fixed << std::setprecision(6);
  o << "{\"mos\":" << r.mos
    << ",\"confidence\":" << r.confidence
    << ",\"bandwidth\":\"" << ToString(r.bandwidth) << "\""
    << ",\"delay_ms\":" << r.delay_ms
    << ",\"clock_drift_ppm\":" << r.clock_drift_ppm
    << ",\"active_speech_seconds\":" << r.active_speech_seconds
    << ",\"clipping_ratio\":" << r.clipping_ratio
    << ",\"missing_disturbance\":" << r.missing_disturbance
    << ",\"added_disturbance\":" << r.added_disturbance
    << ",\"bad_section_fraction\":" << r.bad_section_fraction
    << ",\"dimensions\":{"
    << "\"coloration\":" << r.dimensions.coloration
    << ",\"noisiness\":" << r.dimensions.noisiness
    << ",\"discontinuity\":" << r.dimensions.discontinuity
    << ",\"loudness\":" << r.dimensions.loudness << "}"
    << ",\"events\":[";
  for (size_t i = 0; i < r.events.size(); ++i) {
    if (i) o << ',';
    const auto& e = r.events[i];
    o << "{\"type\":\"" << ToString(e.type) << "\",\"start_ms\":" << e.start_ms
      << ",\"duration_ms\":" << e.duration_ms << ",\"severity\":" << e.severity << "}";
  }
  o << "]}";
  return o.str();
}

namespace {

uint16_t U16(std::istream& in) {
  uint8_t b[2];
  in.read(reinterpret_cast<char*>(b), 2);
  return static_cast<uint16_t>(b[0] | (b[1] << 8));
}

uint32_t U32(std::istream& in) {
  uint8_t b[4];
  in.read(reinterpret_cast<char*>(b), 4);
  return static_cast<uint32_t>(b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24));
}

}  // namespace

AudioBuffer LoadWav(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open WAV: " + path);
  char riff[4], wave[4];
  in.read(riff, 4);
  U32(in);
  in.read(wave, 4);
  if (std::string(riff, 4) != "RIFF" || std::string(wave, 4) != "WAVE") {
    throw std::runtime_error("invalid WAV");
  }

  uint16_t format = 0, channels = 0, bits = 0;
  uint32_t sr = 0;
  std::vector<uint8_t> data;
  while (in && (!sr || data.empty())) {
    char id[4];
    if (!in.read(id, 4)) break;
    uint32_t size = U32(in);
    std::string sid(id, 4);
    if (sid == "fmt ") {
      format = U16(in);
      channels = U16(in);
      sr = U32(in);
      U32(in);
      U16(in);
      bits = U16(in);
      if (size > 16) in.seekg(size - 16, std::ios::cur);
    } else if (sid == "data") {
      data.resize(size);
      in.read(reinterpret_cast<char*>(data.data()), size);
    } else {
      in.seekg(size, std::ios::cur);
    }
    if (size & 1) in.seekg(1, std::ios::cur);
  }
  if (!sr || channels == 0 || data.empty()) throw std::runtime_error("incomplete WAV");

  AudioBuffer out;
  out.sample_rate = static_cast<int>(sr);
  if (format == 1 && bits == 16) {
    const size_t frames = data.size() / (channels * 2);
    out.samples.resize(frames);
    for (size_t f = 0; f < frames; ++f) {
      double s = 0.0;
      for (uint16_t c = 0; c < channels; ++c) {
        const size_t i = (f * channels + c) * 2;
        int16_t v = static_cast<int16_t>(data[i] | (data[i + 1] << 8));
        s += v / 32768.0;
      }
      out.samples[f] = static_cast<float>(s / channels);
    }
  } else if (format == 3 && bits == 32) {
    const size_t frames = data.size() / (channels * 4);
    out.samples.resize(frames);
    for (size_t f = 0; f < frames; ++f) {
      double s = 0.0;
      for (uint16_t c = 0; c < channels; ++c) {
        float v;
        std::memcpy(&v, data.data() + (f * channels + c) * 4, 4);
        s += v;
      }
      out.samples[f] = static_cast<float>(s / channels);
    }
  } else {
    throw std::runtime_error("WAV must be PCM16 or IEEE float32");
  }
  return out;
}

}  // namespace openvq
