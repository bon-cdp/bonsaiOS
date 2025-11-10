"""
Tiny Structured Corpus Generator

Generates a grammatically structured mini-language for testing
sheaf-wreath language models on small datasets.

The corpus has clear algebraic structure:
- Deterministic syntactic patterns
- Natural patches (function words vs content words)
- Small vocabulary (~40-50 tokens)
"""

import numpy as np
from typing import List, Dict, Tuple


class TinyCorpusGenerator:
    """
    Generates grammatically structured sentences from templates.

    The language has:
    - ~40-50 unique tokens
    - Clear POS categories (DET, NOUN, VERB, ADJ, ADV, PREP)
    - Deterministic patterns (templates)
    - Natural frequency distribution (Zipf-like)
    """

    def __init__(self, seed: int = 42):
        np.random.seed(seed)

        # Vocabulary organized by part of speech
        self.vocab = {
            'DET': ['the', 'a', 'an'],
            'NOUN': ['cat', 'dog', 'bird', 'mat', 'rug', 'tree',
                    'house', 'car', 'book', 'table', 'chair'],
            'VERB': ['sat', 'ran', 'flew', 'jumped', 'walked',
                    'looked', 'ate', 'slept'],
            'ADJ': ['big', 'small', 'red', 'blue', 'quick', 'slow'],
            'ADV': ['quickly', 'slowly', 'quietly', 'loudly'],
            'PREP': ['on', 'in', 'under', 'over', 'near', 'by']
        }

        # Sentence templates (syntactic patterns)
        self.templates = [
            ['DET', 'NOUN', 'VERB', 'PREP', 'DET', 'NOUN'],  # "the cat sat on the mat"
            ['DET', 'ADJ', 'NOUN', 'VERB'],                   # "the big dog ran"
            ['DET', 'NOUN', 'VERB', 'ADV'],                   # "a bird flew quickly"
            ['DET', 'ADJ', 'NOUN', 'VERB', 'PREP', 'DET', 'NOUN'],  # "the small cat jumped on the chair"
            ['NOUN', 'VERB', 'NOUN'],                         # "dog ate book" (telegraphic)
            ['DET', 'NOUN', 'VERB', 'DET', 'ADJ', 'NOUN'],    # "the cat looked the red house"
        ]

        # Build flat vocabulary list
        self.flat_vocab = []
        self.word_to_pos = {}
        for pos, words in self.vocab.items():
            for word in words:
                self.flat_vocab.append(word)
                self.word_to_pos[word] = pos

        self.vocab_size = len(self.flat_vocab)
        self.word_to_idx = {word: idx for idx, word in enumerate(self.flat_vocab)}
        self.idx_to_word = {idx: word for word, idx in self.word_to_idx.items()}

    def generate_sentence(self) -> List[str]:
        """Generate a single grammatical sentence."""
        template = np.random.choice(range(len(self.templates)))
        sentence = []

        for pos in self.templates[template]:
            word = np.random.choice(self.vocab[pos])
            sentence.append(word)

        return sentence

    def generate_corpus(self, n_sentences: int = 100) -> List[List[str]]:
        """Generate a corpus of sentences."""
        corpus = []
        for _ in range(n_sentences):
            sentence = self.generate_sentence()
            corpus.append(sentence)
        return corpus

    def get_word_frequency(self, word: str, corpus: List[List[str]]) -> int:
        """Count word frequency in corpus."""
        count = 0
        for sentence in corpus:
            count += sentence.count(word)
        return count

    def get_frequency_band(self, word: str, corpus: List[List[str]]) -> str:
        """Classify word into frequency band (high/mid/low)."""
        freq = self.get_word_frequency(word, corpus)

        # Thresholds based on typical Zipf distribution
        if freq >= 30:
            return "high_freq"
        elif freq >= 10:
            return "mid_freq"
        else:
            return "low_freq"

    def print_statistics(self, corpus: List[List[str]]):
        """Print corpus statistics."""
        print("="*70)
        print("Tiny Corpus Statistics")
        print("="*70)

        total_tokens = sum(len(sent) for sent in corpus)
        unique_tokens = len(set(word for sent in corpus for word in sent))

        print(f"\nSentences: {len(corpus)}")
        print(f"Total tokens: {total_tokens}")
        print(f"Unique tokens: {unique_tokens}")
        print(f"Avg sentence length: {total_tokens / len(corpus):.1f}")

        # Frequency distribution
        freq_dist = {}
        for sent in corpus:
            for word in sent:
                freq_dist[word] = freq_dist.get(word, 0) + 1

        sorted_freq = sorted(freq_dist.items(), key=lambda x: x[1], reverse=True)

        print(f"\nTop 10 most frequent words:")
        for word, count in sorted_freq[:10]:
            pos = self.word_to_pos.get(word, "UNK")
            print(f"  {word:12s} ({pos}): {count:3d}")

        # Frequency bands
        high_freq = [w for w, c in sorted_freq if c >= 30]
        mid_freq = [w for w, c in sorted_freq if 10 <= c < 30]
        low_freq = [w for w, c in sorted_freq if c < 10]

        print(f"\nFrequency bands:")
        print(f"  High (≥30): {len(high_freq)} tokens")
        print(f"  Mid (10-29): {len(mid_freq)} tokens")
        print(f"  Low (<10): {len(low_freq)} tokens")

        # POS distribution
        pos_counts = {}
        for sent in corpus:
            for word in sent:
                pos = self.word_to_pos.get(word, "UNK")
                pos_counts[pos] = pos_counts.get(pos, 0) + 1

        print(f"\nPart-of-speech distribution:")
        for pos, count in sorted(pos_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pos:6s}: {count:4d} ({100*count/total_tokens:.1f}%)")

    def corpus_to_training_data(self, corpus: List[List[str]], context_size: int = 4
                                ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Convert corpus to sheaf training data.

        Given a sentence, creates (context → next_word) pairs.

        Args:
            corpus: List of sentences (list of words)
            context_size: Number of preceding words as context

        Returns:
            (contexts, targets) where:
                contexts: List of [context_size x 1] arrays (word indices)
                targets: List of [1 x 1] arrays (next word index)
        """
        contexts = []
        targets = []

        for sentence in corpus:
            # Convert words to indices
            indices = [self.word_to_idx[word] for word in sentence]

            # Create sliding windows
            for i in range(context_size, len(indices)):
                context = indices[i-context_size:i]
                target = indices[i]

                # Convert to numpy arrays (shape expected by sheaf learner)
                context_array = np.array([[idx] for idx in context], dtype=float)
                target_array = np.array([[target]], dtype=float)

                contexts.append(context_array)
                targets.append(target_array)

        return contexts, targets


def test_tiny_corpus():
    """Test the corpus generator."""
    print("\n" + "="*70)
    print("Testing Tiny Corpus Generator")
    print("="*70)

    # Generate corpus
    gen = TinyCorpusGenerator(seed=42)
    corpus = gen.generate_corpus(n_sentences=100)

    # Print first 10 sentences
    print("\nFirst 10 generated sentences:")
    for i, sent in enumerate(corpus[:10]):
        print(f"  {i+1}. {' '.join(sent)}")

    # Print statistics
    gen.print_statistics(corpus)

    # Convert to training data
    print("\n" + "="*70)
    print("Training Data Conversion")
    print("="*70)

    contexts, targets = gen.corpus_to_training_data(corpus, context_size=4)

    print(f"\nGenerated {len(contexts)} training examples")
    print(f"Context shape: {contexts[0].shape}")
    print(f"Target shape: {targets[0].shape}")

    # Show first example
    print(f"\nExample training pair:")
    context_words = [gen.idx_to_word[int(contexts[0][i, 0])] for i in range(4)]
    target_word = gen.idx_to_word[int(targets[0][0, 0])]

    print(f"  Context: {context_words}")
    print(f"  Target:  {target_word}")

    print("\n" + "="*70)
    print("✅ Tiny corpus generator working!")
    print("="*70)


if __name__ == "__main__":
    test_tiny_corpus()
