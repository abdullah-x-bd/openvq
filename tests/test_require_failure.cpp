#include "test_support.h"

int main() {
  OPENVQ_REQUIRE(false && "Release-safe check self-test");
  return 0;
}
