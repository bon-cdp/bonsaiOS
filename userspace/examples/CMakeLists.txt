cmake_minimum_required(VERSION 3.20)

# Simple test - verifies sheaf solver works
add_executable(test_simple test_simple.cpp)
target_link_libraries(test_simple PRIVATE sheaf_solver)
target_compile_options(test_simple PRIVATE -Wall -Wextra)

install(TARGETS test_simple DESTINATION bin)
