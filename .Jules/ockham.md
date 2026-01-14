# Ockham's Journal

## 2026-01-11 - DirectorService Refactor
**Observation:** `DirectorService.generate_plan` was a long method (approx 70 lines) mixing configuration logic, API orchestration, and response parsing.
**Action:** Refactored `DirectorService` by extracting:
- `_build_generation_config`: Encapsulated Gemini configuration logic.
- `_parse_and_save_plan`: Encapsulated response parsing and state saving.
- Simplified `_build_outfit_instructions` logic to be more linear and readable.
**Delta:** Code is now more modular and easier to test.

## 2026-01-14 - CinematographerService Refactor
**Observation:** `CinematographerService.generate_assets` was a long method (>150 lines) mixing setup, loop logic, error handling, and file saving.
**Action:** Refactored `CinematographerService` by extracting:
- `_generate_keyframe_a`: Encapsulated master keyframe logic.
- `_generate_sequential_keyframes`: Encapsulated the iterative generation loop.
- `_load_reference_poses`: Encapsulated fallback logic for loading images.
- Created `tests/test_cinematographer.py` to ensure functional parity.
**Delta:** Reduced main method complexity, improved readability, and added test coverage.
