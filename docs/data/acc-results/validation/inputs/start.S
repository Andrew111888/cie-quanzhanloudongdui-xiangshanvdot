.section .text.init
.globl _start
_start:
  la sp, __stack_top
  la t0, __bss_start
  la t1, __bss_end
1: bgeu t0, t1, 2f
  sd zero, 0(t0)
  addi t0, t0, 8
  j 1b
2:
  # Enable floating and vector architectural state (FS=Dirty, VS=Dirty).
  li t0, 0x6600
  csrs mstatus, t0
  la t0, trap_entry
  csrw mtvec, t0
  # Kunminghu V2 resets with NMIE=0 and MDT=1. Enable ordinary trap handling.
  li t0, 8
  csrs 0x744, t0
  li t0, 1
  slli t0, t0, 42
  csrc mstatus, t0
  csrw vstart, zero
  call main
  .word 0x0000006b
3: j 3b

.align 2
trap_entry:
  addi sp, sp, -32
  sd t0, 0(sp)
  sd t1, 8(sp)
  sd t2, 16(sp)
  csrr t0, mcause
  li t1, 2
  bne t0, t1, unexpected_trap
  la t0, expected_illegal
  lw t1, 0(t0)
  beqz t1, unexpected_trap
  sw zero, 0(t0)
  csrr t0, mepc
  addi t0, t0, 4
  csrw mepc, t0
  ld t0, 0(sp)
  ld t1, 8(sp)
  ld t2, 16(sp)
  addi sp, sp, 32
  mret
unexpected_trap:
  li a0, 99
  .word 0x0000006b
  j unexpected_trap
