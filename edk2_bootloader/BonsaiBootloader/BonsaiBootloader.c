/**
 * @file BonsaiBootloader.c
 * @brief BonsaiOS UEFI Bootloader - EDK2 Version
 *
 * Wreath-Sheaf Architecture - Algebraic Operating System
 * Built with proper EDK2 toolchain for correct PE/COFF format
 */

#include <Uefi.h>
#include <Library/UefiLib.h>
#include <Library/UefiApplicationEntryPoint.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/MemoryAllocationLib.h>
#include <Protocol/LoadedImage.h>
#include <Protocol/SimpleFileSystem.h>
#include <Guid/FileInfo.h>

#define KERNEL_STACK_SIZE (16 * 1024) // 16KB stack

/**
 * Load a file from the ESP
 */
EFI_STATUS
LoadKernelFile (
  IN  EFI_HANDLE   ImageHandle,
  IN  CHAR16       *FileName,
  OUT VOID         **Buffer,
  OUT UINTN        *Size
  )
{
  EFI_STATUS                       Status;
  EFI_LOADED_IMAGE_PROTOCOL        *LoadedImage;
  EFI_SIMPLE_FILE_SYSTEM_PROTOCOL  *FileSystem;
  EFI_FILE_PROTOCOL                *Root;
  EFI_FILE_PROTOCOL                *File;
  EFI_FILE_INFO                    *FileInfo;
  UINTN                            FileInfoSize;

  Status = gBS->HandleProtocol(ImageHandle, &gEfiLoadedImageProtocolGuid, (VOID **)&LoadedImage);
  if (EFI_ERROR(Status)) return Status;

  Status = gBS->HandleProtocol(LoadedImage->DeviceHandle, &gEfiSimpleFileSystemProtocolGuid, (VOID **)&FileSystem);
  if (EFI_ERROR(Status)) return Status;

  Status = FileSystem->OpenVolume(FileSystem, &Root);
  if (EFI_ERROR(Status)) return Status;

  Status = Root->Open(Root, &File, FileName, EFI_FILE_MODE_READ, 0);
  if (EFI_ERROR(Status)) {
    Root->Close(Root);
    return Status;
  }

  FileInfoSize = 0;
  Status = File->GetInfo(File, &gEfiFileInfoGuid, &FileInfoSize, NULL);
  if (Status != EFI_BUFFER_TOO_SMALL) {
    File->Close(File);
    Root->Close(Root);
    return Status;
  }

  FileInfo = AllocatePool(FileInfoSize);
  if (!FileInfo) {
    File->Close(File);
    Root->Close(Root);
    return EFI_OUT_OF_RESOURCES;
  }

  Status = File->GetInfo(File, &gEfiFileInfoGuid, &FileInfoSize, FileInfo);
  if (EFI_ERROR(Status)) {
    FreePool(FileInfo);
    File->Close(File);
    Root->Close(Root);
    return Status;
  }

  *Size = (UINTN)FileInfo->FileSize;
  FreePool(FileInfo);

  *Buffer = AllocatePool(*Size);
  if (!*Buffer) {
    File->Close(File);
    Root->Close(Root);
    return EFI_OUT_OF_RESOURCES;
  }

  Status = File->Read(File, Size, *Buffer);
  if (EFI_ERROR(Status)) {
    FreePool(*Buffer);
    *Buffer = NULL;
  }

  File->Close(File);
  Root->Close(Root);

  return Status;
}

/**
 * Jump to kernel (AArch64 assembly)
 */
VOID
JumpToKernel (
  IN VOID  *KernelEntry,
  IN VOID  *StackTop
  )
{
  // Simple approach: kernel takes no arguments for now
  // Stack is already set up
  __asm__ volatile (
    "mov sp, %0\n"
    "br %1\n"
    :
    : "r"(StackTop), "r"(KernelEntry)
    : "memory"
  );
}

