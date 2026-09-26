#pragma once

#include <cstdlib>
#include <iostream>

namespace openvq_test {
inline void Require(bool ok, const char* expression, const char* file, int line) {
  if (!ok) {
    std::cerr << file << ":" << line << ": requirement failed: " << expression << "\n";
    std::exit(1);
  }
}
}  // namespace openvq_test

#define OPENVQ_REQUIRE(expr) \
  ::openvq_test::Require(static_cast<bool>(expr), #expr, __FILE__, __LINE__)
