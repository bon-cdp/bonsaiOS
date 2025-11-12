# BonsaiOS - Algebraic Operating System

**A wreath-sheaf based OS for NVIDIA Jetson AGX Orin Nano**
*Built with love by bon-cdp and AI collaborator* 🌱

---

## 🎯 Vision

**"What if an operating system could reason about itself algebraically?"**

BonsaiOS replaces heuristic OS algorithms (scheduling, compilation, resource allocation) with **closed-form algebraic solutions** using wreath-sheaf theory. Instead of tuning parameters, we solve linear algebra on the GPU.

**The Central Hypothesis:**
Complex OS decisions can be reduced to sheaf cohomology problems and solved optimally in one step.

---

## ✅ Current Status (Quarter 1 Complete!)

**What Works:**
- ✅ **UEFI Bootloader** (EDK2, 16KB, loads kernel & exits boot services)
- ✅ **Freestanding Kernel** (3.1KB, no std library, runs at EL1)
- ✅ **UART Console** (115200 baud, interactive command loop)
- ✅ **Sheaf Solver Demo** (minimal register allocation using wreath-sheaf framework)
- ✅ **Clean Boot Chain** (UEFI → Kernel @ 0x40000000 → Interactive shell)

**Commands Available:**
```
bonsai> help
  help   - Show help
  echo   - Echo input
  sheaf  - Run algebraic solver demo (register allocation)
  status - System status
```

**File Sizes:**
- Bootloader: 16KB (EDK2 PE32+)
- Kernel: 3.1KB (includes console + sheaf solver!)
- Total footprint: <20KB

---

## 🚀 Quick Start

### Hardware Required
- NVIDIA Jetson AGX Orin Nano Developer Kit
- USB drive (FAT32)
- USB-to-TTL serial adapter (CP2102/FTDI recommended)

### Build & Deploy

```bash
# 1. Build bootloader (EDK2)
cd ~/edk2
export GCC5_AARCH64_PREFIX=aarch64-linux-gnu-
source edksetup.sh
build -p BonsaiPkg/BonsaiPkg.dsc -a AARCH64 -t GCC5 -b DEBUG

# 2. Build kernel
cd ~/edk2/BonsaiPkg/Kernel
make

# 3. Deploy to USB
cp ~/edk2/Build/BonsaiPkg/DEBUG_GCC5/AARCH64/BonsaiBootloader.efi /media/usb/EFI/BOOT/BOOTAA64.EFI
cp ~/edk2/BonsaiPkg/Kernel/bonsai_kernel.bin /media/usb/
sync

# 4. Boot Orin from USB
```

### Connect Serial Console

**Wiring (Orin 40-pin header):**
- Pin 6 (GND) → Adapter GND
- Pin 8 (TX) → Adapter RX
- Pin 10 (RX) → Adapter TX

**On Ubuntu:**
```bash
screen /dev/ttyUSB0 115200
# or
picocom -b 115200 /dev/ttyUSB0
```

You'll see:
```
       _
      /\
     /**\     BonsaiOS Kernel v0.2
    /****\    Wreath-sheaf: algebraic OS
   /******\
  /********\
     ||

  [OK] Kernel running
  [OK] UART initialized
  [OK] Console ready

Type 'help' for commands.

bonsai>
```

---

## 🏗️ Architecture

### Boot Flow
```
UEFI Firmware
    ↓
EDK2 Bootloader (~/edk2/BonsaiPkg/BonsaiBootloader/)
    ↓ Loads bonsai_kernel.bin
    ↓ Allocates 16KB stack
    ↓ Calls ExitBootServices()
    ↓ Jumps to 0x40000000
    ↓
Kernel Entry (~/edk2/BonsaiPkg/Kernel/start.S)
    ↓ Disables interrupts
    ↓ Calls kmain()
    ↓
Interactive Console (~/edk2/BonsaiPkg/Kernel/kmain.c)
    ↓ Initializes UART @ 0x03100000
    ↓ Command loop
    ↓
Sheaf Solver (~/edk2/BonsaiPkg/Kernel/sheaf.c)
    ↓ Algebraic problem solving
```

### Kernel Design
- **Language:** C (freestanding, `-ffreestanding -nostdlib`)
- **Entry Point:** 0x40000000 (physical)
- **Stack:** 16KB (allocated by bootloader)
- **I/O:** UART only (UEFI ConOut unavailable after ExitBootServices)
- **Dependencies:** ZERO (no libc, no std, no runtime)

### Sheaf Solver
Minimal demonstration of wreath-sheaf theory:
- **Input:** 2-patch register allocation problem
- **Output:** Residual (cohomological obstruction)
- **Algorithm:** Simplified least-squares (full solver in development)
- **Size:** ~500 bytes compiled

---

## 📋 Roadmap

