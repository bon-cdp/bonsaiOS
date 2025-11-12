/**
 * @file main_minimal.c
 * @brief Minimal BonsaiOS UEFI Bootloader (No gnu-efi dependency)
 *
 * Direct UEFI implementation for AArch64
 */

// UEFI basic types
typedef unsigned long long UINT64;
typedef unsigned int UINT32;
typedef unsigned short CHAR16;
typedef void VOID;
typedef UINT64 UINTN;
typedef UINT64 EFI_STATUS;
typedef VOID *EFI_HANDLE;

#define EFI_SUCCESS 0

// Simple console output
typedef struct {
    VOID *_buf;
    EFI_STATUS (*OutputString)(VOID *This, CHAR16 *String);
    // ... other functions omitted for simplicity
} SIMPLE_TEXT_OUTPUT_INTERFACE;

typedef struct {
    CHAR16 _pad[60];  // Padding to reach ConOut
    SIMPLE_TEXT_OUTPUT_INTERFACE *ConOut;
} EFI_SYSTEM_TABLE;

// Entry point
EFI_STATUS efi_main(EFI_HANDLE ImageHandle, EFI_SYSTEM_TABLE *SystemTable)
{
    CHAR16 msg[] = L"BonsaiOS v0.1 - UEFI Bootloader Active!\r\n";

    // Print message
    SystemTable->ConOut->OutputString(SystemTable->ConOut, msg);

    // Hang (for now)
    while(1);

    return EFI_SUCCESS;
}
