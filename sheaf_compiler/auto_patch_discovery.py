"""
Automatic Patch Discovery

Automatically discovers the optimal number and type of patches
for a language modeling task using cohomological obstruction as
the optimization metric.

Key insight: Lower obstruction = better algebraic structure capture.
"""

import numpy as np
from typing import List, Dict, Tuple, Callable
from tiny_corpus import TinyCorpusGenerator
from language_model import (
    SheafLanguageModel,
    ConditioningFunctions,
    train_language_model
)


class AutoPatchDiscovery:
    """
    Automatic patch discovery using obstruction-guided search.

    Strategy:
    1. Try multiple conditioning functions
    2. For each, measure cohomological obstruction
    3. Return the best (lowest obstruction)
    """

    def __init__(self, corpus_gen: TinyCorpusGenerator, corpus: List[List[str]]):
        """
        Initialize auto-discovery.

        Args:
            corpus_gen: TinyCorpusGenerator instance
            corpus: Generated corpus
        """
        self.corpus_gen = corpus_gen
        self.corpus = corpus
        self.results = []

    def try_conditioning(self,
                        name: str,
                        conditioning_fn: Callable,
                        n_characters: int = 4,
                        context_size: int = 4,
                        verbose: bool = False) -> Dict:
        """
        Try a conditioning function and measure obstruction.

        Args:
            name: Human-readable name for this conditioning
            conditioning_fn: The conditioning function
            n_characters: Number of character projections
            context_size: Context window size
            verbose: Print details

        Returns:
            Dictionary with results
        """
        if verbose:
            print(f"\nTrying: {name}")
            print("-" * 60)

        solution, residual = train_language_model(
            self.corpus,
            self.corpus_gen,
            conditioning_fn,
            n_characters=n_characters,
            context_size=context_size,
            verbose=verbose
        )

        result = {
            'name': name,
            'conditioning_fn': conditioning_fn,
            'n_patches': len(solution),
            'patch_names': list(solution.keys()),
            'obstruction': residual,
            'solution': solution
        }

        self.results.append(result)
        return result

    def discover_best(self,
                     strategies: List[str] = ['single', 'frequency', 'pos', 'first_letter'],
                     n_characters: int = 4,
                     context_size: int = 4,
                     verbose: bool = True) -> Dict:
        """
        Discover the best conditioning strategy.

        Args:
            strategies: List of strategy names to try
            n_characters: Number of character projections
            context_size: Context window size
            verbose: Print progress

        Returns:
            Best result dictionary
        """
        if verbose:
            print("="*70)
            print("Automatic Patch Discovery")
            print("="*70)
            print(f"\nCorpus: {len(self.corpus)} sentences, "
                  f"{self.corpus_gen.vocab_size} vocabulary")
            print(f"Strategies to try: {strategies}")
            print(f"Characters: {n_characters}, Context: {context_size}")

        # Map strategy names to conditioning functions
        strategy_map = {
            'single': (
                "Single Patch (Baseline)",
                ConditioningFunctions.single_patch
            ),
            'frequency': (
                "Frequency-Based (high/mid/low)",
                ConditioningFunctions.frequency_based(self.corpus_gen, self.corpus)
            ),
            'pos': (
                "Part-of-Speech Based",
                ConditioningFunctions.pos_based(self.corpus_gen)
            ),
            'first_letter': (
                "First Letter (a-m vs n-z)",
                ConditioningFunctions.first_letter_based(self.corpus_gen)
            ),
            'position': (
                "Position-Based (modulo 3)",
                ConditioningFunctions.position_based
            )
        }

        # Try each strategy
        for strategy in strategies:
            if strategy not in strategy_map:
                print(f"\n⚠ Unknown strategy: {strategy}, skipping")
                continue

            name, conditioning_fn = strategy_map[strategy]
            self.try_conditioning(
                name,
                conditioning_fn,
                n_characters=n_characters,
                context_size=context_size,
                verbose=verbose
            )

        # Find best
        best = min(self.results, key=lambda x: x['obstruction'])

        if verbose:
            print("\n" + "="*70)
            print("Discovery Complete!")
            print("="*70)
            self._print_summary(best)

        return best

    def _print_summary(self, best: Dict):
        """Print summary of results."""
        print("\nAll strategies tried:")
        print("-"*70)
        for r in sorted(self.results, key=lambda x: x['obstruction']):
            print(f"  {r['name']:30s}: {r['obstruction']:12.4e} "
                  f"({r['n_patches']} patches)")

        print("\n✓ Best strategy:")
        print(f"  Name: {best['name']}")
        print(f"  Patches: {best['n_patches']}")
        print(f"  Patch names: {best['patch_names']}")
        print(f"  Cohomological obstruction: {best['obstruction']:.6e}")

        # Improvement over baseline
        baseline = next((r for r in self.results if r['n_patches'] == 1), None)
        if baseline and best != baseline:
            improvement = (1 - best['obstruction'] / baseline['obstruction']) * 100
            print(f"  Improvement over baseline: {improvement:.1f}%")


def test_auto_discovery():
    """Test automatic patch discovery."""
    print("\n" + "="*70)
    print("Testing Automatic Patch Discovery")
    print("="*70)

    # Generate corpus
    gen = TinyCorpusGenerator(seed=42)
    corpus = gen.generate_corpus(n_sentences=100)

    # Run auto-discovery
    discoverer = AutoPatchDiscovery(gen, corpus)

    best = discoverer.discover_best(
        strategies=['single', 'frequency', 'pos', 'first_letter'],
        n_characters=4,
        context_size=4,
        verbose=True
    )

    print("\n" + "="*70)
    print("✅ Auto-discovery test complete!")
    print("="*70)

    return best


if __name__ == "__main__":
    best_result = test_auto_discovery()
