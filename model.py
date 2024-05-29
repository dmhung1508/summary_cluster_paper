from sentence_transformers import SentenceTransformer


class SentenceEmbedding():
    def __init__(self, path_model):
        self.path_model = path_model
        self.model = SentenceTransformer(self.path_model)
    def get_embedding(self, articles):
        id_articles, embeddings, titlePapers = [], [], []
        for article in articles:
            outputs = self.model.encode(article[1])
            id_articles.append(article[0])
            embeddings.append(outputs)
        return id_articles, embeddings, titlePapers
    def get_model(self):
        return self.model


