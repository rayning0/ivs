import glob
import os
import socket

import requests
import streamlit as st


def join_url(base, *parts):
    return "/".join([base.rstrip("/")] + [p.strip("/") for p in parts])


def detect_environment():
    """Detect if running on Mac or Nebius VM based on hostname/IP"""
    try:
        hostname = socket.gethostname()

        # Are we on Nebius VM?
        if "computeinstance" in hostname.lower():
            return "nebius"

        # Check if we can reach the Nebius internal IP
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(1)
        result = test_socket.connect_ex(("10.96.0.49", 8000))
        test_socket.close()

        if result == 0:  # Connection successful
            return "nebius"
        else:
            return "mac"

    except Exception:
        return "mac"


# Set API configuration based on environment
ENVIRONMENT = detect_environment()

if ENVIRONMENT == "nebius":
    # Nebius VM configuration
    API = "https://raymond.hopto.org/api"  # Use HTTPS
    THUMBNAIL_BASE = "https://raymond.hopto.org/data"
    ENV_LABEL = "🌐 Nebius VM"
else:
    # Mac configuration
    API = "http://localhost:8000"  # Local dev hits FastAPI directly
    THUMBNAIL_BASE = "http://localhost:8000/static"  # Local thumbnails
    ENV_LABEL = "💻 Mac"

st.title("In-Video Search")
st.write("by Raymond Gan, 10/27/2025")

# Show environment indicator
st.info(f"Running on: {ENV_LABEL} | API: {API} | Thumbnails: {THUMBNAIL_BASE}")

