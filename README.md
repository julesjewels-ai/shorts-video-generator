# Dance Loop Logic Tool

This tool automates the creation of 18-second loopable dance video concepts using Google's **Gemini 3 Pro**. It acts as a "Director" to generate a scene plan with strict loop logic and a "Cinematographer" to generate consistent character keyframes for each scene. Finally, it outputs instructions compatible with Veo (or other video generators).

## Features

-   **High-Reasoning Planning**: Uses Gemini 3 Pro's "Thinking Mode" to ensure the final scene loops perfectly back to the first scene.
-   **Consistent Character Generation**: Uses a conversational editing workflow to keep characters, clothing, and lighting consistent across multiple keyframes (A -> B -> C).
-   **Configurable Prompts**: All system prompts and user requests are stored as text files for easy customization without touching code.
-   **SOLID Architecture**: Built with a modular design for easy extension.
-   **Comprehensive Documentation**: Full guides for both users and developers in the `docs/` folder.

## Prerequisites

-   Python 3.8+
-   A Google Cloud Project with access to Gemini 3 Pro (v1alpha).

## Installation

1.  Navigate to the project directory:
    ```bash
    cd /path/to/dance_loop_gen
    ```

2.  **Set up a Virtual Environment**:
    It is recommended to use a virtual environment to manage dependencies.

    *   **Create the virtual environment**:
        ```bash
        python3 -m venv .venv
        ```
    *   **Activate the virtual environment**:
        *   On macOS/Linux:
            ```bash
            source .venv/bin/activate
            ```
        *   On Windows:
            ```bash
            .venv\Scripts\activate
            ```

3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Environment Variables**:
    Create a `.env` file in the root of the project (or ensure `GEMINI_API_KEY` is set in your environment):
    ```bash
    export GEMINI_API_KEY="your-api-key-here"
    ```

2.  **Config File**:
    Settings can be adjusted in `config.py` if needed (e.g., model names, output directory).

## Usage

Run the tool as a module from the parent directory:

```bash
python3 -m dance_loop_gen.main
```

### 🌐 Web Interface (Recommended)

For a more user-friendly experience with real-time progress tracking and a results gallery:

1.  **Start the server**:
    ```bash
    python3 -m dance_loop_gen.web.server
    ```
2.  **Access the UI**: Open your browser to `http://localhost:8000`.

**Features of the Web UI:**
- **Live Monitoring**: Watch the Director and Cinematographer work via WebSockets.
- **Configuration Hub**: Edit character outfits, settings, and SEO keywords directly in the browser.
- **Results Gallery**: Browse previous generation runs and download assets.
- **One-Click Generation**: Trigger new videos with a single button.

### What Happens?

1.  **Director Phase**: The tool reads the user request from `prompts/default_user_request.txt` and uses Gemini to plan 3 scenes. It enforces that the end pose of Scene 3 matches the start pose of Scene 1.
2.  **Cinematographer Phase**:
    -   Generates **Keyframe A** (Master Shot) based on Scene 1.
    -   Generates **Keyframe B** by asking Gemini to "edit" Keyframe A (change pose only).
    -   Generates **Keyframe C** by asking Gemini to "edit" Keyframe B.
3.  **Instruction Phase**: Saves all assets and a `veo_instructions.json` file containing the prompt, audio, and image paths for each scene.
4.  **SEO Metadata Phase**: Generates 3 alternative metadata options (title, description, tags) with emotional hooks targeting your audience.

## Customization

You can fully customize the behavior by editing the text files in the `prompts/` directory:

-   **`default_user_request.txt`**: Change this to define the specific style, vibe, and audience for your video.
    *   *Example: "Style: 90s Hip Hop. Vibe: High energy."*
-   **`director_system.txt`**: The system instructions for the planning phase. Edit this to change the strictness of the loop logic or the JSON structure.
-   **`cinematographer_master.txt`**: The prompt template for the very first image (Master Shot).
-   **`cinematographer_edit.txt`**: The prompt template used to transform the previous image into the next pose.

### Character Outfits

You can customize the appearance of the dance characters:

-   **`leader_outfit.txt`**: Define the leader's appearance and clothing.
    *   *Example: "a joyful young Spanish man wearing a traditional dark waistcoat with gold embroidery."*
-   **`follower_outfit.txt`**: Define the follower's appearance and clothing.
    *   *Example: "a blonde younger woman wearing a traditional flowing pink dress and a white flower in her hair."*

**Smart Fallback Logic:**
-   If both files are empty, the AI Director has full creative freedom.
-   If only one is defined, the AI will design a matching, complementary outfit for the other character.

You can provide reference images to guide the position and pose of the dancers in the first keyframe.

#### Single Reference Pose
-   **`reference_pose.png`**, **`.jpg`**, or **`.jpeg`**: Place an image in the `prompts/` directory.
    *   The AI will use this image as a guide for body positions, framing, and composition.

#### Multiple Reference Poses (Batch Iteration)
-   **`reference_pose_1.png`**, **`reference_pose_2.png`**, etc.
    *   When processing in **Batch Mode** (via CSV or Web UI), the tool will cycle through these images.
    *   Video 1 uses pose 1, Video 2 uses pose 2, and so on.

**Smart Fallback Logic:**
-   If numbered files exist, they take priority.
-   If no numbered files but `reference_pose.png/jpg` exists, it's used for all videos.
-   If no reference image is provided, the AI Cinematographer decides the pose based on the scene description.

