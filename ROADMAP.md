# BonsaiOS Development Roadmap

**Last Updated:** November 12, 2025
**Current Milestone:** Quarter 1 Complete ✅

---

## Quarter 1: Boot & Console ✅ COMPLETE

**Timeline:** November 2025
**Status:** SHIPPED

**Achievements:**
- [x] EDK2 UEFI bootloader (16KB, PE32+ format)
- [x] Freestanding AArch64 kernel (3.1KB)
- [x] UART driver @ 115200 baud
- [x] Interactive command shell
- [x] Minimal sheaf solver (register allocation demo)
- [x] Clean boot chain: UEFI → Kernel @ 0x40000000 → Console

**Technical Milestones:**
- Kernel runs bare metal after `ExitBootServices()`
- Zero dependencies (no libc, no std library)
- Command parser with 4 built-in commands
- Algebraic problem solving demonstrated

---

## Quarter 2: Hardware Acceleration 🔄 IN PROGRESS

**Timeline:** December 2025 - February 2026
**Goal:** USB input, visual output, memory management

### Milestone 2.1: USB XHCI Keyboard Driver

**Priority:** HIGH
**Complexity:** ⭐⭐⭐⭐⭐
**Estimated Time:** 2-4 weeks
**Lines of Code:** 3000-5000

#### Why This Matters
After `ExitBootServices()`, UEFI's keyboard support is gone. To make BonsaiOS usable without serial console, we need a full USB stack.

#### Technical Requirements

**1. XHCI Controller Initialization**
- Map Orin's XHCI MMIO registers (base address from device tree)
- Reset controller and verify hardware version
- Allocate DMA-coherent memory for ring buffers
- Set up operational register space

**Files to Create:**
```
kernel/drivers/usb/
├── xhci.h           # XHCI register definitions
├── xhci_init.c      # Controller initialization
├── xhci_ring.c      # Transfer ring management
├── xhci_event.c     # Event handler (TRBs)
└── xhci_port.c      # Port status & enumeration
```

**Key Structs:**
```c
struct xhci_regs {
    volatile uint32_t cap_length;    // Capability registers
    volatile uint32_t hcs_params1;   // Structural parameters
    volatile uint32_t op_usb_cmd;    // USB command register
    volatile uint32_t op_usb_sts;    // USB status register
    // ... (100+ registers)
};

struct xhci_trb {
    uint64_t parameter;
    uint32_t status;
    uint32_t control;
};
```

**2. USB Device Enumeration**
- Detect device attachment on ports
- Issue USB RESET to device
- Send GET_DESCRIPTOR requests
- Parse device/configuration/interface descriptors
- SET_CONFIGURATION to activate device

**Protocol Flow:**
```
Port Status Change Event
    ↓
USB Reset (50ms delay)
    ↓
Get Device Descriptor (8 bytes)
    ↓
Set Address
    ↓
Get Full Device Descriptor
    ↓
Get Configuration Descriptor
    ↓
Set Configuration
    ↓
Device Ready
```

**3. HID Keyboard Driver**
- Match interface class/subclass (0x03/0x01)
- Parse HID Report Descriptor
- Set boot protocol mode
- Install interrupt endpoint handler
- Decode HID reports → scancodes → ASCII

**HID Report Structure:**
```c
struct hid_keyboard_report {
    uint8_t modifiers;    // Ctrl, Shift, Alt, etc.
    uint8_t reserved;
    uint8_t keys[6];      // Up to 6 simultaneous keys
};
```

**Scancode Translation Table:**
```c
// USB HID Usage ID → ASCII
static const char usb_to_ascii[256] = {
    [0x04] = 'a', [0x05] = 'b', ... // lowercase
    [0x1E] = '1', [0x1F] = '2', ... // numbers
    // + shift combinations
};
```

#### Implementation Phases

**Phase 1: Basic XHCI (Week 1)**
- [ ] Map XHCI registers from device tree
- [ ] Initialize controller (reset, start, halt)
- [ ] Allocate command ring
- [ ] Send NOP command, verify response
- **Validation:** Can send XHCI commands

**Phase 2: Port Management (Week 2)**
- [ ] Implement port status polling
- [ ] Detect USB device connect/disconnect
- [ ] Issue port reset
- [ ] Read port speed (USB 2.0/3.0)
- **Validation:** Detect keyboard insertion

**Phase 3: Device Enumeration (Week 2-3)**
- [ ] Allocate device slot
- [ ] Send SET_ADDRESS
- [ ] Get descriptors (device, config, interface)
- [ ] Parse HID class-specific descriptors
- **Validation:** Device enumerated, address assigned

