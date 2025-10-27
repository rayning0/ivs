import glob
import os

import requests
import streamlit as st

API = "http://localhost:8000"

st.title("In-Video Search")
st.write("by Raymond Gan, 10/27/2025")

with st.expander("Process a video"):
    default_video_path = os.path.expanduser("~/ivs/data/videos/test2.mp4")
    vp = st.text_input("Video path (on this machine)", default_video_path)

    # Extract filename as video ID from path
    video_filename = os.path.basename(vp)
    video_id = os.path.splitext(video_filename)[0]  # Remove .mp4 extension

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
                st.write(f"**Subtitle segments:** {result.get('subtitle_segments', 0)}")
            except Exception:
                st.error("Could not parse response")
        else:
            st.error(f"❌ Processing failed (Status: {r.status_code})")
            st.write(f"Error: {r.text}")

query = st.text_input(
    "**Find (dialogue, description, person, object, scene):**", "man in suit"
)

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

        # Convert absolute path to relative path for Streamlit
        if expanded_path.startswith(os.path.expanduser("~/ivs/data/")):
            relative_path = expanded_path.replace(os.path.expanduser("~/ivs/data/"), "")
            video_url = f"{API}/static/{relative_path}"
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
                    st.image(f"{API}{item['thumb_url']}")
                except Exception:
                    pass  # Ignore thumbnail errors for exact matches
        elif item.get("thumb_url"):
            # Show thumbnail with fallback
            try:
                st.image(
                    f"{API}{item['thumb_url']}",
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

            if deleted_files:
                st.success(f"✅ Deleted {len(deleted_files)} files:")
                for file in deleted_files[:10]:  # Show first 10 files
                    st.write(f"  • {file}")
                if len(deleted_files) > 10:
                    st.write(f"  • ... and {len(deleted_files) - 10} more files")
            else:
                st.info("No files found to delete.")

    with col2:
        st.info(
            """
        **What gets deleted:**
        - All thumbnail images (*.jpg)
        - Search indexes (*.faiss)
        - Metadata files (*.jsonl)

        **What stays:**
        - Video files in /videos/
        - Directory structure
        """
        )
