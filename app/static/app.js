// EPO Board of Appeal decisions -- RAG vs GraphRAG. Vanilla JS, no build step.

const TIER_LABEL = {
  binding: "Enlarged Board (binding)",
  landmark: "landmark / OJ-published",
  distributed: "headnoted / distributed",
  routine: "routine",
};

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

// The model writes markdown (headings, **bold**, bullet lists) -- render it
// properly rather than dumping asterisks and hashes as literal text. `marked`
// converts markdown -> HTML; `DOMPurify` neutralises anything unsafe in that
// HTML before it touches the DOM (the source is an LLM completion, not a fixed
// template, so this is not optional even for a local demo).
//
// Both post-processing passes below (unverified-case-number highlighting,
// [n]-citation linking) then run on that clean HTML, never on raw text --
// sanitizing happens exactly once, before either pass, in `renderAnswerHtml`.
// Neither regex can match inside markup the other inserts (a `<span ...>` tag
// has no `[digit]` and no `letter digit/digit` substring), so the two passes
// can run in either order without corrupting each other's output.

function renderMarkdown(text) {
  const rawHtml = window.marked ? window.marked.parse(text || "") : escapeHtml(text);
  return window.DOMPurify ? window.DOMPurify.sanitize(rawHtml) : rawHtml;
}

function markUnverified(html, unverifiedCaseNumbers) {
  for (const caseNo of unverifiedCaseNumbers || []) {
    const escaped = caseNo.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = escaped.replace(/ /, "\\s?");
    html = html.replace(
      new RegExp(pattern, "g"),
      (match) => `<span class="unverified" title="Not among the retrieved sources for this answer">${match}</span>`
    );
  }
  return html;
}

function linkCitations(html) {
  return html.replace(/\[(\d+)\]/g, (match, n) =>
    `<span class="cite" data-n="${n}" title="Jump to source ${n}">${match}</span>`
  );
}

function renderAnswerHtml(text, unverifiedCaseNumbers, { linkCites } = {}) {
  let html = renderMarkdown(text);
  html = markUnverified(html, unverifiedCaseNumbers);
  if (linkCites) html = linkCitations(html);
  return html;
}

const GROUP_LABEL = { pharma: "Pharma generics", examiner: "EPO examiner" };

async function loadExamples() {
  const chipsEl = document.getElementById("chips");
  try {
    const res = await fetch("/api/examples");
    const examples = await res.json();
    chipsEl.innerHTML = "";
    for (const [group, questions] of Object.entries(examples)) {
      const label = document.createElement("span");
      label.className = "chip-group-label";
      label.textContent = GROUP_LABEL[group] || group;
      chipsEl.appendChild(label);
      for (const q of questions) {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = q.length > 70 ? q.slice(0, 68) + "…" : q;
        chip.title = q;
        chip.addEventListener("click", () => {
          document.getElementById("question").value = q;
          document.getElementById("ask-form").requestSubmit();
        });
        chipsEl.appendChild(chip);
      }
    }
  } catch (err) {
    chipsEl.innerHTML = '<span class="chips-loading">Could not load example questions.</span>';
  }
}

function renderBaseline(result) {
  const el = document.getElementById("baseline-column");
  const answerHtml = renderAnswerHtml(result.answer, result.unverifiedCaseNumbers);

  const chunksHtml = (result.chunks || [])
    .map(
      (c) => `<li class="chunk-item">
        <div class="score">similarity ${c.score.toFixed(3)} &middot; ${escapeHtml(c.citation || c.id)}</div>
        <div class="snippet">${escapeHtml((c.text || "").slice(0, 220))}${(c.text || "").length > 220 ? "…" : ""}</div>
      </li>`
    )
    .join("");

  const unverified = result.unverifiedCaseNumbers && result.unverifiedCaseNumbers.length > 0;

  el.innerHTML = `
    <h2>Vector-only RAG <span class="score" style="float:right">${result.elapsedMs} ms</span></h2>
    <div class="answer-text">${answerHtml}</div>
    <div class="validation-line ${unverified ? "bad" : "ok"}">
      ${unverified
        ? `Mentions ${result.unverifiedCaseNumbers.length} case number(s) not found in the retrieved passages -- cannot be verified.`
        : "No case numbers mentioned outside the retrieved passages (structurally, still not proof the prose is faithful to them)."}
    </div>
    <div class="section-label">Retrieved passages (flat, no structure)</div>
    <ul class="chunk-list">${chunksHtml}</ul>
  `;
}

