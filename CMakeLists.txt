cmake_minimum_required(VERSION 3.20)
project(BonsaiOS VERSION 0.1.0 LANGUAGES CXX ASM)

# Target: NVIDIA Jetson AGX Orin (AArch64)
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# Cross-compilation toolchain
# Set via: -DCMAKE_TOOLCHAIN_FILE=cmake/aarch64-toolchain.cmake
# Or use: -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler flags for embedded/kernel development
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -O2")

# Architecture-specific flags (only for cross-compilation)
if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64" AND CMAKE_CROSSCOMPILING)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=armv8.2-a+crypto+fp16")  # Orin is ARMv8.2
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-exceptions -fno-rtti")  # For kernel code
endif()

# Options
option(BUILD_KERNEL "Build kernel components" ON)
option(BUILD_USERSPACE "Build userspace components" ON)
option(BUILD_SHEAF_SOLVER "Build sheaf solver library" ON)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/kernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/sheaf_solver/include)

# Subdirectories
if(BUILD_SHEAF_SOLVER)
    add_subdirectory(kernel/sheaf_solver)
endif()

if(BUILD_KERNEL)
    add_subdirectory(kernel)
endif()

if(BUILD_USERSPACE)
    add_subdirectory(userspace)
endif()

# Install targets
install(DIRECTORY ${CMAKE_BINARY_DIR}/bin/ DESTINATION bin)
install(DIRECTORY ${CMAKE_BINARY_DIR}/lib/ DESTINATION lib)

# Print configuration summary
message(STATUS "========================================")
message(STATUS "BonsaiOS Configuration")
message(STATUS "========================================")
message(STATUS "Version: ${PROJECT_VERSION}")
message(STATUS "Target: ${CMAKE_SYSTEM_PROCESSOR}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Build Kernel: ${BUILD_KERNEL}")
message(STATUS "Build Userspace: ${BUILD_USERSPACE}")
message(STATUS "Build Sheaf Solver: ${BUILD_SHEAF_SOLVER}")
message(STATUS "========================================")
