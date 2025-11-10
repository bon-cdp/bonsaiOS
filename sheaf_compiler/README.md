# Sheaf-Wreath MLIR Compiler

**An MLIR representation of algebraic sheaf-wreath attention for FHE-friendly transformers.**

## Overview

This project provides an MLIR lowering for the **GeneralizedSheafLearner** framework, enabling the HEIR team to integrate our algebraic attention mechanism into their FHE compiler toolchain.

### Key Properties
- **FHE Depth 0**: All operations are rotations (Galois automorphisms) or plaintext multiplications
- **No Gradient Descent**: Learning via closed-form least squares
- **Automatic Patch Discovery**: Conditioning functions partition problems into sheaves
- **Proven Results**: Zero cohomological obstruction on diverse tasks

## Theoretical Foundation

See the three foundational papers in `/bon-notes/`:
- **a.pdf**: Wreath product attention via character theory
- **b.pdf**: Applications to Navier-Stokes and theorem proving
- **c.pdf**: Generalized sheaf learner with auto-patch discovery

## Project Structure

```
sheaf_compiler/
├── character_theory_attention.py  # Character projections (DFT basis)
├── unified_sheaf_learner.py       # Sheaf solver with gluing constraints
├── generalized_sheaf_learner.py   # Auto-patch discovery
├── mlir/
│   ├── sheaf_ops.py              # Python MLIR emitter
│   ├── examples/
│   │   ├── counting.mlir         # Single-patch example
│   │   ├── copy.mlir             # Multi-patch conditional routing
│   │   └── nse_vorticity.mlir    # Gluing constraints
│   └── dialect/
│       └── SheafOps.td           # MLIR dialect definition
└── README.md                      # This file
```

## Usage (Planned)

```python
from generalized_sheaf_learner import GeneralizedSheafLearner
from mlir.sheaf_ops import SheafMLIREmitter

# 1. Train model (closed-form)
learner = GeneralizedSheafLearner()
solution, residual = learner.fit(data, targets, config, conditioning_fn)

# 2. Export to MLIR
emitter = SheafMLIREmitter(learner.sheaf_structure, solution)
mlir_code = emitter.emit()

# 3. Integrate into HEIR FHE pipeline
# (HEIR team uses the .mlir file in their compiler)
```

## Status

🚧 **Work in Progress** 🚧

Currently implementing:
- [x] Python sheaf-wreath learner (complete)
- [ ] MLIR dialect definition
- [ ] Python → MLIR emitter
- [ ] Example .mlir files
- [ ] HEIR integration guide

## Contact

For questions about the mathematical framework, see the papers in `/bon-notes/`.
