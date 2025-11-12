/**
 * @file unified_sheaf_learner.cpp
 * @brief Implementation of the unified sheaf learner - The Oracle
 */

#include "sheaf_solver/unified_sheaf_learner.hpp"
#include <iostream>
#include <cmath>

namespace sheaf {

UnifiedSheafLearner::UnifiedSheafLearner(bool verbose)
    : verbose_(verbose)
    , fitted_(false)
    , solution_{}
{}

SheafSolution UnifiedSheafLearner::fit(const SheafProblem& problem) {
    if (verbose_) {
        std::cout << "================================================================================\n";
        std::cout << "Fitting Unified Sheaf Learner\n";
        std::cout << "Found " << problem.patches.size() << " patches.\n";
        std::cout << "Found " << problem.gluings.size() << " gluing constraints.\n";
        std::cout << "================================================================================\n";
    }

    // Step 1: Build local systems
    auto local_result = build_local_systems(problem);

    // Step 2: Build gluing constraints
    auto gluing_result = build_gluing_system(problem, local_result);

    // Step 3: Assemble global system
#ifdef USE_EIGEN3
    size_t local_rows = 0;
    for (const auto& mat : local_result.matrices) {
        local_rows += mat.rows();
    }
    size_t total_rows = local_rows + gluing_result.A_gluing.rows();
    size_t total_cols = local_result.matrices.empty() ? 0 : local_result.matrices[0].cols();

    // Stack matrices vertically
    Matrix A_sheaf(total_rows, total_cols);
    Vector b_sheaf(total_rows);

    // Copy local systems
    size_t row_offset = 0;
    for (size_t i = 0; i < local_result.matrices.size(); ++i) {
        const auto& mat = local_result.matrices[i];
        const auto& vec = local_result.targets[i];
        size_t n_rows = mat.rows();

        A_sheaf.block(row_offset, 0, n_rows, mat.cols()) = mat;
        b_sheaf.segment(row_offset, n_rows) = vec;
        row_offset += n_rows;
    }

    // Copy gluing constraints
    if (gluing_result.A_gluing.rows() > 0) {
        A_sheaf.block(row_offset, 0, gluing_result.A_gluing.rows(), gluing_result.A_gluing.cols()) = gluing_result.A_gluing;
        b_sheaf.segment(row_offset, gluing_result.b_gluing.size()) = gluing_result.b_gluing;
    }

    if (verbose_) {
        std::cout << "\nAssembled Global System 'A_sheaf':\n";
        std::cout << "  - Shape: (" << A_sheaf.rows() << ", " << A_sheaf.cols() << ")\n";
        std::cout << "  - Local data rows (accuracy): " << local_rows << "\n";
        std::cout << "  - Gluing rows (consistency): " << gluing_result.A_gluing.rows() << "\n";
    }

    // Step 4: Solve the global least-squares problem
    // w* = (A^H A)^{-1} A^H b
    const real_t lambda_ridge = 1e-8;
    Matrix A_H_A = A_sheaf.adjoint() * A_sheaf;
    A_H_A.diagonal().array() += lambda_ridge;
    Vector A_H_b = A_sheaf.adjoint() * b_sheaf;

    Vector w_solution = A_H_A.llt().solve(A_H_b);

    // Compute residual
    Vector residuals = A_sheaf * w_solution - b_sheaf;
    real_t residual_error = residuals.squaredNorm();

    if (residual_error < EPSILON) {
        residual_error = 0.0;
    }

    if (verbose_) {
        std::cout << "\nGlobal System Solved:\n";
        std::cout << "  - Total weights learned: " << w_solution.size() << "\n";
        std::cout << "  - Final Residual (Obstruction): " << residual_error << "\n";
    }

    solution_ = unpack_solution(w_solution, local_result, residual_error);
    fitted_ = true;

    return solution_;
#else
    // Simplified non-Eigen version - placeholder
    SheafSolution sol;
    sol.residual_error = 1.0;
    sol.converged = false;
    fitted_ = false;
    return sol;
#endif
}

UnifiedSheafLearner::LocalSystemsResult
UnifiedSheafLearner::build_local_systems(const SheafProblem& problem) {
    LocalSystemsResult result;
    size_t current_col_offset = 0;

    if (verbose_) {
        std::cout << "\nBuilding Local Systems (Patches):\n";
    }

    for (const auto& patch : problem.patches) {
        const size_t n_samples = patch.V_samples.size();
        const size_t n_weights = patch.config.n_positions * patch.config.n_characters;

        patch_configs_[patch.name] = patch.config;

        CyclicGroupCharacters group(patch.config.n_positions);

#ifdef USE_EIGEN3
        Matrix A_patch(n_samples, n_weights);
        Vector b_patch(n_samples);

        for (size_t i = 0; i < n_samples; ++i) {
            Vector feature_row = get_feature_row(patch.V_samples[i], patch.config, group);
            A_patch.row(i) = feature_row.transpose();
            b_patch(i) = patch.targets[i](0, 0);  // Assume d_model = 1 for now
        }

        result.matrices.push_back(A_patch);
        result.targets.push_back(b_patch);
#endif

        result.patch_offsets[patch.name] = current_col_offset;
        result.patch_n_weights[patch.name] = n_weights;
        current_col_offset += n_weights;

        if (verbose_) {
            std::cout << "  - Patch '" << patch.name << "': " << n_samples << " samples, "
                      << n_weights << " weights\n";
        }
    }

    return result;
}

UnifiedSheafLearner::GluingSystemResult
UnifiedSheafLearner::build_gluing_system(
    const SheafProblem& problem,
    const LocalSystemsResult& local_info
) {
    GluingSystemResult result;

    if (problem.gluings.empty()) {
#ifdef USE_EIGEN3
        result.A_gluing = Matrix(0, 0);
        result.b_gluing = Vector(0);
#endif
        return result;
    }

    if (verbose_) {
        std::cout << "\nBuilding Gluing Systems (Constraints):\n";
    }

#ifdef USE_EIGEN3
    size_t total_weights = 0;
    for (const auto& [name, n_weights] : local_info.patch_n_weights) {
        total_weights += n_weights;
    }

    result.A_gluing = Matrix(problem.gluings.size(), total_weights);
    result.b_gluing = Vector::Zero(problem.gluings.size());

    for (size_t i = 0; i < problem.gluings.size(); ++i) {
        const auto& gluing = problem.gluings[i];

        const auto& config1 = patch_configs_[gluing.patch_1];
        const auto& config2 = patch_configs_[gluing.patch_2];

        CyclicGroupCharacters group1(config1.n_positions);
        CyclicGroupCharacters group2(config2.n_positions);

        Vector feature1 = get_feature_row(gluing.constraint_data_1, config1, group1);
        Vector feature2 = get_feature_row(gluing.constraint_data_2, config2, group2);

        // Constraint: prediction_1 - prediction_2 = 0
        size_t offset1 = local_info.patch_offsets.at(gluing.patch_1);
        size_t offset2 = local_info.patch_offsets.at(gluing.patch_2);

        result.A_gluing.row(i).segment(offset1, feature1.size()) = feature1.transpose();
        result.A_gluing.row(i).segment(offset2, feature2.size()) -= feature2.transpose();
        result.b_gluing(i) = 0.0;

        if (verbose_) {
            std::cout << "  - Gluing " << (i+1) << " ('" << gluing.patch_1
                      << "' <-> '" << gluing.patch_2 << "')\n";
        }
    }
#endif

    return result;
}

Vector UnifiedSheafLearner::get_feature_row(
    const Matrix& V,
    const PatchConfig& config,
    const CyclicGroupCharacters& group
) const {
#ifdef USE_EIGEN3
    auto projs = group.decompose_into_characters(V);

    Vector feature_row(config.n_positions * config.n_characters);

    for (size_t p = 0; p < config.n_positions; ++p) {
        for (size_t j = 0; j < config.n_characters; ++j) {
            if (j < projs.size()) {
                size_t col_idx = p * config.n_characters + j;
                feature_row(col_idx) = projs[j](p, 0);
            }
        }
    }

    return feature_row;
#else
    return Vector(1);  // Placeholder
#endif
}

SheafSolution UnifiedSheafLearner::unpack_solution(
    const Vector& w_solution,
    const LocalSystemsResult& local_info,
    real_t residual_error
) {
    SheafSolution sol;
    sol.residual_error = residual_error;
    sol.converged = (residual_error < EPSILON);

#ifdef USE_EIGEN3
    for (const auto& [name, offset] : local_info.patch_offsets) {
        size_t n_weights = local_info.patch_n_weights.at(name);
        const auto& config = patch_configs_[name];

        Vector weights_flat = w_solution.segment(offset, n_weights);

        // Reshape to [n_positions, n_characters]
        Matrix weights(config.n_positions, config.n_characters);
        for (size_t p = 0; p < config.n_positions; ++p) {
            for (size_t j = 0; j < config.n_characters; ++j) {
                weights(p, j) = weights_flat(p * config.n_characters + j);
            }
        }

        sol.weights[name] = weights;
    }
#endif

    return sol;
}

Matrix UnifiedSheafLearner::predict(const std::string& patch_name, const Matrix& V) const {
    if (!fitted_) {
        throw std::runtime_error("Model not fitted");
    }

#ifdef USE_EIGEN3
    const auto& config = patch_configs_.at(patch_name);
    const auto& weights = solution_.weights.at(patch_name);

    CyclicGroupCharacters group(config.n_positions);
    Vector feature_row = get_feature_row(V, config, group);

    // Prediction = dot(feature_row, weights_flat)
    Vector weights_flat(config.n_positions * config.n_characters);
    for (size_t p = 0; p < config.n_positions; ++p) {
        for (size_t j = 0; j < config.n_characters; ++j) {
            weights_flat(p * config.n_characters + j) = weights(p, j);
        }
    }

    complex_t prediction = feature_row.dot(weights_flat);

    Matrix result(1, 1);
    result(0, 0) = prediction;
    return result;
#else
    return Matrix(1, 1);
#endif
}

} // namespace sheaf
