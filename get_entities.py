import nltk
from nltk import word_tokenize, pos_tag
from rdflib import Graph, RDFS, Literal, SKOS, URIRef
from fuzzywuzzy import fuzz
import string

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

def normalize(text):
    """Lowercase and remove punctuation for consistent matching."""
    return text.lower().translate(str.maketrans('', '', string.punctuation))

def get_entity_name(subject):
    """Extract canonical entity name (local name) from any URIRef (# or /)."""
    if isinstance(subject, URIRef):
        s = str(subject)
        if '#' in s:
            return s.split('#')[-1]
        else:
            return s.rstrip('/').split('/')[-1]
    else:
        return str(subject)

def build_label_to_entity_map(graph):
    """
    Build a mapping from normalized label/altLabel -> canonical entity name.
    Also store entity depth in hierarchy (subClassOf).
    """
    label_to_entity = {}
    entity_depth = {}

    def get_depth(entity):
        # Recursively calculate depth via rdfs:subClassOf
        depths = []
        for parent in graph.objects(entity, RDFS.subClassOf):
            parent_depth = get_depth(parent)
            depths.append(parent_depth)
        return max(depths, default=-1) + 1

    for s in graph.subjects():
        entity_name = get_entity_name(s)
        entity_depth[entity_name] = get_depth(s)
        for p in [RDFS.label, SKOS.prefLabel, SKOS.altLabel]:
            for o in graph.objects(s, p):
                if isinstance(o, Literal):
                    label_norm = normalize(str(o))
                    label_to_entity[label_norm] = entity_name

    return label_to_entity, entity_depth

def get_entities(sentence, ontology_file, threshold=90):
    """
    Extract nouns/phrases from a sentence and map them to ontology entities.
    Returns canonical entity names (local names) with hierarchy awareness.
    """
    # Tokenize & POS-tag
    tokens = word_tokenize(sentence)
    tagged_tokens = pos_tag(tokens)
    nouns = [word for word, pos in tagged_tokens if pos.startswith('NN')]

    # Load ontology
    g = Graph()
    if ontology_file.endswith('.ttl'):
        g.parse(ontology_file, format='ttl')
    else:
        g.parse(ontology_file, format='xml')

    # Build mapping
    label_to_entity, entity_depth = build_label_to_entity_map(g)

    matched_entities = set()
    sentence_norm = normalize(sentence)

    # Match longest labels first (multi-word support)
    for label_norm, entity_name in sorted(label_to_entity.items(), key=lambda x: -len(x[0])):
        if label_norm in sentence_norm:
            matched_entities.add(entity_name)
        else:
            # Fuzzy match individual nouns
            for noun in nouns:
                if fuzz.ratio(normalize(noun), label_norm) >= threshold:
                    matched_entities.add(entity_name)

    # If multiple matches exist, prioritize **deepest entities**
    if len(matched_entities) > 1:
        matched_entities = sorted(matched_entities, key=lambda x: -entity_depth.get(x, 0))

    return list(matched_entities)