**Phase 4: HID Keyboard (Week 3-4)**
- [ ] Install interrupt IN endpoint
- [ ] Parse HID reports
- [ ] Implement scancode → ASCII table
- [ ] Handle modifier keys (Shift, Ctrl, Alt)
- [ ] Integrate with kernel console input
- **Validation:** Typing on USB keyboard works!

#### Reference Implementations

**Circle Library (Raspberry Pi 4):**
- File: `lib/usb/xhcidevice.cpp` (~1500 LOC)
- Good: Clean structure, well-documented
- Bad: C++, tied to Circle framework

**EDK2 XHCI Driver:**
- Path: `MdeModulePkg/Bus/Pci/XhciDxe/`
- Good: Production-quality, handles edge cases
- Bad: UEFI-specific, complex abstractions

**Linux Kernel:**
- File: `drivers/usb/host/xhci-ring.c`
- Good: Handles all USB 3.0 features
- Bad: Too complex for minimal OS

**OSDev Wiki:**
- URL: https://wiki.osdev.org/XHCI
- Good: Beginner-friendly overview
- Bad: Incomplete implementation details

#### Hardware Specifics (Orin)

**XHCI Controller Location:**
```bash
# From Linux device tree:
usb@3610000 {
    compatible = "nvidia,tegra234-xusb";
    reg = <0x0 0x3610000 0x0 0x40000>;  # XHCI base
    interrupts = <GIC_SPI 163 IRQ_TYPE_LEVEL_HIGH>;
};
```

**Base Address:** 0x03610000 (physical)
**IRQ:** 163 (if using interrupts)

**DMA Considerations:**
- Orin uses SMMU (IOMMU) - may need bypass mode
- Ring buffers need physical addresses (not virtual)
- Align to 64-byte boundaries

#### Testing Strategy

**Test 1: Controller Init**
```c
// Expected: XHCI operational
print_xhci_version();  // Should show "1.10" or "1.20"
```

**Test 2: Port Detection**
```c
// Insert USB keyboard
// Expected: "Port 1: Device connected, speed = USB 2.0"
```

**Test 3: Enumeration**
```c
// Expected: Device descriptor printed
// Vendor ID, Product ID, Class = HID
```

**Test 4: Keyboard Input**
```
bonsai> [type on USB keyboard]
hello from usb!
bonsai> help
```

#### Known Challenges

1. **DMA Setup**
   - Solution: Use identity-mapped physical memory initially
   - Future: Integrate with MMU/page tables

2. **Timing Requirements**
   - USB requires precise delays (10ms reset, 50ms settle)
   - Solution: Implement udelay() using ARM timer

3. **Interrupt Handling**
   - XHCI uses MSI/MSI-X on PCIe
   - Solution: Start with polling, add IRQs in Phase 2

4. **Multiple Devices**
   - What if user plugs in hub + keyboard + mouse?
   - Solution: Handle one keyboard for now, expand later

#### Success Criteria

- [ ] USB keyboard detected on boot
- [ ] Keypresses appear in console
- [ ] Modifier keys (Shift, Ctrl) work
- [ ] Can type commands and run `sheaf` solver
- [ ] No serial cable needed for interaction

---

### Milestone 2.2: Framebuffer/GPU Output

**Priority:** MEDIUM
**Estimated Time:** 2-3 weeks

**Goals:**
- Replace UART text output with HDMI framebuffer
- Basic text console (80x25 or similar)
- Blit ASCII font to screen

**Technical Approach:**
1. Query UEFI GOP (Graphics Output Protocol) for framebuffer address
2. Get framebuffer before ExitBootServices, store address
3. Implement pixel plotting (RGB888 or RGB565)
4. Load embedded font (8x16 bitmap)
5. Render text to framebuffer

**Files:**
```
kernel/drivers/video/
├── framebuffer.h
├── framebuffer.c
├── font_8x16.c    # Embedded bitmap font
└── console.c      # Terminal emulator
```

**Advantages:**
- Visual feedback without serial cable
- Foundation for GUI later
- GPU can draw to same framebuffer

---

### Milestone 2.3: Memory Management

**Priority:** HIGH (prerequisite for everything else)
**Estimated Time:** 3-4 weeks

**Components:**

**1. ARMv8 MMU Setup**
- Configure translation tables (4KB pages)
- Identity map kernel code (0x40000000)
- Map UART/XHCI/GPU MMIO regions
- Enable MMU in EL1

**2. Physical Memory Allocator**
- Parse UEFI memory map (before ExitBootServices)
- Buddy allocator or bitmap allocator
- kmalloc()/kfree() interface

**3. Heap**
- Simple bump allocator initially
- Later: dlmalloc or jemalloc port

