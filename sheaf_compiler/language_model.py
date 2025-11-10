"""
Sheaf Language Model

A high-level wrapper for applying sheaf-wreath attention to language modeling.

Key features:
- Automatic conversion from corpus to training data
- Support for various conditioning functions
- Integration with GeneralizedSheafLearner
- MLIR generation for trained models
"""

import numpy as np
from typing import List, Callable, Tuple, Dict, Optional
from generalized_sheaf_learner import GeneralizedSheafLearner
from tiny_corpus import TinyCorpusGenerator


class SheafLanguageModel:
    """
    Sheaf-wreath attention language model.

    Usage:
        model = SheafLanguageModel(vocab_size=40, n_characters=8)
        solution, residual = model.fit(corpus, conditioning_fn)
    """

    def __init__(self, vocab_size: int, n_characters: int = 8, context_size: int = 4):
        """
        Initialize the language model.

        Args:
            vocab_size: Size of vocabulary
            n_characters: Number of character projections (DFT basis functions)
            context_size: Number of tokens in context window
        """
        self.vocab_size = vocab_size
        self.n_characters = n_characters
        self.context_size = context_size
        self.learner = GeneralizedSheafLearner(verbose=False)
        self.solution = None
        self.residual = None

    def fit(self,
            contexts: List[np.ndarray],
            targets: List[np.ndarray],
            conditioning_fn: Callable[[np.ndarray, np.ndarray], str]
            ) -> Tuple[Dict, float]:
        """
        Train the language model.

        Args:
            contexts: List of context sequences [context_size x 1]
            targets: List of target tokens [1 x 1]
            conditioning_fn: Function (context, target) -> patch_id

        Returns:
            (solution, residual) tuple
        """
        problem_config = {
            'n_characters': self.n_characters,
            'd_model': 1  # Predicting single token
        }

        self.solution, self.residual = self.learner.fit(
            contexts,
            targets,
            problem_config,
            conditioning_fn
        )

        return self.solution, self.residual

    def predict(self, context: np.ndarray, patch_name: str) -> float:
        """
        Predict next token given context (requires solution).

        Args:
            context: Context sequence [context_size x 1]
            patch_name: Which patch to use for prediction

        Returns:
            Predicted token index (as float)
        """
        if self.solution is None:
            raise ValueError("Model not trained yet. Call fit() first.")

        # TODO: Implement prediction using learned weights
        # This requires implementing the forward pass:
        # 1. Character projections
        # 2. Position-dependent weighting
        # 3. Summation

        raise NotImplementedError("Prediction not yet implemented")


# ============================================================================
# Conditioning Functions
# ============================================================================

class ConditioningFunctions:
    """
    Collection of conditioning functions for language modeling.

    Each function maps (context, target) → patch_id string.
    """

    @staticmethod
    def single_patch(context: np.ndarray, target: np.ndarray) -> str:
        """Single patch (baseline) - no conditioning."""
        return "main"

    @staticmethod
    def frequency_based(corpus_gen: TinyCorpusGenerator,
                       corpus: List[List[str]]):
        """
        Frequency-based conditioning: high/mid/low frequency words.

        Returns a conditioning function closure.
        """
        def condition(context: np.ndarray, target: np.ndarray) -> str:
            target_idx = int(target[0, 0])
            target_word = corpus_gen.idx_to_word[target_idx]
            freq_band = corpus_gen.get_frequency_band(target_word, corpus)
            return freq_band

        return condition

    @staticmethod
    def position_based(context: np.ndarray, target: np.ndarray) -> str:
        """Position in context (first/mid/last token)."""
        # Use first token in context as conditioning
        first_idx = int(context[0, 0])
        return f"pos_{first_idx % 3}"  # 3 patches based on modulo

    @staticmethod
    def first_letter_based(corpus_gen: TinyCorpusGenerator):
        """First letter of target word (a-m vs n-z)."""
        def condition(context: np.ndarray, target: np.ndarray) -> str:
            target_idx = int(target[0, 0])
            target_word = corpus_gen.idx_to_word[target_idx]
            first_letter = target_word[0].lower()

            if first_letter < 'n':
                return "first_half_alphabet"
            else:
                return "second_half_alphabet"

        return condition

    @staticmethod
    def pos_based(corpus_gen: TinyCorpusGenerator):
        """Part-of-speech based conditioning."""
        def condition(context: np.ndarray, target: np.ndarray) -> str:
            target_idx = int(target[0, 0])
            target_word = corpus_gen.idx_to_word[target_idx]
            pos = corpus_gen.word_to_pos.get(target_word, "UNK")
            return f"pos_{pos}"

        return condition

    @staticmethod
    def random_k_patches(k: int, seed: int = 42):
        """Random partitioning into k patches (for ablation)."""
        np.random.seed(seed)

        def condition(context: np.ndarray, target: np.ndarray) -> str:
            target_idx = int(target[0, 0])
            patch_id = target_idx % k  # Deterministic but "random"
            return f"random_patch_{patch_id}"

        return condition


