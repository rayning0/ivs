import os

import faiss
import numpy as np

DIM = 512
INDEX_PATH = os.path.join("../data", "shots.faiss")
index = faiss.IndexFlatIP(DIM)


def load_index():
    global index
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)


def save_index():
    os.makedirs("../data", exist_ok=True)
    faiss.write_index(index, INDEX_PATH)


def add_vectors(vectors):
    X = np.asarray(vectors, dtype="float32")
    faiss.normalize_L2(X)
    index.add(X)


def search_vector(vec, k=8):
    Q = np.asarray([vec], dtype="float32")
    faiss.normalize_L2(Q)
    distances, indices = index.search(Q, k)
    return indices[0].tolist(), distances[0].tolist()
