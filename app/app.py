import os

from asr import transcribe_to_segments
from fastapi import FastAPI, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from index import add_vectors as add_img_vectors
from index import load_index as load_img_index
from index import save_index as save_img_index
from index import search_vector as search_img
from models import embed_images, embed_text
from PIL import Image
from store import append, load_all

# transcript FAISS + ASR
from subs_index import add_segments as add_subs_segments
from subs_index import load_index as load_subs_index
from subs_index import load_meta_all as load_subs_meta
from subs_index import save_index as save_subs_index
from subs_index import search_vector as search_subs
from video_tools import detect_scenes, extract_midframe

app = FastAPI()

# Serve everything in ~/ivs/data under /static
app.mount("/static", StaticFiles(directory="../data"), name="static")

# load indices
load_img_index()
load_subs_index()


@app.post("/process_video")
def process_video(
    video_path: str = Form(...),
    video_id: str = Form(...),
    scene_threshold: int = Form(27),
):
    """
    Process BOTH:
      1) Video shots (thumbnails + image embeddings)
      2) Audio transcript (ASR) → text embeddings
    """
    print(f"Processing video: {video_path}")
    assert os.path.exists(video_path), f"Video not found: {video_path}"

    try:
        # ----- 1) SHOTS → image embeddings -----
        scenes = detect_scenes(video_path, threshold=scene_threshold)
        thumbs, metas = [], []
        for s, e in scenes:
            thumb, mid = extract_midframe(video_path, s, e)
            thumbs.append(thumb)
            metas.append(
                {
                    "video_id": video_id,
                    "video_path": video_path,
                    "start": s,
                    "end": e,
                    "mid": mid,
                    "thumb_rel": os.path.relpath(thumb, "../data"),
                }
            )

        if thumbs:
            images = [Image.open(p).convert("RGB") for p in thumbs]
            vecs = embed_images(images)
            add_img_vectors(vecs)
            save_img_index()
            for m in metas:
                append(m)

        # ----- 2) TRANSCRIPT (ASR) → text embeddings -----
        # If ASR fails (e.g., not installed), we still succeed on vision path.
        try:
            # [{"start","end","text"}]
            segments = transcribe_to_segments(video_path)
            if segments:
                texts = [seg["text"] for seg in segments]
                tvecs = embed_text(texts)
                tmeta = [
                    {
                        "video_id": video_id,
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"],
                    }
                    for seg in segments
                ]
                add_subs_segments(tvecs, tmeta)
                save_subs_index()
            transcribed = len(segments)
        except Exception:
            transcribed = 0

        return {"shots": len(metas), "transcript_segments": transcribed}
    except Exception as e:
        print(f"Error processing video: {e}")
        raise HTTPException(
            status_code=500, detail=f"Video processing failed: {str(e)}"
        )


def _minmax(scores):
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-8:
        return [0.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


@app.post("/search")
def search(query: str = Form(...), k: int = Form(8), alpha: float = Form(0.6)):
    """
    Fused search:
      - Vision index (image shots) scored by CLIP(text→image)
      - Transcript index (subtitle/ASR) scored by CLIP(text→text)
    alpha weights vision; (1 - alpha) weights transcript.
    """
    qvec = embed_text([query])[0]

    # Vision
    vid_idx, vid_scores = search_img(qvec, k)
    img_meta = load_all()
    vid_results = []
    for i, s in zip(vid_idx, vid_scores):
        if 0 <= i < len(img_meta):
            m = img_meta[i].copy()
            m["score_v"] = float(s)
            m["type"] = "vision"
            m["thumb_url"] = f"/static/{m['thumb_rel']}"
            vid_results.append(m)

    # Transcript
    sub_idx, sub_scores = search_subs(qvec, k)
    subs_meta = load_subs_meta()
    sub_results = []
    for i, s in zip(sub_idx, sub_scores):
        if 0 <= i < len(subs_meta):
            m = subs_meta[i].copy()
            m["score_t"] = float(s)
            m["type"] = "transcript"
            # thumb is optional for transcript hits
            m["thumb_url"] = None
            sub_results.append(m)

    # Normalize & fuse
    nv = _minmax([r["score_v"] for r in vid_results]) if vid_results else []
    nt = _minmax([r["score_t"] for r in sub_results]) if sub_results else []
    for r, s in zip(vid_results, nv):
        r["norm_v"] = s
    for r, s in zip(sub_results, nt):
        r["norm_t"] = s

    fused = []
    for r in vid_results:
        r["final"] = alpha * r.get("norm_v", 0.0) + (1 - alpha) * 0.0
        fused.append(r)
    for r in sub_results:
        r["final"] = alpha * 0.0 + (1 - alpha) * r.get("norm_t", 0.0)
        fused.append(r)

    # Deduplicate results by video_id and time range
    seen = set()
    deduplicated = []
    for r in fused:
        # Create a unique key based on video_id, start, and end times
        key = (r.get("video_id", ""), r.get("start", 0), r.get("end", 0))
        if key not in seen:
            seen.add(key)
            deduplicated.append(r)

    deduplicated.sort(key=lambda x: x["final"], reverse=True)
    return {"results": deduplicated[:k], "alpha_used": alpha}
