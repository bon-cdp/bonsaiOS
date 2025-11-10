# Sheaf-Wreath MLIR: Quick Start

**Get started with algebraic learning and MLIR generation in 5 minutes**

---

## Installation

```bash
# Already done if you're reading this!
# Dependencies: numpy, scipy
```

---

## 1-Minute Example: Counting Task

```python
import numpy as np
from generalized_sheaf_learner import GeneralizedSheafLearner
from sheaf_emitter import SheafMLIREmitter, SheafMLIRConfig

# Generate data: [a, a+s, a+2s, a+3s] → a+4s
data = []
targets = []
for _ in range(100):
    a, s = np.random.randint(-10, 11), np.random.choice([1,2,3])
    seq = np.array([[a+i*s] for i in range(4)], dtype=float)
    target = np.array([[a+4*s]], dtype=float)
    data.append(seq)
    targets.append(target)

# Train (closed-form, instant)
learner = GeneralizedSheafLearner()
solution, residual = learner.fit(
    data, targets,
    problem_config={'n_characters': 4, 'd_model': 1},
    conditioning_function=lambda v, t: "counting"
)

print(f"Cohomological obstruction: {residual:.6e}")  # Should be ~0

# Generate MLIR
emitter = SheafMLIREmitter(solution)
print(emitter.emit())
```

**Output**: Working MLIR code with FHE depth 0!

---

## Run All Examples

```bash
cd bonsaiOS/sheaf_compiler/mlir
python3 generate_all_examples.py
```

Generates 8 `.mlir` files from 4 tasks:
- ✓ Counting (1 file)
- ✓ Copy (3 files, 3 patches)
- ✓ Proofs (2 files, 2 theorems)
- ✓ NSE (2 files, 2 patches + gluing)

---

## Your Own Problem

```python
# Step 1: Create your data
your_V, your_T = your_data_generator()

# Step 2: Define conditioning (how to partition into patches)
def my_conditioning(sample, target):
    # Return a patch identifier
    return f"patch_{int(sample[0, 0]) % 3}"  # Example: 3 patches

# Step 3: Train
learner = GeneralizedSheafLearner()
solution, residual = learner.fit(
    your_V, your_T,
    problem_config={'n_characters': 8, 'd_model': 1},
    conditioning_function=my_conditioning
)

print(f"Patches discovered: {list(solution.keys())}")
print(f"Obstruction: {residual:.6e}")

# Step 4: Generate MLIR
emitter = SheafMLIREmitter(solution)
with open("my_model.mlir", "w") as f:
    f.write(emitter.emit())
```

---

## Key Concepts

### Cohomological Obstruction
The residual error from the single least-squares solve.
- **0**: Perfect learning (algebraically exact)
- **>0**: Problem not perfectly algebraic (but still close)

### Conditioning Function
Maps `(sample, target) → patch_id`

Examples:
```python
# Single patch (no conditioning)
lambda v, t: "main"

# Conditional on first element
lambda v, t: f"patch_{int(v[0,0])}"

# Spatial partitioning
lambda v, t: "left" if some_logic(v) else "right"
```

### Character Count
Number of DFT basis functions (typically 4-8).
More characters = more expressiveness but larger models.

---

## Understanding the MLIR

Generated MLIR has 3 parts:

### 1. Character Projections (DFT)
```mlir
%c0 = sheaf.character_project %input {
  character_id = 0 : i32,
  n_positions = 4 : i32
}
```
**What it does**: Projects onto DFT basis
**FHE depth**: 0 (rotations only)

### 2. Position-Dependent Weighting
```mlir
%pos3_0 = sheaf.position_weight %c0, %w0 {
  position = 3 : i32
}
```
**What it does**: Applies learned weight
**FHE depth**: 0 (plaintext multiplication)

### 3. Aggregation
```mlir
%sum = complex.add %pos3_0, %pos3_1
%prediction = complex.re %sum
```
**What it does**: Combines all characters
**FHE depth**: 0 (addition)

**Total FHE depth: 0** ✓

---

## Troubleshooting

### High Obstruction (residual > 0.1)
- Problem may not be algebraic
- Try more characters
- Check conditioning function
- Inspect learned weights

### Import Errors
```bash
cd bonsaiOS/sheaf_compiler
# Make sure you're in the right directory
python3 -c "import numpy, scipy; print('OK')"
```

### MLIR Doesn't Parse
- Our dialect is conceptual (not yet implemented in MLIR)
- Share with HEIR team for integration
- See `INTEGRATION_GUIDE.md` for lowering strategy

---

## Next Steps

1. **Read the papers** (`/bon-notes/*.pdf`) for theory
2. **Run examples** (`mlir/generate_all_examples.py`)
3. **Try your problem** (use template above)
4. **Examine MLIR** (`mlir/examples/*.mlir`)
5. **Share with HEIR** (see `INTEGRATION_GUIDE.md`)

---

## Files Reference

```
sheaf_compiler/
├── character_theory_attention.py  # DFT projections
├── unified_sheaf_learner.py       # Sheaf solver
├── generalized_sheaf_learner.py   # Auto-patch discovery
├── mlir/
│   ├── sheaf_emitter.py           # MLIR generator
│   ├── generate_all_examples.py   # Run this!
│   ├── DESIGN.md                  # Dialect spec
│   └── examples/                  # Generated .mlir files
├── INTEGRATION_GUIDE.md           # For HEIR team
├── QUICKSTART.md                  # This file
└── README.md                      # Overview
```

---

**Questions?** See `INTEGRATION_GUIDE.md` or email shakilflynn@gmail.com

**Theory?** Read papers in `/bon-notes/`

**Ready to integrate?** Share with HEIR team!

---

*Last updated: November 10, 2025*