**Why This Matters:**
- XHCI needs DMA buffers
- GPU needs large allocations
- Future: Process isolation

---

## Quarter 3: GPU-Accelerated Sheaf Solver

**Timeline:** March - May 2026

### Milestone 3.1: CUDA Driver (Bare Metal)

**Challenge Level:** ⭐⭐⭐⭐⭐
**Estimated Time:** 6-8 weeks

**Goal:** Submit CUDA kernel to Orin GPU, retrieve result

**Steps:**
1. Map GPU MMIO registers (GR, FIFO, memory)
2. Initialize PMU (Power Management Unit)
3. Load GPU firmware from disk
4. Set up channel for kernel submission
5. Allocate GPU memory (BAR1 mapping)
6. Compile CUDA → PTX → SASS
7. Submit "Hello GPU" kernel
8. Poll for completion

**Reference:**
- NVIDIA Open GPU Kernel Modules (linux/kernel-open/)
- Nouveau driver (open-source reverse engineering)
- CUDA Programming Guide (Chapter 2: Hardware)

### Milestone 3.2: Sheaf Solver on GPU

**Input:** Process scheduling matrix (N threads × M features)
**Output:** Optimal schedule vector

**Workflow:**
```
CPU: Package thread state → matrix A
  ↓
GPU: Solve A^H A w = A^H b (LLT decomposition)
  ↓
CPU: Apply schedule, context switch
```

**Performance Goal:** <1ms for 100 threads

---

## Quarter 4: Self-Hosting Compiler

**Timeline:** June - August 2026

### Milestone 4.1: Minimal C Compiler

**Option A:** Port TinyCC to BonsaiOS
**Option B:** Write simple compiler (subset of C)

**Requirements:**
- Parse C syntax
- Generate AArch64 assembly
- Link to kernel

### Milestone 4.2: Sheaf-Optimized Codegen

**Integration Point:** Register allocation

**Traditional Approach:**
- Graph coloring heuristic
- May spill even when optimal allocation exists

**Sheaf Approach:**
- Model as 2-patch problem (basic blocks)
- Solve for globally consistent allocation
- Residual = 0 → no spills needed

**Demo:**
- Compile BonsaiOS kernel with sheaf compiler
- Compare code size vs GCC
- Measure compilation time

---

## Future Work (Year 2+)

### Advanced Features
- [ ] Multitasking / context switching
- [ ] Process isolation (MMU)
- [ ] File system (FAT32 or custom)
- [ ] Network stack (Ethernet driver)
- [ ] USB hub support
- [ ] USB mass storage (for loading programs)

### Sheaf Framework Extensions
- [ ] Scheduler using sheaf cohomology
- [ ] Memory allocator (optimal page placement)
- [ ] I/O scheduling (minimize latency)
- [ ] Power management (DVFS using algebraic model)

### Research Goals
- [ ] Formal verification of sheaf solver
- [ ] Performance comparison: Sheaf vs heuristic algorithms
- [ ] GPU utilization analysis
- [ ] Self-optimization measurements

---

## Dependencies & Prerequisites

### Hardware
- **Required:**
  - NVIDIA Jetson AGX Orin Nano Dev Kit
  - USB-to-TTL serial adapter (current)
  - USB keyboard (for USB driver milestone)

- **Optional:**
  - HDMI monitor (for framebuffer)
  - USB hub (for multi-device testing)
  - Logic analyzer (for debugging USB)

### Software
- **Build Tools:**
  - aarch64-linux-gnu-gcc (cross-compiler)
  - EDK2 build environment
  - git, make, cmake

- **Development:**
  - screen/picocom (serial console)
  - QEMU aarch64 (testing, when MMU added)
  - GDB with AArch64 support

---

## Community & Collaboration

**Help Wanted:**
- USB XHCI driver implementation
- GPU/CUDA reverse engineering
- ARMv8 MMU/paging setup
- Documentation improvements

**How to Contribute:**
1. Fork https://github.com/bon-cdp/bonsaiOS
2. Check ROADMAP.md for open tasks
3. Submit PR with tests
4. Join discussions in Issues

---

## Timeline Summary

| Quarter | Milestone | Status | ETA |
|---------|-----------|--------|-----|
| Q1 2025 | Boot + Console | ✅ DONE | Nov 2025 |
| Q2 2026 | USB + Framebuffer + MMU | 🔄 IN PROGRESS | Feb 2026 |
| Q3 2026 | GPU + Sheaf Solver | ⏳ PLANNED | May 2026 |
| Q4 2026 | Self-Hosting Compiler | ⏳ PLANNED | Aug 2026 |

---

**Last Updated:** November 12, 2025
**Next Review:** December 1, 2025 (after USB driver progress)
