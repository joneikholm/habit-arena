// Habit Arena front end: plain JS, no build step.
const $ = (id) => document.getElementById(id);
const state = {
  tab: "log",          // "log" | "results"
  view: "live",        // results view: "live" | "backtest"
  dataset: "own",      // backtest data: "own" | "synthetic"
  cfg: null,           // your own config (the Log page always uses it)
  exclude: { live: new Set(), backtest: new Set() },
};
let chart = null;
const COLORS = ["#2f6fde", "#e07b39", "#1e8e4e", "#9b59b6", "#c0392b", "#16a2b8", "#8a6d3b", "#555"];

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

function showError(err) {
  $("error").hidden = !err;
  $("error").textContent = err ? String(err.message || err) : "";
}

const fmt = (v) => (v === null || v === undefined ? "–" : Number(v).toFixed(2));

function parseNumber(text) {
  const v = Number(String(text).trim().replace(",", "."));
  return text.trim() === "" || Number.isNaN(v) ? null : v;
}

function toggle(selector, attr, value) {
  document.querySelectorAll(selector).forEach((b) => b.classList.toggle("on", b.dataset[attr] === value));
}

// ---------- navigation ----------

function setTab(tab) {
  state.tab = tab;
  toggle("#tabs button", "tab", tab);
  $("tab-log").hidden = tab !== "log";
  $("tab-results").hidden = tab !== "results";
  showError(null);
  if (tab === "log") showLog();
  else showResults();
}

function showLog() {
  $("log-view").hidden = false;
  $("fields-view").hidden = true;
  renderLog();
}

function showFields() {
  $("log-view").hidden = true;
  $("fields-view").hidden = false;
  startEditor();
}

function setView(view) {
  state.view = view;
  toggle("[data-view]", "view", view);
  $("live-only").hidden = view !== "live";
  $("backtest-only").hidden = view !== "backtest";
  $("live-log-box").hidden = view !== "live";
  showResults();
}

async function setDataset(ds) {
  state.dataset = ds;
  toggle("[data-dataset]", "dataset", ds);
  $("seed-box").hidden = ds !== "synthetic";
  if (ds === "synthetic" && !$("hidden-rule").textContent) {
    const synth = await api("/api/config?dataset=synthetic");
    $("hidden-rule").textContent = synth.hidden_rule;
  }
  showResults();
}

function showResults() {
  if (state.view === "live") renderLive();
  else clearBacktest();
}

// ---------- fields editor ----------

const ROLLUPS = {
  number: ["last", "sum", "mean", "max", "min", "count"],
  scale: ["last", "mean", "max", "min"],
  yesno: ["last", "max", "min", "count"],
  choice: ["last", "min", "max"],
};
const ROLLUP_HELP = {
  last: "once a day (new replaces old)", sum: "add up (total)", mean: "average",
  max: "highest", min: "lowest", count: "count entries",
};
const TYPE_HELP = {
  number: "number (typed)", scale: "scale (tap a number)", yesno: "yes / no", choice: "choice (named options)",
};
let draft = null;

function startEditor() {
  draft = structuredClone({ student: state.cfg.student, target: state.cfg.target, fields: state.cfg.fields });
  renderEditor();
}

function changed() {
  const saved = JSON.stringify({ student: state.cfg.student, target: state.cfg.target, fields: state.cfg.fields });
  const dirty = JSON.stringify(draft) !== saved;
  $("cfg-save").disabled = !dirty;
  $("cfg-undo").disabled = !dirty;
  $("cfg-msg").textContent = dirty ? "Unsaved changes." : "";
}

const toName = (text) => text.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");

function input(type, value, onchange, disabled) {
  const el = document.createElement("input");
  el.type = type;
  el.value = value ?? "";
  el.disabled = !!disabled;
  if (type === "text") el.className = "wide";
  el.onchange = () => { onchange(el.value); changed(); };
  return el;
}

function select(values, value, onchange, disabled, help) {
  const el = document.createElement("select");
  for (const v of values) {
    const o = document.createElement("option");
    o.value = v;
    o.textContent = help ? help[v] : v;
    el.append(o);
  }
  el.value = value;
  el.disabled = !!disabled;
  el.onchange = () => { onchange(el.value); changed(); renderEditor(); };
  return el;
}

function labelled(text, el) {
  const l = document.createElement("label");
  const s = document.createElement("span");
  s.textContent = text;
  l.append(s, el);
  return l;
}

