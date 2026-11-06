#include "VVdotDatapath.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using Vector = std::array<uint32_t, 4>;
struct Input { Vector a, b; std::string name; int32_t expected; bool directed; };

static uint32_t random_word(uint32_t &state) {
  state ^= state << 13; state ^= state >> 17; state ^= state << 5;
  return state;
}
static int byte(const Vector &value, unsigned lane) {
  unsigned x = (value[lane / 4] >> ((lane % 4) * 8)) & 255;
  return x < 128 ? int(x) : int(x) - 256;
}
static int32_t reference(const Vector &a, const Vector &b) {
  int32_t result = 0;
  for (unsigned lane = 0; lane < 8; ++lane) result += byte(a, lane) * byte(b, lane);
  return result;
}
static Vector repeated(int value, uint32_t sentinel) {
  uint32_t x = uint32_t(value & 255) * 0x01010101u;
  return {x, x, sentinel, ~sentinel};
}
static std::string hex128(const Vector &value) {
  std::ostringstream text;
  text << std::hex << std::setfill('0');
  for (int i = 3; i >= 0; --i) text << std::setw(8) << value[i];
  return text.str();
}

int main(int argc, char **argv) {
  VerilatedContext context;
  context.commandArgs(argc, argv);
  VVdotDatapath dut(&context);
  std::vector<Input> inputs;
  const int edges[][2] = {{1,1},{-1,1},{-128,-128},{-128,127},{127,127},{0,-128}};
  const char *names[] = {"positive","negative","boundary_min_min","boundary_min_max","boundary_max_max","boundary_zero"};
  for (unsigned i = 0; i < 6; ++i) {
    Vector a = repeated(edges[i][0], 0xf03c5aa5u ^ i);
    Vector b = repeated(edges[i][1], 0x859ae6b7u ^ i);
    inputs.push_back({a, b, names[i], reference(a, b), true});
  }
  uint32_t rng = 20261106u;
  for (unsigned i = 0; i < 1000; ++i) {
    Vector a, b;
    for (unsigned word = 0; word < 4; ++word) { a[word] = random_word(rng); b[word] = random_word(rng); }
    inputs.push_back({a, b, "random_" + std::to_string(i), reference(a, b), false});
  }
  bool pending_valid = false, expected_valid = false;
  Input pending{}, expected{};
  unsigned cycles = 0, checks = 0, directed_checks = 0;
  auto step = [&](const Input &input, bool enable1, bool enable2, const char *phase) {
    for (unsigned word = 0; word < 4; ++word) { dut.io_vs1[word] = input.a[word]; dut.io_vs2[word] = input.b[word]; }
    dut.io_enable1 = enable1; dut.io_enable2 = enable2;
    if (enable2) { expected_valid = pending_valid; if (pending_valid) expected = pending; }
    if (enable1) { pending = input; pending_valid = true; }
    dut.clock = 0; dut.eval();
    dut.clock = 1; dut.eval();
    ++cycles;
    if (expected_valid) {
      Vector actual;
      for (unsigned word = 0; word < 4; ++word) actual[word] = dut.io_result[word];
      Vector wanted = {uint32_t(expected.expected), 0, 0, 0};
      if (actual != wanted) {
        std::cerr << "RTL_MISMATCH name=" << expected.name << " phase=" << phase
                  << " cycle=" << cycles << " signed_expected=" << expected.expected
                  << " expected128=" << hex128(wanted) << " actual128=" << hex128(actual) << '\n';
        dut.final(); std::exit(42);
      }
      ++checks;
      if (expected.directed && std::string(phase) == "throughput") {
        ++directed_checks;
        std::cout << "RTL_CASE_PASS name=" << expected.name << " signed_expected=" << expected.expected
                  << " actual128=" << hex128(actual) << '\n';
      }
    }
  };
  step(inputs[0], false, false, "initialize");
  for (const auto &input : inputs) step(input, true, true, "throughput");
  step(inputs.back(), false, true, "throughput");
  if (directed_checks != 6) return 3;
  for (unsigned i = 0; i < inputs.size(); ++i) {
    bool enable1 = (random_word(rng) & 3u) != 0;
    bool enable2 = (random_word(rng) & 3u) != 0;
    step(inputs[i], enable1, enable2, "independent_enables");
  }
  step(inputs.back(), false, true, "drain");
  dut.final();
  std::cout << "VDOT_RTL_PASS directed_cases=6 random_cases=1000 seed=20261106"
            << " arithmetic_cases=" << inputs.size() << " enable_stress_cycles=" << inputs.size()
            << " checked_cycles=" << checks << " total_cycles=" << cycles << '\n';
  return 0;
}
