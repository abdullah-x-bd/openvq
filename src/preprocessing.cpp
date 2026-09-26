#include "openvq/preprocessing.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <utility>
#include <vector>

namespace openvq {
namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr double kEps = 1e-12;

double Clamp(double x,double lo,double hi){return std::max(lo,std::min(hi,x));}

double Rms(const std::vector<float>& x,std::size_t b,std::size_t e){
  if(b>=e||b>=x.size())return 0.0;
  e=std::min(e,x.size());
  double s=0.0;
  for(std::size_t i=b;i<e;++i)s+=static_cast<double>(x[i])*x[i];
  return std::sqrt(s/std::max<std::size_t>(1,e-b));
}

double Db(double x){return 20.0*std::log10(std::max(x,1e-9));}

void RemoveDc(std::vector<float>* x){
  if(x->empty())return;
  const double m=std::accumulate(x->begin(),x->end(),0.0)/x->size();
  for(float& v:*x)v=static_cast<float>(v-m);
}

std::vector<float> ResampleSinc(const std::vector<float>& in,int in_rate,int out_rate){
  if(in_rate<=0||out_rate<=0)throw std::invalid_argument("sample rate must be positive");
  if(in.empty()||in_rate==out_rate)return in;
  const double ratio=static_cast<double>(out_rate)/in_rate;
  const std::size_t out_n=static_cast<std::size_t>(std::llround(in.size()*ratio));
  std::vector<float> out(out_n,0.0f);
  constexpr int radius=16;
  const double cutoff=std::min(1.0,ratio)*0.94;
  for(std::size_t n=0;n<out_n;++n){
    const double src=static_cast<double>(n)/ratio;
    const int center=static_cast<int>(std::floor(src));
    double acc=0.0,norm=0.0;
    for(int k=center-radius+1;k<=center+radius;++k){
      if(k<0||k>=static_cast<int>(in.size()))continue;
      const double d=src-k;
      const double z=kPi*d*cutoff;
      const double sinc=std::abs(z)<1e-9?1.0:std::sin(z)/z;
      const double wd=d/radius;
      const double window=std::abs(wd)<=1.0?0.5*(1.0+std::cos(kPi*wd)):0.0;
      const double w=cutoff*sinc*window;
      acc+=w*in[k];norm+=w;
    }
    out[n]=static_cast<float>(norm==0.0?0.0:acc/norm);
  }
  return out;
}

std::vector<double> Envelope(const std::vector<float>& x,int sr,int hz){
  const int block=std::max(1,sr/hz);
  std::vector<double> out;
  out.reserve((x.size()+block-1)/block);
  for(std::size_t b=0;b<x.size();b+=block){
    const std::size_t e=std::min(x.size(),b+static_cast<std::size_t>(block));
    double s=0.0;
    for(std::size_t i=b;i<e;++i)s+=std::abs(x[i]);
    out.push_back(s/std::max<std::size_t>(1,e-b));
  }
  return out;
}

double Corr(const std::vector<double>& a,const std::vector<double>& b,int shift,
            std::size_t begin,std::size_t end){
  end=std::min(end,a.size());
  double aa=0,bb=0,ab=0;std::size_t n=0;
  for(std::size_t i=begin;i<end;++i){
    const long j=static_cast<long>(i)+shift;
    if(j<0||j>=static_cast<long>(b.size()))continue;
    const double x=a[i],y=b[static_cast<std::size_t>(j)];
    aa+=x*x;bb+=y*y;ab+=x*y;++n;
  }
  if(n<8||aa<kEps||bb<kEps)return -1.0;
  return ab/std::sqrt(aa*bb);
}

std::pair<int,double> BestShift(const std::vector<double>& a,
                                const std::vector<double>& b,
                                int lo,int hi,
                                std::size_t begin,std::size_t end){
  int best=0;double best_c=-2.0;
  for(int s=lo;s<=hi;++s){
    const double c=Corr(a,b,s,begin,end);
    if(c>best_c){best_c=c;best=s;}
  }
  return {best,best_c};
}

AlignmentMap BuildAlignment(const std::vector<float>& ref,
                            const std::vector<float>& deg,
                            int sr,const AnalysisOptions& options){
  constexpr int env_hz=200;
  const auto re=Envelope(ref,sr,env_hz);
  const auto de=Envelope(deg,sr,env_hz);
  const int max_shift=std::max(1,options.max_delay_ms*env_hz/1000);
  auto global=BestShift(re,de,-max_shift,max_shift,0,re.size());

  AlignmentMap out;
  out.sample_rate=sr;
  out.global_delay_samples=
      static_cast<double>(global.first)*sr/env_hz;

  if(!options.enable_local_alignment||re.size()<40){
    out.knots.push_back({0.0,out.global_delay_samples,
                         Clamp((global.second+1.0)*0.5,0.0,1.0)});
    out.knots.push_back({static_cast<double>(ref.size()),
                         static_cast<double>(ref.size())+out.global_delay_samples,
                         Clamp((global.second+1.0)*0.5,0.0,1.0)});
    out.mean_confidence=Clamp((global.second+1.0)*0.5,0.0,1.0);
    return out;
  }

  constexpr int segments=12;
  const int radius=std::max(2,40*env_hz/1000);
  double previous_delay_bins=global.first;
  std::vector<double> times,delays,conf;
  for(int seg=0;seg<segments;++seg){
    const std::size_t b=re.size()*seg/segments;
    const std::size_t e=re.size()*(seg+1)/segments;
    if(e<=b+12)continue;
    const int pred=static_cast<int>(std::llround(previous_delay_bins));
    auto local=BestShift(re,de,pred-radius,pred+radius,b,e);
    // A low-correlation region is evidence of missing/unmatched content, not a
    // license for the aligner to jump to another phoneme.
    double chosen=previous_delay_bins;
    if(local.second>=0.15){
      const double center_s=(static_cast<double>(b+e)*0.5)/env_hz;
      const double prev_s=times.empty()?center_s:times.back();
      const double dt=std::max(0.05,center_s-prev_s);
      // Bound path slope to clock drift plus modest local jitter. This prevents
      // alignment from warping around a genuinely missing word.
      const double max_change=std::max(1.0,dt*env_hz*0.008+2.0);
      chosen=Clamp(local.first,previous_delay_bins-max_change,
                   previous_delay_bins+max_change);
    }
    const double center_bin=static_cast<double>(b+e)*0.5;
    const double ref_sample=center_bin*sr/env_hz;
    const double delay_samples=chosen*sr/env_hz;
    out.knots.push_back({ref_sample,ref_sample+delay_samples,
                         Clamp((local.second+1.0)*0.5,0.0,1.0)});
    times.push_back(ref_sample/sr);
    delays.push_back(delay_samples/sr);
    conf.push_back(out.knots.back().confidence);
    previous_delay_bins=chosen;
  }

  if(out.knots.empty()){
    out.knots.push_back({0.0,out.global_delay_samples,
                         Clamp((global.second+1.0)*0.5,0.0,1.0)});
  }
  if(out.knots.front().reference_sample>0.0){
    const double d=out.knots.front().degraded_sample-
                   out.knots.front().reference_sample;
    out.knots.insert(out.knots.begin(),{0.0,d,out.knots.front().confidence});
  }
  if(out.knots.back().reference_sample<static_cast<double>(ref.size())){
    const double d=out.knots.back().degraded_sample-
                   out.knots.back().reference_sample;
    out.knots.push_back({static_cast<double>(ref.size()),
                         static_cast<double>(ref.size())+d,
                         out.knots.back().confidence});
  }

  if(times.size()>=3){
    const double mt=std::accumulate(times.begin(),times.end(),0.0)/times.size();
    const double md=std::accumulate(delays.begin(),delays.end(),0.0)/delays.size();
    double num=0,den=0;
    for(std::size_t i=0;i<times.size();++i){
      num+=(times[i]-mt)*(delays[i]-md);
      den+=(times[i]-mt)*(times[i]-mt);
    }
    if(den>kEps)out.clock_drift_ppm=Clamp(num/den*1e6,-5000.0,5000.0);
  }
  out.mean_confidence=conf.empty()?Clamp((global.second+1.0)*0.5,0.0,1.0):
      std::accumulate(conf.begin(),conf.end(),0.0)/conf.size();
  return out;
}

}  // namespace