function setType(f, type) {
  for (const k of ["min", "max", "options", "ordered"]) delete f[k];
  f.type = type;
  if (type === "number") Object.assign(f, { min: 0, max: 10 });
  if (type === "scale") Object.assign(f, { min: 1, max: 10 });
  if (type === "choice") Object.assign(f, { options: ["low", "medium", "high"], ordered: true });
  f.rollup = ROLLUPS[type][0];
}

function renderEditor() {
  const counts = state.cfg.entry_counts || {};
  const anyData = Object.values(counts).some((n) => n > 0);
  const student = $("cfg-student");
  student.value = draft.student;
  student.disabled = anyData;
  student.onchange = () => { draft.student = student.value.trim(); changed(); };
  $("cfg-student-note").textContent = anyData
    ? "Locked: your entries are stored under this name."
    : "Never your real name.";
  const grid = $("cfg-fields");
  grid.innerHTML = "";
  draft.fields.forEach((f, idx) => {
    const n = counts[f.name] || 0;
    const saved = state.cfg.fields.some((g) => g.name === f.name);
    const locked = saved && n > 0;
    const card = document.createElement("div");
    card.className = "card";
    const h = document.createElement("h3");
    h.textContent = f.name ? pretty(f.name) : "(new field)";
    const del = document.createElement("button");
    del.textContent = "Delete";
    del.className = "danger";
    del.onclick = () => {
      draft.fields.splice(idx, 1);
      if (draft.target === f.name) draft.target = "";
      renderEditor();
      changed();
    };
    h.append(del);
    card.append(h);
    card.append(labelled("Name", input("text", f.name, (v) => {
      const old = f.name;
      f.name = toName(v);
      if (draft.target === old) draft.target = f.name;
      renderEditor();
    }, locked)));
    card.append(labelled("Type", select(Object.keys(TYPE_HELP), f.type, (v) => setType(f, v), locked, TYPE_HELP)));
    if (f.type === "number" || f.type === "scale") {
      const range = document.createElement("div");
      range.className = "row";
      const num = (k) => input("number", f[k], (v) => { f[k] = Number(String(v).replace(",", ".")); });
      range.append(labelled("Lowest", num("min")), labelled("Highest", num("max")));
      card.append(range);
    }
    if (f.type === "choice") {
      card.append(labelled("Options", input("text", f.options.join(", "), (v) => {
        f.options = v.split(",").map(toName).filter(Boolean);
        renderEditor();
      }, locked)));
      const ord = document.createElement("input");
      ord.type = "checkbox";
      ord.checked = f.ordered;
      ord.disabled = locked;
      ord.onchange = () => {
        f.ordered = ord.checked;
        if (!f.ordered) f.rollup = "last";
        changed();
        renderEditor();
      };
      card.append(labelled("Ordered", ord));
      const hint = document.createElement("div");
      hint.className = "note";
      hint.textContent = f.ordered
        ? `Low to high: ${f.options.join(" < ")}. One column, ${f.options.map((o, i) => `${o} = ${(i / Math.max(1, f.options.length - 1)).toFixed(2)}`).join(", ")}.`
        : `No order: one-hot, one column per option (${f.options.map((o) => "prev_" + f.name + "_" + o).join(", ")}).`;
      card.append(hint);
    }
    const rollups = f.type === "choice" && !f.ordered ? ["last"] : ROLLUPS[f.type];
    card.append(labelled("Per day", select(rollups, f.rollup, (v) => (f.rollup = v), false, ROLLUP_HELP)));
    if (f.type === "number" || f.type === "scale") {
      const t = document.createElement("input");
      t.type = "radio";
      t.name = "target";
      t.checked = draft.target === f.name;
      t.onchange = () => { draft.target = f.name; changed(); };
      card.append(labelled("Target", t));
    }
    const note = document.createElement("div");
    note.className = "note";
    note.textContent = locked
      ? `${n} entries logged. Name, type and options are locked so the old entries keep their meaning.`
      : n ? "" : "No entries yet.";
    card.append(note);
    grid.append(card);
  });
}

$("cfg-add").onclick = () => {
  const f = { name: "new_field_" + (draft.fields.length + 1) };
  setType(f, "scale");
  draft.fields.push(f);
  renderEditor();
  changed();
};

$("cfg-undo").onclick = startEditor;

