/**
 * @file sheaf.h
 * @brief Minimal freestanding sheaf solver for BonsaiOS kernel
 *
 * No std library, no dynamic allocation, fixed-size arrays only.
 * Demonstrates wreath-sheaf algebraic framework for OS decisions.
 */

#pragma once

// Fixed-size configuration
#define MAX_PATCHES 4
#define MAX_SAMPLES_PER_PATCH 8
#define MAX_WEIGHTS 16
#define MAX_CONSTRAINTS 8

// Simple types
typedef double real_t;

/**
 * A minimal 2x2 matrix (for demo purposes)
 */
typedef struct {
    real_t data[2][2];
} Matrix2x2;

/**
 * Patch configuration
 */
typedef struct {
    int n_positions;
    int n_chars;
} PatchConfig;

/**
 * Patch data (simplified)
 */
typedef struct {
    const char *name;
    real_t samples[MAX_SAMPLES_PER_PATCH];  // Flattened data
    real_t targets[MAX_SAMPLES_PER_PATCH];
    int n_samples;
    PatchConfig config;
} Patch;

/**
 * Sheaf problem
 */
typedef struct {
    Patch patches[MAX_PATCHES];
    int n_patches;
    real_t residual;  // Output: cohomological obstruction
    int converged;
} SheafProblem;

/**
 * Solve a minimal sheaf problem
 * Returns 0 on success, -1 on error
 */
int sheaf_solve(SheafProblem *problem);

/**
 * Demo: 2-patch register allocation problem
 */
void sheaf_demo_register_allocation(SheafProblem *problem);
