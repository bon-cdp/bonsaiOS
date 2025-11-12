/**
 * @file main.c
 * @brief BonsaiOS UEFI Bootloader
 *
 * This bootloader:
 * 1. Initializes UEFI services
 * 2. Loads the kernel from disk
 * 3. Allocates a new stack for the kernel
 * 4. Creates a boot_info structure
 * 5. Exits boot services and transfers control to the kernel
 */

#include <efi.h>
#include <efilib.h>
#include "../../include/boot_info.h" // Shared header

#define KERNEL_STACK_SIZE (16 * 1024) // 16KB stack

// Function to print an EFI_STATUS error
void PrintError(EFI_STATUS Status, CHAR16* Message) {
    if (EFI_ERROR(Status)) {
        Print(L"ERROR: %s - %r\n", Message, Status);
    }
}

// Loads a file from the EFI System Partition into a buffer
EFI_STATUS LoadFileFromEsp(
    EFI_HANDLE ImageHandle,
    CHAR16* FileName,
    VOID** FileBuffer,
    UINTN* FileSize
) {
    // ... (previous implementation of LoadFileFromEsp)
    // This function is assumed to be correct from previous steps.
    // For brevity, it is not repeated here, but it should be included.
    EFI_STATUS Status;
    EFI_LOADED_IMAGE_PROTOCOL* LoadedImage = NULL;
    EFI_SIMPLE_FILE_SYSTEM_PROTOCOL* SimpleFileSystem = NULL;
    EFI_FILE_PROTOCOL* Root = NULL;
    EFI_FILE_PROTOCOL* FileHandle = NULL;
    EFI_FILE_INFO* FileInfo = NULL;
    UINTN FileInfoSize = 0;

    Status = uefi_call_wrapper(BS->HandleProtocol, 3, ImageHandle, &gEfiLoadedImageProtocolGuid, (VOID**)&LoadedImage);
    if (EFI_ERROR(Status)) return Status;

    Status = uefi_call_wrapper(BS->HandleProtocol, 3, LoadedImage->DeviceHandle, &gEfiSimpleFileSystemProtocolGuid, (VOID**)&SimpleFileSystem);
    if (EFI_ERROR(Status)) return Status;

    Status = uefi_call_wrapper(SimpleFileSystem->OpenVolume, 2, SimpleFileSystem, &Root);
    if (EFI_ERROR(Status)) return Status;

    Status = uefi_call_wrapper(Root->Open, 5, Root, &FileHandle, FileName, EFI_FILE_MODE_READ, EFI_FILE_READ_ONLY);
    if (EFI_ERROR(Status)) return Status;

    FileInfoSize = 0;
    Status = uefi_call_wrapper(FileHandle->GetInfo, 4, FileHandle, &gEfiFileInfoGuid, &FileInfoSize, NULL);
    if (Status != EFI_BUFFER_TOO_SMALL) return Status;

    Status = uefi_call_wrapper(BS->AllocatePool, 3, EfiLoaderData, FileInfoSize, (VOID**)&FileInfo);
    if (EFI_ERROR(Status)) return Status;

    Status = uefi_call_wrapper(FileHandle->GetInfo, 4, FileHandle, &gEfiFileInfoGuid, &FileInfoSize, FileInfo);
    if (EFI_ERROR(Status)) return Status;
    *FileSize = FileInfo->FileSize;

    Status = uefi_call_wrapper(BS->AllocatePool, 3, EfiLoaderData, *FileSize, FileBuffer);
    if (EFI_ERROR(Status)) return Status;

    Status = uefi_call_wrapper(FileHandle->Read, 3, FileHandle, FileSize, *FileBuffer);
    if (EFI_ERROR(Status)) {
        uefi_call_wrapper(BS->FreePool, 1, *FileBuffer);
        *FileBuffer = NULL;
        return Status;
    }

    uefi_call_wrapper(FileHandle->Close, 1, FileHandle);
    uefi_call_wrapper(Root->Close, 1, Root);
    uefi_call_wrapper(BS->FreePool, 1, FileInfo);

    return EFI_SUCCESS;
}


