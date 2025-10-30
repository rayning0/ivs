import glob
import os
import socket

import requests
import streamlit as st


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
    API = "http://10.96.0.49:8000"  # Internal IP for API calls
    THUMBNAIL_BASE = "http://204.12.171.209:8000"  # External IP for thumbnails
    ENV_LABEL = "🌐 Nebius VM"
else:
    # Mac configuration
    API = "http://localhost:8000"  # Local API
    THUMBNAIL_BASE = "http://localhost:8000"  # Local thumbnails
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
    '"they toss us away like yesterday\'s jam"',
    "woman in elevator",
    "man with glasses and big hair",
    "woman walks by red shoes in window",
    "old woman falls down stairs",
    "0118999",
    "tv ad",
    '"I am declaring war"',
    '"80 million people"',
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
    try:
        r = requests.post(
            f"{API}/search", data={"query": query, "k": k, "alpha": alpha}
        )

        if r.status_code != 200:
            st.error(f"❌ API Error: {r.status_code} - {r.text}")
            st.stop()

        search_data = r.json()

        if not search_data.get("results"):
            st.info("No results yet. Make sure you processed at least one video.")
            st.stop()

    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.stop()

    for item in search_data.get("results", []):

        def format_timestamp(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        # Create video player with timestamp
        video_path = item.get("video_path", f"~/ivs/data/videos/{item['video_id']}.mp4")
        expanded_path = os.path.expanduser(video_path)

        # Convert absolute path to relative path for Streamlit
        if expanded_path.startswith(os.path.expanduser("~/ivs/data/")):
            relative_path = expanded_path.replace(os.path.expanduser("~/ivs/data/"), "")
            # Use THUMBNAIL_BASE for video URLs too (external IP on Nebius)
            video_url = f"{THUMBNAIL_BASE}/static/{relative_path}"
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
                    st.image(f"{THUMBNAIL_BASE}{item['thumb_url']}")
                except Exception:
                    pass  # Ignore thumbnail errors for exact matches
        elif item.get("thumb_url"):
            # Show thumbnail with fallback
            try:
                st.image(
                    f"{THUMBNAIL_BASE}{item['thumb_url']}",
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
    st.warning("⚠️ This will delete ALL processed data and clear all caches!")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear All Data", type="secondary"):
            data_dir = os.path.expanduser("~/ivs/data")
            deleted_count = 0

            # Clear the essential files that affect search
            try:
                import shutil

                # Clear data directory completely
                if os.path.exists(data_dir):
                    shutil.rmtree(data_dir)
                    os.makedirs(data_dir, exist_ok=True)
                    os.makedirs(os.path.join(data_dir, "thumbs"), exist_ok=True)
                    os.makedirs(os.path.join(data_dir, "videos"), exist_ok=True)
                    deleted_count = 1  # Count as 1 operation

                # Clear Python caches
                project_dir = os.path.expanduser("~/ivs")
                for root, dirs, files in os.walk(project_dir):
                    for dir_name in dirs:
                        if dir_name == "__pycache__":
                            shutil.rmtree(os.path.join(root, dir_name))
                            deleted_count += 1

                if deleted_count > 0:
                    st.success(f"✅ Cleared all data and caches!")
                    st.info("🔄 **Next step:** Restart backend server below")
                else:
                    st.info("No data found to clear.")

            except Exception as e:
                st.error(f"❌ Error clearing data: {e}")

    with col2:
        # Add restart backend button
        if st.button("🔄 Restart Backend Server", type="primary"):
            try:
                import subprocess
                import time

                st.write("🔄 Restarting backend server...")

                # Kill existing backend processes
                subprocess.run(["pkill", "-f", "gunicorn"], capture_output=True)
                time.sleep(2)

                # Start backend server
                backend_dir = os.path.expanduser("~/ivs/app")
                result = subprocess.run(
                    ["./run.sh"],
                    cwd=backend_dir,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    st.success("✅ Backend server restarted successfully!")
                else:
                    st.warning(f"⚠️ Backend restart may have issues: {result.stderr}")

            except Exception as e:
                st.error(f"❌ Failed to restart backend: {e}")
                st.write(
                    "💡 **Manual restart:** Run `cd ~/ivs/app && ./run.sh` in terminal"
                )

        st.info(
            """
        **Simple 2-Step Process:**

        1️⃣ **Clear All Data** - Removes all processed data and caches
        2️⃣ **Restart Backend** - Fresh server start

        **What gets cleared:**
        - All thumbnails, search indexes, metadata
        - Python caches

        **What stays:**
        - Video files and source code
        - Directory structure
        """
        )
