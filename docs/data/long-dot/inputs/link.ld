OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS {
  . = 0x80000000;
  .text : { KEEP(*(.text.init)) *(.text*) }
  .rodata : { *(.rodata*) *(.srodata*) }
  .data : { *(.data*) *(.sdata*) }
  . = ALIGN(16);
  __bss_start = .;
  .bss : { *(.bss*) *(.sbss*) *(COMMON) }
  __bss_end = .;
  . = ALIGN(16);
  . += 65536;
  __stack_top = .;
}
