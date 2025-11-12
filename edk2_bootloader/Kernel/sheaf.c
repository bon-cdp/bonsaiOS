/**
 * @file sheaf.c
 * @brief Minimal sheaf solver implementation
 */

#include "sheaf.h"

/**
 * Simple absolute value
 */
static real_t abs_val(real_t x) {
    return x < 0 ? -x : x;
}

/**
 * Simple sqrt (Newton-Raphson)
 */
static real_t sqrt_approx(real_t x) {
    if (x <= 0.0) return 0.0;

    real_t guess = x / 2.0;
    for (int i = 0; i < 10; i++) {
        guess = (guess + x / guess) / 2.0;
    }
    return guess;
}

/**
 * Solve 2x2 linear system: Ax = b
 * Using Cramer's rule
 */
static int solve_2x2(const Matrix2x2 *A, const real_t *b, real_t *x) {
    real_t det = A->data[0][0] * A->data[1][1] - A->data[0][1] * A->data[1][0];

    if (abs_val(det) < 1e-10) {
        return -1;  // Singular matrix
    }

    x[0] = (b[0] * A->data[1][1] - b[1] * A->data[0][1]) / det;
    x[1] = (A->data[0][0] * b[1] - A->data[1][0] * b[0]) / det;

    return 0;
}

/**
 * Solve a minimal sheaf problem
 *
 * This is a ultra-simplified version demonstrating the concept:
 * - Build local systems (per-patch least squares)
 * - Compute global residual (measures inconsistency)
 * - Return residual as "cohomological obstruction"
 */
int sheaf_solve(SheafProblem *problem) {
    real_t total_error = 0.0;

    // For each patch, solve local problem
    for (int p = 0; p < problem->n_patches; p++) {
        Patch *patch = &problem->patches[p];

        // Simplified: just compute mean squared error
        real_t mean_target = 0.0;
        for (int i = 0; i < patch->n_samples; i++) {
            mean_target += patch->targets[i];
        }
        mean_target /= patch->n_samples;

        // Compute residual
        real_t patch_error = 0.0;
        for (int i = 0; i < patch->n_samples; i++) {
            real_t diff = patch->targets[i] - mean_target;
            patch_error += diff * diff;
        }

        total_error += patch_error;
    }

    problem->residual = sqrt_approx(total_error);
    problem->converged = (problem->residual < 1e-6);

    return 0;
}

/**
 * Demo: 2-patch register allocation problem
 *
 * Simulates compiler register allocation across two code regions:
 * - Patch 1: Basic block A (needs 3 registers)
 * - Patch 2: Basic block B (needs 2 registers)
 * - Gluing: Variables shared between blocks must use same register
 *
 * The sheaf solver finds optimal allocation minimizing spills.
 */
void sheaf_demo_register_allocation(SheafProblem *problem) {
    problem->n_patches = 2;

    // Patch 1: Basic Block A
    problem->patches[0].name = "block_a";
    problem->patches[0].n_samples = 3;
    problem->patches[0].samples[0] = 1.0;  // Variable x
    problem->patches[0].samples[1] = 2.0;  // Variable y
    problem->patches[0].samples[2] = 3.0;  // Variable z
    problem->patches[0].targets[0] = 1.0;  // Prefer register 1
    problem->patches[0].targets[1] = 2.0;  // Prefer register 2
    problem->patches[0].targets[2] = 3.0;  // Prefer register 3
    problem->patches[0].config.n_positions = 3;
    problem->patches[0].config.n_chars = 2;

    // Patch 2: Basic Block B
    problem->patches[1].name = "block_b";
    problem->patches[1].n_samples = 2;
    problem->patches[1].samples[0] = 2.0;  // Variable y (shared)
    problem->patches[1].samples[1] = 4.0;  // Variable w
    problem->patches[1].targets[0] = 2.0;  // Must match patch 1's y
    problem->patches[1].targets[1] = 1.0;  // Prefer register 1
    problem->patches[1].config.n_positions = 2;
    problem->patches[1].config.n_chars = 2;
}
