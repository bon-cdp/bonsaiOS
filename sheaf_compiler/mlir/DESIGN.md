# Sheaf Dialect Design

## Overview

This dialect represents sheaf-wreath attention operations for FHE-compatible algebraic transformers.

## Core Operations

### 1. `sheaf.character_project`

Projects a tensor onto the j-th irreducible character of the cyclic group C_n.

**Syntax:**
```
%result = sheaf.character_project %input {
  character_id = <j> : i32,
  n_positions = <n> : i32
} : tensor<NxT> -> tensor<NxT>
```

**Semantics:**
```
Proj_χj(V) = (1/n) Σ_{k=0}^{n-1} χ_j(g^k) · rotate(V, k)
```

Where `χ_j(g^k) = e^(2πijk/n)` (DFT basis).

**FHE Properties:**
- Depth 0 (rotations only, Galois automorphisms)
- No ciphertext-ciphertext multiplication

---

### 2. `sheaf.position_weight`

Applies position-dependent character weighting (wreath product structure).

**Syntax:**
```
%result = sheaf.position_weight %char_proj, %weight {
  position = <p> : i32
} : tensor<NxT>, tensor<T> -> T
```

**Semantics:**
Extracts element at position `p` from `%char_proj` and multiplies by `%weight`.

**FHE Properties:**
- Depth 0 (plaintext-ciphertext multiplication)

---

### 3. `sheaf.patch` (attribute)

Marks regions of computation as belonging to a specific patch in the sheaf.

**Syntax:**
```
%result = some.operation %input {
  sheaf.patch = @patch_name
} : ...
```

**Semantics:**
Metadata indicating this operation is part of patch `patch_name`.

---

### 4. `sheaf.gluing_constraint`

Enforces consistency between overlapping patches.

**Syntax:**
```
sheaf.gluing_constraint {
  patch_1 = @patch_left,
  patch_2 = @patch_right,
  constraint_type = "periodic" | "dirichlet" | "equality"
}
```

**Semantics:**
Specifies how predictions from different patches must agree.

---

## Dialect Structure

```
sheaf.structure {
  sheaf.patch @patch_0 {
    patch_id = 0 : i32,
    n_characters = 8 : i32,
    n_positions = 4 : i32,
    conditioning_value = "label"
  }

  sheaf.patch @patch_1 {
    ...
  }

  sheaf.gluing_constraint {
    patch_1 = @patch_0,
    patch_2 = @patch_1,
    ...
  }
}
```

---

## Type System

### Complex Numbers
Since character projections involve DFT (complex exponentials), we use:
- `complex<f32>` for single-precision
- `complex<f64>` for double-precision

### Tensors
- `tensor<NxT>` where N = sequence length, T = data type

---

## Lowering Strategy

```
Sheaf Dialect
     ↓
Linalg Dialect (matrix operations)
     ↓
Tensor/Arith Dialect (elementwise ops)
     ↓
HEIR FHE Dialects
     ↓
Concrete (FHE library)
```

---

## Design Principles

1. **FHE Depth 0**: All operations must be rotations or plaintext multiplications
2. **Algebraic**: No approximations, exact decomposition
3. **Composable**: Works with existing MLIR dialects
4. **Metadata-rich**: Preserves sheaf structure for optimization

---

## Comparison to Standard Attention

| Property | Standard Attention | Sheaf-Wreath Attention |
|----------|-------------------|------------------------|
| Parameters | O(n²) | O(n·k) |
| Learning | Gradient descent | Closed-form |
| FHE Depth | ≥5 (softmax) | 0 (rotations) |
| Interpretability | Opaque weights | Character frequencies |
| Compositionality | Monolithic | Sheaf patches |

---

## Future Extensions

- Multi-head sheaf attention
- Sheaf cohomology optimization passes
- Automatic patch discovery (from conditioning function)
- Integration with HEIR's existing FHE passes
