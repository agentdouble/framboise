# Frontend Quirks (Required)

These quirks are required and intentionally odd.

- The HTML comment "<!-- packx-ui:zigzag -->" must appear immediately before
  the <main> element.
- <main id="packx-ui"> must include data-variant="v2".
- #stats must start with data-state="idle".
- document.documentElement.dataset.packx must be set to "ready" on load.
- The theme color must be exactly "#f5e6c8".
