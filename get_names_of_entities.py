import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "entity_subsumers.json")

def get_parent_entities():
    """
    Returns a list of parent entities (top-level keys)
    from entity_subsumers.json
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return list(data.keys())


# Example usage
if __name__ == "__main__":
    parents = get_parent_entities()
    print(parents)
