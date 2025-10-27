import os

from faster_whisper import WhisperModel


def get_best_device():
    """Return best available device for faster-whisper"""
    # try:
    #     WhisperModel("tiny", device="cuda", compute_type="int8")
    #     return "cuda"  # For Nvidia GPU in VM
    # except ValueError:
    return "cpu"  # Force CPU for Whisper to avoid cuDNN errors


_model = None


def get_model(model_size="base"):
    global _model
    if _model is None:
        device = get_best_device()
        _model = WhisperModel(model_size, device=device, compute_type="int8")
    return _model


def transcribe_to_segments(video_path, vad=True):
    """
    Returns list of dicts: [{"start": float, "end": float, "text": str}, ...]
    """
    assert os.path.exists(video_path), f"Not found: {video_path}"
    model = get_model()
    segments, _ = model.transcribe(video_path, vad_filter=vad)
    out = []
    for seg in segments:
        out.append(
            {
                "start": float(seg.start or 0.0),
                "end": float(seg.end or 0.0),
                "text": (seg.text or "").strip(),
            }
        )
    return out
