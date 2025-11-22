from sentence_transformers import SentenceTransformer
from django.conf import settings

MODEL_NAME = getattr(settings, 'EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')

class EmbeddingClient:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, texts):
        # texts: list[str]
        return self.model.encode(texts, show_progress_bar=False).tolist()
