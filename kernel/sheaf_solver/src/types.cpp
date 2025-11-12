/**
 * @file types.cpp
 * @brief Implementation of basic types (when Eigen3 not available)
 */

#include "sheaf_solver/types.hpp"

#ifndef USE_EIGEN3

namespace sheaf {

// BasicMatrix implementation
template<typename T>
BasicMatrix<T>::BasicMatrix(size_t rows, size_t cols)
    : data_(rows * cols)
    , rows_(rows)
    , cols_(cols)
{}

template<typename T>
T& BasicMatrix<T>::operator()(size_t i, size_t j) {
    return data_[i * cols_ + j];
}

template<typename T>
const T& BasicMatrix<T>::operator()(size_t i, size_t j) const {
    return data_[i * cols_ + j];
}

// BasicVector implementation
template<typename T>
BasicVector<T>::BasicVector(size_t size)
    : data_(size)
{}

template<typename T>
T& BasicVector<T>::operator()(size_t i) {
    return data_[i];
}

template<typename T>
const T& BasicVector<T>::operator()(size_t i) const {
    return data_[i];
}

// Explicit template instantiations
template class BasicMatrix<complex_t>;
template class BasicMatrix<real_t>;
template class BasicVector<complex_t>;
template class BasicVector<real_t>;

} // namespace sheaf

#endif // !USE_EIGEN3
