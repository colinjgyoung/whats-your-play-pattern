# What’s Your Play Pattern? (nnherit)

A mobile-first, static web app that helps facilitators and playful practitioners discover their **primary** and **secondary** Play Pattern in about 3 minutes.

## What this app does

- Presents a landing screen and 10 scenario-based multiple-choice questions.
- Calculates scores locally in the browser (no backend, no login, no database).
- Shows a result page with full copy for all 12 Play Patterns.
- Includes a screenshot/share-friendly result card.
- Includes a static email-confirmation section that opens a hosted field guide PDF. It does not send email or collect addresses server-side unless you connect a third-party form/email service.

## Project files

- `index.html` – semantic structure and app sections.
- `styles.css` – mobile-first visual design and responsive layout.
- `patterns.js` – editable source of truth for:
  - all 12 pattern result copy,
  - shared CTA/disclaimer,
  - all questions/answers/scoring mappings.
- `app.js` – app state, rendering, scoring, tie-break logic.
- `field-guide.pdf` – downloadable branded 12-pattern field guide opened by the email confirmation flow.
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

## Result sharing and direct result links

The **Share result** button does not try to upload a screenshot or PDF because this is a static site with no backend. Instead it creates a direct result URL using the user’s answer choices, for example:

```text
https://your-site.github.io/whats-your-play-pattern/?answers=0120120120#result
```

When someone opens that link, the app rebuilds the same result page locally in the browser so they can read the full result and click through to nnherit.

On mobile, the button opens the native share sheet when supported. On desktop, it copies a fuller result summary plus the direct result link to the clipboard.

## Field guide PDF and email form setup

The repository includes `field-guide.pdf`, a branded complete 12-pattern guide generated from the pattern copy in `patterns.js`.

This app is still fully static, so GitHub Pages **cannot send emails or collect email addresses into a database by itself**. The current form:

- validates that an email address was entered,
- shows an on-page confirmation message,
- stores the request only in the visitor’s own browser local storage,
- opens the configured field guide PDF in a new tab.

To host the PDF on GitHub Pages:

1. Keep `field-guide.pdf` in the project root, or replace it with your final edited PDF using the same filename.
2. Commit and push the PDF with the rest of the site.
3. GitHub Pages will publish it at:

   ```text
   https://your-site.github.io/your-repo/field-guide.pdf
   ```

If you want to put the PDF somewhere else, update this value in `patterns.js`:

```js
fieldGuidePdfUrl: "field-guide.pdf"
```

For real email collection or automated email delivery, connect the form to a static-friendly form service such as Formspree, Basin, Netlify Forms, ConvertKit, Mailchimp, or another email platform.


## Regenerate the field guide PDF

The included PDF is generated from the result copy in `patterns.js`, plus a branded cover, usage notes, and a closing nnherit CTA. To regenerate it after editing pattern copy, run:

```bash
python3 tools/generate_field_guide.py
```

The script uses Python standard library PDF writing and Node only to read the existing `patterns.js` data object. It overwrites `field-guide.pdf`.
