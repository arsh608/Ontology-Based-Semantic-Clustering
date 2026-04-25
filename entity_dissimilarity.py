import os
import json
import math
from rdflib import Graph, RDFS, RDF, OWL, URIRef
from glob import glob
from tqdm import tqdm

# --- Configurable ---
# File patterns to load (will load any matching in the working directory)
FILE_PATTERNS = ["*.owl", "*.rdf", "*.ttl", "*.xml", "*.jsonld"]
OUTPUT_SUBSUMERS = "entity_subsumers.json"
OUTPUT_MATRIX = "dissimilarity_matrix.json"
# --------------------

def load_graph_from_files(folder="."):
    g = Graph()
    files_loaded = []
    for pat in FILE_PATTERNS:
        for path in glob(os.path.join(folder, pat)):
            try:
                # let rdflib sniff format; many OWL are RDF/XML
                g.parse(path)
                files_loaded.append(path)
            except Exception as e:
                print(f"Warning: failed to parse {path}: {e}")
    return g, files_loaded

def collect_candidate_classes(g):
    """
    Collect a set of URIs that we will treat as ontology classes / entities.
    Strategy:
      - all subjects having rdf:type owl:Class or rdfs:Class
      - all subjects/objects used in rdfs:subClassOf triples
    Return: set of URIRefs
    """
    classes = set()

    # 1) subjects typed as owl:Class or rdfs:Class
    for s in g.subjects(RDF.type, OWL.Class):
        if isinstance(s, URIRef):
            classes.add(s)
    for s in g.subjects(RDF.type, RDFS.Class):
        if isinstance(s, URIRef):
            classes.add(s)

    # 2) any subject or object of rdfs:subClassOf
    for s, o in g.subject_objects(RDFS.subClassOf):
        if isinstance(s, URIRef):
            classes.add(s)
        if isinstance(o, URIRef):
            classes.add(o)

    # 3) optionally include classes that appear as rdfs:label subjects (defensive)
    for s in g.subjects(RDFS.label, None):
        if isinstance(s, URIRef):
            classes.add(s)

    return classes

def get_parents_map(g):
    """
    Build a mapping: class_uri -> set(parent_class_uri)
    Only using rdfs:subClassOf relations.
    """
    parents = {}
    for s, o in g.subject_objects(RDFS.subClassOf):
        if not isinstance(s, URIRef) or not isinstance(o, URIRef):
            continue
        parents.setdefault(s, set()).add(o)
        # ensure parent has an entry too (maybe empty)
        parents.setdefault(o, set())
    return parents

def compute_all_subsumers(classes, parents_map):
    """
    For each class, return set of subsumers (itself + all ancestors via parents_map).
    parents_map: class -> set(parents)
    Uses iterative DFS (avoids recursion limits).
    """
    subsumers = {}
    # small helper to traverse upward
    for c in classes:
        visited = set()
        stack = [c]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            # add parents if any
            for p in parents_map.get(node, set()):
                if p not in visited:
                    stack.append(p)
        # visited now contains the node and all ancestors (including node)
        subsumers[c] = visited
    return subsumers

def disnorm_from_sets(A, B):
    r"""
    Compute disnorm between two sets A and B:
      numerator = |A \ B| + |B \ A|
      denom = numerator + |A ∩ B|
      ratio = numerator / denom  (if denom > 0 else 0)
      dis = log2(1 + ratio)
    Returns float in [0,1]
    """
    A_minus_B = A - B
    B_minus_A = B - A
    inter = A & B

    numerator = len(A_minus_B) + len(B_minus_A)
    denom = numerator + len(inter)
    ratio = (numerator / denom) if denom > 0 else 0.0
    return math.log2(1.0 + ratio)  # log base 2

def get_local_name(uri):
    """
    Extract the local name from a URI (part after # or last /).
    """
    uri_str = str(uri)
    if '#' in uri_str:
        return uri_str.split('#')[-1]
    else:
        return uri_str.split('/')[-1]

def build_dissimilarity_matrix(entities, subsumers_map, uri_to_name):
    """
    entities: list of entity URIs (URIRef)
    subsumers_map: dict URIRef -> set(URIRef)
    uri_to_name: dict URIRef -> str (local name)
    Returns nested dict: name -> { name: float }
    """
    n = len(entities)
    # Pre-convert sets to python builtin sets of strings for faster json-friendly operations
    str_subs = {uri_to_name[e]: set(uri_to_name[x] for x in subsumers_map[e]) for e in entities}

    # Prepare empty nested dict
    matrix = {uri_to_name[e]: {} for e in entities}

    # compute only upper triangle then mirror
    for i in tqdm(range(n), desc="Computing dissimilarities"):
        ei = entities[i]
        si = uri_to_name[ei]
        Ai = str_subs[si]
        for j in range(i, n):
            ej = entities[j]
            sj = uri_to_name[ej]
            if i == j:
                d = 0.0
            else:
                Bj = str_subs[sj]
                d = disnorm_from_sets(Ai, Bj)
            matrix[si][sj] = d
            matrix[sj][si] = d  # symmetric
    return matrix, str_subs

def save_json(obj, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def main():
    print("Loading ontology files from current directory...")
    g, files_loaded = load_graph_from_files(".")
    print(f"Files loaded: {len(files_loaded)}")
    for p in files_loaded:
        print("  -", p)
    print("Total triples in merged graph:", len(g))

    print("Collecting candidate classes/entities...")
    classes = collect_candidate_classes(g)
    classes = sorted(classes, key=lambda u: str(u))  # stable order
    print(f"Collected {len(classes)} candidate classes/entities")

    # Create mapping from URI to local name
    uri_to_name = {c: get_local_name(c) for c in classes}
    names = list(uri_to_name.values())
    if len(names) != len(set(names)):
        print("Warning: Some local names are not unique. Using full URIs instead.")
        uri_to_name = {c: str(c) for c in classes}

    print("Building parents map from rdfs:subClassOf ...")
    parents_map = get_parents_map(g)

    print("Computing subsumers (node itself + all ancestors) for each entity...")
    subsumers_map = compute_all_subsumers(classes, parents_map)
    # convert to JSON-serializable form: name -> list(name)
    subsumers_json = {uri_to_name[k]: sorted([uri_to_name[x] for x in v]) for k, v in subsumers_map.items()}

    print(f"Saving subsumers to {OUTPUT_SUBSUMERS} ...")
    save_json(subsumers_json, OUTPUT_SUBSUMERS)
    print("Saved.")

    print("Computing dissimilarity matrix...")
    matrix, subs_as_str = build_dissimilarity_matrix(classes, subsumers_map, uri_to_name)

    print(f"Saving dissimilarity matrix to {OUTPUT_MATRIX} ...")
    save_json(matrix, OUTPUT_MATRIX)
    print("Saved.")

    print("All done.")
    print(f"Outputs:\n - {OUTPUT_SUBSUMERS}\n - {OUTPUT_MATRIX}")

if __name__ == "__main__":
    main()

