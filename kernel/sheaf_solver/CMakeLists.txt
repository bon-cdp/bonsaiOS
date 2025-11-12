cmake_minimum_required(VERSION 3.20)

# Sheaf Solver Library
# C++ port of the Python wreath-sheaf algebraic learning framework

project(sheaf_solver VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories
set(SHEAF_SOLVER_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)
include_directories(${SHEAF_SOLVER_INCLUDE_DIR})

# Find Eigen3 (header-only linear algebra library)
find_package(Eigen3 3.4 QUIET)
if(NOT Eigen3_FOUND)
    message(STATUS "Eigen3 not found, will use embedded minimal matrix library")
    # We'll create a minimal matrix library if Eigen is not available
endif()

# Source files
set(SHEAF_SOLVER_SOURCES
    src/types.cpp
    src/cyclic_group.cpp
    src/unified_sheaf_learner.cpp
)

set(SHEAF_SOLVER_HEADERS
    include/sheaf_solver/character_theory.hpp
    include/sheaf_solver/cyclic_group.hpp
    include/sheaf_solver/unified_sheaf_learner.hpp
    include/sheaf_solver/generalized_sheaf_learner.hpp
    include/sheaf_solver/types.hpp
)

# Build as static library for kernel/userspace linking
add_library(sheaf_solver STATIC ${SHEAF_SOLVER_SOURCES})

target_include_directories(sheaf_solver PUBLIC
    $<BUILD_INTERFACE:${SHEAF_SOLVER_INCLUDE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Link Eigen if available
if(Eigen3_FOUND)
    target_link_libraries(sheaf_solver PUBLIC Eigen3::Eigen)
    target_compile_definitions(sheaf_solver PUBLIC USE_EIGEN3)
endif()

# Compiler options
target_compile_options(sheaf_solver PRIVATE
    -Wall -Wextra -Werror
    -Wno-sign-compare  # Allow sign comparison for Eigen compatibility
    # Note: exceptions and RTTI enabled for userspace, disable for kernel builds later
)

# Install targets
install(TARGETS sheaf_solver
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(DIRECTORY ${SHEAF_SOLVER_INCLUDE_DIR}/
    DESTINATION include
    FILES_MATCHING PATTERN "*.hpp"
)

message(STATUS "Sheaf Solver library configured")