function tierBadge(tier) {
  if (!tier) return "";
  return `<span class="badge tier-${tier}">${escapeHtml(TIER_LABEL[tier] || tier)}</span>`;
}

function outcomeBadge(outcomeType) {
  if (!outcomeType) return "";
  return `<span class="badge outcome">${escapeHtml(outcomeType.replace(/_/g, " "))}</span>`;
}

function renderSourceCardBody(s) {
  const grounds = (s.grounds || [])
    .filter((g) => g.label)
    .map((g) => `${escapeHtml(g.label)} — ${g.met === true ? "met" : g.met === false ? "not met" : "undetermined"}`)
    .join("<br>");
  const cites = [
    ...((s.citedCases || []).filter(Boolean)),
    ...((s.articles || []).map((a) => a.label || a.code).filter(Boolean)),
  ].join(" &middot; ");

  return `
    <p><strong>${escapeHtml(s.caseNumber || s.reference)}</strong> &mdash; ${escapeHtml(s.citation || "")}</p>
    <p>${tierBadge(s.authorityTier)}${outcomeBadge(s.outcomeType)}</p>
    <p>Board ${escapeHtml(s.boardCode || "unknown")} &middot; decided ${escapeHtml(s.decisionDate || "unknown")}
       &middot; cited ${s.timesCited || 0}x in this corpus</p>
    <p>${escapeHtml(s.authorityReason || "")}</p>
    ${grounds ? `<p>${grounds}</p>` : ""}
    ${cites ? `<p>Cites: ${cites}</p>` : ""}
    <p>Found by: ${(s.channels || []).map(escapeHtml).join(", ") || "unknown"}</p>
    <div class="text-block">${escapeHtml(s.text || "")}</div>
  `;
}

function openDetail(html) {
  document.getElementById("detail-card").innerHTML =
    `<span class="close-btn" id="detail-close">&times;</span>` + html;
  document.getElementById("detail-overlay").classList.remove("hidden");
  document.getElementById("detail-close").addEventListener("click", closeDetail);
}

function closeDetail() {
  document.getElementById("detail-overlay").classList.add("hidden");
}

let currentGraphNetwork = null;
let currentSources = [];