with st.expander("Process a video"):
    # Video selection dropdown
    video_options = {
        "episode1.mp4": os.path.expanduser("~/ivs/data/videos/episode1.mp4"),
        "episode2.mp4": os.path.expanduser("~/ivs/data/videos/episode2.mp4"),
    }

    selected_video = st.selectbox(
        "Pick video to process. 2 video clips from British comedy 'The IT Crowd':",
        options=list(video_options.keys()),
        index=0,
    )

    vp = video_options[selected_video]

    # Extract filename as video ID from path
    video_filename = os.path.basename(vp)
    video_id = os.path.splitext(video_filename)[0]  # Remove .mp4 extension

    # Check if thumbnails already exist for this video
    thumbs_dir = os.path.expanduser("~/ivs/data/thumbs")
    # Use the full filename (with .mp4) to match thumbnail naming pattern
    existing_thumbs = glob.glob(os.path.join(thumbs_dir, f"{video_filename}_*.jpg"))
    already_processed = len(existing_thumbs) > 0

    if already_processed:
        st.success(
            f"✅ {video_id} already processed ({len(existing_thumbs)} thumbnails found)"
        )
        st.info(
            "💡 To reprocess, delete existing thumbnails in Data Management section below"
        )
    else:
        st.write("**Shot Detection Threshold:**")
        st.caption("20-25 = Very Sensitive (many short shots)")
        st.caption("26-30 = Balanced (1 new shot every few seconds)")
        st.caption("31-35 = Less Sensitive (fewer, longer shots)")
        thr = st.slider("Threshold", 20, 40, 27, label_visibility="collapsed")

        if st.button("Process"):
            r = requests.post(
                f"{API}/process_video",
                data={"video_path": vp, "video_id": video_id, "shot_threshold": thr},
            )
            if r.status_code == 200:
                try:
                    result = r.json()
                    st.success(f"✅ Processing complete!")
                    st.write(f"**Shots detected:** {result.get('shots', 0)}")
                    st.write(
                        f"**Frames processed:** {result.get('total_frames_processed', 0)} (3 per shot)"
                    )
                    st.write(
                        f"**Subtitle segments:** {result.get('subtitle_segments', 0)}"
                    )

                    # Display processing time
                    processing_time = result.get("processing_time_seconds", 0)
                    if processing_time > 0:
                        minutes = int(processing_time // 60)
                        seconds = processing_time % 60
                        if minutes > 0:
                            st.write(f"**Processing time:** {minutes}m {seconds:.1f}s")
                        else:
                            st.write(f"**Processing time:** {seconds:.1f}s")
                except Exception:
                    st.error("Could not parse response")
            else:
                st.error(f"❌ Processing failed (Status: {r.status_code})")
                st.write(f"Error: {r.text}")

# Predefined search examples
search_examples = [
    '"have you tried turning it off and on again?"',
    "woman in elevator",
    "man with glasses and big hair",
    "woman walks by red shoes in window",
    "old woman falls down stairs",
    "0118999",
    "tv ad",
    '"I am declaring war"',
    '"80 million people"',
    "bike shorts",
    "trying on shoes",
]

# Create dropdown with custom input option
selected_example = st.selectbox(
    "**Find (dialogue, description, person, object, scene) in all processed videos:**",
    options=["Type your own search..."] + search_examples,
    index=0,
)

# Handle input based on selection
if selected_example == "Type your own search...":
    query = st.text_input(
        "**Enter your search query:**",
        placeholder="e.g., 'red shoes', 'office workers', 'angry face'",
        label_visibility="collapsed",
    )
else:
    query = selected_example

col1, col2 = st.columns(2)

with col1:
    st.write("**Top K Nearest Neighbors:**")
    st.caption("Lower = Fewer, better search results")
    st.caption("Higher = More, poorer search results")
    k = st.slider("Number of results", 1, 20, 8, label_visibility="collapsed")

with col2:
    st.write("**Search Importance (Images vs Dialogue):**")
    st.caption("0.0 = Dialogue only")
    st.caption("0.6 = Balanced: 60% images, 40% dialogue")
    st.caption("1.0 = Images only")

    alpha = st.slider("Alpha", 0.0, 1.0, 0.6, 0.1, label_visibility="collapsed")

if st.button("Search"):
    r = requests.post(
        f"{API}/search", data={"query": query, "k": k, "alpha": alpha}
    ).json()
    if not r.get("results"):
        st.info("No results yet. Make sure you processed at least one video.")
    for item in r.get("results", []):

        def format_timestamp(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        # Create video player with timestamp
        video_path = item.get("video_path", f"~/ivs/data/videos/{item['video_id']}.mp4")
        expanded_path = os.path.expanduser(video_path)

        # Convert absolute path to relative path under ~/ivs/data/
        if expanded_path.startswith(os.path.expanduser("~/ivs/data/")):
            relative_path = expanded_path.replace(os.path.expanduser("~/ivs/data/"), "")
            # Works on both envs:
            #  - Nebius: https://.../data/<videos/...>
            #  - Mac:    http://localhost:8000/static/<videos/...>
            video_url = join_url(THUMBNAIL_BASE, relative_path)
        else:
            video_url = f"file://{expanded_path}"

        # For exact matches, always show video player prominently
        if item.get("exact_match"):
            st.write(
                f"🎯 **EXACT MATCH:** {item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}]"
            )
            st.write(f"**Quote:** \"{item.get('text', '')}\"")
            st.write(f"**Score:** {item['final']:.3f}")

            # Always show video player for exact matches
            st.video(video_url, start_time=int(item["start"]))

            # Add timestamp and score below video
            subtitle_text = item.get("text", "")
            if subtitle_text:
                st.write(
                    f"{item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] - {subtitle_text} (score={item['final']:.3f})"
                )
            else:
                st.write(
                    f"{item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] score={item['final']:.3f}"
                )

            # Optionally show thumbnail if available
            if item.get("thumb_url"):
                try:
                    # Backend returns: /static/thumbs/... but THUMBNAIL_BASE already includes the path
                    # Mac: THUMBNAIL_BASE = "http://localhost:8000/static", need "thumbs/..."
                    # Nebius: THUMBNAIL_BASE = "https://raymond.hopto.org/data", need "thumbs/..."
                    thumb_path = item["thumb_url"].lstrip("/")
                    if thumb_path.startswith("static/"):
                        thumb_path = thumb_path[7:]  # Remove "static/" prefix
                    thumb_url = join_url(THUMBNAIL_BASE, thumb_path)
                    st.image(thumb_url)
                except Exception:
                    pass  # Ignore thumbnail errors for exact matches
        elif item.get("thumb_url"):
            # Show thumbnail with fallback
            # Backend returns: /static/thumbs/... but THUMBNAIL_BASE already includes the path
            # Mac: THUMBNAIL_BASE = "http://localhost:8000/static", need "thumbs/..."
            # Nebius: THUMBNAIL_BASE = "https://raymond.hopto.org/data", need "thumbs/..."
            thumb_path = item["thumb_url"].lstrip("/")
            if thumb_path.startswith("static/"):
                thumb_path = thumb_path[7:]  # Remove "static/" prefix
            thumb_url = join_url(THUMBNAIL_BASE, thumb_path)
            try:
                st.image(
                    thumb_url,
                    caption=f"{item['video_id']}  "
                    f"[{format_timestamp(item['start'])}–{format_timestamp(item['end'])}]  "
                    f"score={item['final']:.3f}",
                )
                # Add video player with timestamp
                st.video(video_url, start_time=int(item["start"]))

                # Add timestamp and score below video
                subtitle_text = item.get("text", "")
                if subtitle_text:
                    st.write(
                        f"{item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] - {subtitle_text} (score={item['final']:.3f})"
                    )
                else:
                    st.write(
                        f"{item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] score={item['final']:.3f}"
                    )

            except Exception as e:
                # If thumbnail fails to load, show text version with debug info
                st.write(
                    f"**{item['video_id']}** [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] - Thumbnail error: {str(e)[:50]}... (score={item['final']:.3f})"
                )
                # Add video player with timestamp
                st.video(video_url, start_time=int(item["start"]))

                # Add timestamp and score below video
                subtitle_text = item.get("text", "")
                if subtitle_text:
                    st.write(
                        f"{item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] - {subtitle_text} (score={item['final']:.3f})"
                    )
                else:
                    st.write(
                        f"{item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] score={item['final']:.3f}"
                    )
        else:
            st.write(
                f"**{item['video_id']}** [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] - {item.get('text', '')[:100]}... (score={item['final']:.3f})"
            )
            # Add video player with timestamp
            st.video(video_url, start_time=int(item["start"]))

            # Add timestamp and score below video
            subtitle_text = item.get("text", "")
            if subtitle_text:
                st.write(
                    f"{item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] - {subtitle_text} (score={item['final']:.3f})"
                )
            else:
                st.write(
                    f"{item['video_id']} [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] score={item['final']:.3f}"
                )

# Data Management Section
with st.expander("🗑️ Data Management", expanded=False):
    st.warning("⚠️ This will delete ALL processed data!")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Delete All Data", type="secondary"):
            data_dir = os.path.expanduser("~/ivs/data")
            project_dir = os.path.expanduser("~/ivs")
            deleted_files = []

            # Delete all .jpg files in thumbs directory
            thumb_files = glob.glob(os.path.join(data_dir, "thumbs", "*.jpg"))
            for file in thumb_files:
                try:
                    os.remove(file)
                    deleted_files.append(os.path.basename(file))
                except Exception as e:
                    st.error(f"Failed to delete {file}: {e}")

            # Delete all .jsonl and .faiss files in data directory
            data_files = glob.glob(os.path.join(data_dir, "*.jsonl")) + glob.glob(
                os.path.join(data_dir, "*.faiss")
            )
            for file in data_files:
                try:
                    os.remove(file)
                    deleted_files.append(os.path.basename(file))
                except Exception as e:
                    st.error(f"Failed to delete {file}: {e}")

            # Clear Python cache directories
            import shutil

            cache_dirs = []
            for root, dirs, files in os.walk(project_dir):
                for dir_name in dirs:
                    if dir_name == "__pycache__":
                        cache_path = os.path.join(root, dir_name)
                        try:
                            shutil.rmtree(cache_path)
                            cache_dirs.append(os.path.relpath(cache_path, project_dir))
                        except Exception as e:
                            st.error(f"Failed to delete cache {cache_path}: {e}")

            # Delete .pyc files
            pyc_files = []
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    if file.endswith(".pyc"):
                        pyc_path = os.path.join(root, file)
                        try:
                            os.remove(pyc_path)
                            pyc_files.append(os.path.relpath(pyc_path, project_dir))
                        except Exception as e:
                            st.error(f"Failed to delete {pyc_path}: {e}")

            # Delete .DS_Store files (macOS)
            ds_store_files = []
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    if file == ".DS_Store":
                        ds_path = os.path.join(root, file)
                        try:
                            os.remove(ds_path)
                            ds_store_files.append(os.path.relpath(ds_path, project_dir))
                        except Exception as e:
                            st.error(f"Failed to delete {ds_path}: {e}")

            # Report results
            total_deleted = (
                len(deleted_files)
                + len(cache_dirs)
                + len(pyc_files)
                + len(ds_store_files)
            )
            if total_deleted > 0:
                st.success(f"✅ Deleted {total_deleted} items:")

                if deleted_files:
                    st.write(f"**Data files ({len(deleted_files)}):**")
                    for file in deleted_files[:5]:  # Show first 5 files
                        st.write(f"  • {file}")
                    if len(deleted_files) > 5:
                        st.write(f"  • ... and {len(deleted_files) - 5} more files")

                if cache_dirs:
                    st.write(f"**Python cache directories ({len(cache_dirs)}):**")
                    for cache_dir in cache_dirs[:3]:
                        st.write(f"  • {cache_dir}")
                    if len(cache_dirs) > 3:
                        st.write(f"  • ... and {len(cache_dirs) - 3} more")

                if pyc_files:
                    st.write(f"**Python bytecode files ({len(pyc_files)}):**")
                    for pyc_file in pyc_files[:3]:
                        st.write(f"  • {pyc_file}")
                    if len(pyc_files) > 3:
                        st.write(f"  • ... and {len(pyc_files) - 3} more")

                if ds_store_files:
                    st.write(f"**System files ({len(ds_store_files)}):**")
                    for ds_file in ds_store_files[:3]:
                        st.write(f"  • {ds_file}")
                    if len(ds_store_files) > 3:
                        st.write(f"  • ... and {len(ds_store_files) - 3} more")
            else:
                st.info("No files found to delete.")

    with col2:
        st.info(
            """
        **What gets deleted:**
        - All thumbnail images (*.jpg)
        - Search indexes (*.faiss)
        - Metadata files (*.jsonl)
        - Python cache directories (__pycache__)
        - Python bytecode files (*.pyc)
        - System files (.DS_Store)

        **What stays:**
        - Video files in /videos/
        - Directory structure
        - Source code files
        - Virtual environments
        - Running servers (backend/frontend)
        """
        )
