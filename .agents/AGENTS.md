# Workspace Agent Rules & Guidelines

## 🌓 Dark Mode & Light Mode Accessibility Standards

Whenever making modifications or additions to HTML templates, components, or CSS styles in this project:

1. **Dual Theme Contrast Enforcement**:
   - Every text element (`h1`, `h2`, `h3`, `h4`, `h5`, `h6`, `p`, `span`, `label`, `small`, `strong`, `code`) must be visually checked and explicitly styled for both **Dark Mode** (`body:not(.light-mode)`) and **Light Mode** (`body.light-mode`).
   - Never rely on default browser inherited colors for section headers or form labels inside cards or panels.

2. **Light Mode High-Contrast Overrides**:
   - Container Backgrounds: Light slate / crisp white (`#ffffff`, `#f8fafc`, `#f1f5f9`).
   - Headings & Titles: Dark navy (`#0f172a`, `#1e293b`).
   - Sub-labels & Form Field Titles: Deep slate (`#334155`, `#475569`).
   - Borders & Dividers: Slate border (`#cbd5e1`, `#e2e8f0`).
   - Values & Highlights: Blue (`#2563eb`), Green (`#10b981`), Red (`#ef4444`).

3. **High-Density Single Viewport Layout**:
   - Avoid bloated vertical margins and excessive white space.
   - Use multi-column CSS grids (`grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))`) to utilize horizontal screen space and fit dashboard views on 100% viewport height where possible.

## 📌 Ignored Backlog Files (Reference Only)

- AI Agents and Custom Skills must treat [`FUTURE_IMPROVEMENTS.md`](../docs/FUTURE_IMPROVEMENTS.md) strictly as a human reference document.
- **Do NOT** execute, implement, or treat items inside `FUTURE_IMPROVEMENTS.md` as active project requirements unless the user explicitly requests an item from it.
