# What’s Your Play Pattern? (nnherit)

A mobile-first, static web app that helps facilitators and playful practitioners discover their **primary** and **secondary** Play Pattern in about 3 minutes.

## What this app does

- Presents a landing screen and 10 scenario-based multiple-choice questions.
- Calculates scores locally in the browser (no backend, no login, no database).
- Shows a result page with full copy for all 12 Play Patterns.
- Includes a screenshot/share-friendly result card.
- Includes a direct download link to the hosted field guide PDF; no email service or form is required.

## Project files

- `index.html` – semantic structure and app sections.
- `styles.css` – mobile-first visual design and responsive layout.
- `patterns.js` – editable source of truth for:
  - all 12 pattern result copy,
  - shared CTA/disclaimer,
  - all questions/answers/scoring mappings.
- `app.js` – app state, rendering, scoring, tie-break logic.
- `field-guide.pdf` – downloadable branded 12-pattern field guide linked from the result page.
- `tools/generate_field_guide.py` – standard-library PDF generator that rebuilds `field-guide.pdf` from `patterns.js`.

## How to edit questions

Open `patterns.js` and edit `window.PATTERN_APP_DATA.questions`.

Each question object looks like:

```js
{
  q: "Question text",
  options: [
    { text: "Answer A", primary: "Pattern Name", secondary: "Pattern Name" },
    { text: "Answer B", primary: "Pattern Name", secondary: "Pattern Name" },
    { text: "Answer C", primary: "Pattern Name", secondary: "Pattern Name" }
  ]
}
```

Use exact pattern names from `window.PATTERN_APP_DATA.patterns` keys.

## How scoring works

- Every selected answer gives:
  - **+2** to its `primary` pattern
  - **+1** to its `secondary` pattern
- After question 10:
  - Highest total score = **primary pattern**
  - Second highest total score = **secondary pattern**
- Tie-break rule:
  - If scores are equal, the pattern that received points **most recently** ranks higher.

Tie-break is implemented by tracking every scoring event in sequence and comparing the latest event timestamp per pattern.

## Deploy on GitHub Pages

1. Push this project to a GitHub repository.
2. In GitHub, go to **Settings → Pages**.
3. Under **Build and deployment**:
   - **Source**: `Deploy from a branch`
   - **Branch**: `main` (or your default), folder `/ (root)`
4. Save and wait for Pages to publish.
5. Your site URL appears in the Pages settings panel.

## Embed in Google Sites

After deploying:

1. Open your Google Site in edit mode.
2. Click **Insert → Embed**.
3. Choose **By URL** and paste the GitHub Pages URL.
4. Click **Insert**.
5. Resize the embed block for mobile-friendly visibility.
6. Publish your Google Site.

Tip: Keep enough vertical height so question choices and result card are fully visible on phones.
