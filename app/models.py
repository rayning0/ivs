import torch
from sentence_transformers import SentenceTransformer

if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

TEXT_MODEL = "clip-ViT-B-32"
IMG_MODEL  = "clip-ViT-B-32"

text_model = SentenceTransformer(TEXT_MODEL, device=device)
img_model  = SentenceTransformer(IMG_MODEL,  device=device)

def embed_text(texts, batch_size=64):
    return text_model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=batch_size
    )

def embed_images(pil_images, batch_size=16):
    return img_model.encode(
        pil_images,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=batch_size
    )
