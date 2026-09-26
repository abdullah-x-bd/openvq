#include "openvq/openvq.h"
#include "openvq/trace.h"
#include <iostream>

int main(int argc,char** argv){
  if(argc!=3){
    std::cerr<<"usage: openvq_trace_cli reference.wav degraded.wav\n";
    return 2;
  }
  try{
    const auto ref=openvq::LoadWav(argv[1]);
    const auto deg=openvq::LoadWav(argv[2]);
    std::cout<<openvq::TraceToJson(openvq::TraceAnalyzer().Analyze(ref,deg))<<"\n";
  }catch(const std::exception& e){
    std::cerr<<"openvq_trace_cli: "<<e.what()<<"\n";return 1;
  }
}
