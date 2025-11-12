cmake_minimum_required(VERSION 3.13)
project(BonsaiKernel C CXX ASM)

# Set target architecture
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# Specify the cross compiler
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)
set(CMAKE_ASM_COMPILER aarch64-linux-gnu-gcc)

# Compiler flags
set(CMAKE_C_FLAGS "-ffreestanding -fno-stack-protector -fno-pie -fpic -Wall -Wextra -std=gnu11")
set(CMAKE_CXX_FLAGS "-ffreestanding -fno-stack-protector -fno-pie -fpic -Wall -Wextra -std=gnu++20")
set(CMAKE_ASM_FLAGS "-g") # Add debug info for assembly

# Linker flags
set(CMAKE_EXE_LINKER_FLAGS "-ffreestanding -nostdlib -static -T ${CMAKE_CURRENT_BINARY_DIR}/kernel.lds")

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/gnu-efi/inc
    ${CMAKE_SOURCE_DIR}/gnu-efi/inc/aarch64
)

# Source files
set(KERNEL_SOURCES
    start.S
    kmain.cpp
)

# Create the kernel executable
add_executable(bonsai_kernel ${KERNEL_SOURCES})

# Set properties for the executable
set_target_properties(bonsai_kernel PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)

# Configure the linker script from the template
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/kernel.lds.in"
    "${CMAKE_CURRENT_BINARY_DIR}/kernel.lds"
    @ONLY
)

# Add a custom command to convert the ELF executable to a raw binary
add_custom_command(
    TARGET bonsai_kernel POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:bonsai_kernel> ${CMAKE_BINARY_DIR}/bonsai_kernel.bin
    COMMENT "Converting ELF to raw binary: bonsai_kernel.bin"
)
