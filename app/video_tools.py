import math
import os
import subprocess

from scenedetect import SceneManager, VideoManager
from scenedetect.detectors import ContentDetector


def detect_shots(video_path, threshold=27):
    vm = VideoManager([video_path])
    sm = SceneManager()
    sm.add_detector(ContentDetector(threshold=threshold))
    vm.set_downscale_factor()
    vm.start()
    sm.detect_scenes(frame_source=vm)
    shots = sm.get_scene_list()
    times = [(s.get_seconds(), e.get_seconds()) for s, e in shots]
    vm.release()
    return times


def extract_midframe(video_path, start, end, out_dir="../data/thumbs"):
    """Extract a single frame from the middle of a shot (legacy function)"""
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


def extract_multiframes(video_path, start, end, out_dir="../data/thumbs", num_frames=3):
    """
    Extract multiple frames from a shot for multi-frame pooling.
    Returns list of (frame_path, timestamp) tuples.
    """
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.basename(video_path)
    shot_id = f"{base_name}_{math.floor(start*1000)}_{math.floor(end*1000)}"

    frames = []

    # Sample frames at different points in the shot
    if num_frames == 1:
        # Single frame at middle
        times = [start + (end - start) * 0.5]
    elif num_frames == 2:
        # Two frames: 25% and 75%
        times = [start + (end - start) * 0.25, start + (end - start) * 0.75]
    else:
        # Three or more frames: distributed across the shot
        times = []
        for i in range(num_frames):
            if num_frames == 1:
                t = start + (end - start) * 0.5
            else:
                t = start + (end - start) * (i / (num_frames - 1))
            times.append(t)

    for i, extract_time in enumerate(times):
        frame_path = os.path.join(
            out_dir, f"{shot_id}_frame{i+1}_{math.floor(extract_time*1000)}.jpg"
        )

        # Skip if frame already exists
        if os.path.exists(frame_path):
            frames.append((frame_path, extract_time))
            continue

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
                    frame_path,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Check if the extracted image is not blank
            if os.path.exists(frame_path) and os.path.getsize(frame_path) > 1000:
                frames.append((frame_path, extract_time))
            else:
                # If frame extraction failed, try a fallback time
                fallback_time = start + (end - start) * 0.5
                if abs(extract_time - fallback_time) > 0.1:  # Only if different enough
                    try:
                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-ss",
                                str(fallback_time),
                                "-i",
                                video_path,
                                "-frames:v",
                                "1",
                                "-q:v",
                                "2",
                                frame_path,
                            ],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        if (
                            os.path.exists(frame_path)
                            and os.path.getsize(frame_path) > 1000
                        ):
                            frames.append((frame_path, fallback_time))
                    except subprocess.CalledProcessError:
                        pass

        except subprocess.CalledProcessError:
            pass

    return frames
