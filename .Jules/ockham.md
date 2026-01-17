# Ockham's Journal

## 2026-01-11 - DirectorService Refactor
**Observation:** `DirectorService.generate_plan` was a long method (approx 70 lines) mixing configuration logic, API orchestration, and response parsing.
**Action:** Refactored `DirectorService` by extracting:
- `_build_generation_config`: Encapsulated Gemini configuration logic.
- `_parse_and_save_plan`: Encapsulated response parsing and state saving.
- Simplified `_build_outfit_instructions` logic to be more linear and readable.
**Delta:** Code is now more modular and easier to test.

## 2026-01-13 - CinematographerService Refactor
**Observation:** `CinematographerService.generate_assets` was a "Long Function" (approx 160 lines) mixing asset loading, loop logic, and API orchestration.
**Action:** Refactored `CinematographerService` by extracting:
- `_load_reference_poses`: Encapsulated reference pose loading logic.
- `_generate_keyframe_a`: Encapsulated the master shot generation logic.
- `_generate_sequential_keyframes`: Encapsulated the iterative editing loop and history management.
**Delta:** Simplified the main `generate_assets` method to a high-level orchestration flow. Added comprehensive unit tests.

## 2026-01-17 - Streaming Architecture
**Observation:** `DirectorService` blocked generation until completion, and `server.py` lacked a mechanism for real-time feedback of the generation content.
**Action:**
- Created `core/stream_models.py` with `StreamChunk` Pydantic model.
- Added `generate_plan_stream` to `DirectorService` and `IDirector`.
- Implemented `/ws/generate_stream` in `web/server.py` using a non-blocking thread-pool iterator pattern for the synchronous service generator.
**Delta:** Enabled real-time streaming of AI tokens to the user without blocking the event loop, following SOLID principles.