double AlignmentMap::MapReferenceSample(double reference_sample) const{
  if(knots.empty())return reference_sample+global_delay_samples;
  if(reference_sample<=knots.front().reference_sample){
    return knots.front().degraded_sample+
           (reference_sample-knots.front().reference_sample);
  }
  if(reference_sample>=knots.back().reference_sample){
    return knots.back().degraded_sample+
           (reference_sample-knots.back().reference_sample);
  }
  auto it=std::upper_bound(knots.begin(),knots.end(),reference_sample,
      [](double x,const AlignmentKnot& k){return x<k.reference_sample;});
  const auto& b=*it;const auto& a=*(it-1);
  const double t=(reference_sample-a.reference_sample)/
                 std::max(1e-9,b.reference_sample-a.reference_sample);
  return a.degraded_sample+t*(b.degraded_sample-a.degraded_sample);
}

bool AlignmentMap::Covers(double reference_sample,std::size_t frame_samples,
                          std::size_t degraded_size) const{
  const double b=MapReferenceSample(reference_sample);
  const double e=MapReferenceSample(reference_sample+frame_samples);
  return b>=0.0&&e>=0.0&&
         b+frame_samples<=static_cast<double>(degraded_size)&&
         e<=static_cast<double>(degraded_size)+1.0;
}

