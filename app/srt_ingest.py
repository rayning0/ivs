import re

_ts = re.compile(r"(\d+):(\d+):(\d+),(\d+)")


def _to_seconds(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _parse_ts(ts):
    # "00:00:05,000 --> 00:00:07,000"
    left, right = [t.strip() for t in ts.split("-->")]
    lh, lm, ls, lms = _ts.search(left).groups()
    rh, rm, rs, rms = _ts.search(right).groups()
    return _to_seconds(lh, lm, ls, lms), _to_seconds(rh, rm, rs, rms)


def parse_srt_text(srt_text):
    """
    Returns [{"start": float, "end": float, "text": str}, ...]
    """
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    segments = []
    for b in blocks:
        lines = [ln.strip("\ufeff").strip() for ln in b.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        # lines[0] may be index; lines[1] is timestamps
        if "-->" in lines[0]:
            ts_line = lines[0]
            text_lines = lines[1:]
        else:
            ts_line = lines[1]
            text_lines = lines[2:]
        start, end = _parse_ts(ts_line)
        text = " ".join(text_lines).strip()
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return segments
