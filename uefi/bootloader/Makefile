# Makefile for BonsaiOS UEFI Bootloader (AArch64)

# Toolchain
CC = aarch64-linux-gnu-gcc
LD = aarch64-linux-gnu-ld
OBJCOPY = aarch64-linux-gnu-objcopy

# gnu-efi paths (local build)
GNUEFI_DIR = ../../gnu-efi
EFIINC = $(GNUEFI_DIR)/inc
EFILIB = $(GNUEFI_DIR)/aarch64/lib
EFICRT0 = $(GNUEFI_DIR)/aarch64/gnuefi/crt0-efi-aarch64.o
EFILDS = $(GNUEFI_DIR)/gnuefi/elf_aarch64_efi.lds

# Compiler flags for UEFI (AArch64 doesn't have red-zone)
CFLAGS = -I$(EFIINC) -I$(EFIINC)/aarch64 -I$(EFIINC)/protocol -I../../include \
         -fno-stack-protector -fpic -fshort-wchar \
         -Wall -DEFI_FUNCTION_WRAPPER

# Linker flags
LDFLAGS = -nostdlib -znocombreloc -T $(EFILDS) -shared -Bsymbolic \
          -L$(EFILIB) -L$(GNUEFI_DIR)/aarch64/gnuefi $(EFICRT0)

# Libraries
LIBS = -lefi -lgnuefi

# Target
TARGET = BOOTAA64.EFI
OBJS = main.o

all: $(TARGET)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

bootloader.so: $(OBJS)
	$(LD) $(LDFLAGS) $(OBJS) -o $@ $(LIBS)

$(TARGET): bootloader.so
	$(OBJCOPY) -j .text -j .sdata -j .data -j .dynamic \
	           -j .dynsym -j .rel -j .rela -j .reloc \
	           --target=efi-app-aarch64 $< $@
	@echo ""
	@echo "=========================================="
	@echo "BonsaiOS UEFI Bootloader Built!"
	@echo "=========================================="
	@echo "Output: $(TARGET)"
	@echo "Size: $$(ls -lh $(TARGET) | awk '{print $$5}')"
	@echo ""
	@echo "To deploy:"
	@echo "  1. Copy $(TARGET) to USB drive (FAT32)"
	@echo "  2. In UEFI shell: fs0:\\$(TARGET)"
	@echo "=========================================="
	@echo ""

clean:
	rm -f *.o *.so $(TARGET)

.PHONY: all clean
