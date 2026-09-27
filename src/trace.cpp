#include "openvq/trace.h"
#include "openvq/preprocessing.h"
#include "trace_spectral.h"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <numeric>
#include <sstream>
#include <vector>

namespace openvq {
namespace {
constexpr double kEps=1e-12;

double Clamp(double x,double lo,double hi){return std::max(lo,std::min(hi,x));}
double Db(double x){return 20.0*std::log10(std::max(x,1e-9));}
double Rms(const std::vector<float>& x,std::size_t b,std::size_t e){
  if(b>=e||b>=x.size())return 0.0;e=std::min(e,x.size());
  double s=0;for(std::size_t i=b;i<e;++i)s+=double(x[i])*x[i];
  return std::sqrt(s/std::max<std::size_t>(1,e-b));
}
double Similarity(const std::array<double,64>& a,const std::array<double,64>& b){
  const double ma=std::accumulate(a.begin(),a.end(),0.0)/a.size();
  const double mb=std::accumulate(b.begin(),b.end(),0.0)/b.size();
  double aa=0,bb=0,ab=0;
  for(std::size_t i=0;i<a.size();++i){const double x=a[i]-ma,y=b[i]-mb;aa+=x*x;bb+=y*y;ab+=x*y;}
  if(aa<kEps||bb<kEps)return 0.0;
  return Clamp((ab/std::sqrt(aa*bb)+1)*0.5,0.0,1.0);
}
}  // namespace

TraceResult TraceAnalyzer::Analyze(const AudioBuffer& reference,
                                   const AudioBuffer& degraded,
                                   const AnalysisOptions& options) const {
  const PreparedPair pair=PreparePair(reference,degraded,options);
  TraceResult out;
  out.frontend_id=kFrontendId;out.trace_schema_id=kTraceSchemaId;out.trace_implementation_id=kTraceImplementationId;
  out.sample_rate=pair.sample_rate;out.frame_ms=options.frame_ms;out.hop_ms=options.hop_ms;
  out.global_delay_ms=pair.alignment.global_delay_samples*1000.0/pair.sample_rate;
  out.clock_drift_ppm=pair.alignment.clock_drift_ppm;
  out.alignment_confidence=pair.alignment.mean_confidence;
  out.input_clipping_ratio=pair.degraded_input_clipping_ratio;

  const std::size_t frame=std::max(1,options.frame_ms*pair.sample_rate/1000);
  const std::size_t hop=std::max(1,options.hop_ms*pair.sample_rate/1000);
  double peak=0;
  for(std::size_t rb=0;rb+frame<=pair.reference.size();rb+=hop)peak=std::max(peak,Rms(pair.reference,rb,rb+frame));
  const double vad=std::max(-55.0,Db(peak+1e-9)+options.vad_relative_db);

  for(std::size_t rb=0;rb+frame<=pair.reference.size();rb+=hop){
    TraceFrame q;
    q.start_ms=rb*1000.0/pair.sample_rate;
    q.mapped_start_ms=pair.alignment.MapReferenceSample(rb)*1000.0/pair.sample_rate;
    q.alignment_confidence=pair.alignment.ConfidenceAt(rb);
    q.reference_rms_db=Db(Rms(pair.reference,rb,rb+frame)+1e-9);
    q.reference_active=q.reference_rms_db>=vad;
    q.valid=pair.alignment.Covers(rb,frame,pair.degraded.size());
    q.unmatched=!q.valid;

    std::vector<float> rf(frame),df(frame,0.0f);
    for(std::size_t i=0;i<frame;++i)rf[i]=pair.reference[rb+i];
    if(q.valid){
      double dd=0;
      for(std::size_t i=0;i<frame;++i){df[i]=SampleAlignedDegraded(pair,rb+i);dd+=double(df[i])*df[i];}
      q.degraded_rms_db=Db(std::sqrt(dd/frame)+1e-9);
    }
    q.reference_bands_db=trace_internal::Bands(rf,pair.sample_rate);
    q.degraded_bands_db=trace_internal::Bands(df,pair.sample_rate);
    q.local_similarity=q.valid?Similarity(q.reference_bands_db,q.degraded_bands_db):0.0;
    out.frames.push_back(q);
  }
  return out;
}

std::string TraceToJson(const TraceResult& r){
  std::ostringstream o;o<<std::fixed<<std::setprecision(7);
  o<<"{\"frontend_id\":\""<<r.frontend_id<<"\",\"trace_schema_id\":\""<<r.trace_schema_id
   <<"\",\"trace_implementation_id\":\""<<r.trace_implementation_id
   <<"\",\"sample_rate\":"<<r.sample_rate<<",\"frame_ms\":"<<r.frame_ms<<",\"hop_ms\":"<<r.hop_ms
   <<",\"global_delay_ms\":"<<r.global_delay_ms<<",\"clock_drift_ppm\":"<<r.clock_drift_ppm
   <<",\"alignment_confidence\":"<<r.alignment_confidence<<",\"input_clipping_ratio\":"<<r.input_clipping_ratio
   <<",\"frames\":[";
  for(std::size_t n=0;n<r.frames.size();++n){
    if(n)o<<",";const auto& f=r.frames[n];
    o<<"{\"start_ms\":"<<f.start_ms<<",\"mapped_start_ms\":"<<f.mapped_start_ms
     <<",\"reference_active\":"<<(f.reference_active?"true":"false")
     <<",\"valid\":"<<(f.valid?"true":"false")<<",\"unmatched\":"<<(f.unmatched?"true":"false")
     <<",\"alignment_confidence\":"<<f.alignment_confidence<<",\"local_similarity\":"<<f.local_similarity
     <<",\"reference_rms_db\":"<<f.reference_rms_db<<",\"degraded_rms_db\":"<<f.degraded_rms_db
     <<",\"reference_bands_db\":[";
    for(int i=0;i<64;++i){if(i)o<<",";o<<f.reference_bands_db[i];}
    o<<"],\"degraded_bands_db\":[";
    for(int i=0;i<64;++i){if(i)o<<",";o<<f.degraded_bands_db[i];}
    o<<"]}";
  }
  o<<"]}";
  return o.str();
}
}  // namespace openvq