function focusSourceCard(n) {
  document.querySelectorAll(".source-item").forEach((el) => el.classList.remove("focused"));
  document.querySelectorAll(".cite").forEach((el) => el.classList.remove("focused"));
  const card = document.querySelector(`.source-item[data-n="${n}"]`);
  if (card) {
    card.classList.add("focused");
    card.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  document.querySelectorAll(`.cite[data-n="${n}"]`).forEach((el) => el.classList.add("focused"));
  if (currentGraphNetwork) {
    const source = currentSources.find((s) => s.n === n);
    if (source) {
      const nodeId = `decision:${source.reference}`;
      try {
        currentGraphNetwork.selectNodes([nodeId]);
        currentGraphNetwork.focus(nodeId, { scale: 1.1, animation: { duration: 400 } });
      } catch (e) { /* node may not be in the "cited only" graph -- fine */ }
    }
  }
}

// Needle's graph-node fill palette (tokens/data-viz.css --node-1..12) --
// softer and more saturated than the chart series, built for exactly this:
// node fills in a graph visualisation, used in a fixed order rather than
// picked for aesthetics. Text on every fill is dark (#1A1B1D per the design
// system's own graph-node specimen) since all twelve are light/mid-tone.
const NODE_INK = "#1A1B1D";
function renderGraph(graph) {
  const container = document.getElementById("graph-panel");
  const typeStyle = {
    Decision: { shape: "box", color: { background: "#4D8DDA", border: "#2f5fb3" }, font: { color: "#FFFFFF" } },
    Paragraph: { shape: "ellipse", color: { background: "#56C7E4", border: "#2f92a6" }, font: { color: NODE_INK } },
    Board: { shape: "star", color: { background: "#FFC354", border: "#c98f1f" }, font: { color: NODE_INK } },
    Outcome: { shape: "hexagon", color: { background: "#D8C7AE", border: "#a9906a" }, font: { color: NODE_INK } },
    Ground: { shape: "triangle", color: { background: "#8DCC93", border: "#4a9451" }, font: { color: NODE_INK } },
    Case: { shape: "diamond", color: { background: "#F16767", border: "#c93c3c" }, font: { color: "#FFFFFF" } },
    Article: { shape: "square", color: { background: "#FFDF81", border: "#c9a227" }, font: { color: NODE_INK } },
  };

  const nodes = new vis.DataSet(
    graph.nodes.map((n) => ({
      id: n.id,
      label: n.label && n.label.length > 22 ? n.label.slice(0, 20) + "…" : n.label,
      title: n.text ? n.text.slice(0, 300) : n.label,
      ...(typeStyle[n.type] || {}),
    }))
  );
  const edges = new vis.DataSet(
    graph.edges.map((e, i) => ({
      id: i,
      from: e.source,
      to: e.target,
      label: e.type,
      font: { size: 9, color: "#4D5157", align: "middle" }, // --text-weak
      color: { color: "#BBBEC3" }, // --border-strong
      arrows: "to",
    }))
  );

  currentGraphNetwork = new vis.Network(
    container,
    { nodes, edges },
    {
      layout: { improvedLayout: true },
      physics: { stabilization: true, barnesHut: { springLength: 110 } },
      interaction: { hover: true },
    }
  );

  currentGraphNetwork.on("click", (params) => {
    if (!params.nodes.length) return;
    const node = graph.nodes.find((n) => n.id === params.nodes[0]);
    if (!node) return;
    if (node.type === "Decision") {
      const source = currentSources.find((s) => `decision:${s.reference}` === node.id);
      if (source) {
        focusSourceCard(source.n);
        openDetail(renderSourceCardBody(source));
        return;
      }
    }
    openDetail(`<h3>${escapeHtml(node.label)}</h3><p>${escapeHtml(node.type)}</p>
      ${node.text ? `<div class="text-block">${escapeHtml(node.text)}</div>` : ""}
      ${node.outcomeType ? `<p>outcome: ${escapeHtml(node.outcomeType)}</p>` : ""}`);
  });
}

function renderGraphrag(result) {
  const el = document.getElementById("graphrag-column");
  currentSources = result.sources || [];

  const v = result.validation || {};
  const answerHtml = v.refused
    ? `<div class="refused-banner">${escapeHtml(result.answer)}</div>` +
      (result.rawAnswer
        ? `<details class="raw-answer"><summary>Show the original ungrounded answer</summary>` +
          `${renderAnswerHtml(result.rawAnswer, v.unverifiedCaseNumbers, { linkCites: true })}</details>`
        : "")
    : renderAnswerHtml(result.answer, v.unverifiedCaseNumbers, { linkCites: true });

  const validationClass = v.refused ? "bad"
    : v.citationsInRange && (!v.unverifiedCaseNumbers || v.unverifiedCaseNumbers.length === 0)
    ? "ok" : v.citationsInRange ? "warn" : "bad";
  const validationText = v.refused
    ? `Answer refused &mdash; ${v.unverifiedCaseNumbers.length} case number(s) cited outside the ` +
      `retrieved sources for this question`
    : `${v.citationsFound || 0} citation(s) found, all resolve to real graph nodes` +
      (v.unverifiedCaseNumbers && v.unverifiedCaseNumbers.length
        ? ` &mdash; but mentions ${v.unverifiedCaseNumbers.length} case number(s) outside the provided sources`
        : "");

  const sourcesHtml = currentSources
    .map((s) => {
      const notCited = !s.cited ? '<div class="not-cited">retrieved, not cited in the final answer</div>' : "";
      return `<li class="source-item" data-n="${s.n}">
        <div><strong>[${s.n}]</strong> ${escapeHtml(s.citation || s.caseNumber)}
          ${tierBadge(s.authorityTier)}${outcomeBadge(s.outcomeType)}</div>
        <div class="score">Board ${escapeHtml(s.boardCode || "?")} &middot; ${escapeHtml(s.decisionDate || "?")}
          &middot; cited ${s.timesCited || 0}x</div>
        <div class="snippet">${escapeHtml((s.text || "").slice(0, 180))}${(s.text || "").length > 180 ? "…" : ""}</div>
        ${notCited}
      </li>`;
    })
    .join("");

  const explainHtml = Object.entries(result.retrievalExplain || {})
    .map(([channel, count]) => `<div><strong>${escapeHtml(channel)}</strong>: ${count} decisions found</div>`)
    .join("") || "<div>No channel breakdown available.</div>";

  el.innerHTML = `
    <h2>GraphRAG <span class="score" style="float:right">${result.elapsedMs} ms</span></h2>
    <div class="answer-text">${answerHtml}</div>
    <div class="validation-line ${validationClass}">${validationText}</div>
    <div class="graph-panel" id="graph-panel"></div>
    <div class="section-label">Sources (click a [n] above, or a card below)</div>
    <ul class="source-list">${sourcesHtml}</ul>
    <div class="explain-toggle" id="explain-toggle">Show retrieval channel breakdown</div>
    <div class="explain-panel" id="explain-panel">${explainHtml}</div>
  `;

  renderGraph(result.graph);

  el.querySelectorAll(".cite").forEach((span) => {
    span.addEventListener("click", () => focusSourceCard(Number(span.dataset.n)));
  });
  el.querySelectorAll(".source-item").forEach((item) => {
    item.addEventListener("click", () => {
      const n = Number(item.dataset.n);
      const source = currentSources.find((s) => s.n === n);
      focusSourceCard(n);
      if (source) openDetail(renderSourceCardBody(source));
    });
  });
  const explainToggle = document.getElementById("explain-toggle");
  explainToggle.addEventListener("click", () => {
    const open = document.getElementById("explain-panel").classList.toggle("open");
    explainToggle.textContent = open
      ? "Hide retrieval channel breakdown"
      : "Show retrieval channel breakdown";
  });
}

function renderDeep(result) {
  const el = document.getElementById("deep-column");

  const answerHtml = result.refused
    ? `<div class="refused-banner">${escapeHtml(result.answer)}</div>` +
      (result.rawAnswer
        ? `<details class="raw-answer"><summary>Show the original ungrounded answer</summary>` +
          `${renderMarkdown(result.rawAnswer)}</details>`
        : "")
    : renderMarkdown(result.answer);

  const topicsHtml = (result.topicCards || [])
    .map((c) => `<div class="topic-card">
        <div class="topic-label">${escapeHtml(c.topic_label)}</div>
        <div class="topic-summary">${escapeHtml(c.doctrine_summary)}</div>
      </div>`)
    .join("") || "<div>No topics produced.</div>";

  const unsupported = (result.faithfulness || []).filter((v) => !v.supported);
  const faithfulnessHtml = (result.faithfulness || [])
    .map((v) => `<li class="${v.supported ? "ok" : "bad"}">
        <strong>${escapeHtml(v.case_number)}</strong> -- ${v.supported ? "supported" : "unsupported"}:
        ${escapeHtml(v.reason)}
      </li>`)
    .join("") || "<li>No citations checked.</li>";

  const retrievalHtml = (result.retrievalIterations || [])
    .map((it) => `<div>round ${it.round}: ${it.seedCount} seeds, sufficient=${it.assessment.sufficient}
        -- ${escapeHtml(it.assessment.reason)}</div>`)
    .join("") || "<div>No retrieval rounds recorded.</div>";

  el.innerHTML = `
    <h2>Deep multi-agent analysis <span class="score" style="float:right">${result.elapsedMs} ms</span></h2>
    <div class="answer-text">${answerHtml}</div>
    <div class="validation-line ${result.refused ? "bad" : unsupported.length ? "warn" : "ok"}">
      ${result.faithfulness.length} citation(s) checked by the faithfulness critic,
      ${unsupported.length} unsupported${result.redrafts ? ` (after ${result.redrafts} redraft attempt(s))` : ""}
    </div>
    <div class="section-label">Topic cards (Leiden-detected clusters, one summarizer agent each)</div>
    ${topicsHtml}
    <div class="explain-toggle" id="deep-explain-toggle">Show retrieval rounds and faithfulness verdicts</div>
    <div class="explain-panel" id="deep-explain-panel">
      <div class="section-label">Iterative retrieval</div>
      ${retrievalHtml}
      <div class="section-label">Faithfulness verdicts</div>
      <ul>${faithfulnessHtml}</ul>
    </div>
  `;

  const toggle = document.getElementById("deep-explain-toggle");
  toggle.addEventListener("click", () => {
    const open = document.getElementById("deep-explain-panel").classList.toggle("open");
    toggle.textContent = open ? "Hide retrieval rounds and faithfulness verdicts"
                               : "Show retrieval rounds and faithfulness verdicts";
  });
}

async function askDeep() {
  const question = document.getElementById("question").value.trim();
  if (!question) return;
  const button = document.getElementById("deep-button");
  button.disabled = true;
  const originalText = button.textContent;
  button.innerHTML = '<span class="spinner"></span>Running (this takes 1-2 minutes)…';
  document.getElementById("deep-column").innerHTML =
    '<h2>Deep multi-agent analysis</h2><div class="empty-state"><span class="spinner"></span>' +
    'Assessing retrieval, inducing subgraph, running Leiden, summarizing topics, ' +
    'synthesizing, checking faithfulness…</div>';
  try {
    const res = await fetch("/api/ask/deep", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderDeep(data.deep);
  } catch (err) {
    document.getElementById("deep-column").innerHTML =
      `<h2>Deep multi-agent analysis</h2><div class="empty-state">Request failed: ${escapeHtml(err.message)}</div>`;
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

function renderCaveats(caveats) {
  if (!caveats || !caveats.length) return;
  document.getElementById("caveats").innerHTML =
    caveats.map((c) => `<p>${escapeHtml(c)}</p>`).join("");
}

function setLoading(isLoading) {
  const button = document.getElementById("ask-button");
  button.disabled = isLoading;
  button.innerHTML = isLoading ? '<span class="spinner"></span>Asking…' : "Ask";
  if (isLoading) {
    document.getElementById("baseline-column").innerHTML =
      '<h2>Vector-only RAG</h2><div class="empty-state"><span class="spinner"></span>Retrieving and generating…</div>';
    document.getElementById("graphrag-column").innerHTML =
      '<h2>GraphRAG</h2><div class="empty-state"><span class="spinner"></span>Retrieving, expanding the graph, and generating…</div>';
  }
}

async function ask(question) {
  setLoading(true);
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderBaseline(data.baseline);
    renderGraphrag(data.graphrag);
    renderCaveats(data.caveats);
  } catch (err) {
    document.getElementById("baseline-column").innerHTML =
      `<h2>Vector-only RAG</h2><div class="empty-state">Request failed: ${escapeHtml(err.message)}</div>`;
    document.getElementById("graphrag-column").innerHTML =
      `<h2>GraphRAG</h2><div class="empty-state">Request failed: ${escapeHtml(err.message)}</div>`;
  } finally {
    setLoading(false);
  }
}

document.getElementById("ask-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const question = document.getElementById("question").value.trim();
  if (question) {
    ask(question);
    document.getElementById("deep-button").disabled = false;
  }
});

document.getElementById("deep-button").addEventListener("click", askDeep);

document.getElementById("detail-overlay").addEventListener("click", (e) => {
  if (e.target.id === "detail-overlay") closeDetail();
});

loadExamples();
