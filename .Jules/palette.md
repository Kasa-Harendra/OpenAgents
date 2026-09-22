## 2024-05-24 - Add ARIA Labels to Icon-Only Buttons
**Learning:** Found that multiple components (PromptInput, Sidebar, ThemeToggle) were relying solely on `title` attributes for tooltips instead of utilizing `aria-label` for screen reader accessibility, resulting in lack of context for keyboard and screen reader users navigating icon-only buttons.
**Action:** Always ensure that icon-only interactive elements contain an `aria-label` attribute if they do not contain visible text content, even if they have a `title` attribute for tooltips.
