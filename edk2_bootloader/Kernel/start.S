.section .text
.global _start

_start:
    // Kernel entry - no arguments passed from bootloader
    // Stack pointer (sp) already set by bootloader

    // Disable interrupts
    msr daifset, #0xf

    // Call kernel main
    bl kmain

    // Halt if kmain returns
halt:
    wfi
    b halt
