import numpy as np


class FakeWordOverlapEmbedder:
    """Deterministic, network-free stand-in for SentenceTransformer in tests.

    Encodes text as a normalized bag-of-words hash vector. Good enough to test
    chunking/indexing/retrieval logic without downloading a real model
    (this sandbox has no network access to huggingface.co).
    """

    VOCAB_SIZE = 256

    def encode(self, texts):
        vectors = []
        for text in texts:
            vec = np.zeros(self.VOCAB_SIZE, dtype="float32")
            for word in text.lower().split():
                vec[hash(word) % self.VOCAB_SIZE] += 1.0
            norm = np.linalg.norm(vec)
            vectors.append(vec / norm if norm > 0 else vec)
        return np.array(vectors, dtype="float32")
