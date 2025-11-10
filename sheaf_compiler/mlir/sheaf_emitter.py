"""
Sheaf-Wreath MLIR Emitter

Generates MLIR code from trained GeneralizedSheafLearner models.

This emitter takes the learned weights and sheaf structure and produces
MLIR IR that can be integrated into the HEIR FHE compiler pipeline.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class SheafMLIRConfig:
    """Configuration for MLIR generation."""
    module_name: str = "sheaf_model"
    function_name: str = "forward"
    use_f32: bool = True  # vs f64
    include_metadata: bool = True
    add_comments: bool = True


class SheafMLIREmitter:
    """
    Emits MLIR code from a trained sheaf-wreath model.

    Takes the solution from GeneralizedSheafLearner or UnifiedSheafLearner
    and generates MLIR IR representing the learned model.
    """

    def __init__(self, solution: Dict[str, Any], config: Optional[SheafMLIRConfig] = None):
        """
        Initialize the emitter.

        Args:
            solution: Dictionary from learner.fit() containing:
                - Patch names → {weights: ndarray, config: dict}
            config: Optional configuration for MLIR generation
        """
        self.solution = solution
        self.config = config or SheafMLIRConfig()
        self.indent_level = 0

    def _indent(self) -> str:
        """Get current indentation string."""
        return "  " * self.indent_level

    def _comment(self, text: str) -> str:
        """Add comment if enabled."""
        if self.config.add_comments:
            return f"{self._indent()}// {text}\n"
        return ""

    def _type_str(self) -> str:
        """Get float type string."""
        return "f32" if self.config.use_f32 else "f64"

    def emit(self) -> str:
        """
        Generate complete MLIR module.

        Returns:
            MLIR IR as a string
        """
        mlir_code = []

        # Module header
        mlir_code.append(f"module @{self.config.module_name} {{\n")
        self.indent_level += 1

        # Main forward function
        mlir_code.append(self._emit_forward_function())

        # Sheaf structure metadata
        if self.config.include_metadata:
            mlir_code.append(self._emit_sheaf_metadata())

        self.indent_level -= 1
        mlir_code.append("}\n")

        return "".join(mlir_code)

    def _emit_forward_function(self) -> str:
        """
        Emit the main forward pass function.

        This is where the actual computation happens:
          1. Character projections
          2. Position-dependent weighting
          3. Summation
        """
        code = []

        # Get info from first patch (assumes all patches have same n_positions for now)
        first_patch = next(iter(self.solution.values()))
        n_positions = first_patch['config'].get('n_positions', 4)
        n_characters = first_patch['config']['n_characters']

        code.append(self._comment("Forward pass: Character decomposition + Wreath product attention"))
        code.append(f"{self._indent()}func.func @{self.config.function_name}(")
        code.append(f"%input: tensor<{n_positions}x{self._type_str()}>) -> {self._type_str()} {{\n")

        self.indent_level += 1

        # Emit character projections
        code.append(self._emit_character_projections(n_positions, n_characters))

        # Emit position-dependent weighting (using first patch for now)
        code.append(self._emit_position_weighting(first_patch, n_positions, n_characters))

        # Return statement
        code.append(f"{self._indent()}return %prediction : {self._type_str()}\n")

        self.indent_level -= 1
        code.append(f"{self._indent()}}}\n\n")

        return "".join(code)

    def _emit_character_projections(self, n_positions: int, n_characters: int) -> str:
        """Emit character projection operations."""
        code = []

        code.append(self._comment(f"Step 1: Project onto {n_characters} characters (DFT basis)"))

        for j in range(n_characters):
            code.append(f"{self._indent()}%c{j} = sheaf.character_project %input {{")
            code.append(f"character_id = {j} : i32, n_positions = {n_positions} : i32}}\n")
            code.append(f"{self._indent()}  : tensor<{n_positions}x{self._type_str()}> -> ")
            code.append(f"tensor<{n_positions}xcomplex<{self._type_str()}>>\n")

        code.append("\n")
        return "".join(code)

    def _emit_position_weighting(self, patch: Dict[str, Any], n_positions: int, n_characters: int) -> str:
        """Emit position-dependent weighting (wreath product)."""
        code = []

        weights = patch['weights']  # Shape: [n_positions, n_characters]

        code.append(self._comment(f"Step 2: Position-dependent character weighting (wreath product)"))
        code.append(self._comment(f"Weights shape: [{n_positions}, {n_characters}]"))
        code.append("\n")

        # For simplicity, predict at the last position
        pred_pos = n_positions - 1

        code.append(self._comment(f"Prediction at position {pred_pos}"))

        # Emit weight constants for this position
        for j in range(n_characters):
            weight_val = np.abs(weights[pred_pos, j])  # Take magnitude of complex weight
            code.append(f"{self._indent()}%w{j} = arith.constant ")
            code.append(f"{weight_val:.6f} : {self._type_str()}\n")

        code.append("\n")

        # Emit position weighting ops
        for j in range(n_characters):
            code.append(f"{self._indent()}%pos{pred_pos}_{j} = sheaf.position_weight %c{j}, %w{j} {{")
            code.append(f"position = {pred_pos} : i32}}\n")
            code.append(f"{self._indent()}  : tensor<{n_positions}xcomplex<{self._type_str()}>>, ")
            code.append(f"{self._type_str()} -> complex<{self._type_str()}>\n")

        code.append("\n")

        # Sum all weighted characters
        code.append(self._comment("Step 3: Sum all weighted characters (depth 0)"))

        if n_characters == 1:
            code.append(f"{self._indent()}%prediction_complex = %pos{pred_pos}_0 : complex<{self._type_str()}>\n")
        else:
            # Build a tree of additions
            current_sum = f"%pos{pred_pos}_0"
            for j in range(1, n_characters):
                next_var = f"%sum_{j}" if j < n_characters - 1 else "%prediction_complex"
                code.append(f"{self._indent()}{next_var} = complex.add {current_sum}, %pos{pred_pos}_{j} : ")
                code.append(f"complex<{self._type_str()}>\n")
                current_sum = next_var

        # Extract real part
        code.append("\n")
        code.append(self._comment("Extract real part (predictions are real-valued)"))
        code.append(f"{self._indent()}%prediction = complex.re %prediction_complex : ")
        code.append(f"complex<{self._type_str()}> -> {self._type_str()}\n\n")

        return "".join(code)

    def _emit_sheaf_metadata(self) -> str:
        """Emit sheaf structure metadata."""
        code = []

        code.append(self._comment("Sheaf Structure Metadata"))
        code.append(f"{self._indent()}sheaf.structure {{\n")

        self.indent_level += 1

        # Emit patch info
        for patch_name, patch_data in self.solution.items():
            config = patch_data['config']

            code.append(f"{self._indent()}sheaf.patch @{patch_name} {{\n")
            self.indent_level += 1

            code.append(f"{self._indent()}n_characters = {config['n_characters']} : i32,\n")
            code.append(f"{self._indent()}n_positions = {config.get('n_positions', 'unknown')} : i32\n")

            self.indent_level -= 1
            code.append(f"{self._indent()}}}\n\n")

        # TODO: Emit gluing constraints if they exist

        self.indent_level -= 1
        code.append(f"{self._indent()}}}\n")

        return "".join(code)


def test_emitter():
    """Test the MLIR emitter with a simple example."""
    print("="*70)
    print("Testing Sheaf MLIR Emitter")
    print("="*70)

    # Create a mock solution (as if from GeneralizedSheafLearner)
    mock_solution = {
        'counting_patch': {
            'weights': np.array([
                [1.0, 0.0, 0.0, 0.0],  # Position 0
                [1.0, 0.0, 0.0, 0.0],  # Position 1
                [1.0, 0.0, 0.0, 0.0],  # Position 2
                [1.0, 0.0, 0.0, 0.0],  # Position 3 (used for prediction)
            ]),
            'config': {
                'n_characters': 4,
                'n_positions': 4,
                'd_model': 1
            }
        }
    }

    # Create emitter and generate MLIR
    emitter = SheafMLIREmitter(mock_solution, SheafMLIRConfig(
        module_name="counting_task",
        function_name="predict",
        add_comments=True
    ))

    mlir_code = emitter.emit()

    print("\nGenerated MLIR:")
    print("="*70)
    print(mlir_code)

    # Save to file
    output_path = "examples/counting_generated.mlir"
    with open(output_path, 'w') as f:
        f.write(mlir_code)

    print(f"\n✓ Saved to {output_path}")
    print("="*70)


if __name__ == "__main__":
    test_emitter()
