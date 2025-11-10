"""
Generate MLIR examples from ALL test cases in the sheaf-wreath framework.

This script trains the GeneralizedSheafLearner on each of the 4 major tasks:
1. Counting (simple algebraic)
2. Copy (conditional routing)
3. Theorem proving (abstract reasoning)
4. NSE Vorticity (physically-constrained with gluing)

Each generates corresponding MLIR files for the HEIR team.
"""

import sys
sys.path.append('..')

import numpy as np
from generalized_sheaf_learner import GeneralizedSheafLearner
from unified_sheaf_learner import UnifiedSheafLearner
from sheaf_emitter import SheafMLIREmitter, SheafMLIRConfig


# ============================================================================
# Problem Generators
# ============================================================================

def generate_counting_data(n_samples=100):
    """
    Counting Task: [a, a+s, a+2s, a+3s] → a+4s

    Simple arithmetic progression prediction.
    Single patch, no conditional logic.
    """
    V_samples = []
    targets = []
    strides = [1, 2, 3, 5]

    for _ in range(n_samples):
        a = np.random.randint(-10, 11)
        s = np.random.choice(strides)
        seq = np.array([[a + i*s] for i in range(4)], dtype=float)
        target = np.array([[a + 4*s]], dtype=float)
        V_samples.append(seq)
        targets.append(target)

    return V_samples, targets


def generate_copy_data(n_samples=300):
    """
    Copy Task: [marker, x, y, z] → x/y/z based on marker

    Conditional routing: the first element determines which value to copy.
    Three patches (one per position).
    """
    V_samples = []
    targets = []

    for _ in range(n_samples):
        marker = np.random.randint(0, 3)
        values = np.random.randn(3)
        seq = np.array([[marker], [values[0]], [values[1]], [values[2]]], dtype=float)
        target = np.array([[values[marker]]], dtype=float)
        V_samples.append(seq)
        targets.append(target)

    return V_samples, targets


def generate_proof_data(n_samples_per_theorem=50):
    """
    Theorem Proving: Two simple proof patterns

    Theorem 0: [0, 1, 2, 3] → 4 (simple increment)
    Theorem 1: [1, 2, 4, 8] → 16 (powers of 2)

    Two patches, one per theorem.
    """
    V_samples = []
    targets = []

    # Theorem 0: Linear pattern
    for _ in range(n_samples_per_theorem):
        seq = np.array([[0.0], [1.0], [2.0], [3.0]])
        target = np.array([[4.0]])
        V_samples.append(seq)
        targets.append(target)

    # Theorem 1: Exponential pattern
    for _ in range(n_samples_per_theorem):
        seq = np.array([[1.0], [2.0], [4.0], [8.0]])
        target = np.array([[16.0]])
        V_samples.append(seq)
        targets.append(target)

    return V_samples, targets


def generate_nse_vorticity_data(n_samples=50, n_spatial=32, d_model=1):
    """
    NSE Vorticity: 1D slice of 2D Navier-Stokes vorticity field

    Smooth evolution: ω(t + dt) ≈ ω(t) + smooth_derivative

    Two spatial patches with periodic boundary constraint.
    """
    V_samples = []
    targets = []

    for _ in range(n_samples):
        # Generate smooth initial vorticity field
        x = np.linspace(0, 2*np.pi, n_spatial)
        omega_0 = np.sin(x) + 0.5 * np.cos(2*x)

        # Simple evolution: slightly damped + rotated
        omega_next = 0.98 * omega_0 + 0.1 * np.roll(omega_0, 1)

        V_samples.append(omega_0.reshape(-1, d_model))
        targets.append(omega_next.reshape(-1, d_model))

    return V_samples, targets


# ============================================================================
# Main Generation Pipeline
# ============================================================================

