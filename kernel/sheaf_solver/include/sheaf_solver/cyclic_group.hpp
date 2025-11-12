/**
 * @file cyclic_group.hpp
 * @brief Cyclic Group Character Theory
 *
 * Implements the mathematical foundation: characters of cyclic groups C_n
 * These form the DFT basis and are the core of the wreath product attention.
 *
 * Mathematical Background:
 * - C_n = cyclic group of order n
 * - Has exactly n irreducible 1-dimensional characters
 * - χ_j(g^k) = ω^(jk) where ω = e^(2πi/n)
 * - Character table IS the DFT matrix
 * - Maschke's theorem: every representation decomposes into characters
 */

#pragma once

#include "types.hpp"

namespace sheaf {

class CyclicGroupCharacters {
public:
    /**
     * @brief Construct character table for C_n
     * @param n Group order (should be power of 2 for FHE compatibility)
     */
    explicit CyclicGroupCharacters(size_t n);

    /**
     * @brief Get group order
     */
    size_t order() const { return n_; }

    /**
     * @brief Evaluate character χ_j on group element g^k
     * @param j Character index (0 to n-1)
     * @param k Group element power (0 to n-1)
     * @return χ_j(g^k) = ω^(jk)
     */
    complex_t character(size_t j, size_t k) const;

    /**
     * @brief Project representation V onto character χ_j subspace
     *
     * This is the KEY operation of wreath product attention:
     * Proj_{χ_j}(V) = (1/n) Σ_{k=0}^{n-1} χ̄_j(g^k) · g^k(V)
     *
     * where g^k(V) means "rotate V by k positions"
     *
     * @param V Value tensor [seq_len, d_model]
     * @param j Character index
     * @return Projected tensor [seq_len, d_model]
     */
    Matrix project_onto_character(const Matrix& V, size_t j) const;

    /**
     * @brief Decompose V into all character subspaces
     *
     * By Maschke's theorem: V = Σ_{j=0}^{n-1} Proj_{χ_j}(V)
     *
     * @param V Value tensor [seq_len, d_model]
     * @return Vector of n projected tensors (one per character)
     */
    std::vector<Matrix> decompose_into_characters(const Matrix& V) const;

    /**
     * @brief Reconstruct V from character decomposition
     *
     * V_out = Σ_j coefficients[j] · projections[j]
     *
     * @param coefficients Character weights [n]
     * @param projections Character projections from decompose_into_characters
     * @return Reconstructed tensor
     */
    Matrix reconstruct_from_characters(
        const Vector& coefficients,
        const std::vector<Matrix>& projections
    ) const;

    /**
     * @brief Learn character weights via least squares
     *
     * Given samples and targets, find optimal character coefficients:
     * Σ_j c_j · Proj_{χ_j}(V) ≈ target
     *
     * This is a LINEAR problem - no gradient descent needed!
     *
     * @param V_samples Input samples
     * @param targets Target outputs
     * @return Optimal character coefficients
     */
    Vector learn_character_weights(
        const std::vector<Matrix>& V_samples,
        const std::vector<Matrix>& targets
    ) const;

    /**
     * @brief Get the full character table (DFT matrix)
     * @return [n x n] matrix where entry [j,k] = χ_j(g^k)
     */
    const Matrix& get_character_table() const { return characters_; }

private:
    size_t n_;              // Group order
    complex_t omega_;       // Primitive n-th root of unity: e^(2πi/n)
    Matrix characters_;     // Character table (DFT matrix)

    /**
     * @brief Compute the character table
     */
    void compute_character_table();

    /**
     * @brief Rotate matrix V by k positions (cyclic shift along axis 0)
     */
    Matrix rotate(const Matrix& V, size_t k) const;
};

} // namespace sheaf
