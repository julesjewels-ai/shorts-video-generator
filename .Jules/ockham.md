# Ockham's Journal

## 2026-01-11 - DirectorService Refactor
**Observation:** `DirectorService.generate_plan` was a long method (approx 70 lines) mixing configuration logic, API orchestration, and response parsing.
**Action:** Refactored `DirectorService` by extracting:
- `_build_generation_config`: Encapsulated Gemini configuration logic.
- `_parse_and_save_plan`: Encapsulated response parsing and state saving.
- Simplified `_build_outfit_instructions` logic to be more linear and readable.
**Delta:** Code is now more modular and easier to test.

## 2026-01-12 - CinematographerService Refactor
**Observation:** `CinematographerService.generate_assets` was a monolithic method (approx 150 lines) handling initialization, API interaction for multiple steps, and file I/O, violating SRP.
**Action:** Refactored `CinematographerService` by extracting:
- `_load_reference_poses`: Encapsulated fallback logic for loading reference images.
- `_generate_keyframe_a`: Encapsulated logic for the master keyframe generation.
- `_generate_sequential_keyframes`: Encapsulated the iterative loop for generating subsequent keyframes.
**Delta:** `generate_assets` is now a high-level orchestrator, significantly reducing cognitive load and improving testability.
