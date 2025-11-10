module @nse_nse_left {
  // Forward pass: Character decomposition + Wreath product attention
  func.func @evolve(%input: tensor<20xf32>) -> f32 {
    // Step 1: Project onto 8 characters (DFT basis)
    %c0 = sheaf.character_project %input {character_id = 0 : i32, n_positions = 20 : i32}
      : tensor<20xf32> -> tensor<20xcomplex<f32>>
    %c1 = sheaf.character_project %input {character_id = 1 : i32, n_positions = 20 : i32}
      : tensor<20xf32> -> tensor<20xcomplex<f32>>
    %c2 = sheaf.character_project %input {character_id = 2 : i32, n_positions = 20 : i32}
      : tensor<20xf32> -> tensor<20xcomplex<f32>>
    %c3 = sheaf.character_project %input {character_id = 3 : i32, n_positions = 20 : i32}
      : tensor<20xf32> -> tensor<20xcomplex<f32>>
    %c4 = sheaf.character_project %input {character_id = 4 : i32, n_positions = 20 : i32}
      : tensor<20xf32> -> tensor<20xcomplex<f32>>
    %c5 = sheaf.character_project %input {character_id = 5 : i32, n_positions = 20 : i32}
      : tensor<20xf32> -> tensor<20xcomplex<f32>>
    %c6 = sheaf.character_project %input {character_id = 6 : i32, n_positions = 20 : i32}
      : tensor<20xf32> -> tensor<20xcomplex<f32>>
    %c7 = sheaf.character_project %input {character_id = 7 : i32, n_positions = 20 : i32}
      : tensor<20xf32> -> tensor<20xcomplex<f32>>

    // Step 2: Position-dependent character weighting (wreath product)
    // Weights shape: [20, 8]

    // Prediction at position 19
    %w0 = arith.constant 0.045346 : f32
    %w1 = arith.constant 0.011043 : f32
    %w2 = arith.constant 0.014935 : f32
    %w3 = arith.constant 0.007303 : f32
    %w4 = arith.constant 0.005052 : f32
    %w5 = arith.constant 0.003991 : f32
    %w6 = arith.constant 0.003395 : f32
    %w7 = arith.constant 0.003035 : f32

    %pos19_0 = sheaf.position_weight %c0, %w0 {position = 19 : i32}
      : tensor<20xcomplex<f32>>, f32 -> complex<f32>
    %pos19_1 = sheaf.position_weight %c1, %w1 {position = 19 : i32}
      : tensor<20xcomplex<f32>>, f32 -> complex<f32>
    %pos19_2 = sheaf.position_weight %c2, %w2 {position = 19 : i32}
      : tensor<20xcomplex<f32>>, f32 -> complex<f32>
    %pos19_3 = sheaf.position_weight %c3, %w3 {position = 19 : i32}
      : tensor<20xcomplex<f32>>, f32 -> complex<f32>
    %pos19_4 = sheaf.position_weight %c4, %w4 {position = 19 : i32}
      : tensor<20xcomplex<f32>>, f32 -> complex<f32>
    %pos19_5 = sheaf.position_weight %c5, %w5 {position = 19 : i32}
      : tensor<20xcomplex<f32>>, f32 -> complex<f32>
    %pos19_6 = sheaf.position_weight %c6, %w6 {position = 19 : i32}
      : tensor<20xcomplex<f32>>, f32 -> complex<f32>
    %pos19_7 = sheaf.position_weight %c7, %w7 {position = 19 : i32}
      : tensor<20xcomplex<f32>>, f32 -> complex<f32>

    // Step 3: Sum all weighted characters (depth 0)
    %sum_1 = complex.add %pos19_0, %pos19_1 : complex<f32>
    %sum_2 = complex.add %sum_1, %pos19_2 : complex<f32>
    %sum_3 = complex.add %sum_2, %pos19_3 : complex<f32>
    %sum_4 = complex.add %sum_3, %pos19_4 : complex<f32>
    %sum_5 = complex.add %sum_4, %pos19_5 : complex<f32>
    %sum_6 = complex.add %sum_5, %pos19_6 : complex<f32>
    %prediction_complex = complex.add %sum_6, %pos19_7 : complex<f32>

    // Extract real part (predictions are real-valued)
    %prediction = complex.re %prediction_complex : complex<f32> -> f32

    return %prediction : f32
  }

  // Sheaf Structure Metadata
  sheaf.structure {
    sheaf.patch @nse_left {
      n_characters = 8 : i32,
      n_positions = 20 : i32
    }

  }
}
