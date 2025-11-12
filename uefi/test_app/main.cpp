#include <efi.h>
#include <efilib.h>

// Use C++-style name mangling
extern "C" EFI_STATUS
EFIAPI
efi_main(EFI_HANDLE ImageHandle, EFI_SYSTEM_TABLE *SystemTable)
{
    // Initialize gnu-efi library
    InitializeLib(ImageHandle, SystemTable);

    // Clear screen
    uefi_call_wrapper(ST->ConOut->ClearScreen, 1, ST->ConOut);

    // Print a message
    Print((CHAR16*)L"Hello from C++ UEFI!\n");
    Print((CHAR16*)L"This is a test application.\n");
    Print((CHAR16*)L"If you can see this, our C++ toolchain for UEFI is working.\n");

    // Wait for a key press before exiting
    Print((CHAR16*)L"\nPress any key to exit...\n");
    EFI_INPUT_KEY Key;
    uefi_call_wrapper(ST->ConIn->Reset, 2, ST->ConIn, FALSE);
    uefi_call_wrapper(ST->BootServices->WaitForEvent, 3, 1, &ST->ConIn->WaitForKey, NULL);
    uefi_call_wrapper(ST->ConIn->ReadKeyStroke, 2, ST->ConIn, &Key);

    return EFI_SUCCESS;
}