PreparedPair PreparePair(const AudioBuffer& reference,
                         const AudioBuffer& degraded,
                         const AnalysisOptions& options){
  if(reference.sample_rate<=0||degraded.sample_rate<=0)
    throw std::invalid_argument("invalid sample rate");
  if(reference.samples.empty()||degraded.samples.empty())
    throw std::invalid_argument("empty audio");
  PreparedPair out;
  out.sample_rate=options.target_sample_rate;
  out.reference=ResampleSinc(reference.samples,reference.sample_rate,out.sample_rate);
  out.degraded=ResampleSinc(degraded.samples,degraded.sample_rate,out.sample_rate);
  RemoveDc(&out.reference);RemoveDc(&out.degraded);
  out.alignment=BuildAlignment(out.reference,out.degraded,out.sample_rate,options);
  return out;
}

float SampleAlignedDegraded(const PreparedPair& pair,double reference_sample){
  const double p=pair.alignment.MapReferenceSample(reference_sample);
  if(p<0.0||p>=static_cast<double>(pair.degraded.size()-1))return 0.0f;
  const std::size_t i=static_cast<std::size_t>(std::floor(p));
  const double f=p-i;
  return static_cast<float>((1.0-f)*pair.degraded[i]+f*pair.degraded[i+1]);
}

ActiveLevelStats MeasureMatchedActiveLevel(
    const PreparedPair& pair,int frame_ms,int hop_ms,double vad_relative_db){
  ActiveLevelStats out;
  const std::size_t frame=static_cast<std::size_t>(
      std::max(1,frame_ms*pair.sample_rate/1000));
  const std::size_t hop=static_cast<std::size_t>(
      std::max(1,hop_ms*pair.sample_rate/1000));
  double peak=0.0;
  for(std::size_t rb=0;rb+frame<=pair.reference.size();rb+=hop)
    peak=std::max(peak,Rms(pair.reference,rb,rb+frame));
  const double vad=std::max(-55.0,Db(peak+1e-9)+vad_relative_db);

  double rr=0.0,dd=0.0;std::size_t samples=0;
  for(std::size_t rb=0;rb+frame<=pair.reference.size();rb+=hop){
    if(Db(Rms(pair.reference,rb,rb+frame)+1e-9)<vad)continue;
    ++out.active_frames;
    if(!pair.alignment.Covers(rb,frame,pair.degraded.size()))continue;
    ++out.covered_active_frames;
    for(std::size_t i=0;i<frame;++i){
      const double r=pair.reference[rb+i];
      const double d=SampleAlignedDegraded(pair,rb+i);
      rr+=r*r;dd+=d*d;++samples;
    }
  }
  if(out.active_frames){
    out.active_coverage_fraction=
        static_cast<double>(out.covered_active_frames)/out.active_frames;
    out.lost_active_speech_fraction=1.0-out.active_coverage_fraction;
  }
  if(samples){
    out.reference_db=Db(std::sqrt(rr/samples)+1e-9);
    out.degraded_db=Db(std::sqrt(dd/samples)+1e-9);
    out.delta_db=std::abs(out.degraded_db-out.reference_db);
  }
  return out;
}

}  // namespace openvq
