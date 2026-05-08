const data = window.PATTERN_APP_DATA;

const state = { index: 0, answers: Array(data.questions.length).fill(null), events: [], scores: {} };
Object.keys(data.patterns).forEach((k) => (state.scores[k] = 0));

const el = (id) => document.getElementById(id);
const views = { landing: el("landing"), quiz: el("quiz"), result: el("result") };

function show(view) {
  Object.values(views).forEach((v) => v.classList.remove("panel--active"));
  views[view].classList.add("panel--active");
}

function renderQuestion() {
  const q = data.questions[state.index];
  el("question-title").textContent = `Scenario ${state.index + 1}`;
  el("question-scenario").textContent = q.q;
  el("progress-label").textContent = `Question ${state.index + 1} of ${data.questions.length}`;
  el("progress-bar").style.width = `${((state.index + 1) / data.questions.length) * 100}%`;

  const form = el("answers-form");
  form.innerHTML = `
    <fieldset class="answer-group">
      <legend class="sr-only">Choose one option</legend>
      ${q.options
        .map((opt, i) => `<label class="answer-option"><input type="radio" name="answer" value="${i}" ${state.answers[state.index] === i ? "checked" : ""}> ${opt.text}</label>`)
        .join("")}
    </fieldset>
  `;

  el("next-btn").disabled = state.answers[state.index] === null;
  el("back-btn").disabled = state.index === 0;
  form.onchange = () => {
    const picked = document.querySelector('input[name="answer"]:checked');
    state.answers[state.index] = picked ? Number(picked.value) : null;
    el("next-btn").disabled = state.answers[state.index] === null;
  };
}

function recomputeScores() {
  Object.keys(state.scores).forEach((k) => (state.scores[k] = 0));
  state.events = [];
  state.answers.forEach((picked, qi) => {
    if (picked === null) return;
    const opt = data.questions[qi].options[picked];
    state.scores[opt.primary] += 2;
    state.events.push({ pattern: opt.primary, t: state.events.length });
    state.scores[opt.secondary] += 1;
    state.events.push({ pattern: opt.secondary, t: state.events.length });
  });
}

function topTwo() {
  const latest = {};
  state.events.forEach((e) => (latest[e.pattern] = e.t));
  return Object.keys(state.scores)
    .sort((a, b) => state.scores[b] - state.scores[a] || (latest[b] ?? -1) - (latest[a] ?? -1))
    .slice(0, 2);
}

function resultCode() {
  return state.answers.map((answer) => (answer === null ? "x" : String(answer))).join("");
}

function resultUrl() {
  const url = new URL(window.location.href);
  url.searchParams.set("answers", resultCode());
  url.hash = "result";
  return url.toString();
}

function hydrateSharedAnswers() {
  const params = new URLSearchParams(window.location.search);
  const answerCode = params.get("answers");
  if (!answerCode || answerCode.length !== data.questions.length || /[^0-2]/.test(answerCode)) return false;

  const answers = [...answerCode].map(Number);
  const isValid = answers.every((answer, index) => data.questions[index].options[answer]);
  if (!isValid) return false;

  state.answers = answers;
  state.index = data.questions.length;
  renderResult();
  show("result");
  return true;
}

function fullResultText(primary, secondary, resultLink) {
  const p = data.patterns[primary];
  return [
    "What’s Your Play Pattern?",
    "",
    `Primary: ${primary}`,
    p.summary,
    "",
    `Secondary: ${secondary}`,
    "",
    "Your strength:",
    p.strength,
    "",
    "Try this next:",
    p.next,
    "",
    "Read the full result and explore nnherit:",
    resultLink,
  ].join("\n");
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.top = "-999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

function renderResult() {
  recomputeScores();
  const [primary, secondary] = topTwo();
  const p = data.patterns[primary];
  el("primary-name").textContent = primary;
  el("primary-summary").textContent = p.summary;
  el("secondary-name").textContent = secondary;
  el("result-disclaimer").textContent = data.shared.disclaimer;
  el("shared-cta-copy").textContent = data.shared.cta;

  el("result-details").innerHTML = `
    <p>${p.description.replace(/\n\n/g, "</p><p>")}</p>
    <details class="result-section" open><summary>Your strength</summary><p>${p.strength}</p></details>
    <details class="result-section"><summary>Your danger zone</summary><p>${p.danger}</p></details>
    <details class="result-section"><summary>Try this next</summary><p>${p.next}</p></details>
    <details class="result-section"><summary>Good pairings</summary><p>${p.pairings}</p></details>
    <details class="result-section"><summary>nnherit bridge</summary><p>${p.bridge}</p></details>
  `;

  el("score-note").textContent = "Scoring: each answer gives +2 to one pattern and +1 to a second pattern. Ties are resolved by the most recently scored pattern.";

  el("share-btn").onclick = async () => {
    const link = resultUrl();
    const text = fullResultText(primary, secondary, link);

    if (navigator.share) {
      try {
        await navigator.share({ title: "What’s Your Play Pattern?", text, url: link });
        return;
      } catch (error) {
        if (error.name === "AbortError") return;
      }
    }

    await copyText(text);
    alert("Full result and direct result link copied to clipboard.");
  };
}

el("start-btn").onclick = () => { show("quiz"); renderQuestion(); };
el("next-btn").onclick = () => {
  if (state.answers[state.index] === null) return;
  state.index += 1;
  if (state.index < data.questions.length) renderQuestion();
  else { renderResult(); show("result"); }
};
el("back-btn").onclick = () => {
  if (state.index === 0) return;
  state.index -= 1;
  renderQuestion();
};
el("restart-btn").onclick = () => {
  const url = new URL(window.location.href);
  url.searchParams.delete("answers");
  url.hash = "";
  window.location.href = url.toString();
};

el("email-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = el("email");
  const status = el("email-status");

  if (!input.checkValidity()) {
    status.textContent = "Please enter a valid email address first.";
    input.focus();
    return;
  }

  localStorage.setItem("playPatternFieldGuideRequest", JSON.stringify({ email: input.value, requestedAt: new Date().toISOString() }));
  status.textContent = "Thanks — request confirmed. Opening the field guide now.";

  window.setTimeout(() => {
    window.open(data.shared.fieldGuidePdfUrl, "_blank", "noopener");
  }, 650);
});

el("field-guide-download").href = data.shared.fieldGuidePdfUrl;

hydrateSharedAnswers();
