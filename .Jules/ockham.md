# Ockham's Journal

## 2026-01-11 - DirectorService Refactor
**Observation:** `DirectorService.generate_plan` was a long method (approx 70 lines) mixing configuration logic, API orchestration, and response parsing.
**Action:** Refactored `DirectorService` by extracting:
- `_build_generation_config`: Encapsulated Gemini configuration logic.
- `_parse_and_save_plan`: Encapsulated response parsing and state saving.
- Simplified `_build_outfit_instructions` logic to be more linear and readable.
**Delta:** Code is now more modular and easier to test.

## 2026-01-12 - CinematographerService Refactor
**Observation:** `CinematographerService.generate_assets` was a "Long Function" (approx 120 lines) containing mixed abstractions: loading assets, API calls for the master shot, and a complex loop for sequential edits with special history management.
**Action:** Refactored `CinematographerService` by extracting:
- `_generate_keyframe_a`: Encapsulated master shot generation and reference pose handling.
- `_generate_sequential_keyframes`: Encapsulated the loop for subsequent scenes and history management.
**Delta:** significantly improved readability and separation of concerns. Added unit tests where none existed.
