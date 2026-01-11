# 📖 User Guide: Dance Loop Gen

Welcome to **Dance Loop Gen**! This guide will help you get started and make the most of the AI-powered video generation system for creating loopable dance shorts.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to the project directory
cd dance_loop_gen

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your-api-key-here
```

### 3. Run the Tool

**CLI Mode:**
```bash
python3 -m main
```

**Web Interface (Recommended):**
```bash
python3 -m web.server
# Then open http://localhost:8000
```

---

## 📋 Input Configuration

### High-Impact Inputs (Essential for Quality)

These three inputs define the uniqueness of your video:

#### 1. Style
- **What it is**: Creative style direction (e.g., "90s Hip Hop", "Cinematic Bachata").
- **Best Practice**: Be descriptive about lighting and camera style.

#### 2. Music
- **What it is**: Genre, mood, and tempo details.
- **Example**: `[Romantic Bachata], [Acoustic Guitar], 110-120 BPM`

#### 3. Description
- **What it is**: The primary visual concept and "vibe".
- **Example**: `Intimate outdoor terrace at sunset, warm Mediterranean vibes, golden hour lighting`

---

## 🎨 Scene Variety Control

Control how much backgrounds change between keyframes:

| Level | Effect |
|-------|--------|
| **0-3** | Minimal - Nearly identical backgrounds, only pose changes |
| **4-6** | Moderate - Lighting shifts, minor objects, 1-2 background elements |
| **7-9** | Significant - Weather/time changes, background characters |
| **10** | Dramatic - Major environment transformations, crowds |

---

## 📊 CSV Batch Processing

Process multiple videos automatically from a CSV file.

### Required Columns

| Column | Description |
|--------|-------------|
| `Created` | `FALSE` or `TRUE` - processing status |
| `Style` | Creative style direction |
| `Duration` | Video duration (e.g., "18s") |
| `Music` | Music style/genre |
| `Description` | Rich concept description |
| `Keywords/Tags` | Target keywords and hashtags |

---

## 📁 Output Files

Generated files are saved to `output/`:

| File | Description |
|------|-------------|
| `keyframe_A.png` | Master shot (Scene 1 start) |
| `keyframe_B.png` | Scene 2 start frame |
| `keyframe_C.png` | Scene 3 start frame |
| `veo_instructions.json` | Video generation payload |
| `metadata_options.json` | 3 SEO alternatives |

---

## 💡 Pro Tips

1. **Be Specific About Vocals**: Instead of "Female singer," use "Mature female vocals with clear articulation and emotional depth"
2. **Specify Tempo**: Include BPM (e.g., "110-120 BPM") to match dance rhythm
3. **Iterate with Low Resolution**: Use `image_resolution: low` during development.

---

## ❓ Troubleshooting

### API Key Not Found
Ensure `.env` exists in project root with `GEMINI_API_KEY`.

### Module Import Errors
Ensure you are running with `python3 -m main` or `python3 -m web.server` from the project root.
