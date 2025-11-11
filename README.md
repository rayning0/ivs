# In-Video Search System
### by Raymond Gan. See [YouTube video](https://youtu.be/NrETEo9I7Cg) of my demo. Try it at https://raymond.hopto.org.
#### (To save money, my site only runs when I turn on Nebius VM.)


Inspired by [Netflix's In-Video Search System](https://netflixtechblog.com/building-in-video-search-936766f0017c), I built my own in 3 days at [Tubi's](https://tubi.tv) Oct. 2025 company hackathon.

It's a semantic video search system to let you quickly find and play specific moments in videos with natural language queries. You may search multiple videos by dialogue, descriptions, people, objects, or scenes.

Built in Python with FastAPI backend and Streamlit frontend. I used these AI models: OpenAI [CLIP](https://openai.com/index/clip/) for images, OpenAI [Whisper](https://openai.com/index/whisper/) for speech recognition, and [FAISS (Facebook AI Similarity Search)](https://www.pinecone.io/learn/series/faiss/faiss-tutorial/) for vector embeddings.

Viewers may use this to quickly find/jump to favorite scenes, video editors to make movie trailers/social media clips, and advertisers to jump to specific ad products in videos. Content moderators or standards and practices lawyers could use this to quickly find objectionable content.

My project got voted by my coworkers in the top 18 projects out of 62!

[![Click to see demo video](https://github.com/rayning0/ivs/blob/main/thumb_for_video.png)](https://www.youtube.com/watch?v=HM2WybZwpxM)

## Features

- 🎬 **Automatic Shot Detection**: Intelligently detects shot changes in videos
- 🖼️ **Multi-Frame Pooling**: Netflix-style shot representation using 3 frames per shot
- 🔍 **Dual-Modal Search**: Search by both visual content and spoken dialogue
- ⏱️ **Precise Timestamps**: Jump directly to relevant moments with exact timing
- 🎥 **Inline Video Player**: Play videos directly in browser at exact timestamps
- 🎛️ **Search Balance Control**: Adjustable alpha slider to pick importance of search by images vs dialogue
- 🚀 **Real-time Processing**: Fast video processing + indexing pipeline. Can run either locally on laptop or, for speed, on virtual machine with a GPU. I ran my demo on a Nebius virtual machine using [Nvidia H200 NVLink GPU with Intel Sapphire Rapids](https://nebius.com/h200), on Ubuntu 22.04 (CUDA 12). I configured this Nebius VM from scratch.
- 🧹 **Data Management**: Tools to clear processed data and restart

## Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   FastAPI       │    │   Video Files   │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Processing)  │
│   Port 8501     │    │   Port 8000     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        ▼                        │
         │              ┌─────────────────┐                │
         │              │   AI Models     │                │
         │              OpenAI CLIP/Whisper                │
         │              └─────────────────┘                │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Search UI     │    │   Vector DB     │    │   Thumbnails    │
│   (Results)     │    │   (FAISS)       │    │   (JPG Files)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

#### Backend API (`/app/`)
- **FastAPI Application** ([`app.py`](https://github.com/rayning0/ivs/blob/main/app/app.py)): REST API endpoints for video processing and search
- **Video Processing** ([`video_tools.py`](https://github.com/rayning0/ivs/blob/main/app/video_tools.py)): Shot detection using PySceneDetect and FFmpeg
- **AI Models** ([`models.py`](https://github.com/rayning0/ivs/blob/main/app/models.py)): OpenAI speech (Whisper) and image embeddings (CLIP)
- **Vector Search** ([`index.py`](https://github.com/rayning0/ivs/blob/main/app/index.py)): FAISS = Facebook AI Similarity Search
- **Data Storage** ([`store.py`](https://github.com/rayning0/ivs/blob/main/app/store.py)): JSONL-based metadata persistence
- **Subtitle Search** ([`subs_index.py`](https://github.com/rayning0/ivs/blob/main/app/subs_index.py)): FAISS vector search for subtitle embeddings
- **Speech Recognition** ([`asr.py`](https://github.com/rayning0/ivs/blob/main/app/asr.py)): Automatic Speech Recognition using [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper)

#### Frontend UI (`/ui/`)
- **Streamlit Interface** ([`app.py`](https://github.com/rayning0/ivs/blob/main/ui/app.py)): Web-based user interface for video upload and search
- **Environment Detection**: Automatically detects Mac vs Nebius VM and switches configurations
- **Real-time Results**: Displays search results with thumbnails and timestamps
- **Cross-Platform**: Works seamlessly on both local development (Mac) and remote deployment (Nebius VM)

## Tech Stack

### Backend Technologies
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI applications
- **PySceneDetect**: Automatic shot change detection in videos
- **FFmpeg**: Video processing and multi-frame extraction
- **Sentence Transformers**: CLIP model for semantic embeddings
- **FAISS**: Facebook AI Similarity Search for vector operations
- **Faster-Whisper**: Automatic Speech Recognition (ASR) for subtitle generation
- **PIL (Pillow)**: Image processing and manipulation
- **NumPy**: Multi-frame embedding averaging

### Frontend Technologies
- **Streamlit**: Rapid web app development framework
- **Requests**: HTTP client for API communication

### AI/ML Components
- **CLIP (Contrastive Language-Image Pre-training)**:
  - Model: `clip-ViT-B-32`
  - Handles both text queries and image embeddings
  - Enables semantic similarity between text and images
- **Multi-Frame Pooling**: Averages embeddings from 3 frames per shot for better representation
- **Faster-Whisper ASR**: Automatic speech recognition for subtitle generation
- **Vector Embeddings**: 512-dimensional embeddings for similarity search
- **Shot Detection**: Content-based shot change detection with configurable thresholds
- **Dual-Modal Search**: Fuses image and subtitle search with adjustable weights

### Data Storage
- **Multi-Frame Thumbnails**: JPG files stored in `/data/thumbs/` (3 per shot)
- **Image Metadata**: JSONL format in `/data/shots_meta.jsonl`
- **Image Vector Index**: FAISS index file `/data/shots.faiss`
- **Subtitle Metadata**: JSONL format in `/data/subs_meta.jsonl`
- **Subtitle Vector Index**: FAISS index file `/data/subs.faiss`
- **Static Files**: Served via FastAPI static file mounting

## API Endpoints

### Video Processing
- `POST /process_video`: Process a video file with multi-frame pooling and ASR
  - Parameters: `video_path`, `video_id`, `shot_threshold`
  - Returns: Number of shots detected, frames processed, and subtitle segments

### Search
- `POST /search`: Dual-modal search for video content using text queries
  - Parameters: `query`, `k` (number of results), `alpha` (image vs subtitle weight)
  - Returns: Ranked list of matching video segments with timestamps and relevance scores
  - Alpha: 0.0 = subtitle only, 1.0 = image only, 0.6 = balanced (default)

## Installation & Setup

### Prerequisites
- Python 3.13 (required for `faster-whisper` compatibility)
- FFmpeg installed and available in PATH
- Virtual environment (recommended)

### Backend Setup
```bash
cd app
pip install -r requirements.txt
./run.sh  # Starts server on port 8000
```

### Frontend Setup
```bash
cd ui
pip install -r requirements.txt
./run.sh  # Starts Streamlit UI on port 8501
```

**Note**: The frontend automatically detects whether it's running on Mac or Nebius VM and configures API endpoints and media URLs accordingly. No manual configuration needed!

## Usage

1. **Start Backend**: Run the FastAPI server ([`./run.sh`](https://github.com/rayning0/ivs/blob/main/app/run.sh) in `/app/`)
2. **Start Frontend**: Run Streamlit UI ([`./run.sh`](https://github.com/rayning0/ivs/blob/main/ui/run.sh) in `/ui/`)
   - The UI automatically detects your environment (Mac or Nebius VM)
   - API endpoints and media URLs are configured automatically
3. **Process Video**:
   - Select video from dropdown (episode1.mp4 or episode2.mp4)
   - Adjust shot detection threshold (20-40, default 27)
   - Click "Process" to extract multi-frame thumbnails and subtitles
   - View processing time and statistics
4. **Search Content**:
   - Choose from predefined search examples or type custom queries
   - Adjust search balance (alpha slider: 0.0 = dialogue, 1.0 = images, 0.6 = balanced)
   - Set number of results (K slider)
5. **View Results**:
   - Browse thumbnails and subtitle snippets at full size
   - Click video players to play at exact timestamps
   - See exact match badges for perfect quote matches
   - Use data management tools to delete processed data

## Example Queries

### Predefined Search Examples
The UI now includes a dropdown with common search patterns:
- `"have you tried turning it off and on again?"` (exact quote)
- `woman in elevator` (visual description)
- `man with glasses and big hair` (visual description)
- `woman walks by red shoes in window` (visual description)
- `old woman falls down stairs` (visual description)
- `0118999` (phone number)
- `tv ad` (content type)
- `"I am declaring war"` (exact quote)
- `"80 million people"` (exact quote)
- `bike shorts` (visual description)
- `trying on shoes` (visual description)

### Visual Queries (Alpha = 1.0)
- "woman walks by red shoes in window"
- "outdoor scene with trees"
- "close-up shot of hands"
- "trying on shoes"
- "old woman falling down stairs"

### Dialogue Queries (Alpha = 0.0)
- "Have you tried turning it off and on again?"
- "emergency services"
- "stress is a disease"
- "I am declaring war"

### Mixed Queries (Alpha = 0.6)
- "man in suit talking"
- "person saying hello"
- "office conversation"
- "stress management"

## File Structure

```
ivs/
├── app/                    # Backend API
│   ├── app.py             # FastAPI application with dual-modal search
│   ├── models.py          # AI/ML models (OpenAI CLIP)
│   ├── video_tools.py     # Video processing with multi-frame pooling
│   ├── index.py           # Image vector search (FAISS)
│   ├── subs_index.py      # Subtitle vector search (FAISS)
│   ├── asr.py             # Automatic Speech Recognition (OpenAI faster-whisper)
│   ├── store.py           # Metadata storage
│   ├── requirements.txt   # Backend dependencies
│   └── run.sh             # Server startup script with process cleanup
├── ui/                     # Frontend UI
│   ├── app.py             # Streamlit interface with video players
│   ├── requirements.txt   # Frontend dependencies
│   └── run.sh             # Frontend startup script
├── data/                   # Generated data (excluded from git)
│   ├── thumbs/            # Multi-frame thumbnails (3 per shot)
│   ├── videos/            # Source video files
│   ├── shots_meta.jsonl   # Image metadata
│   ├── shots.faiss        # Image vector index
│   ├── subs_meta.jsonl    # Subtitle metadata
│   └── subs.faiss         # Subtitle vector index
└── full_videos/           # Additional videos (excluded from git)
```

## Performance Notes

- **Shot Detection**: Configurable threshold (20-40) for sensitivity
- **Multi-Frame Processing**: 3x slower than single-frame (3 frames per shot)
- **ASR Processing**: ~1-2x real-time depending on hardware (CUDA recommended)
- **Search Speed**: Sub-second response for dual-modal semantic queries
- **Memory Usage**: CLIP model requires ~2GB RAM for embeddings
- **Storage**: ~150-300KB per shot (3 thumbnails + metadata)
- **Video Player**: Streamlit video component with automatic timestamp seeking

## Recent Updates

### Multi-Frame Pooling (Netflix-style)
- **3 frames per shot** for better representation
- **Averaged embeddings** capture shot dynamics
- **Significantly improved** search accuracy
- **3x storage cost** but much better results

### Dual-Modal Search
- **Image search**: CLIP text→image similarity
- **Subtitle search**: CLIP text→text similarity
- **Adjustable fusion**: Alpha slider controls balance
- **ASR integration**: Automatic speech recognition

### Enhanced UI
- **Inline video players** with timestamp seeking
- **Auto-generated video IDs** from filenames
- **Search balance controls** (alpha slider)
- **Data management tools** for cleanup
- **Accessibility improvements** (proper labels)

### Latest Features (October 2025)
- **Video Selection Dropdown**: Choose between episode1.mp4 and episode2.mp4
- **Smart Processing Detection**: Automatically detects already processed videos
- **Predefined Search Examples**: Dropdown with common search queries
- **Custom Search Input**: Option to type your own queries
- **Processing Time Display**: Shows how long video processing took
- **Search Query Logging**: Console output for debugging search requests
- **Improved Error Handling**: Better connection error management
- **Full-Size Thumbnails**: Thumbnails display at full resolution
- **Exact Match Highlighting**: Special badges for exact quote matches
- **Hybrid GPU/CPU Processing**: CLIP on GPU, Whisper on CPU for stability
- **Automatic Environment Detection**: Seamlessly works on both Mac (localhost) and Nebius VM (HTTPS proxy)
- **Unified Codebase**: Single `app.py` file works on both environments with automatic configuration
- **Smart URL Construction**: Video and thumbnail URLs automatically adapt to environment (local FastAPI vs remote proxy)

## Deployment

### Local Development (Mac)
- Backend: `http://localhost:8000` (FastAPI direct)
- Frontend: `http://localhost:8501` (Streamlit)
- Media: Served via FastAPI `/static` mount

### Remote Deployment (Nebius VM)
- Backend: `https://raymond.hopto.org/api` (HTTPS proxy via Nginx)
- Frontend: `https://raymond.hopto.org` (HTTPS)
- Media: Served directly from `/data` directory
- **Automatic Detection**: Frontend automatically detects environment and configures URLs

The system uses environment detection based on:
- Hostname check (looks for "computeinstance" in Nebius VMs)
- Network connectivity test (checks for Nebius internal IP)
- Falls back to Mac configuration if detection fails

## Development

Built for hackathon demonstration with focus on:
- Rapid prototyping and iteration
- Clear separation of concerns (API + UI)
- Scalable architecture for future enhancements
- Easy deployment and setup
- Production-ready features (multi-frame pooling, dual-modal search)
- Cross-platform compatibility (Mac and Nebius VM)
