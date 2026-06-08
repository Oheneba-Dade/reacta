import os

_MODEL_NAME = "all-MiniLM-L6-v2"
_MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'sentence-transformers')
)


class EmbeddingService:
    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(_MODEL_NAME, cache_folder=_MODEL_DIR)
        return cls._model

    def embed(self, text: str) -> list[float]:
        """Return a 384-dimensional embedding for the given text."""
        model = self._get_model()
        return model.encode(text, convert_to_numpy=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed multiple texts in one forward pass."""
        model = self._get_model()
        return model.encode(texts, convert_to_numpy=True).tolist()


embedding_service = EmbeddingService()
