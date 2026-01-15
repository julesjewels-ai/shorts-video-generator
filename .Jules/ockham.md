# Ockham's Journal

## 2026-01-11 - DirectorService Refactor
**Observation:** `DirectorService.generate_plan` was a long method (approx 70 lines) mixing configuration logic, API orchestration, and response parsing.
**Action:** Refactored `DirectorService` by extracting:
- `_build_generation_config`: Encapsulated Gemini configuration logic.
- `_parse_and_save_plan`: Encapsulated response parsing and state saving.
- Simplified `_build_outfit_instructions` logic to be more linear and readable.
**Delta:** Code is now more modular and easier to test.

## 2026-01-15 - CinematographerService Refactor
**Observation:** `CinematographerService.generate_assets` was a monolithic method (>100 lines) handling both the initial keyframe generation and the sequential editing loop, including complex history management and logging.
**Action:** Refactored `CinematographerService` by extracting:
- `_generate_keyframe_a`: Handles the master shot generation and reference pose logic.
- `_generate_sequential_keyframes`: Handles the iterative editing loop and conversation history management.
**Delta:** `generate_assets` is now a high-level orchestrator (<20 lines), improving readability and testability.
