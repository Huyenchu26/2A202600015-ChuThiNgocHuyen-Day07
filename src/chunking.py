from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        text = text.strip()

        # Split while keeping sentence-ending punctuation attached
        sentences = re.split(r'(?<=[.!?])(?:\s+|\n+)', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sentences = sentences[i:i + self.max_sentences_per_chunk]
            chunks.append(" ".join(chunk_sentences).strip())
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        chunks = []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        
        if not remaining_separators:
            # No more separators, split by character
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i:i + self.chunk_size])
            return chunks
        
        # Try the first separator
        separator = remaining_separators[0]
        rest_separators = remaining_separators[1:]
        
        parts = current_text.split(separator)
        good_chunks = []
        current_chunk = ""
        
        for i, part in enumerate(parts):
            if not current_chunk:
                current_chunk = part
            else:
                # Add separator and next part
                potential = current_chunk + separator + part
                if len(potential) <= self.chunk_size:
                    current_chunk = potential
                else:
                    # Current chunk is full, save it and start new one
                    if current_chunk:
                        good_chunks.append(current_chunk)
                    current_chunk = part
        
        if current_chunk:
            good_chunks.append(current_chunk)
        
        # For chunks that are still too long, recurse with next separator
        for chunk in good_chunks:
            if len(chunk) > self.chunk_size:
                chunks.extend(self._split(chunk, rest_separators))
            else:
                chunks.append(chunk)
        
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))
    
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    
    return dot_product / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size).chunk(text)
        sentence_chunks = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)
        
        def compute_stats(chunks):
            if not chunks:
                return {"count": 0, "avg_length": 0, "chunks": chunks}
            sizes = [len(c) for c in chunks]
            return {
                "count": len(chunks),
                "avg_length": sum(sizes) / len(sizes),
                "chunks": chunks
            }
        
        return {
            "fixed_size": compute_stats(fixed_chunks),
            "by_sentences": compute_stats(sentence_chunks),
            "recursive": compute_stats(recursive_chunks)
        }
