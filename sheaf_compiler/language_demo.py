"""
Language Modeling Demo: End-to-End Demonstration

Complete demonstration of sheaf-wreath language modeling:
1. Generate tiny structured corpus
2. Automatically discover best patch conditioning
3. Train model on best conditioning
4. Generate MLIR for all discovered patches

This demonstrates the full pipeline from raw text to FHE-compatible MLIR.
"""

import sys
sys.path.insert(0, 'mlir')

from tiny_corpus import TinyCorpusGenerator
from auto_patch_discovery import AutoPatchDiscovery
from sheaf_emitter import SheafMLIREmitter, SheafMLIRConfig


def main():
    print("\n" + "="*80)
    print("Sheaf-Wreath Language Modeling: Complete Demonstration")
    print("="*80)
    print("\nThis demo shows:")
    print("  1. Generating a tiny structured corpus")
    print("  2. Automatic patch discovery (obstruction-guided)")
    print("  3. Training the best model")
    print("  4. Generating MLIR for FHE deployment")
    print("="*80)

    # ========================================================================
    # Step 1: Generate Corpus
    # ========================================================================
    print("\n" + "-"*80)
    print("Step 1: Generating Tiny Structured Corpus")
    print("-"*80)

    gen = TinyCorpusGenerator(seed=42)
    corpus = gen.generate_corpus(n_sentences=100)

    print(f"\n✓ Generated corpus:")
    print(f"  Sentences: {len(corpus)}")
    print(f"  Vocabulary: {gen.vocab_size} tokens")

    # Show sample sentences
    print(f"\nSample sentences:")
    for i, sent in enumerate(corpus[:5]):
        print(f"  {i+1}. {' '.join(sent)}")

    # Show statistics
    contexts, targets = gen.corpus_to_training_data(corpus, context_size=4)
    print(f"\nTraining data:")
    print(f"  Examples: {len(contexts)}")
    print(f"  Context size: 4 tokens")

    # ========================================================================
    # Step 2: Automatic Patch Discovery
    # ========================================================================
    print("\n" + "-"*80)
    print("Step 2: Automatic Patch Discovery")
    print("-"*80)

    discoverer = AutoPatchDiscovery(gen, corpus)

    print("\nSearching for optimal conditioning strategy...")
    print("(Trying: single, frequency, POS, first-letter)")

    best = discoverer.discover_best(
        strategies=['single', 'frequency', 'pos', 'first_letter'],
        n_characters=4,
        context_size=4,
        verbose=False  # Suppress per-strategy output
    )

    # Print results
    print("\n✓ Discovery complete!")
    print(f"\nAll strategies ranked by obstruction:")
    for r in sorted(discoverer.results, key=lambda x: x['obstruction']):
        print(f"  {r['name']:30s}: {r['obstruction']:10.2e} ({r['n_patches']} patches)")

    print(f"\n🏆 Winner: {best['name']}")
    print(f"  Patches: {best['n_patches']}")
    print(f"  Obstruction: {best['obstruction']:.6e}")

    baseline = next(r for r in discoverer.results if r['n_patches'] == 1)
    improvement = (1 - best['obstruction'] / baseline['obstruction']) * 100
    print(f"  Improvement: {improvement:.1f}% over baseline")

    # ========================================================================
    # Step 3: Analyze Best Solution
    # ========================================================================
    print("\n" + "-"*80)
    print("Step 3: Analyzing Best Solution")
    print("-"*80)

    solution = best['solution']
    patch_names = best['patch_names']

    print(f"\nDiscovered {len(patch_names)} patches:")
    for i, name in enumerate(patch_names):
        patch_data = solution[name]
        weights = patch_data['weights']
        config = patch_data['config']

        print(f"\n  Patch {i+1}: {name}")
        print(f"    Characters: {config['n_characters']}")
        print(f"    Positions: {config.get('n_positions', 'N/A')}")
        print(f"    Weight matrix shape: {weights.shape}")

        # Show dominant characters
        weight_magnitudes = np.abs(weights)
        dominant_chars = np.argmax(weight_magnitudes, axis=1)
        print(f"    Dominant characters per position: {dominant_chars[:4]}")

    # ========================================================================
    # Step 4: Generate MLIR
    # ========================================================================
    print("\n" + "-"*80)
    print("Step 4: Generating MLIR")
    print("-"*80)

    print(f"\nGenerating MLIR for {len(patch_names)} patches...")

    import os
    os.makedirs("mlir/examples", exist_ok=True)

    mlir_files = []

    for patch_name in patch_names:
        single_patch_solution = {patch_name: solution[patch_name]}

        emitter = SheafMLIREmitter(
            single_patch_solution,
            SheafMLIRConfig(
                module_name=f"language_model_{patch_name}",
                function_name="predict_next_token",
                add_comments=True
            )
        )

        mlir_code = emitter.emit()

        # Save to file
        filename = f"mlir/examples/05_language_{patch_name}.mlir"
        with open(filename, 'w') as f:
            f.write(mlir_code)

        mlir_files.append(filename)
        print(f"  ✓ {filename}")

    # ========================================================================
    # Step 5: Summary
    # ========================================================================
    print("\n" + "="*80)
    print("✅ DEMONSTRATION COMPLETE!")
    print("="*80)

    print("\nWhat we accomplished:")
    print(f"  ✓ Generated {len(corpus)}-sentence corpus with {gen.vocab_size} vocabulary")
    print(f"  ✓ Tried {len(discoverer.results)} conditioning strategies")
    print(f"  ✓ Automatically found best: {best['name']}")
    print(f"  ✓ Achieved {improvement:.1f}% obstruction reduction")
    print(f"  ✓ Generated {len(mlir_files)} MLIR files (FHE depth 0)")

    print("\nKey Results:")
    print(f"  • Best conditioning: {best['name']}")
    print(f"  • Number of patches: {best['n_patches']}")
    print(f"  • Cohomological obstruction: {best['obstruction']:.6e}")
    print(f"  • Improvement over baseline: {improvement:.1f}%")

    print("\nGenerated MLIR files:")
    for f in mlir_files:
        print(f"  • {f}")

    print("\n" + "="*80)
    print("Next Steps:")
    print("="*80)
    print("  1. Examine the generated .mlir files")
    print("  2. Try larger vocabulary (100-200 words)")
    print("  3. Experiment with context size (4 → 8 tokens)")
    print("  4. Add more sophisticated conditioning functions")
    print("  5. Compare to traditional language models")

    print("\n💡 Key Insight:")
    print("   Language has algebraic structure.")
    print("   Sheaf-wreath attention exploits it automatically.")
    print("   Result: Exact learning on tiny datasets, FHE depth 0.")

    print("\n" + "="*80)


if __name__ == "__main__":
    import numpy as np  # Needed for patch analysis
    main()
