# Project Plan: The Bonsai OS

**A project by bon-cdp and a friendly AI collaborator.**

**Version:** 1.0
**Date:** 2025-11-10

---

## 1. Vision & Philosophy

**"What if an operating system could reason about itself algebraically?"**

This project is born from a simple but profound observation: the most complex and heuristic-driven problems in operating systems and compilers—scheduling, resource management, pipelining—are fundamentally problems of maintaining local-to-global consistency under constraints. This is precisely the class of problem that sheaf theory and cohomology are designed to describe.

The **Bonsai OS** is an experimental C++ kernel built from the ground up on a radical premise: that a significant portion of an OS's decision-making can be offloaded to a single, unified algebraic solver.

Our philosophy is a joyful fusion of deep mathematics and hardcore systems engineering. We are not just building an OS; we are "bootstrapping an engine for something bigger." We are creating a system that is minimal, elegant, and intentionally structured from its mathematical roots up—a system that might one day learn to optimize itself. This is a long-term learning hobby, a "year of fun" dedicated to exploring the beautiful, recursive loop of mathematics reasoning about computation.

## 2. The Central Hypothesis

> The complex, heuristic-based algorithms that form the core of modern OS schedulers and compiler optimizers can be replaced by a single, closed-form algebraic solver. This "Algebraic Oracle," based on a sheaf-wreath framework, can compute globally optimal or consistent solutions in a single step, leading to a kernel that is smaller, more predictable, and mathematically verifiable.

## 3. Core Architectural Concepts

### 3.1. The Algebraic Oracle (`SheafSolver`)

The heart of Bonsai OS. This C++ component is a direct port of the `GeneralizedSheafLearner` we developed.
- **Function:** It takes a problem definition (a "sheaf") and returns an optimal solution in one step.
- **Interaction:** Other kernel subsystems (scheduler, memory manager) will not contain complex logic. Instead, they will act as clients to the Oracle. They will formulate their state as a sheaf problem, query the Oracle, and act on the returned solution.
- **Example Query:** The scheduler might pass a list of ready processes and their resource needs. The Oracle returns the optimal schedule for the next time slice.

### 3.2. Kernel Design: Minimal & Monolithic

To begin, we will build a minimal, 64-bit monolithic kernel. While a microkernel is appealing, a monolithic design is simpler to bootstrap. We will enforce strong modularity in the C++ code to keep components decoupled, with the `SheafSolver` being the prime example of a distinct, high-level module.

### 3.3. The "Sheafification" of OS Problems

This is the core intellectual challenge and the source of the project's novelty. We must frame classic OS problems in the language of our algebraic framework.

| OS / Compiler Problem | Sheaf-Wreath Interpretation |
| :--- | :--- |
| **Process Scheduling** | **Patches:** Processes ready to run. <br> **Local Data:** Process state (priority, memory, I/O status). <br> **Conditioning:** Group processes by type (CPU-bound, I/O-bound). <br> **Gluing:** Enforce global constraints like "Total CPU < 100%" or "Process B cannot run until Process A's I/O completes." |
| **Register Allocation** | **Patches:** Basic blocks of code in a function. <br> **Local Data:** Variables used within a block. <br> **Gluing:** Liveness analysis. The set of live registers at the end of block `i` must match the live registers at the start of block `j` if there is a control-flow edge `i -> j`. <br> **Obstruction (`H¹`):** A high residual error after the solve indicates high register pressure, signaling that a variable must be "spilled" to the stack. |
| **Memory Management** | **Patches:** Memory regions (e.g., kernel heap, userspace heaps). <br> **Local Data:** Allocation patterns within a region. <br> **Gluing:** Enforce that the total allocated memory across all patches does not exceed physical RAM. |

## 4. Technical Specification

- **Target Architecture:** x86-64
- **Language:** C++20 (utilizing concepts, modules, and modern features)
- **Build System:** CMake
- **Bootloader:** Limine (modern, flexible, and simplifies setup)
- **Core Libraries:** Fully freestanding (`-ffreestanding`). We will implement our own minimal C library functions (`memcpy`, `memset`, etc.) and kernel-specific utilities. No `std` library.

