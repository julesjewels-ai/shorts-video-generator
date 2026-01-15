# Ockham's Journal

## 2026-01-11 - DirectorService Refactor
**Observation:** `DirectorService.generate_plan` was a long method (approx 70 lines) mixing configuration logic, API orchestration, and response parsing.
**Action:** Refactored `DirectorService` by extracting:
- `_build_generation_config`: Encapsulated Gemini configuration logic.
- `_parse_and_save_plan`: Encapsulated response parsing and state saving.
- Simplified `_build_outfit_instructions` logic to be more linear and readable.
**Delta:** Code is now more modular and easier to test.

## 2026-01-15 - CinematographerService Refactor
**Observation:** `CinematographerService.generate_assets` was a long method (approx 120 lines) that handled initial keyframe generation, looping for sequential keyframes, and history management all in one place.
**Action:** Refactored `CinematographerService` by extracting:
- `_generate_keyframe_a`: Encapsulated the logic for generating the master keyframe and handling reference poses.
- `_generate_sequential_keyframes`: Encapsulated the logic for iterating through remaining scenes and managing the conversation history loop.
**Delta:** Reduced complexity of `generate_assets`, improved readability, and enabled easier testing of individual components.
