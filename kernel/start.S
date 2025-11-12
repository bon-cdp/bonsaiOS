.section .text
.global _start

_start:
    // The bootloader passes a pointer to boot_info_t in x0.
    // The stack pointer (sp) has already been set by the bootloader.
    // We need to preserve the boot_info pointer (x0) across the call to kmain.
    // According to the AArch64 calling convention, x19 is a callee-saved register.
    mov     x19, x0

    // Disable interrupts
    mrs     x0, daif
    orr     x0, x0, #(1 << 7)   // Set I (IRQ) bit
    msr     daif, x0

    // Call the C++ kernel entry point, passing the boot_info pointer as the first argument.
    mov     x0, x19
    bl      kmain

    // If kmain returns, halt the system
halt:
    wfi
    b       halt