// Jumps to the kernel entry point with the new stack and boot info
void jump_to_kernel(void* kernel_entry, void* boot_info, void* stack_top) {
    asm volatile (
        "mov x0, %0\n"   // Argument 1: boot_info pointer
        "mov sp, %1\n"   // Set the new stack pointer
        "br %2\n"        // Branch to kernel entry point
        :
        : "r"(boot_info), "r"(stack_top), "r"(kernel_entry)
        : "x0", "sp"
    );
}

EFI_STATUS
EFIAPI
efi_main(EFI_HANDLE ImageHandle, EFI_SYSTEM_TABLE *SystemTable)
{
    EFI_STATUS Status;
    VOID* KernelBuffer = NULL;
    UINTN KernelSize = 0;
    boot_info_t* BootInfo = NULL;
    VOID* KernelStack = NULL;
    UINTN MapKey = 0;
    UINTN DescriptorSize = 0;
    UINT32 DescriptorVersion = 0;
    EFI_MEMORY_DESCRIPTOR *MemoryMap = NULL;

    InitializeLib(ImageHandle, SystemTable);
    uefi_call_wrapper(ST->ConOut->ClearScreen, 1, ST->ConOut);

    Print(L"BonsaiOS Bootloader v0.3\n");
    Print(L"Status: Loading kernel...\n");

    // Load kernel
    Status = LoadFileFromEsp(ImageHandle, L"\\bonsai_kernel.bin", &KernelBuffer, &KernelSize);
    if (EFI_ERROR(Status)) {
        PrintError(Status, L"Failed to load bonsai_kernel.bin");
        goto Exit;
    }
    Print(L"  [OK] Kernel loaded at 0x%llx\n", KernelBuffer);

    // Allocate memory for boot info structure
    Status = uefi_call_wrapper(BS->AllocatePool, 3, EfiLoaderData, sizeof(boot_info_t), (VOID**)&BootInfo);
    if (EFI_ERROR(Status)) {
        PrintError(Status, L"Failed to allocate pool for boot info");
        goto Exit;
    }
    Print(L"  [OK] Boot info allocated at 0x%llx\n", BootInfo);
    BootInfo->SystemTable = SystemTable;

    // Allocate memory for the kernel stack
    Status = uefi_call_wrapper(BS->AllocatePool, 3, EfiLoaderData, KERNEL_STACK_SIZE, (VOID**)&KernelStack);
    if (EFI_ERROR(Status)) {
        PrintError(Status, L"Failed to allocate pool for kernel stack");
        goto Exit;
    }
    VOID* KernelStackTop = KernelStack + KERNEL_STACK_SIZE;
    Print(L"  [OK] Kernel stack allocated at 0x%llx\n", KernelStack);


    // Get memory map and exit boot services
    UINTN MemoryMapSize = 0;
    Status = uefi_call_wrapper(BS->GetMemoryMap, 5, &MemoryMapSize, MemoryMap, &MapKey, &DescriptorSize, &DescriptorVersion);
    if (Status != EFI_BUFFER_TOO_SMALL) {
         PrintError(Status, L"Failed to get memory map size");
         goto Exit;
    }
    MemoryMapSize += 2 * DescriptorSize; // Add some buffer
    Status = uefi_call_wrapper(BS->AllocatePool, 3, EfiLoaderData, MemoryMapSize, (VOID**)&MemoryMap);
    if(EFI_ERROR(Status)) {
        PrintError(Status, L"Failed to allocate pool for memory map");
        goto Exit;
    }
    Status = uefi_call_wrapper(BS->GetMemoryMap, 5, &MemoryMapSize, MemoryMap, &MapKey, &DescriptorSize, &DescriptorVersion);
    if (EFI_ERROR(Status)) {
        PrintError(Status, L"Failed to get memory map");
        goto Exit;
    }
    Status = uefi_call_wrapper(BS->ExitBootServices, 2, ImageHandle, MapKey);
    if (EFI_ERROR(Status)) {
        // This is tricky. We can't use Print anymore.
        // We'll just have to hang.
        while(1);
    }

    // Jump to kernel
    jump_to_kernel(KernelBuffer, BootInfo, KernelStackTop);

    // Should not be reached
    while(1);

Exit:
    Print(L"\nBootloader halted.\n");
    uefi_call_wrapper(ST->ConIn->Reset, 2, ST->ConIn, FALSE);
    uefi_call_wrapper(ST->BootServices->WaitForEvent, 3, 1, &ST->ConIn->WaitForKey, NULL);
    return Status;
}