$("cfg-save").onclick = async () => {
  if (!draft.target) return showError("Pick a target: the field the models should predict.");
  try {
    await api("/api/config", { method: "PUT", body: draft });
    state.cfg = await api("/api/config?dataset=own");
    showError(null);
    startEditor();
    showLog();
  } catch (e) {
    showError(e);
  }
};

// ---------- logging ----------

// "sleep_hours" -> "Sleep hours", "crazy_late" -> "crazy late"
const pretty = (name) => name.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
const soft = (name) => name.replace(/_/g, " ");

function label(f, value) {
  if (value === undefined || value === null) return "";
  if (f.type === "yesno") return value ? "yes" : "no";
  if (f.type === "choice") return soft(f.options[value]);
  return String(Math.round(value * 100) / 100);
}

const ROLLUP_WORD = { sum: "total", mean: "average", max: "highest", min: "lowest", count: "count" };

async function addEntry(f, value) {
  try {
    await api("/api/entries", { method: "POST", body: { date: $("log-date").value, field: f.name, value } });
    showError(null);
    renderLog();
  } catch (e) {
    showError(e);
  }
}

function controls(f, current) {
  if (f.type === "number") {
    const row = document.createElement("div");
    row.className = "number-row";
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.enterKeyHint = "done";
    input.placeholder = `${f.min}–${f.max}`;
    input.setAttribute("aria-label", pretty(f.name));
    const add = document.createElement("button");
    add.textContent = f.rollup === "last" ? "Save" : "Add";
    const go = () => {
      const v = parseNumber(input.value);
      if (v === null) return showError(`${pretty(f.name)}: type a number`);
      input.value = "";
      input.blur();
      addEntry(f, v);
    };
    add.onclick = go;
    input.onkeydown = (e) => {
      if (e.key === "Enter") go();
    };
    row.append(input, add);
    if (f.rollup === "sum" && f.min <= 1 && f.max >= 1) {
      const one = document.createElement("button");
      one.textContent = "+1";
      one.title = "Add one";
      one.onclick = () => addEntry(f, 1);
      row.prepend(one);
    }
    return row;
  }
  const values =
    f.type === "yesno" ? [["yes", 1], ["no", 0]]
    : f.type === "choice" ? f.options.map((o, i) => [soft(o), i])
    : Array.from({ length: f.max - f.min + 1 }, (_, i) => [String(f.min + i), f.min + i]);
  const box = document.createElement("div");
  box.className = "options";
  const n = values.length;
  const cols = n <= 4 ? n : n <= 10 ? Math.ceil(n / 2) : 6;
  box.style.gridTemplateColumns = `repeat(${cols}, minmax(0, 1fr))`;
  for (const [text, value] of values) {
    const b = document.createElement("button");
    b.textContent = text;
    if (f.rollup === "last" && current === value) b.classList.add("on");
    b.onclick = () => addEntry(f, value);
    box.append(b);
  }
  return box;
}

async function renderLog() {
  const cfg = state.cfg;
  if (!cfg) return;
  $("student").textContent = "Logging as " + cfg.student;
  if (!$("log-date").value) $("log-date").value = cfg.today;
  $("log-date").max = cfg.today;
  let entries = [], days = {};
  try {
    [entries, days] = await Promise.all([
      api("/api/entries?date=" + $("log-date").value),
      api("/api/days?dataset=own"),
    ]);
  } catch (e) {
    return showError(e);
  }
  const rolled = days[$("log-date").value] || {};
  const grid = $("fields");
  grid.innerHTML = "";
  for (const f of cfg.fields) {
    const mine = entries.filter((e) => e.field === f.name);
    const card = document.createElement("div");
    card.className = "card";
    const head = document.createElement("div");
    head.className = "card-head";
    const title = document.createElement("div");
    const h = document.createElement("h3");
    h.textContent = pretty(f.name);
    title.append(h);
    if (f.name === cfg.target) {
      const t = document.createElement("span");
      t.className = "tag";
      t.textContent = "target";
      title.append(t);
    }
    // the day's value, top right; once-a-day fields clear it with ×
    const pill = document.createElement("span");
    const v = rolled[f.name];
    if (v === undefined) {
      pill.className = "pill empty";
      pill.textContent = "not logged";
    } else {
      pill.className = "pill";
      pill.textContent = f.rollup === "last" ? label(f, v) : `${ROLLUP_WORD[f.rollup]} ${label(f, v)}`;
      if (f.rollup === "last") {
        const clear = document.createElement("button");
        clear.textContent = "×";
        clear.title = "Clear this day's value";
        clear.setAttribute("aria-label", "Clear " + pretty(f.name));
        clear.onclick = async () => {
          for (const e of mine) await api("/api/entries/" + e.id, { method: "DELETE" });
          renderLog();
        };
        pill.append(clear);
      }
    }
    head.append(title, pill);
    card.append(head, controls(f, v));
    if (f.rollup !== "last" && mine.length) {
      const ul = document.createElement("ul");
      ul.className = "entries";
      for (const e of mine) {
        const li = document.createElement("li");
        li.textContent = `${label(f, e.value)} · ${e.timestamp.slice(11, 16)}`;
        const del = document.createElement("button");
        del.textContent = "×";
        del.title = "Delete this entry";
        del.onclick = async () => {
          await api("/api/entries/" + e.id, { method: "DELETE" });
          renderLog();
        };
        li.append(del);
        ul.append(li);
      }
      card.append(ul);
    }
    grid.append(card);
  }
}

