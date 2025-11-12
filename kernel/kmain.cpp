#include "boot_info.h"

// Kernel entry point
extern "C" void kmain(boot_info_t *boot_info) {
    if (boot_info && boot_info->SystemTable) {
        boot_info->SystemTable->ConOut->OutputString(boot_info->SystemTable->ConOut, (CHAR16*)L"Welcome to Bonsai OS! (Kernel is running)\n");
    }

    // Loop indefinitely
    while (1) {
        asm volatile("wfi"); // Wait For Interrupt
    }
}
