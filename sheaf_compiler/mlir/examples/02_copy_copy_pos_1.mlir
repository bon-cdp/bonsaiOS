module @copy_task_copy_pos_1 {
  // Forward pass: Character decomposition + Wreath product attention
  func.func @predict(%input: tensor<4xf32>) -> f32 {
    // Step 1: Project onto 4 characters (DFT basis)
    %c0 = sheaf.character_project %input {character_id = 0 : i32, n_positions = 4 : i32}
      : tensor<4xf32> -> tensor<4xcomplex<f32>>
    %c1 = sheaf.character_project %input {character_id = 1 : i32, n_positions = 4 : i32}
      : tensor<4xf32> -> tensor<4xcomplex<f32>>
    %c2 = sheaf.character_project %input {character_id = 2 : i32, n_positions = 4 : i32}
      : tensor<4xf32> -> tensor<4xcomplex<f32>>
    %c3 = sheaf.character_project %input {character_id = 3 : i32, n_positions = 4 : i32}
      : tensor<4xf32> -> tensor<4xcomplex<f32>>

    // Step 2: Position-dependent character weighting (wreath product)
    // Weights shape: [4, 4]

    // Prediction at position 3
    %w0 = arith.constant 0.250000 : f32
    %w1 = arith.constant 0.249999 : f32
    %w2 = arith.constant 0.250001 : f32
    %w3 = arith.constant 0.250001 : f32

    %pos3_0 = sheaf.position_weight %c0, %w0 {position = 3 : i32}
      : tensor<4xcomplex<f32>>, f32 -> complex<f32>
    %pos3_1 = sheaf.position_weight %c1, %w1 {position = 3 : i32}
      : tensor<4xcomplex<f32>>, f32 -> complex<f32>
    %pos3_2 = sheaf.position_weight %c2, %w2 {position = 3 : i32}
      : tensor<4xcomplex<f32>>, f32 -> complex<f32>
    %pos3_3 = sheaf.position_weight %c3, %w3 {position = 3 : i32}
      : tensor<4xcomplex<f32>>, f32 -> complex<f32>

    // Step 3: Sum all weighted characters (depth 0)
    %sum_1 = complex.add %pos3_0, %pos3_1 : complex<f32>
    %sum_2 = complex.add %sum_1, %pos3_2 : complex<f32>
    %prediction_complex = complex.add %sum_2, %pos3_3 : complex<f32>

    // Extract real part (predictions are real-valued)
    %prediction = complex.re %prediction_complex : complex<f32> -> f32

    return %prediction : f32
  }

  // Sheaf Structure Metadata
  sheaf.structure {
    sheaf.patch @copy_pos_1 {
      n_characters = 4 : i32,
      n_positions = 4 : i32
    }

  }
}
