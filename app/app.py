from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from PIL import Image
import os

from models import embed_text, embed_images
from index import load_index, save_index, add_vectors, search_vector
from video_tools import detect_scenes, extract_midframe
from store import append, load_all

app = FastAPI()
app.mount("/static", StaticFiles(directory="../data"), name="static")
load_index()

@app.post("/process_video")
def process_video(video_path: str = Form(...), video_id: str = Form(...), scene_threshold: int = Form(27)):
    assert os.path.exists(video_path), f"Video not found: {video_path}"
    scenes = detect_scenes(video_path, threshold=scene_threshold)
    if not scenes:
        return {"shots": 0}

    thumbs, metas = [], []
    for (s, e) in scenes:
        thumb, mid = extract_midframe(video_path, s, e)
        thumbs.append(thumb)
        metas.append({
            "video_id": video_id,
            "video_path": video_path,
            "start": s,
            "end": e,
            "mid": mid,
            "thumb_rel": os.path.relpath(thumb, "../data")
        })

    images = [Image.open(p).convert("RGB") for p in thumbs]
    vecs = embed_images(images)
    add_vectors(vecs)
    save_index()

    for m in metas:
        append(m)

    return {"shots": len(metas)}

@app.post("/search")
def search(query: str = Form(...), k: int = Form(8)):
    qvec = embed_text([query])[0]
    idxs, scores = search_vector(qvec, k)

    meta = load_all()
    results = []
    for i,score in zip(idxs, scores):
        if 0 <= i < len(meta):
            m = meta[i].copy()
            m["score"] = float(score)
            m["thumb_url"] = f"/static/{m['thumb_rel']}"
            results.append(m)
    return {"results": results}
