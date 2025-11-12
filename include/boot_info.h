#pragma once

#include <efi.h>

typedef struct {
    // UEFI System Table, so we can access console output, etc.
    EFI_SYSTEM_TABLE *SystemTable;

    // Add other info here later, e.g.:
    // - Memory Map
    // - Framebuffer info
    // - ACPI tables
} boot_info_t;