### Scene Variety Control

Control how much the background and scene elements change between keyframes while maintaining dancer and style consistency.

**Configuration** (`.env`):
```bash
# 0 = Minimal change (default), 10 = Dramatic change
SCENE_VARIETY=5
```

**Per-Video CSV Control**:
Add optional `Scene_Variety` column to your CSV:
```csv
Scene_Variety
5
```

**Variety Levels**:
-   **0-3**: Minimal variation - nearly identical backgrounds, only pose changes
-   **4-6**: Moderate variation - lighting shifts, minor objects, 1-2 background people/animals
-   **7-9**: Significant variation - weather changes, time of day shifts, background characters
-   **10**: Dramatic variation - major environment transformations, crowds, dramatic time/weather changes

**Consistency Guarantees:**
-   ✅ Same two dancers in every frame
-   ✅ Identical clothing throughout
-   ✅ Consistent overall style and vibe
-   ✅ Only backgrounds vary (based on variety level)

### Metadata Configuration

Configure metadata generation by editing `prompts/metadata_config.txt`:

-   **`language`**: Output language for title, description, and tags (default: English).
    *   *Example: `language: Spanish`*
-   **`target_keywords`**: Comma-separated keywords to incorporate (leave empty for AI to decide).
    *   *Example: `target_keywords: bachata, sensual dance, couple dancing`*
-   **`spreadsheet_path`**: Path to a spreadsheet with SEO research data. The entire file is sent to the AI for analysis.
    *   *Example: `spreadsheet_path: seo_research.csv`*

**SEO Specialist Service:**
The tool includes an SEO Specialist that generates 3 emotionally-targeted metadata alternatives:
1. **Nostalgic/Warm**: Evokes memories and comfort
2. **Aspirational/Passionate**: Inspires desire and romance
3. **Community/Belonging**: Creates shared identity

## CSV Batch Processing

Process multiple videos from a CSV file automatically. The tool will:
- Read video concepts from CSV rows
- Process only rows where `Created=FALSE`
- Automatically update CSV when each video completes

### CSV File Format

Your CSV must include these columns:

| Column | Description | Required |
|--------|-------------|----------|
| Created | `FALSE` or `TRUE` - processing status | ✅ Required |
| Style | Creative style direction | ✅ Required |
| Title (Spanish) | Original Spanish title | Optional |
| Title (English) | Original English title | Optional |
| Improved Title | Refined Spanish title | Optional |
| Improve Title English | Refined English title | Optional |
| Duration | Video duration (e.g., "18s") | ✅ Required |
| Music | Music style/genre | ✅ Required |
| Description | Rich concept description | ✅ Required |
| Keywords/Tags | Target keywords and hashtags | ✅ Required |

**See `prompts/test_batch.csv` for a complete example.**

### How to Use

1. **Create your CSV file** with video concepts (see format above)

2. **Set the CSV path** in your `.env` file:
   ```bash
   CSV_INPUT_PATH=./prompts/my_batch.csv
   ```

3. **Run the tool normally:**
   ```bash
   python3 -m dance_loop_gen.main
   ```

The tool will automatically:
- Create a timestamped backup of your CSV
- Process all rows where `Created=FALSE`
- Enrich prompts with CSV data
- Update `Created=TRUE` after successful generation
- Continue processing if individual videos fail

### Configuration Options

Add these to your `.env` file:

```bash
# Path to CSV file (required for batch mode)
CSV_INPUT_PATH=./prompts/batch_concepts.csv

# Automatically update CSV after generation (default: true)
CSV_AUTO_UPDATE=true

# Create backup before processing (default: true)
CSV_CREATE_BACKUP=true
```

### Batch Process Flow

For each row in the CSV, the prompt context is enriched with:
- **Creative Direction**: Style, music type, duration
- **Concept Description**: Rich description from CSV
- **Target Metadata**: Suggested titles and keywords
- **Base Context**: Content from `default_user_request.txt`

The setting will use `setting.txt` if provided, otherwise defaults to a clean, subtle background that keeps focus on the dancers.


## Output

All generated files are saved in the `output/` directory:

-   `keyframe_A.png`: Master generated image.
-   `keyframe_B.png`: Second scene start frame.
-   `keyframe_C.png`: Third scene start frame.
-   `veo_instructions.json`: The final JSON payload for video generation.
-   `metadata_options.json`: 3 metadata alternatives with recommendation.
-   `metadata_options.csv`: Same data in spreadsheet format.

## Project Structure

-   `main.py`: CLI entry point.
-   `services/`: Logic for Director, Cinematographer, SEO Specialist, etc.
-   `web/`: FastAPI backend and Vanilla JS frontend for the web interface.
-   `core/`: Pydantic models.
-   `prompts/`: Text content for prompts and configuration.
-   `utils/`: Helper functions.
-   `docs/`: Detailed project documentation (User Guide, Dev Guide, etc.).

## 📚 Documentation

For more detailed information, please refer to the following:

-   [User Guide](docs/user_guide.md): How to use the tool and configure inputs.
-   [Developer Guide](docs/developer_guide.md): Technical architecture and service patterns.
-   [API Reference](docs/api_reference.md): Data models and schema.
-   [Roadmap](docs/roadmap.md): Future plans and ideas.
-   [Developer Log](docs/devlog.md): Development history.


