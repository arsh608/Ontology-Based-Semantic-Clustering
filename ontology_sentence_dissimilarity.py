import numpy as np
import json
import math
from get_entities import get_entities
import os

# Load ontology file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ontology_file = os.path.join(BASE_DIR, "new_islam_ontology_tur.ttl")

# Load entity level dissimilarity matrix
with open("entity_dissimilarity.json", "r") as f:
    dissimilarity_matrix = json.load(f)


# Get sentence level dissimilarity score
def sentence_dissimilarity(entities_a, entities_b, default_dissim=1.0):

    # Edge cases
    if not entities_a:
        return 0.0
    if not entities_b:
        return default_dissim

    total = 0.0

    for ea in entities_a:
        min_d = math.inf

        for eb in entities_b:
            if ea in dissimilarity_matrix and eb in dissimilarity_matrix[ea]:
                d = dissimilarity_matrix[ea][eb]
            elif eb in dissimilarity_matrix and ea in dissimilarity_matrix[eb]:
                d = dissimilarity_matrix[eb][ea]
            else:
                d = default_dissim

            min_d = min(min_d, d)

        total += min_d

    return total / len(entities_a)

# Extract entities from each sentence
def get_entities_from_sentences(sentences):
    all_entities = []
    
    for sent in sentences:
        entities_a = get_entities(sent, ontology_file)
        all_entities.append(entities_a)
    
    return all_entities

# Sentence Level Dissimilarity Matrix
def ontology_sentence_dissimilarity_matrix(sentences):
    entities_per_sentence = get_entities_from_sentences(sentences)
    n = len(entities_per_sentence)
    matrix = np.zeros((n, n))

    for i in range(n):
        matrix[i][i] = 0  # explicitly set diagonal to zero
        for j in range(i + 1, n):  # only upper triangle (excluding diagonal)
            score = sentence_dissimilarity(
                entities_per_sentence[i],
                entities_per_sentence[j]
            )
            matrix[i][j] = score
            matrix[j][i] = score  # mirror to lower triangle

    return matrix