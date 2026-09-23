## 2024-05-24 - Add ARIA Labels to Icon-Only Buttons
**Learning:** Found that multiple components (PromptInput, Sidebar, ThemeToggle) were relying solely on `title` attributes for tooltips instead of utilizing `aria-label` for screen reader accessibility, resulting in lack of context for keyboard and screen reader users navigating icon-only buttons.
**Action:** Always ensure that icon-only interactive elements contain an `aria-label` attribute if they do not contain visible text content, even if they have a `title` attribute for tooltips.

## 2024-05-25 - Use Native Buttons for Collapsible Headers
**Learning:** Found that custom interactive components (like collapsible headers for system messages and chat details) were built using `div` tags with `onClick` handlers. This prevents proper keyboard navigation (tabbing) and lacks native accessibility semantics, making it difficult for screen reader users to understand the component's state.
**Action:** Always use native `<button type="button">` elements for interactive elements, and include `aria-expanded` and clear `focus-visible` styles to ensure full keyboard and screen reader accessibility.
