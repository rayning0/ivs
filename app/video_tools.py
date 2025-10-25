import os, math, subprocess
from scenedetect import VideoManager, SceneManager
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
    out = os.path.join(out_dir, f"{os.path.basename(video_path)}_{math.floor(mid*1000)}.jpg")
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(mid), "-i", video_path, "-frames:v", "1", "-q:v", "2", out],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return out, mid
