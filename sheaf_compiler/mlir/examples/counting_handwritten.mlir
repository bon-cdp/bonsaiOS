// Hand-written MLIR example: Counting Task
// Problem: Given sequence [a, a+s, a+2s, a+3s], predict a+4s
// This demonstrates the simplest sheaf structure (single patch)

// Using builtin tensor dialect + custom sheaf ops (conceptual)
module @counting_task {

  // Input: 4-element sequence
  func.func @count_predict(%input: tensor<4xf32>) -> f32 {

    // Step 1: Character decomposition via DFT
    // Project input onto each of 4 characters (χ_0, χ_1, χ_2, χ_3)

    %c0 = sheaf.character_project %input {character_id = 0 : i32, n_positions = 4 : i32}
      : tensor<4xf32> -> tensor<4xcomplex<f32>>

    %c1 = sheaf.character_project %input {character_id = 1 : i32, n_positions = 4 : i32}
      : tensor<4xf32> -> tensor<4xcomplex<f32>>

    %c2 = sheaf.character_project %input {character_id = 2 : i32, n_positions = 4 : i32}
      : tensor<4xf32> -> tensor<4xcomplex<f32>>

    %c3 = sheaf.character_project %input {character_id = 3 : i32, n_positions = 4 : i32}
      : tensor<4xf32> -> tensor<4xcomplex<f32>>

    // Step 2: Position-dependent character weighting
    // At position 3 (last), combine characters with learned weights

    // Learned weights (from closed-form solution)
    %w0 = arith.constant dense<1.0> : tensor<f32>
    %w1 = arith.constant dense<0.0> : tensor<f32>
    %w2 = arith.constant dense<0.0> : tensor<f32>
    %w3 = arith.constant dense<0.0> : tensor<f32>

    // Position 3 output (wreath product attention)
    %pos3_0 = sheaf.position_weight %c0, %w0 {position = 3 : i32}
      : tensor<4xcomplex<f32>>, tensor<f32> -> complex<f32>

    %pos3_1 = sheaf.position_weight %c1, %w1 {position = 3 : i32}
      : tensor<4xcomplex<f32>>, tensor<f32> -> complex<f32>

    %pos3_2 = sheaf.position_weight %c2, %w2 {position = 3 : i32}
      : tensor<4xcomplex<f32>>, tensor<f32> -> complex<f32>

    %pos3_3 = sheaf.position_weight %c3, %w3 {position = 3 : i32}
      : tensor<4xcomplex<f32>>, tensor<f32> -> complex<f32>

    // Step 3: Sum (FHE depth 0)
    %sum_01 = complex.add %pos3_0, %pos3_1 : complex<f32>
    %sum_012 = complex.add %sum_01, %pos3_2 : complex<f32>
    %prediction_complex = complex.add %sum_012, %pos3_3 : complex<f32>

    // Extract real part (predictions are real-valued)
    %prediction = complex.re %prediction_complex : complex<f32> -> f32

    return %prediction : f32
  }

  // Metadata: Sheaf structure
  // This is a single-patch model with patch_id=0, name="counting_patch"
  sheaf.structure {
    sheaf.patch @counting_patch {
      patch_id = 0 : i32,
      n_characters = 4 : i32,
      n_positions = 4 : i32,
      conditioning_value = "counting_patch"
    }

    // No gluing constraints (single patch)
  }
}
