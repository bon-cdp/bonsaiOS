# BonsaiOS - Minimal Wreath-Sheaf OS for NVIDIA Orin

## Project Structure

```
bonsaiOS/
├── kernel/                    # Kernel source code
│   ├── arch/aarch64/          # AArch64-specific code (boot, MMU, interrupts)
│   ├── drivers/               # Hardware drivers
│   │   ├── gpio/              # GPIO driver for pin control
│   │   ├── uart/              # UART driver for serial console
│   │   └── i2c/               # I2C driver for peripherals
│   ├── mm/                    # Memory management
│   └── sheaf_solver/          # Core wreath-sheaf algebraic solver
│
├── userspace/                 # Userspace programs
│   ├── init/                  # Init system
│   └── examples/              # Example C++ programs for board I/O
│
├── buildroot/                 # Buildroot configuration for minimal Linux
│
├── sheaf_compiler/            # Original Python implementation (reference)
│   ├── character_theory_attention.py
│   ├── unified_sheaf_learner.py
│   └── generalized_sheaf_learner.py
│
├── docs/                      # Documentation
├── scripts/                   # Build and deployment scripts
│
├── TURTLES                    # Philosophy: Turtles all the way down
├── Bonsai-OS-Plan.md          # Master plan
└── README.md                  # Project overview
```

## Build Targets

### Phase 1: Minimal Linux Base (Pragmatic Path)
- **Target**: ~300MB bootable system
- **Components**: Linux kernel + busybox + GCC + essential libs
- **Goal**: Fast path to working I/O and development environment

### Phase 2: Sheaf Solver Integration
- **Port**: Python → C++20
- **Integration**: Kernel module or userspace daemon
- **Libraries**: Eigen (linear algebra)

### Phase 3: Custom Bare-Metal Kernel (Pure Path)
- **Target**: ~50-100MB pure BonsaiOS
- **Components**: Custom kernel with sheaf solver as core
- **Goal**: Minimal, mathematically elegant system

## Key Files (To Be Created)

- `CMakeLists.txt` - Main build configuration
- `kernel/sheaf_solver/` - C++ port of algebraic solver
- `scripts/build_usb.sh` - USB drive creation script
- `buildroot/.config` - Buildroot minimal configuration
- `kernel/arch/aarch64/start.S` - Boot entry point
- `docs/IO_API.md` - Board I/O usage guide

## Size Target

**Total OS image: < 2GB** (ideally ~500MB-1GB with headroom)

## Development Flow

1. Build cross-compilation toolchain
2. Configure buildroot for minimal Orin image
3. Port sheaf solver to C++
4. Build kernel with drivers
5. Create bootable USB image
6. Test on Orin hardware
