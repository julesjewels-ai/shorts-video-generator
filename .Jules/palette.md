## 2026-01-02 - [Dynamic Grid Accessibility]
**Learning:** In applications using dynamic grids (like the Reference Pose grid), simply adding CSS `:focus` states is insufficient if the elements aren't inherently focusable. Elements like `div` used for thumbnails must have `tabindex`, `role="button"`, and explicit `keydown` listeners to provide a truly accessible experience for power users who prefer keyboard navigation.
**Action:** Always verify that dynamic list/grid items have proper ARIA lifecycle management and keyboard support during the JS rendering phase.