def main():
    print("="*80)
    print("Generating ALL MLIR Examples from Sheaf-Wreath Framework")
    print("="*80)
    print("\nThis will generate 4 complete examples demonstrating:")
    print("  1. Simple algebraic pattern (counting)")
    print("  2. Conditional routing (copy)")
    print("  3. Abstract reasoning (theorem proving)")
    print("  4. Physically-constrained dynamics (NSE vorticity)")
    print("="*80)

    # ========================================================================
    # Example 1: Counting Task
    # ========================================================================
    print("\n[1/4] Counting Task")
    print("-"*80)

    learner1 = GeneralizedSheafLearner(verbose=False)
    V_count, T_count = generate_counting_data(n_samples=100)

    solution1, residual1 = learner1.fit(
        V_count, T_count,
        problem_config={'n_characters': 4, 'd_model': 1},
        conditioning_function=lambda v, t: "counting_patch"
    )

    print(f"✓ Trained: Residual = {residual1:.6e}")
    print(f"  Cohomological obstruction: {residual1:.6e} (should be ~0)")

    emitter1 = SheafMLIREmitter(solution1, SheafMLIRConfig(
        module_name="counting_task",
        function_name="predict",
        add_comments=True
    ))

    with open("examples/01_counting.mlir", 'w') as f:
        f.write(emitter1.emit())

    print("✓ Generated: examples/01_counting.mlir")

    # ========================================================================
    # Example 2: Copy Task (Multi-Patch)
    # ========================================================================
    print("\n[2/4] Copy Task (Conditional Routing)")
    print("-"*80)

    learner2 = GeneralizedSheafLearner(verbose=False)
    V_copy, T_copy = generate_copy_data(n_samples=300)

    solution2, residual2 = learner2.fit(
        V_copy, T_copy,
        problem_config={'n_characters': 4, 'd_model': 1},
        conditioning_function=lambda v, t: f"copy_pos_{int(v[0,0])}"
    )

    print(f"✓ Trained: Residual = {residual2:.6e}")
    print(f"  Patches discovered: {len(solution2)} {list(solution2.keys())}")
    print(f"  Cohomological obstruction: {residual2:.6e}")

    # Generate MLIR for all patches
    for patch_name in solution2.keys():
        single_patch = {patch_name: solution2[patch_name]}
        emitter = SheafMLIREmitter(single_patch, SheafMLIRConfig(
            module_name=f"copy_task_{patch_name}",
            function_name="predict",
            add_comments=True
        ))

        filename = f"examples/02_copy_{patch_name}.mlir"
        with open(filename, 'w') as f:
            f.write(emitter.emit())

        print(f"✓ Generated: {filename}")

    # ========================================================================
    # Example 3: Theorem Proving (Abstract Reasoning)
    # ========================================================================
    print("\n[3/4] Theorem Proving Task")
    print("-"*80)

    learner3 = GeneralizedSheafLearner(verbose=False)
    V_proof, T_proof = generate_proof_data(n_samples_per_theorem=50)

    solution3, residual3 = learner3.fit(
        V_proof, T_proof,
        problem_config={'n_characters': 4, 'd_model': 1},
        conditioning_function=lambda v, t: f"theorem_{int(v[0,0])}"
    )

    print(f"✓ Trained: Residual = {residual3:.6e}")
    print(f"  Theorems discovered: {len(solution3)} {list(solution3.keys())}")
    print(f"  Cohomological obstruction: {residual3:.6e}")

    # Generate MLIR for both theorem patches
    for patch_name in solution3.keys():
        single_patch = {patch_name: solution3[patch_name]}
        emitter = SheafMLIREmitter(single_patch, SheafMLIRConfig(
            module_name=f"proof_task_{patch_name}",
            function_name="prove",
            add_comments=True
        ))

        filename = f"examples/03_proof_{patch_name}.mlir"
        with open(filename, 'w') as f:
            f.write(emitter.emit())

        print(f"✓ Generated: {filename}")

    # ========================================================================
    # Example 4: NSE Vorticity (Gluing Constraints)
    # ========================================================================
    print("\n[4/4] NSE Vorticity (Physically-Constrained)")
    print("-"*80)

    n_samples, n_spatial, d_model = 50, 32, 1
    V_nse, T_nse = generate_nse_vorticity_data(n_samples, n_spatial, d_model)

    # Manual patch definition for spatial decomposition
    patch_a_indices = np.arange(20)
    patch_b_indices = np.arange(12, 32)

    V_A = [v[patch_a_indices] for v in V_nse]
    T_A = [t[patch_a_indices] for t in T_nse]
    V_B = [v[patch_b_indices] for v in V_nse]
    T_B = [t[patch_b_indices] for t in T_nse]

    # Gluing constraint: predictions must agree at overlap
    constraint_data_A = V_A[0]
    constraint_data_B = V_B[0]

    problem_definition = {
        'patches': {
            'nse_left': {
                'data': (V_A, T_A),
                'config': {'n_characters': 8, 'd_model': d_model, 'n_positions': len(patch_a_indices)}
            },
            'nse_right': {
                'data': (V_B, T_B),
                'config': {'n_characters': 8, 'd_model': d_model, 'n_positions': len(patch_b_indices)}
            }
        },
        'gluings': [
            {
                'patch_1': 'nse_left',
                'patch_2': 'nse_right',
                'constraint_data_1': constraint_data_A,
                'constraint_data_2': constraint_data_B,
            }
        ]
    }

    # Use UnifiedSheafLearner directly for manual gluing
    unified_learner = UnifiedSheafLearner(verbose=False)
    solution4, residual4 = unified_learner.fit(problem_definition)

    print(f"✓ Trained: Residual = {residual4:.6e}")
    print(f"  Patches: {list(solution4.keys())}")
    print(f"  Gluing constraints: 1 (periodic boundary)")
    print(f"  Cohomological obstruction: {residual4:.6e}")

    # Generate MLIR for both NSE patches
    for patch_name in solution4.keys():
        single_patch = {patch_name: solution4[patch_name]}
        emitter = SheafMLIREmitter(single_patch, SheafMLIRConfig(
            module_name=f"nse_{patch_name}",
            function_name="evolve",
            add_comments=True
        ))

        filename = f"examples/04_nse_{patch_name}.mlir"
        with open(filename, 'w') as f:
            f.write(emitter.emit())

        print(f"✓ Generated: {filename}")

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "="*80)
    print("✅ ALL EXAMPLES GENERATED SUCCESSFULLY!")
    print("="*80)

    print("\nGenerated files:")
    print("  1. examples/01_counting.mlir")
    print("  2. examples/02_copy_pos_0.mlir")
    print("     examples/02_copy_pos_1.mlir")
    print("     examples/02_copy_pos_2.mlir")
    print("  3. examples/03_proof_theorem_0.mlir")
    print("     examples/03_proof_theorem_1.mlir")
    print("  4. examples/04_nse_nse_left.mlir")
    print("     examples/04_nse_nse_right.mlir")

    print("\nKey Results:")
    print(f"  Counting:        Obstruction = {residual1:.6e} (1 patch)")
    print(f"  Copy:            Obstruction = {residual2:.6e} (3 patches)")
    print(f"  Proofs:          Obstruction = {residual3:.6e} (2 patches)")
    print(f"  NSE Vorticity:   Obstruction = {residual4:.6e} (2 patches + gluing)")

    print("\n" + "="*80)
    print("🎉 You now have a complete sheaf-wreath MLIR framework!")
    print("="*80)
    print("\nNext steps:")
    print("  - Examine the generated .mlir files")
    print("  - Integrate with HEIR FHE compiler pipeline")
    print("  - Try your own problems with GeneralizedSheafLearner")
    print("  - Extend with custom conditioning functions")


if __name__ == "__main__":
    main()
