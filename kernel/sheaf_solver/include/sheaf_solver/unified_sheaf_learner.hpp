/**
 * @file unified_sheaf_learner.hpp
 * @brief Unified Sheaf Learner - The Core of BonsaiOS
 *
 * This is "Turtle 2" in the hierarchy: the Global Solver.
 *
 * It takes a collection of local problems (patches) and gluing constraints
 * and solves them ALL in a single, closed-form linear algebra step.
 *
 * The magic: instead of iterative optimization, we construct ONE large
 * linear system that simultaneously enforces:
 * 1. Local accuracy (each patch fits its data)
 * 2. Global consistency (patches agree on overlaps)
 *
 * The residual error IS the "cohomological obstruction" - it directly
 * quantifies whether the problem is fundamentally solvable.
 *
 * This will replace traditional OS schedulers, resource managers, and
 * eventually compiler optimizers. The same mathematical principle
 * solves all these problems.
 */

#pragma once

#include "types.hpp"
#include "cyclic_group.hpp"
#include <memory>

namespace sheaf {

/**
 * @brief Problem definition for sheaf learning
 */
struct SheafProblem {
    std::vector<Patch> patches;
    std::vector<GluingConstraint> gluings;
};

/**
 * @brief Unified Sheaf Learner
 *
 * Solves arbitrary problems with local-to-global structure in one step.
 */
class UnifiedSheafLearner {
public:
    /**
     * @brief Construct learner with optional verbosity
     */
    explicit UnifiedSheafLearner(bool verbose = false);

    /**
     * @brief Fit the model to a sheaf problem
     *
     * This is THE ONE-STEP SOLVE that replaces gradient descent:
     *
     * 1. Build block-diagonal matrix A_local for local data fitting
     * 2. Build constraint matrix A_gluing for global consistency
     * 3. Stack them: A_sheaf = [A_local; A_gluing]
     * 4. Solve: w* = (A_sheaf^H A_sheaf)^{-1} A_sheaf^H b_sheaf
     * 5. Compute residual: ||A_sheaf w* - b_sheaf||^2
     *
     * The residual IS the cohomological obstruction.
     * Zero residual = perfect learnability.
     *
     * @param problem Sheaf problem definition
     * @return Solution with learned weights and residual error
     */
    SheafSolution fit(const SheafProblem& problem);

    /**
     * @brief Predict using learned solution
     *
     * @param patch_name Name of patch to use
     * @param V Input sample
     * @return Predicted output
     */
    Matrix predict(const std::string& patch_name, const Matrix& V) const;

    /**
     * @brief Get the last solution
     */
    const SheafSolution& get_solution() const { return solution_; }

    /**
     * @brief Check if model has been fitted
     */
    bool is_fitted() const { return fitted_; }

private:
    bool verbose_;
    bool fitted_;
    SheafSolution solution_;
    std::unordered_map<std::string, PatchConfig> patch_configs_;

    /**
     * @brief Build local accuracy systems for each patch
     */
    struct LocalSystemsResult {
        std::vector<Matrix> matrices;
        std::vector<Vector> targets;
        std::unordered_map<std::string, size_t> patch_offsets;
        std::unordered_map<std::string, size_t> patch_n_weights;
    };
    LocalSystemsResult build_local_systems(const SheafProblem& problem);

    /**
     * @brief Build global consistency constraints
     */
    struct GluingSystemResult {
        Matrix A_gluing;
        Vector b_gluing;
    };
    GluingSystemResult build_gluing_system(
        const SheafProblem& problem,
        const LocalSystemsResult& local_info
    );

    /**
     * @brief Get feature row for a sample (character projections at all positions)
     */
    Vector get_feature_row(
        const Matrix& V,
        const PatchConfig& config,
        const CyclicGroupCharacters& group
    ) const;

    /**
     * @brief Unpack flat solution vector into structured form
     */
    SheafSolution unpack_solution(
        const Vector& w_solution,
        const LocalSystemsResult& local_info,
        real_t residual_error
    );
};

} // namespace sheaf
