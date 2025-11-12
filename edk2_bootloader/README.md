# BonsaiOS

Minimal algebraic operating system for NVIDIA Jetson AGX Orin Nano

```
       _
      /\
     /**\     BonsaiOS v0.1 - Made with love
    /****\    NVIDIA Jetson AGX Orin Nano
   /******\
  /********\  Wreath-sheaf: algebraic OS design
     ||
```

## Philosophy

Replace heuristic OS algorithms with algebraic sheaf theory. Scheduler, memory manager, and compiler optimizer become ONE linear solver. No gradient descent, pure closed-form solutions.

## Current State

✅ UEFI bootloader running on Orin
✅ EDK2 build infrastructure
✅ Proper PE32+ format validated

## Architecture Roadmap

### Phase 1: Kernel Foundation (Next)
**Goal:** Boot to a C/C++ runtime with memory management

1. **ELF Loader**
   - Parse kernel ELF from filesystem
   - Relocate sections to physical memory
   - Jump to kernel entry point

2. **Memory Manager**
   - Parse UEFI memory map before ExitBootServices()
   - Implement page allocator (4KB pages)
   - Heap allocator (malloc/free for kernel)

3. **Kernel Entry**
   - Initialize stack
   - Set up exception vectors (ARM64 EL1)
   - Basic console output (keep UEFI ConOut for now)

**Deliverable:** `kernel.elf` that prints "BonsaiOS kernel running"

### Phase 2: Hardware Abstraction
**Goal:** Direct hardware I/O without UEFI

1. **Serial Console**
   - UART driver for Orin (replace UEFI console)
   - Interrupt-driven or polling TX/RX
   - printf() implementation

2. **Timer**
   - ARM Generic Timer access
   - Microsecond-precision timing
   - Scheduler tick foundation

3. **GPIO**
   - Memory-mapped I/O for Tegra GPIO controller
   - Pin configuration (input/output/pullup)
   - Basic read/write operations

**Deliverable:** Blink LED, read button, serial echo program

### Phase 3: Process Model
**Goal:** Run user C/C++ programs

1. **ELF Loader (Userspace)**
   - Load `/bin/app.elf` from filesystem
   - Set up user address space (separate page tables)
   - Copy to user memory

2. **System Calls**
   - SVC instruction handler (EL0 → EL1)
   - Basic syscalls: read, write, exit, gpio_set, gpio_get
   - Return to userspace

3. **Minimal Scheduler**
   - Round-robin (no preemption yet)
   - Process table (16 max)
   - Context switch (save/restore registers)

**Deliverable:** Run `/bin/hello.elf` and `/bin/blink.elf` from shell

### Phase 4: Development Environment
**Goal:** Write code on the device

1. **Filesystem**
   - FAT32 read/write (already have USB/SD from UEFI)
   - Simple VFS layer
   - Open/close/read/write

2. **Shell**
   - Command parser (space-delimited args)
   - Built-in commands: ls, cat, run, kill
   - Exec() to launch ELF binaries

3. **GCC Toolchain**
   - Port aarch64-none-elf-gcc (static binary)
   - Minimal libc (syscall wrappers)
   - Compile on-device: `gcc hello.c -o hello.elf`

**Deliverable:** Edit C file, compile, run—all on Orin

### Phase 5: Sheaf Solver Integration
**Goal:** Algebraic OS core

1. **Port Existing Solver**
   - Move `~/Documents/orin/bonsaiOS/kernel/sheaf_solver/` to kernel
   - Replace Eigen with custom matrix ops (no heap allocation)
   - Kernel-space API

2. **Algebraic Scheduler**
   - Process priorities as sheaf sections
   - Solve linear system for optimal CPU allocation
   - Replace round-robin with closed-form solution

3. **Memory as Sheaf**
   - Memory regions as opens in topology
   - Allocation = compatible sections
   - Automatic defragmentation via gluing

**Deliverable:** Provably optimal scheduler (no heuristics)

## Build Instructions

```bash
# Set up EDK2 environment
cd ~/edk2
export GCC5_AARCH64_PREFIX=aarch64-linux-gnu-
source edksetup.sh

# Build bootloader
build -a AARCH64 -t GCC5 -p BonsaiPkg/BonsaiPkg.dsc

# Output: Build/BonsaiPkg/DEBUG_GCC5/AARCH64/BonsaiBootloader.efi
# Copy to USB as BOOTAA64.EFI
```

## Hardware Requirements

- NVIDIA Jetson AGX Orin Nano
- USB drive (FAT32)
- Serial console (optional, for debugging)
- Monitor + keyboard (UEFI console)

## Design Principles

1. **No bloat:** Every line serves a purpose
2. **Algebraic first:** Replace loops with matrix ops
3. **Provable:** Closed-form solutions over heuristics
4. **Minimal dependencies:** Build from scratch
5. **Console-only:** No GUI, no X11, pure text

## Next Immediate Steps

1. Create `kernel/` directory structure
2. Write minimal kernel entry (ARM64 assembly)
3. Implement page allocator
4. Parse UEFI memory map
5. Load and execute kernel.elf from bootloader

---

Built with love. Made with Claude Code.