### ✅ Quarter 1: Boot & Console (COMPLETE)
- UEFI bootloader
- Kernel boots to interactive shell
- UART I/O working
- Sheaf solver proof-of-concept

### 🔄 Quarter 2: Hardware Acceleration (IN PROGRESS)
**Next Milestones:**
1. **USB XHCI Keyboard Driver** (see ROADMAP.md)
   - Map XHCI MMIO registers
   - Initialize ring buffers & event handlers
   - Enumerate USB devices
   - Implement HID keyboard protocol
   - Estimated: 3000-5000 LOC, 2-4 weeks

2. **Framebuffer/GPU Output**
   - Replace UART with visual console
   - Basic GPU initialization
   - Text rendering

3. **Memory Management**
   - Page table setup (ARMv8 MMU)
   - Heap allocator
   - Virtual memory

### Quarter 3: GPU-Accelerated Sheaf Solver
- CUDA driver for Orin GPU
- Port sheaf solver to GPU
- Process scheduler using algebraic oracle

### Quarter 4: Self-Hosting Compiler
- Integrate sheaf solver into compiler backend
- Self-optimizing code generation
- Recompile BonsaiOS with its own compiler

---

## 📁 Repository Structure

```
bonsaiOS/
├── edk2_bootloader/          # EDK2 UEFI bootloader + kernel
│   ├── BonsaiBootloader/     # UEFI application (16KB)
│   ├── Kernel/               # Freestanding kernel (3.1KB)
│   │   ├── start.S          # AArch64 entry point
│   │   ├── kmain.c          # Console & command loop
│   │   ├── sheaf.c          # Algebraic solver
│   │   └── Makefile
│   └── BonsaiPkg.dsc        # EDK2 build configuration
├── uefi/ (deprecated)        # Old gnu-efi bootloader (superseded)
├── kernel/                   # Future: expanded kernel modules
│   └── sheaf_solver/        # Full C++ sheaf framework
├── ROADMAP.md               # Detailed future plans
└── README.md                # This file
```

---

## 🔧 Technical Details

### Why EDK2 instead of gnu-efi?
- **Proper PE/COFF format** (2 sections vs 6)
- **Industry standard** (used by NVIDIA, Microsoft, Intel)
- **Smaller binaries** (16KB vs 50KB)
- **Better toolchain integration**

### Why UART instead of USB keyboard?
After `ExitBootServices()`, UEFI's `ConIn` protocol is **gone**. You need your own driver:
- **UART:** Already works (30 min hardware setup)
- **USB:** Requires full XHCI driver (~3000 LOC, 2-4 weeks)

See `ROADMAP.md` for USB keyboard implementation plan.

### Kernel Memory Map
```
0x40000000 - 0x40000C40  Kernel code (.text)
0x40000C40 - 0x40001000  Kernel data (.data/.bss)
0x........  - 0x........  Stack (16KB, grows down)
0x03100000              UART MMIO
0x........              GPU MMIO (future)
```

---

## 🧮 The Sheaf Solver

**Current Demo:** Register allocation across 2 basic blocks
```
Problem:
  Patch 1 (block_a): variables x, y, z → prefer registers 1, 2, 3
  Patch 2 (block_b): variables y, w → prefer registers 2, 1
  Gluing: variable 'y' must use same register in both blocks

Solver computes residual (obstruction to consistency).
If residual = 0, allocation is globally optimal.
```

**Full Framework** (in `kernel/sheaf_solver/`):
- Cyclic group character theory
- Wreath product decomposition
- Sheaf cohomology solver
- Currently uses Eigen for userspace testing
- Will be ported to freestanding + GPU

---

## 📚 References

**Hardware:**
- [NVIDIA Jetson AGX Orin Developer Kit](https://developer.nvidia.com/embedded/jetson-agx-orin-developer-kit)
- [L4T Documentation](https://docs.nvidia.com/jetson/archives/r35.3.1/DeveloperGuide/index.html)

**Software:**
- [EDK2 TianoCore](https://github.com/tianocore/edk2)
- [Circle - Raspberry Pi Bare Metal](https://github.com/rsta2/circle) (USB reference)
- [OSDev Wiki](https://wiki.osdev.org/)

**Mathematics:**
- *Advanced Modern Algebra* - Joseph J. Rotman
- *Algebraic Geometry* - Robin Hartshorne

---

## 🤝 Contributing

This is a research/learning project. Contributions welcome for:
- USB XHCI driver implementation
- GPU/CUDA integration
- Sheaf solver optimizations
- Documentation improvements

**Contact:** bon-cdp on GitHub

---

## 📄 License

MIT License - See LICENSE file

---

**Status:** Quarter 1 Complete ✅ | Interactive kernel running on hardware
**Next:** USB keyboard driver (see ROADMAP.md)