// ---------- results: leaderboard + chart (shared by live and backtest) ----------

function renderBoard(result, rerun) {
  const el = $("board");
  const exclude = state.exclude[state.view];
  const lb = result.leaderboard;
  const scored = new Map(lb.board.map((b) => [b.model, b]));
  const info = new Map(result.models.map((m) => [m.name, m]));
  const order = [...lb.board.map((b) => b.model), ...result.models.map((m) => m.name).filter((n) => !scored.has(n))];
  const note = lb.board.length
    ? `Average error over the <b>${lb.shared_days}</b> days where every ticked model made a guess. Lower is better. Untick a late starter to compare over more days.`
    : "Nothing scored yet.";
  let html = `<p class="muted board-note">${note}</p><div class="board">`;
  order.forEach((name, i) => {
    const b = scored.get(name);
    const m = info.get(name) || {};
    // an empty model says "waiting for your code" on the right; don't repeat it here
    const code = m.issue ? `<span class="error">${m.issue}</span>` : m.source === "no code yet" ? "" : m.source || "";
    const days = b ? ` · ${b.own_days} days` : "";
    const score = b
      ? `<div class="score">${fmt(b.mae)}</div>`
      : m.ready === false
        ? `<div class="score wait">waiting for your code</div>`
        : `<div class="score wait">starts after ${m.min_days} day${m.min_days === 1 ? "" : "s"}</div>`;
    html += `<label class="board-row${i === 0 && b ? " best" : ""}">
      <input type="checkbox" data-model="${name}" ${exclude.has(name) ? "" : "checked"}>
      <span class="name"><b>${name}</b><small>${code}${days}</small></span>${score}</label>`;
  });
  for (const e of result.load_errors || []) html += `<div class="board-row error">${e.file}: ${e.error}</div>`;
  el.innerHTML = html + "</div>";
  el.querySelectorAll("input[type=checkbox]").forEach((cb) => {
    cb.onchange = () => {
      cb.checked ? exclude.delete(cb.dataset.model) : exclude.add(cb.dataset.model);
      rerun();
    };
  });
}

function renderChart(rolling) {
  if (chart) chart.destroy();
  chart = null;
  const dates = [...new Set(Object.values(rolling).flat().map((p) => p.date))].sort();
  $("chart-box").hidden = dates.length === 0;
  if (!dates.length) return;
  const datasets = Object.entries(rolling).map(([model, pts], i) => {
    const byDate = new Map(pts.map((p) => [p.date, p.mae]));
    return {
      label: model,
      data: dates.map((d) => (byDate.has(d) ? byDate.get(d) : null)),
      borderColor: COLORS[i % COLORS.length],
      backgroundColor: COLORS[i % COLORS.length],
      spanGaps: true,
      pointRadius: 2,
      tension: 0.2,
    };
  });
  chart = new Chart($("chart"), {
    type: "line",
    data: { labels: dates, datasets },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12 } } },
      scales: {
        x: { ticks: { maxTicksLimit: window.innerWidth < 640 ? 4 : 10, maxRotation: 0 } },
        y: { beginAtZero: true, title: { display: true, text: "error" } },
      },
    },
  });
}

// ---------- live ----------

