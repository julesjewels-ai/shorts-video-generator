# Ockham's Journal

## 2026-01-11 - DirectorService Refactor
**Observation:** `DirectorService.generate_plan` was a long method (approx 70 lines) mixing configuration logic, API orchestration, and response parsing.
**Action:** Refactored `DirectorService` by extracting:
- `_build_generation_config`: Encapsulated Gemini configuration logic.
- `_parse_and_save_plan`: Encapsulated response parsing and state saving.
- Simplified `_build_outfit_instructions` logic to be more linear and readable.
**Delta:** Code is now more modular and easier to test.

## 2026-01-13 - CinematographerService Refactor
**Observation:** `CinematographerService.generate_assets` was a "Long Function" (approx 100 lines) with mixed responsibilities: initial setup, keyframe A generation with specific logic, and a loop for subsequent keyframes with different logic (history resetting).
**Action:** Refactored `CinematographerService` by extracting:
- `_generate_keyframe_a`: Encapsulated logic for the first keyframe, including reference pose handling.
- `_generate_subsequent_keyframes`: Encapsulated the loop for generating keyframes B-H, including history management.
- Simplified `generate_assets` to be a high-level orchestrator.
**Delta:** Split one large function into three focused methods. Added test coverage.
