# Read through MAKEFILES by the parent and generated native Makefiles.
# User objects do not use the generated model PCH. Keep the adapter here so
# model objects can load their PCH as the first header.
ifndef VDOT_ROOT
$(error Source scripts/env.sh before loading this compatibility Makefile)
endif
emu.o main.o verilator.o waveform.o: override CXXFLAGS += -include "$(VDOT_ROOT)/configs/verilator_5_022_trace.h"

# Opt-in host compiler workaround for large generated decoder expressions.
ifeq ($(VDOT_CPP_DECODER_O0),1)
include $(VDOT_ROOT)/configs/gcc_decode_compat.mk
endif
