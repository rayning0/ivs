import streamlit as st, requests

API = "http://localhost:8000"

st.title("In-Video Search (Mac Demo)")

with st.expander("Process a video"):
    vp = st.text_input("Video path (on this machine)", "/Users/rgan/ivs/data/videos/3min1.mp4")
    vid = st.text_input("Video ID", "sample")
    thr = st.slider("Scene threshold", 20, 40, 27)
    if st.button("Process"):
        r = requests.post(f"{API}/process_video",
                          data={"video_path": vp, "video_id": vid, "scene_threshold": thr})
        st.write(f"Status: {r.status_code}")
        st.write(f"Response: {r.text}")
        if r.status_code == 200:
            try:
                st.write(r.json())
            except:
                st.write("Could not parse JSON response")

query = st.text_input("Query", "man in suit")
k = st.slider("Top K", 1, 20, 8)

if st.button("Search"):
    r = requests.post(f"{API}/search", data={"query": query, "k": k}).json()
    if not r.get("results"):
        st.info("No results yet. Make sure you processed at least one video.")
    for item in r.get("results", []):
        st.image(f"{API}{item['thumb_url']}", width=280,
                 caption=f"{item['video_id']}  "
                         f"[{item['start']:.2f}s–{item['end']:.2f}s]  "
                         f"score={item['score']:.3f}")
