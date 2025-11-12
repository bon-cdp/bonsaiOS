/**
 * @file types.hpp
 * @brief Core types for the Sheaf Solver
 *
 * Defines basic types used throughout the sheaf-wreath framework.
 * Uses standard C++ containers and types suitable for embedded/kernel use.
 */

#pragma once

// Include C++ standard library headers BEFORE defining namespace
#include <cstdint>
#include <cstddef>
#include <complex>
#include <vector>
#include <string>
#include <unordered_map>

#ifdef USE_EIGEN3
#include <Eigen/Dense>
#endif

namespace sheaf {

// Fundamental types
using real_t = double;
using complex_t = std::complex<double>;
using size_t = std::size_t;

// Matrix and vector types (to be replaced with Eigen if available)
#ifdef USE_EIGEN3
using Matrix = Eigen::MatrixXcd;
using Vector = Eigen::VectorXcd;
using RealMatrix = Eigen::MatrixXd;
using RealVector = Eigen::VectorXd;
#else
// Minimal implementations when Eigen is not available
template<typename T>
class BasicMatrix {
public:
    BasicMatrix(size_t rows, size_t cols);
    T& operator()(size_t i, size_t j);
    const T& operator()(size_t i, size_t j) const;
    size_t rows() const { return rows_; }
    size_t cols() const { return cols_; }
private:
    std::vector<T> data_;
    size_t rows_, cols_;
};

template<typename T>
class BasicVector {
public:
    explicit BasicVector(size_t size);
    T& operator()(size_t i);
    const T& operator()(size_t i) const;
    size_t size() const { return data_.size(); }
private:
    std::vector<T> data_;
};

using Matrix = BasicMatrix<complex_t>;
using Vector = BasicVector<complex_t>;
using RealMatrix = BasicMatrix<real_t>;
using RealVector = BasicVector<real_t>;
#endif

// Problem configuration
struct PatchConfig {
    size_t n_positions;    // Sequence length
    size_t n_characters;   // Number of character projections to use
    size_t d_model;        // Embedding dimension (typically 1 for simple problems)
};

// Patch data for sheaf learning
struct Patch {
    std::string name;
    std::vector<Matrix> V_samples;  // Input samples
    std::vector<Matrix> targets;    // Target outputs
    PatchConfig config;
};

// Gluing constraint between two patches
struct GluingConstraint {
    std::string patch_1;
    std::string patch_2;
    Matrix constraint_data_1;  // Data point from patch 1
    Matrix constraint_data_2;  // Data point from patch 2
};

// Solution structure
struct SheafSolution {
    std::unordered_map<std::string, Matrix> weights;  // Learned weights per patch
    real_t residual_error;                            // Cohomological obstruction
    bool converged;
};

// Constants
constexpr real_t PI = 3.14159265358979323846;
constexpr real_t EPSILON = 1e-12;

} // namespace sheaf