async function renderLive() {
  let result, days;
  try {
    const ex = [...state.exclude.live].join(",");
    [result, days] = await Promise.all([
      api("/api/live?exclude=" + encodeURIComponent(ex)),
      api("/api/days?dataset=own"),
    ]);
  } catch (e) {
    return showError(e);
  }
  if (state.tab !== "results" || state.view !== "live") return;
  const loggedToday = (days[state.cfg.today] || {})[state.cfg.target] !== undefined;
  $("predict").disabled = !loggedToday;
  if (!$("predict-msg").dataset.keep) {
    $("predict-msg").textContent = loggedToday
      ? "Trains every model on all your days and saves its guess for tomorrow."
      : `Log today's ${soft(state.cfg.target)} first.`;
  }
  delete $("predict-msg").dataset.keep;
  renderBoard(result, renderLive);
  renderChart(result.rolling);
  const byDate = {};
  for (const r of result.records) (byDate[r.date] ||= { actual: r.actual, preds: {} }).preds[r.model] = r.predicted;
  const models = result.models.map((m) => m.name);
  const dates = Object.keys(byDate).sort().reverse();
  if (!dates.length) {
    $("live-log").innerHTML = '<p class="muted">No predictions yet.</p>';
    return;
  }
  let html = "<div class=scroll><table><tr><th>Day</th><th>Actual</th>" + models.map((m) => `<th>${m}</th>`).join("") + "</tr>";
  for (const d of dates) {
    const row = byDate[d];
    html += `<tr><td>${d}</td><td class="num">${fmt(row.actual)}</td>`;
    for (const m of models) {
      const p = row.preds[m];
      const err = p !== undefined && row.actual !== null ? ` <span class="muted">(off ${fmt(Math.abs(p - row.actual))})</span>` : "";
      html += `<td class="num">${p === undefined ? "–" : fmt(p) + err}</td>`;
    }
    html += "</tr>";
  }
  $("live-log").innerHTML = html + "</table></div>";
}

$("predict").onclick = async () => {
  try {
    const r = await api("/api/predict", { method: "POST" });
    if (!r.ok) return showError(r.message);
    const skipped = r.skipped.length ? ` ${r.skipped.length} model(s) not ready yet.` : "";
    $("predict-msg").textContent = r.made.length
      ? `Saved ${r.made.length} guesses for ${r.target_date}.` + skipped
      : "No model is ready yet: the first guess needs two logged days (a yesterday and a today).";
    $("predict-msg").dataset.keep = "1";
    showError(null);
    renderLive();
  } catch (e) {
    showError(e);
  }
};

// ---------- backtest ----------

function clearBacktest() {
  $("board").innerHTML = '<p class="muted">Press "Run backtest".</p>';
  $("backtest-msg").textContent = "Replays the past: for each day, train on the days before it, guess it, measure the error.";
  renderChart({});
}

async function runBacktest() {
  $("backtest-msg").textContent = "Running…";
  try {
    const ex = [...state.exclude.backtest].join(",");
    const r = await api(`/api/backtest?dataset=${state.dataset}&exclude=${encodeURIComponent(ex)}`);
    if (state.tab !== "results" || state.view !== "backtest") return;
    $("backtest-msg").textContent = `${r.rows} days with a target, ${r.evaluated} replayed.`;
    renderBoard(r, runBacktest);
    renderChart(r.rolling);
    showError(null);
  } catch (e) {
    $("backtest-msg").textContent = "";
    showError(e);
  }
}
$("run-backtest").onclick = runBacktest;

$("seed").onclick = async () => {
  try {
    await api("/api/seed", { method: "POST", body: { days: Number($("seed-days").value) } });
    showError(null);
    runBacktest();
  } catch (e) {
    showError(e);
  }
};

// ---------- start ----------

document.querySelectorAll("#tabs button").forEach((b) => (b.onclick = () => setTab(b.dataset.tab)));
document.querySelectorAll("[data-view]").forEach((b) => (b.onclick = () => setView(b.dataset.view)));
document.querySelectorAll("[data-dataset]").forEach((b) => (b.onclick = () => setDataset(b.dataset.dataset)));
$("edit-fields").onclick = showFields;
$("fields-back").onclick = showLog;
$("log-date").onchange = renderLog;

(async () => {
  try {
    state.cfg = await api("/api/config?dataset=own");
  } catch (e) {
    return showError(e);
  }
  setTab("log");
})();
