# Makefile for BonsaiOS Kernel (minimal, AArch64)

CC = aarch64-linux-gnu-gcc
LD = aarch64-linux-gnu-ld
OBJCOPY = aarch64-linux-gnu-objcopy

CFLAGS = -ffreestanding -nostdlib -nostartfiles -O2 -Wall -Wextra
LDFLAGS = -T link.lds -nostdlib

OBJS = start.o kmain.o sheaf.o
TARGET = bonsai_kernel.elf
BINARY = bonsai_kernel.bin

all: $(BINARY)

%.o: %.S
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

$(TARGET): $(OBJS)
	$(LD) $(LDFLAGS) $(OBJS) -o $@

$(BINARY): $(TARGET)
	$(OBJCOPY) -O binary $< $@
	@echo ""
	@echo "=========================================="
	@echo "BonsaiOS Kernel Built!"
	@echo "=========================================="
	@echo "Output: $(BINARY)"
	@echo "Size: $$(ls -lh $(BINARY) | awk '{print $$5}')"
	@echo ""

clean:
	rm -f *.o $(TARGET) $(BINARY)

.PHONY: all clean