## 5. The Roadmap: A Year of Fun

### Quarter 1: The Bare Metal (Months 1-3)
*The goal is to leave the bootloader and print "Welcome to Bonsai OS!" from our own C++ kernel code.*
- **Engineering:**
    - Set up the x86-64 C++ cross-compiler toolchain.
    - Write the initial bootloader entry code in assembly (`start.asm`).
    - Configure the Limine bootloader.
    - Set up a basic Global Descriptor Table (GDT) and Interrupt Descriptor Table (IDT).
    - Implement a basic serial driver for `printf`-style debugging.
    - Implement a framebuffer driver to print text to the screen.
    - Implement a physical memory manager (bitmap or stack-based).
- **Research:**
    - Read Tanenbaum's *Modern Operating Systems*.
    - Study the x86-64 architecture manual (Volume 3).

### Quarter 2: The Living System (Months 4-6)
*The goal is to have multiple, isolated processes running, scheduled by the first version of our Algebraic Oracle.*
- **Engineering:**
    - Implement virtual memory management (paging).
    - Implement a kernel heap (`kmalloc`).
    - Create the basic `Process` and `Thread` data structures.
    - Implement context switching.
    - **Port the `GeneralizedSheafLearner` to C++ to create the `SheafSolver` (The Oracle).**
    - Implement a simple, round-robin scheduler and then replace it with a query to the Oracle.
- **Research:**
    - Re-read Rotman's chapters on Group Cohomology and Homology.
    - Read the "Dragon Book" (Compilers) to prepare for Phase 3.

### Quarter 3: The Toolchain (Months 7-9)
*The goal is to load and run a simple, dynamically-loaded program from a virtual disk.*
- **Engineering:**
    - Implement a minimal virtual file system (VFS) and an initial RAM disk (initrd) driver.
    - Implement basic system calls (e.g., `read`, `write`, `exit`).
    - Begin work on a minimal C compiler (or port a simple one like `tcc`) that targets Bonsai OS.
    - Design the "sheafification" of the compiler's instruction scheduling problem.
- **Research:**
    - Study compiler backend design and optimization passes.
    - Explore how liveness analysis maps to sheaf gluing conditions.

### Quarter 4: The Recursive Loop (Months 10-12)
*The goal is to have the Bonsai OS compile a program using its own self-optimizing compiler.*
- **Engineering:**
    - Integrate the `SheafSolver` into the compiler's optimization pipeline. The compiler will now query the kernel's Oracle to optimize the code it generates.
    - Set up the toolchain to be self-hosting.
    - **The Final Goal:** Use the `bonsai-cc` compiler, running on Bonsai OS, to re-compile a new version of the Bonsai OS kernel itself.
- **Research & Analysis:**
    - Write the final paper documenting the architecture, the results, and the profound implications of a self-optimizing, algebraically-driven system.
    - Analyze the learned weights from the scheduler and compiler to see if they reveal novel, human-readable optimization strategies.

## 6. Foundational Reading List

- **Operating Systems:**
    1. *Modern Operating Systems* by Andrew S. Tanenbaum
    2. The OSDev Wiki (osdev.org)
- **Compilers:**
    3. *Compilers: Principles, Techniques, and Tools* (The "Dragon Book") by Aho, Lam, Sethi, and Ullman
- **Mathematics:**
    4. *Advanced Modern Algebra* by Joseph J. Rotman (focus on Group Theory, Homology, and Cohomology)
    5. *Sheaves in Geometry and Logic* by Mac Lane and Moerdijk (for a deeper dive)

## 7. Getting Started: The First Steps

1.  Set up the `x86_64-elf` cross-compiler and build tools.
2.  Create the initial project directory with a `CMakeLists.txt` file.
3.  Download and integrate the Limine bootloader files.
4.  Write `limine.cfg` to define the boot protocol.
5.  Write `start.asm`, the assembly entry point that sets up the stack and calls `kmain`.
6.  Write `kmain.cpp`, which initializes serial output and prints our first message.
7.  Build and run in QEMU.

---

This plan is ambitious, deeply interesting, and, most importantly, fun. It's a perfect fusion of our journey so far. I am ready when you are.
