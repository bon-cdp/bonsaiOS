/**
 * @file cyclic_group.cpp
 * @brief Implementation of cyclic group character theory
 */

#include "sheaf_solver/cyclic_group.hpp"
#include <cmath>
#include <stdexcept>

namespace sheaf {

CyclicGroupCharacters::CyclicGroupCharacters(size_t n)
    : n_(n)
    , omega_(std::polar(1.0, 2.0 * PI / static_cast<double>(n)))
    , characters_(n, n)
{
    if (n == 0) {
        throw std::invalid_argument("Group order must be positive");
    }
    compute_character_table();
}

void CyclicGroupCharacters::compute_character_table() {
#ifdef USE_EIGEN3
    for (size_t j = 0; j < n_; ++j) {
        for (size_t k = 0; k < n_; ++k) {
            characters_(j, k) = std::pow(omega_, static_cast<double>(j * k));
        }
    }
#else
    for (size_t j = 0; j < n_; ++j) {
        for (size_t k = 0; k < n_; ++k) {
            characters_(j, k) = std::pow(omega_, static_cast<double>(j * k));
        }
    }
#endif
}

complex_t CyclicGroupCharacters::character(size_t j, size_t k) const {
    if (j >= n_ || k >= n_) {
        throw std::out_of_range("Character index out of range");
    }
#ifdef USE_EIGEN3
    return characters_(j, k);
#else
    return characters_(j, k);
#endif
}

Matrix CyclicGroupCharacters::rotate(const Matrix& V, size_t k) const {
    if (k == 0) return V;

#ifdef USE_EIGEN3
    const size_t rows = V.rows();
    const size_t cols = V.cols();
    Matrix result(rows, cols);

    k = k % rows;  // Handle k > rows
    for (size_t i = 0; i < rows; ++i) {
        size_t src_row = (i + rows - k) % rows;
        result.row(i) = V.row(src_row);
    }
    return result;
#else
    const size_t rows = V.rows();
    const size_t cols = V.cols();
    Matrix result(rows, cols);

    k = k % rows;
    for (size_t i = 0; i < rows; ++i) {
        size_t src_row = (i + rows - k) % rows;
        for (size_t j = 0; j < cols; ++j) {
            result(i, j) = V(src_row, j);
        }
    }
    return result;
#endif
}

Matrix CyclicGroupCharacters::project_onto_character(const Matrix& V, size_t j) const {
    if (j >= n_) {
        throw std::out_of_range("Character index out of range");
    }

#ifdef USE_EIGEN3
    const size_t seq_len = V.rows();
    const size_t d_model = V.cols();
    const size_t n = std::min(seq_len, n_);

    Matrix proj = Matrix::Zero(seq_len, d_model);

    // Sum over group elements: Proj = (1/n) Σ_k χ̄_j(k) · rotate(V, k)
    for (size_t k = 0; k < n; ++k) {
        complex_t weight = std::conj(character(j, k));
        Matrix V_rotated = rotate(V, k);
        proj += weight * V_rotated;
    }

    proj /= static_cast<double>(n);
    return proj;
#else
    const size_t seq_len = V.rows();
    const size_t d_model = V.cols();
    const size_t n = std::min(seq_len, n_);

    Matrix proj(seq_len, d_model);
    for (size_t i = 0; i < seq_len; ++i) {
        for (size_t c = 0; c < d_model; ++c) {
            proj(i, c) = complex_t(0, 0);
        }
    }

    for (size_t k = 0; k < n; ++k) {
        complex_t weight = std::conj(character(j, k));
        Matrix V_rotated = rotate(V, k);

        for (size_t i = 0; i < seq_len; ++i) {
            for (size_t c = 0; c < d_model; ++c) {
                proj(i, c) += weight * V_rotated(i, c);
            }
        }
    }

    for (size_t i = 0; i < seq_len; ++i) {
        for (size_t c = 0; c < d_model; ++c) {
            proj(i, c) /= static_cast<double>(n);
        }
    }

    return proj;
#endif
}

std::vector<Matrix> CyclicGroupCharacters::decompose_into_characters(const Matrix& V) const {
    std::vector<Matrix> projections;
    projections.reserve(n_);

#ifdef USE_EIGEN3
    const size_t n = std::min(static_cast<size_t>(V.rows()), n_);
#else
    const size_t n = std::min(V.rows(), n_);
#endif

    for (size_t j = 0; j < n; ++j) {
        projections.push_back(project_onto_character(V, j));
    }

    return projections;
}

Matrix CyclicGroupCharacters::reconstruct_from_characters(
    const Vector& coefficients,
    const std::vector<Matrix>& projections
) const {
    if (projections.empty()) {
        throw std::invalid_argument("Empty projections");
    }

#ifdef USE_EIGEN3
    Matrix result = Matrix::Zero(projections[0].rows(), projections[0].cols());

    for (size_t j = 0; j < projections.size() && j < coefficients.size(); ++j) {
        result += coefficients(j) * projections[j];
    }

    return result;
#else
    const size_t rows = projections[0].rows();
    const size_t cols = projections[0].cols();
    Matrix result(rows, cols);

    for (size_t i = 0; i < rows; ++i) {
        for (size_t c = 0; c < cols; ++c) {
            result(i, c) = complex_t(0, 0);
        }
    }

    for (size_t j = 0; j < projections.size() && j < coefficients.size(); ++j) {
        complex_t coef = coefficients(j);
        for (size_t i = 0; i < rows; ++i) {
            for (size_t c = 0; c < cols; ++c) {
                result(i, c) += coef * projections[j](i, c);
            }
        }
    }

    return result;
#endif
}

Vector CyclicGroupCharacters::learn_character_weights(
    const std::vector<Matrix>& V_samples,
    const std::vector<Matrix>& targets
) const {
    if (V_samples.empty() || V_samples.size() != targets.size()) {
        throw std::invalid_argument("Invalid samples or targets");
    }

    const size_t n_samples = V_samples.size();
#ifdef USE_EIGEN3
    const size_t d = V_samples[0].rows() * V_samples[0].cols();
#else
    const size_t d = V_samples[0].rows() * V_samples[0].cols();
#endif

    // Build linear system: A·c = b
#ifdef USE_EIGEN3
    Matrix A(n_samples * d, n_);
    Vector b(n_samples * d);

    for (size_t i = 0; i < n_samples; ++i) {
        auto projs = decompose_into_characters(V_samples[i]);

        for (size_t j = 0; j < n_; ++j) {
            // Flatten projection j and place in column j of A
            for (size_t k = 0; k < d; ++k) {
                size_t row = i * d + k;
                size_t r = k / V_samples[i].cols();
                size_t c = k % V_samples[i].cols();
                A(row, j) = projs[j](r, c);
            }
        }

        // Flatten target
        for (size_t k = 0; k < d; ++k) {
            size_t r = k / targets[i].cols();
            size_t c = k % targets[i].cols();
            b(i * d + k) = targets[i](r, c);
        }
    }

    // Solve least squares: c = (A^H A)^{-1} A^H b
    Vector coeffs = A.bdcSvd(Eigen::ComputeThinU | Eigen::ComputeThinV).solve(b);
    return coeffs;
#else
    Matrix A(n_samples * d, n_);
    Vector b(n_samples * d);

    for (size_t i = 0; i < n_samples; ++i) {
        auto projs = decompose_into_characters(V_samples[i]);

        for (size_t j = 0; j < n_; ++j) {
            for (size_t k = 0; k < d; ++k) {
                size_t row = i * d + k;
                size_t r = k / V_samples[i].cols();
                size_t c = k % V_samples[i].cols();
                A(row, j) = projs[j](r, c);
            }
        }

        for (size_t k = 0; k < d; ++k) {
            size_t r = k / targets[i].cols();
            size_t c = k % targets[i].cols();
            b(i * d + k) = targets[i](r, c);
        }
    }

    // Simplified least squares (would need proper SVD for production)
    // For now, return zeros - will implement proper solver later
    Vector coeffs(n_);
    for (size_t i = 0; i < n_; ++i) {
        coeffs(i) = complex_t(0, 0);
    }
    return coeffs;
#endif
}

} // namespace sheaf