# ============================================================================
# Convenience Functions
# ============================================================================

def train_language_model(corpus: List[List[str]],
                        corpus_gen: TinyCorpusGenerator,
                        conditioning_fn: Callable,
                        n_characters: int = 8,
                        context_size: int = 4,
                        verbose: bool = True) -> Tuple[Dict, float]:
    """
    Convenience function to train a language model.

    Args:
        corpus: List of sentences
        corpus_gen: TinyCorpusGenerator instance
        conditioning_fn: Function (context, target) -> patch_id
        n_characters: Number of character projections
        context_size: Context window size
        verbose: Print results

    Returns:
        (solution, residual) tuple
    """
    # Convert corpus to training data
    contexts, targets = corpus_gen.corpus_to_training_data(corpus, context_size)

    if verbose:
        print(f"Training data: {len(contexts)} examples")
        print(f"Context size: {context_size}, Characters: {n_characters}")

    # Train
    model = SheafLanguageModel(
        vocab_size=corpus_gen.vocab_size,
        n_characters=n_characters,
        context_size=context_size
    )

    solution, residual = model.fit(contexts, targets, conditioning_fn)

    if verbose:
        print(f"\n✓ Training complete!")
        print(f"  Patches discovered: {len(solution)}")
        print(f"  Patch names: {list(solution.keys())}")
        print(f"  Cohomological obstruction: {residual:.6e}")

    return solution, residual


def test_language_model():
    """Test the language model on tiny corpus."""
    print("\n" + "="*70)
    print("Testing Sheaf Language Model")
    print("="*70)

    # Generate corpus
    gen = TinyCorpusGenerator(seed=42)
    corpus = gen.generate_corpus(n_sentences=100)

    print(f"\nCorpus: {len(corpus)} sentences, {gen.vocab_size} vocabulary")

    # Test 1: Single patch (baseline)
    print("\n" + "-"*70)
    print("Test 1: Single Patch (Baseline)")
    print("-"*70)

    solution1, residual1 = train_language_model(
        corpus, gen,
        conditioning_fn=ConditioningFunctions.single_patch,
        n_characters=4,
        verbose=True
    )

    # Test 2: Frequency-based (3 patches)
    print("\n" + "-"*70)
    print("Test 2: Frequency-Based Conditioning")
    print("-"*70)

    solution2, residual2 = train_language_model(
        corpus, gen,
        conditioning_fn=ConditioningFunctions.frequency_based(gen, corpus),
        n_characters=4,
        verbose=True
    )

    # Test 3: POS-based
    print("\n" + "-"*70)
    print("Test 3: Part-of-Speech Based Conditioning")
    print("-"*70)

    solution3, residual3 = train_language_model(
        corpus, gen,
        conditioning_fn=ConditioningFunctions.pos_based(gen),
        n_characters=4,
        verbose=True
    )

    # Summary
    print("\n" + "="*70)
    print("Summary: Cohomological Obstructions")
    print("="*70)
    print(f"  Single patch:    {residual1:.6e}")
    print(f"  Frequency-based: {residual2:.6e}")
    print(f"  POS-based:       {residual3:.6e}")

    # Determine best
    best_name = ""
    best_residual = min(residual1, residual2, residual3)

    if best_residual == residual1:
        best_name = "Single patch"
    elif best_residual == residual2:
        best_name = "Frequency-based"
    else:
        best_name = "POS-based"

    print(f"\n✓ Best conditioning: {best_name} (obstruction = {best_residual:.6e})")

    print("\n" + "="*70)
    print("✅ Language model tests complete!")
    print("="*70)


if __name__ == "__main__":
    test_language_model()
