import json
import os

import faiss
import numpy as np

DIM = 512
INDEX_PATH = os.path.join("../data", "subs.faiss")
META_PATH = os.path.join("../data", "subs_meta.jsonl")

subs_index = faiss.IndexFlatIP(DIM)


def _normalize(X):
    faiss.normalize_L2(X)
    return X


def load_index():
    global subs_index
    if os.path.exists(INDEX_PATH):
        subs_index = faiss.read_index(INDEX_PATH)


def save_index():
    """Save the subtitle index to a file."""
    os.makedirs("../data", exist_ok=True)
    faiss.write_index(subs_index, INDEX_PATH)


def add_segments(vectors, metas):
    X = _normalize(np.asarray(vectors, dtype="float32"))
    subs_index.add(X)
    os.makedirs("../data", exist_ok=True)
    with open(META_PATH, "a") as f:
        for m in metas:
            f.write(json.dumps(m) + "\n")


def load_meta_all():
    if not os.path.exists(META_PATH):
        return []
    with open(META_PATH) as f:
        return [json.loads(line) for line in f]


def search_vector(vec, k=8):
    Q = _normalize(np.asarray([vec], dtype="float32"))
    distances, indices = subs_index.search(Q, k)
    return indices[0].tolist(), distances[0].tolist()
