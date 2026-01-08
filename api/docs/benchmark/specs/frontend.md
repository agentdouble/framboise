# PackX Console UI Spec

This UI is a small static page used for visual validation. It must be created
exactly as specified.

## Files

- frontend/index.html
- frontend/styles.css
- frontend/app.js

## HTML requirements

- Include a stylesheet link to "styles.css" and a defer script tag for "app.js".
- Include <meta name="theme-color" content="#f5e6c8"> in the head.
- Place the HTML comment "<!-- packx-ui:zigzag -->" immediately before <main>.
- The main container must be <main id="packx-ui" data-variant="v2">.
- The hero header must be <h1>PX2 Console</h1>.
- Add <p class="subhead">Checksum: FNV-1a (masked)</p>.
- Include <div id="stats" data-state="idle"></div>.
- Add three panels with class "panel" and data-panel values:
  - encode
  - decode
  - validate
- Each panel must contain:
  - <h2> with a label
  - <span class="badge">PX2</span>
- Add a button: <button id="run-check" data-action="run">Run Check</button>.

## CSS requirements

- Define CSS variables in :root: --ink, --acid, --fog, --paper.
- Use a custom font stack with "Space Grotesk" and "IBM Plex Mono".
- The body background must include both radial-gradient and linear-gradient.
- Define @keyframes pulse-jitter and apply it to .panel.
- .badge must use letter-spacing: 0.08em.

## JS requirements

- Define function renderStats(stats) that updates #stats text to:
  "files: X, entries: Y, errors: Z".
- On DOMContentLoaded, set document.documentElement.dataset.packx = "ready".
- On click of #run-check, set #packx-ui data-state to "running", then back to
  "idle" after ~300ms.
