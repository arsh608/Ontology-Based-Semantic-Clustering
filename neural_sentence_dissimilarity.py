from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def embed_sentences(sentences, model_name="all-MiniLM-L6-v2"):
    # Load the model (downloads from Hugging Face if not cached)
    model = SentenceTransformer(model_name)

    # Encode the list of sentences into embeddings
    embeddings = model.encode(sentences)

    return embeddings

def neural_sentence_dissimilarity_matrix(sentences):
    embeddings = embed_sentences(sentences)
    
    sim_matrix = cosine_similarity(embeddings)
    sim_matrix = (sim_matrix + sim_matrix.T) / 2
    
    # Convert similarity → dissimilarity
    dissim_matrix = 1 - sim_matrix

    # Clip any tiny negative values due to floating point
    dissim_matrix = np.clip(dissim_matrix, 0, None)
    
    # Set diagonal to 0
    np.fill_diagonal(dissim_matrix, 0)

    return dissim_matrix

