import os, json

META_PATH = os.path.join("../data", "shots_meta.jsonl")

def append(meta: dict):
    os.makedirs(os.path.dirname(META_PATH), exist_ok=True)
    with open(META_PATH, "a") as f:
        f.write(json.dumps(meta) + "\n")

def load_all():
    if not os.path.exists(META_PATH):
        return []
    with open(META_PATH) as f:
        return [json.loads(line) for line in f]
