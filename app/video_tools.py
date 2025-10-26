import math
import os
import subprocess

from scenedetect import SceneManager, VideoManager
from scenedetect.detectors import ContentDetector


def detect_scenes(video_path, threshold=27):
    vm = VideoManager([video_path])
    sm = SceneManager()
    sm.add_detector(ContentDetector(threshold=threshold))
    vm.set_downscale_factor()
    vm.start()
    sm.detect_scenes(frame_source=vm)
    scenes = sm.get_scene_list()
    times = [(s.get_seconds(), e.get_seconds()) for s, e in scenes]
    vm.release()
    return times


def extract_midframe(video_path, start, end, out_dir="../data/thumbs"):
    os.makedirs(out_dir, exist_ok=True)
    mid = start + max(0.0, (end - start) / 2.0)
    out = os.path.join(
        out_dir, f"{os.path.basename(video_path)}_{math.floor(mid*1000)}.jpg"
    )

    # Skip extraction if thumbnail already exists
    if os.path.exists(out):
        return out, mid

    # Try multiple extraction points to avoid blank frames
    extraction_points = [mid, start + (end - start) * 0.3, start + (end - start) * 0.7]

    for attempt, extract_time in enumerate(extraction_points):
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    str(extract_time),
                    "-i",
                    video_path,
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    "-vf",
                    "scale=320:240",  # Resize to standard thumbnail size
                    out,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Check if the extracted image is not blank by checking file size
            if os.path.exists(out) and os.path.getsize(out) > 1000:  # At least 1KB
                return out, mid
            elif attempt < len(extraction_points) - 1:
                # Try next extraction point
                continue

        except subprocess.CalledProcessError:
            if attempt < len(extraction_points) - 1:
                continue
            else:
                raise

    return out, mid
