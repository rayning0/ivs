# In-Video Search System

A semantic video search system that allows you to find specific moments in videos using natural language queries. Built for hackathon demonstration with FastAPI backend and Streamlit frontend.

## Features

- 🎬 **Automatic Scene Detection**: Intelligently detects scene changes in videos
- 🖼️ **Thumbnail Extraction**: Extracts representative frames from each scene
- 🔍 **Semantic Search**: Search videos using natural language descriptions
- ⏱️ **Precise Timestamps**: Jump directly to relevant moments with exact timing
- 🚀 **Real-time Processing**: Fast video processing and indexing pipeline

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
         │              │   (CLIP)        │                │
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
- **FastAPI Application** (`app.py`): REST API endpoints for video processing and search
- **Video Processing** (`video_tools.py`): Scene detection using PySceneDetect and FFmpeg
- **AI Models** (`models.py`): CLIP-based text and image embeddings
- **Vector Search** (`index.py`): FAISS-based similarity search
- **Data Storage** (`store.py`): JSONL-based metadata persistence

#### Frontend UI (`/ui/`)
- **Streamlit Interface** (`app.py`): Web-based user interface for video upload and search
- **Real-time Results**: Displays search results with thumbnails and timestamps

## Tech Stack

### Backend Technologies
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI applications
- **PySceneDetect**: Automatic scene change detection in videos
- **FFmpeg**: Video processing and thumbnail extraction
- **Sentence Transformers**: CLIP model for semantic embeddings
- **FAISS**: Facebook AI Similarity Search for vector operations
- **PIL (Pillow)**: Image processing and manipulation

### Frontend Technologies
- **Streamlit**: Rapid web app development framework
- **Requests**: HTTP client for API communication

### AI/ML Components
- **CLIP (Contrastive Language-Image Pre-training)**:
  - Model: `clip-ViT-B-32`
  - Handles both text queries and image embeddings
  - Enables semantic similarity between text and images
- **Vector Embeddings**: 512-dimensional embeddings for similarity search
- **Scene Detection**: Content-based scene change detection with configurable thresholds

### Data Storage
- **Thumbnails**: JPG files stored in `/data/thumbs/`
- **Metadata**: JSONL format in `/data/shots_meta.jsonl`
- **Vector Index**: FAISS index file `/data/shots.faiss`
- **Static Files**: Served via FastAPI static file mounting

## API Endpoints

### Video Processing
- `POST /process_video`: Process a video file and extract scene thumbnails
  - Parameters: `video_path`, `video_id`, `scene_threshold`
  - Returns: Number of scenes detected and processed

### Search
- `POST /search`: Search for video content using text queries
  - Parameters: `query`, `k` (number of results)
  - Returns: Ranked list of matching video segments with timestamps

## Installation & Setup

### Prerequisites
- Python 3.14+
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
streamlit run app.py  # Starts UI on port 8501
```

## Usage

1. **Start Backend**: Run the FastAPI server (`./run.sh` in `/app/`)
2. **Start Frontend**: Run Streamlit UI (`streamlit run app.py` in `/ui/`)
3. **Process Video**: Upload a video file and set scene detection threshold
4. **Search Content**: Use natural language to find specific moments
5. **View Results**: Browse thumbnails with timestamps and relevance scores

## Example Queries

- "person talking in office"
- "outdoor scene with trees"
- "close-up shot of hands"
- "indoor setting with furniture"
- "person walking down hallway"

## File Structure

```
ivs/
├── app/                    # Backend API
│   ├── app.py             # FastAPI application
│   ├── models.py          # AI/ML models (CLIP)
│   ├── video_tools.py     # Video processing
│   ├── index.py           # Vector search (FAISS)
│   ├── store.py           # Metadata storage
│   ├── requirements.txt   # Backend dependencies
│   └── run.sh             # Server startup script
├── ui/                     # Frontend UI
│   ├── app.py             # Streamlit interface
│   └── requirements.txt   # Frontend dependencies
├── data/                   # Generated data (excluded from git)
│   ├── thumbs/            # Extracted thumbnails
│   ├── shots_meta.jsonl   # Scene metadata
│   └── shots.faiss        # Vector index
└── full_videos/           # Source videos (excluded from git)
```

## Performance Notes

- **Scene Detection**: Configurable threshold (20-40) for sensitivity
- **Processing Speed**: ~10-30 scenes per minute depending on video complexity
- **Search Speed**: Sub-second response for semantic queries
- **Memory Usage**: CLIP model requires ~2GB RAM for embeddings
- **Storage**: ~50-100KB per thumbnail + metadata per scene

## Development

Built for hackathon demonstration with focus on:
- Rapid prototyping and iteration
- Clear separation of concerns (API + UI)
- Scalable architecture for future enhancements
- Easy deployment and setup
