from sklearn.cluster import AgglomerativeClustering
from ontology_sentence_dissimilarity import ontology_sentence_dissimilarity_matrix
from neural_sentence_dissimilarity import neural_sentence_dissimilarity_matrix
from collections import defaultdict
from sklearn.metrics import silhouette_score

def cluster_sentences(sentences, clustering_method, max_clusters=10):

    # Step 1: Compute the symmetric dissimilarity matrix based on clustering_method
    if clustering_method == "ontology":
        dissimilarity_matrix = ontology_sentence_dissimilarity_matrix(sentences)

    elif clustering_method ==  "neural":
        dissimilarity_matrix = neural_sentence_dissimilarity_matrix(sentences)

    else:
        print("Error")
    
    # Step 2: Find optimal number of clusters using silhouette score
    best_n = 2
    best_score = -1
    max_test_clusters = min(len(sentences) - 1, max_clusters)

    for n in range(2, max_test_clusters + 1):
        clustering = AgglomerativeClustering(
            n_clusters=n,
            metric='precomputed',
            linkage='average'
        )
        labels = clustering.fit_predict(dissimilarity_matrix)
        score = silhouette_score(dissimilarity_matrix, labels, metric='precomputed')
        if score > best_score:
            best_score = score
            best_n = n

    # Step 3: Cluster sentences using the optimal number of clusters
    clustering = AgglomerativeClustering(
        n_clusters=best_n,
        metric='precomputed',
        linkage='average'
    )
    labels = clustering.fit_predict(dissimilarity_matrix)

    # Step 4: Group sentences by cluster
    clusters = defaultdict(list)
    for sentence, label in zip(sentences, labels):
        clusters[label].append(sentence)

    return clusters, best_score
