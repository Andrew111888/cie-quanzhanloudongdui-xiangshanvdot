#pragma once
#include <verilated_config.h>

// Difftest's trace callback uses a common name introduced after this version.
// The pinned model accepts the concrete backend pointer; keep that exact type.
// Include only in the four waveform-facing user objects, never before the
// generated model's PCH. No cast or object-layout change is introduced.
#if VERILATOR_VERSION_INTEGER != 5022000
#error "This trace compatibility header is only for Verilator 5.022"
#endif

#ifdef ENABLE_FST
class VerilatedFstC;
using VerilatedTraceBaseC = VerilatedFstC;
#else
class VerilatedVcdC;
using VerilatedTraceBaseC = VerilatedVcdC;
#endif
