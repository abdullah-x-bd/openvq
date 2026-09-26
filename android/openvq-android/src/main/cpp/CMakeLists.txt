cmake_minimum_required(VERSION 3.22.1)
project(openvq_android LANGUAGES CXX)
get_filename_component(OPENVQ_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../../../" ABSOLUTE)
add_library(openvq_android SHARED
    openvq_jni.cpp
    "${OPENVQ_ROOT}/src/openvq.cpp"
    "${OPENVQ_ROOT}/src/calibration.cpp"
    "${OPENVQ_ROOT}/src/advanced.cpp"
    "${OPENVQ_ROOT}/src/hybrid.cpp"
    "${OPENVQ_ROOT}/src/phase4.cpp")
target_include_directories(openvq_android PRIVATE "${OPENVQ_ROOT}/include")
target_compile_features(openvq_android PRIVATE cxx_std_17)
