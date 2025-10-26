import os

import requests
import streamlit as st

API = "http://localhost:8000"

st.title("In-Video Search (Mac Demo)")

with st.expander("Process a video"):
    default_video_path = os.path.expanduser("~/ivs/data/videos/test2.mp4")
    vp = st.text_input("Video path (on this machine)", default_video_path)
    vid = st.text_input("Video ID", "sample")
    thr = st.slider("Scene threshold", 20, 40, 27)
    if st.button("Process"):
        r = requests.post(
            f"{API}/process_video",
            data={"video_path": vp, "video_id": vid, "scene_threshold": thr},
        )
        st.write(f"Status: {r.status_code}")
        st.write(f"Response: {r.text}")
        if r.status_code == 200:
            try:
                st.write(r.json())
            except Exception:
                st.write("Could not parse JSON response")

query = st.text_input("Query", "man in suit")
k = st.slider("Top K", 1, 20, 8)

if st.button("Search"):
    r = requests.post(f"{API}/search", data={"query": query, "k": k}).json()
    if not r.get("results"):
        st.info("No results yet. Make sure you processed at least one video.")
    for item in r.get("results", []):

        def format_timestamp(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        if item.get("thumb_url"):
            # Show thumbnail with fallback
            try:
                st.image(
                    f"{API}{item['thumb_url']}",
                    width=280,
                    caption=f"{item['video_id']}  "
                    f"[{format_timestamp(item['start'])}–{format_timestamp(item['end'])}]  "
                    f"score={item['final']:.3f}",
                )
            except Exception as e:
                # If thumbnail fails to load, show text version with debug info
                st.write(
                    f"**{item['video_id']}** [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] - Thumbnail error: {str(e)[:50]}... (score={item['final']:.3f})"
                )
        else:
            st.write(
                f"**{item['video_id']}** [{format_timestamp(item['start'])}–{format_timestamp(item['end'])}] - {item.get('text', '')[:100]}... (score={item['final']:.3f})"
            )
