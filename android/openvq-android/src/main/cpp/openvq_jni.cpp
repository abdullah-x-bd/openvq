#include <jni.h>
#include <exception>
#include <string>
#include <vector>
#include "openvq/advanced.h"

namespace {
openvq::AudioBuffer FromShortArray(
    JNIEnv* env, jshortArray input, jint sample_rate) {
  const jsize n = env->GetArrayLength(input);
  std::vector<jshort> tmp(static_cast<size_t>(n));
  env->GetShortArrayRegion(input, 0, n, tmp.data());

  openvq::AudioBuffer out;
  out.sample_rate = sample_rate;
  out.samples.resize(static_cast<size_t>(n));
  for (jsize i = 0; i < n; ++i) {
    out.samples[static_cast<size_t>(i)] =
        tmp[static_cast<size_t>(i)] / 32768.0f;
  }
  return out;
}
}

extern "C" JNIEXPORT jstring JNICALL
Java_ai_openvq_OpenVqNative_analyzePcm16(
    JNIEnv* env,
    jobject,
    jshortArray reference,
    jshortArray degraded,
    jint sample_rate) {
  try {
    openvq::AdvancedAnalyzer analyzer;
    const auto result = analyzer.Analyze(
        FromShortArray(env, reference, sample_rate),
        FromShortArray(env, degraded, sample_rate));
    const std::string json = openvq::ToJson(result);
    return env->NewStringUTF(json.c_str());
  } catch (const std::exception& e) {
    const std::string json =
        std::string("{\"error\":\"") + e.what() + "\"}";
    return env->NewStringUTF(json.c_str());
  }
}
