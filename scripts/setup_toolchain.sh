#!/bin/bash
# Setup script for BonsaiOS development environment
# Installs cross-compilation toolchain and dependencies

set -e

echo "=========================================="
echo "BonsaiOS Toolchain Setup"
echo "=========================================="
echo

# Check if running on Ubuntu/Debian
if ! command -v apt-get &> /dev/null; then
    echo "Error: This script requires apt-get (Ubuntu/Debian)"
    exit 1
fi

echo "Installing AArch64 cross-compilation toolchain..."
sudo apt-get update
sudo apt-get install -y \
    gcc-aarch64-linux-gnu \
    g++-aarch64-linux-gnu \
    binutils-aarch64-linux-gnu \
    build-essential \
    cmake \
    device-tree-compiler \
    qemu-system-aarch64 \
    qemu-user-static \
    binfmt-support

echo
echo "Installing Eigen3 (linear algebra library)..."
sudo apt-get install -y libeigen3-dev

echo
echo "Installing build tools..."
sudo apt-get install -y \
    git \
    wget \
    rsync \
    bc \
    cpio \
    unzip \
    libncurses-dev \
    flex \
    bison \
    libssl-dev

echo
echo "Checking for Buildroot (for minimal Linux)..."
if [ ! -d "buildroot" ]; then
    echo "Buildroot not found. You can download it with:"
    echo "  cd $(dirname "$0")/.."
    echo "  wget https://buildroot.org/downloads/buildroot-2024.02.tar.gz"
    echo "  tar xf buildroot-2024.02.tar.gz"
    echo "  mv buildroot-2024.02 buildroot"
else
    echo "Buildroot found at: buildroot/"
fi

echo
echo "=========================================="
echo "Toolchain Setup Complete!"
echo "=========================================="
echo
echo "Installed tools:"
echo "  - aarch64-linux-gnu-gcc: $(aarch64-linux-gnu-gcc --version | head -1)"
echo "  - aarch64-linux-gnu-g++: $(aarch64-linux-gnu-g++ --version | head -1)"
echo "  - cmake: $(cmake --version | head -1)"
echo "  - qemu-system-aarch64: $(qemu-system-aarch64 --version | head -1)"
echo
echo "Next steps:"
echo "  1. cd kernel/sheaf_solver"
echo "  2. mkdir build && cd build"
echo "  3. cmake .."
echo "  4. make"
echo
echo "For cross-compilation:"
echo "  cmake -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++ .."
echo
