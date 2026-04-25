from flask import Flask, render_template, request, jsonify
from services import split_into_sentences, get_sentences_from_files
from clustering import cluster_sentences

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.form.get('text')
    files = request.files.getlist('files')
    clustering_method = request.form.get('clustering_method')
    print(files)

    # Initialize sentences list
    sentences = []

    if text:
        # Process text input
        sentences = split_into_sentences(text)
    elif files:
        # Process uploaded files
        sentences = get_sentences_from_files(files)
    else:
        raise ValueError("Neither text nor files were provided.")

    result, best_silhouette_score = cluster_sentences(sentences, clustering_method)
    result_fixed = {int(k): v for k, v in result.items()}

    # Return both the clusters and the best silhouette score
    return jsonify({
        "clusters": result_fixed,
        "best_silhouette_score": best_silhouette_score
    })

if __name__ == '__main__':
    app.run(debug=True)