/**
 * UEFI Application Entry Point
 */
EFI_STATUS
EFIAPI
UefiMain (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  EFI_STATUS  Status;
  VOID        *KernelBuffer = NULL;
  UINTN       KernelSize = 0;
  VOID        *KernelStack = NULL;
  VOID        *KernelStackTop;
  UINTN       MapKey;
  UINTN       MapSize = 0;
  UINTN       DescriptorSize;
  UINT32      DescriptorVersion;
  EFI_MEMORY_DESCRIPTOR  *MemoryMap = NULL;

  // Clear screen
  SystemTable->ConOut->ClearScreen(SystemTable->ConOut);

  // Print welcome banner
  Print(L"\n");
  Print(L"       _\n");
  Print(L"      /\\\n");
  Print(L"     /**\\     BonsaiOS v0.2 - Made with love\n");
  Print(L"    /****\\    NVIDIA Jetson AGX Orin Nano\n");
  Print(L"   /******\\\n");
  Print(L"  /********\\  Wreath-sheaf: algebraic OS design\n");
  Print(L"     ||\n");
  Print(L"\n");

  // Load kernel
  Print(L"  [ ] Loading bonsai_kernel.bin...\n");
  Status = LoadKernelFile(ImageHandle, L"bonsai_kernel.bin", &KernelBuffer, &KernelSize);
  if (EFI_ERROR(Status)) {
    Print(L"  [ERR] Kernel not found: %r\n", Status);
    Print(L"\nBootloader halted. Press any key...\n");
    SystemTable->BootServices->WaitForEvent(1, &SystemTable->ConIn->WaitForKey, NULL);
    return Status;
  }
  Print(L"  [OK] Kernel loaded: %u bytes at 0x%lx\n", KernelSize, KernelBuffer);

  // Allocate kernel stack
  KernelStack = AllocatePool(KERNEL_STACK_SIZE);
  if (!KernelStack) {
    Print(L"  [ERR] Failed to allocate kernel stack\n");
    FreePool(KernelBuffer);
    return EFI_OUT_OF_RESOURCES;
  }
  KernelStackTop = (VOID *)((UINT8 *)KernelStack + KERNEL_STACK_SIZE);
  Print(L"  [OK] Stack allocated: 0x%lx - 0x%lx\n", KernelStack, KernelStackTop);

  // Get memory map
  Status = gBS->GetMemoryMap(&MapSize, MemoryMap, &MapKey, &DescriptorSize, &DescriptorVersion);
  if (Status == EFI_BUFFER_TOO_SMALL) {
    MapSize += 2 * DescriptorSize;
    MemoryMap = AllocatePool(MapSize);
    if (!MemoryMap) {
      FreePool(KernelStack);
      FreePool(KernelBuffer);
      return EFI_OUT_OF_RESOURCES;
    }
    Status = gBS->GetMemoryMap(&MapSize, MemoryMap, &MapKey, &DescriptorSize, &DescriptorVersion);
  }
  if (EFI_ERROR(Status)) {
    Print(L"  [ERR] Failed to get memory map: %r\n", Status);
    FreePool(MemoryMap);
    FreePool(KernelStack);
    FreePool(KernelBuffer);
    return Status;
  }

  Print(L"\n  Booting in 2 seconds...\n");
  Print(L"  (Connect serial console at 115200 baud for interaction)\n\n");

  // Brief delay so user can see message
  gBS->Stall(2000000);  // 2 seconds in microseconds

  // Exit boot services
  Status = gBS->ExitBootServices(ImageHandle, MapKey);
  if (EFI_ERROR(Status)) {
    // Can't print anymore, just hang
    while (1) {
      __asm__ volatile("wfi");
    }
  }

  // Jump to kernel
  JumpToKernel(KernelBuffer, KernelStackTop);

  // Should never return
  while (1) {
    __asm__ volatile("wfi");
  }

  return EFI_SUCCESS;
}
