// Start routine for UEFI application
.section .text
.global _start
.type _start, %function

_start:
    // Save ImageHandle and SystemTable
    stp     x0, x1, [sp, #-16]!

    // Call efi_main(ImageHandle, SystemTable)
    bl      efi_main

    // Restore stack and return
    ldp     x0, x1, [sp], #16
    ret
