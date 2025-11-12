# Makefile for BonsaiOS C++ UEFI Test App (AArch64)

# Toolchain
CXX = aarch64-linux-gnu-g++
LD = aarch64-linux-gnu-ld
OBJCOPY = aarch64-linux-gnu-objcopy

# gnu-efi paths (local build)
GNUEFI_DIR = ../../gnu-efi
EFIINC = $(GNUEFI_DIR)/inc
EFILIB = $(GNUEFI_DIR)/aarch64/lib
EFICRT0 = $(GNUEFI_DIR)/aarch64/gnuefi/crt0-efi-aarch64.o
EFILDS = $(GNUEFI_DIR)/gnuefi/elf_aarch64_efi.lds

# Compiler flags for UEFI C++
CXXFLAGS = -I$(EFIINC) -I$(EFIINC)/aarch64 -I$(EFIINC)/protocol \
           -fno-stack-protector -fpic -fshort-wchar \
           -Wall -fno-rtti -fno-exceptions -std=c++11

# Linker flags
LDFLAGS = -nostdlib -znocombreloc -T $(EFILDS) -shared -Bsymbolic \
          -L$(EFILIB) -L$(GNUEFI_DIR)/aarch64/gnuefi $(EFICRT0)

# Libraries
LIBS = -lefi -lgnuefi

# Target
TARGET = hello_world.efi
OBJS = main.o

all: $(TARGET)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

app.so: $(OBJS)
	$(CXX) $(LDFLAGS) $(OBJS) -o $@ $(LIBS)

$(TARGET): app.so
	$(OBJCOPY) -j .text -j .sdata -j .data -j .dynamic \
	           -j .dynsym -j .rel -j .rela -j .reloc \
	           --target=efi-app-aarch64 $< $@
	@echo "C++ UEFI Test App Built: $(TARGET)"

clean:
	rm -f *.o *.so $(TARGET)

.PHONY: all clean
