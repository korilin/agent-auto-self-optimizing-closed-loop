#!/usr/bin/env python3
"""Local dashboard for self-optimizing loop data.

The server executes repository scripts (`metrics_report.sh` and `weekly_review.sh`)
and exposes a filterable UI for date ranges, skill selection, and metric keys.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Sequence, Tuple
from urllib.parse import parse_qs, urlparse


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AOSO Dashboard</title>
  <style>
    :root {
      --bg: #f8f6f2;
      --panel: #fffefb;
      --ink: #1f2a30;
      --muted: #56656e;
      --line: #d8d2c9;
      --accent: #197278;
      --accent-soft: #d7ecee;
      --warn: #cb4b16;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 20% 0%, #fef7e4 0%, transparent 45%),
        radial-gradient(circle at 90% 20%, #e5f3ff 0%, transparent 40%),
        var(--bg);
    }
    .wrap {
      max-width: 1100px;
      margin: 32px auto;
      padding: 0 16px 32px;
    }
    .hero {
      background: linear-gradient(120deg, #f4ede0, #eaf8f8);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 18px;
    }
    .hero h1 {
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.05;
      letter-spacing: -0.02em;
    }
    .hero p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }
    .filters, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
    }
    label {
      display: flex;
      flex-direction: column;
      font-size: 12px;
      color: var(--muted);
      gap: 6px;
    }
    input, select, button {
      font: inherit;
      border-radius: 9px;
      border: 1px solid var(--line);
      padding: 9px 10px;
      background: #fff;
      color: var(--ink);
    }
    input:focus, select:focus, button:focus {
      outline: 2px solid var(--accent-soft);
      outline-offset: 1px;
    }
    button {
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      cursor: pointer;
      align-self: end;
    }
    .meta {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 10px;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 10px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fff;
    }
    .card .k {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .card .v {
      font-size: 18px;
      font-weight: 700;
      line-height: 1.15;
      word-break: break-word;
    }
    .list {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      font-size: 13px;
    }
    details {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px 10px;
      margin-top: 10px;
      background: #fff;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 12px;
      color: #20333f;
    }
    .hint {
      color: var(--warn);
      font-size: 12px;
      min-height: 16px;
      margin-top: 8px;
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) {
      .grid { grid-template-columns: 1fr; }
      .cards { grid-template-columns: 1fr; }
      .hero h1 { font-size: 24px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Self-Optimizing Loop Dashboard</h1>
      <p>Filter by date, skill, cutover, and metric key. The page executes local project scripts to load data.</p>
    </section>

    <section class="filters">
      <div class="grid">
        <label>Start Date
          <input id="startDate" type="date" />
        </label>
        <label>End Date
          <input id="endDate" type="date" />
        </label>
        <label>Cutover
          <input id="cutoverDate" type="date" />
        </label>
        <label>Skill
          <select id="skillName"><option value="">(all)</option></select>
        </label>
        <label>Metric Key Filter
          <input id="metricFilter" type="text" placeholder="token|duration|success" />
        </label>
      </div>
      <div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
        <button id="refreshBtn" type="button">Refresh Dashboard</button>
      </div>
      <div class="hint" id="hint"></div>
    </section>

    <section class="panel">
      <div class="meta" id="metaText">Loading...</div>
      <div class="cards" id="cards"></div>
      <ul class="list" id="sections"></ul>
      <details>
        <summary>Raw Overall Output</summary>
        <pre id="overallRaw"></pre>
      </details>
      <details>
        <summary>Raw Skill Output</summary>
        <pre id="skillRaw"></pre>
      </details>
      <details>
        <summary>Weekly Review (Last 7 Days of Selected Range)</summary>
        <pre id="weeklyRaw"></pre>
      </details>
    </section>
  </div>

  <script>
    const nodes = {
      startDate: document.getElementById("startDate"),
      endDate: document.getElementById("endDate"),
      cutoverDate: document.getElementById("cutoverDate"),
      skillName: document.getElementById("skillName"),
      metricFilter: document.getElementById("metricFilter"),
      refreshBtn: document.getElementById("refreshBtn"),
      hint: document.getElementById("hint"),
      cards: document.getElementById("cards"),
      sections: document.getElementById("sections"),
      overallRaw: document.getElementById("overallRaw"),
      skillRaw: document.getElementById("skillRaw"),
      weeklyRaw: document.getElementById("weeklyRaw"),
      metaText: document.getElementById("metaText"),
    };

    async function fetchJSON(url) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    }

    function renderOptions(payload) {
      nodes.startDate.value = payload.default_start || "";
      nodes.endDate.value = payload.default_end || "";
      nodes.cutoverDate.value = payload.default_cutover || "";
      const current = nodes.skillName.value;
      nodes.skillName.innerHTML = '<option value="">(all)</option>';
      for (const skill of payload.skills || []) {
        const opt = document.createElement("option");
        opt.value = skill;
        opt.textContent = skill;
        if (skill === current) opt.selected = true;
        nodes.skillName.appendChild(opt);
      }
    }

    function matchMetricFilter(key, query) {
      if (!query) return true;
      return key.toLowerCase().includes(query.toLowerCase());
    }

    function renderCards(metrics, metricFilter) {
      nodes.cards.innerHTML = "";
      const entries = Object.entries(metrics || {}).filter(([k]) => matchMetricFilter(k, metricFilter));
      if (entries.length === 0) {
        nodes.cards.innerHTML = '<div class="card"><div class="k">status</div><div class="v">No metrics matched filter.</div></div>';
        return;
      }
      for (const [key, value] of entries) {
        const el = document.createElement("div");
        el.className = "card";
        el.innerHTML = `<div class="k">${key}</div><div class="v">${value}</div>`;
        nodes.cards.appendChild(el);
      }
    }

    function renderSections(sections) {
      nodes.sections.innerHTML = "";
      for (const sec of sections || []) {
        const li = document.createElement("li");
        li.textContent = `${sec.title} (${Object.keys(sec.metrics || {}).length} metrics)`;
        nodes.sections.appendChild(li);
      }
    }

    async function refreshDashboard() {
      nodes.hint.textContent = "";
      const params = new URLSearchParams();
      if (nodes.startDate.value) params.set("start", nodes.startDate.value);
      if (nodes.endDate.value) params.set("end", nodes.endDate.value);
      if (nodes.cutoverDate.value) params.set("cutover", nodes.cutoverDate.value);
      if (nodes.skillName.value) params.set("skill", nodes.skillName.value);
      const metricFilter = nodes.metricFilter.value.trim();

      try {
        const report = await fetchJSON(`/api/report?${params.toString()}`);
        const metrics = report.flat_metrics || {};
        renderCards(metrics, metricFilter);
        renderSections(report.sections || []);
        nodes.overallRaw.textContent = report.overall_raw || "";
        nodes.skillRaw.textContent = report.skill_raw || "(no skill query)";
        nodes.weeklyRaw.textContent = report.weekly_raw || "(empty)";
        nodes.metaText.textContent =
          `rows=${report.row_count} | data_file=${report.data_file} | generated_at=${report.generated_at}`;
      } catch (err) {
        nodes.hint.textContent = `Load failed: ${err.message}`;
      }
    }

    async function boot() {
      try {
        const options = await fetchJSON("/api/options");
        renderOptions(options);
        await refreshDashboard();
      } catch (err) {
        nodes.hint.textContent = `Initialization failed: ${err.message}`;
      }
    }

    nodes.refreshBtn.addEventListener("click", refreshDashboard);
    boot();
  </script>
</body>
</html>
"""


def _is_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _today() -> str:
    return date.today().strftime("%Y-%m-%d")


@dataclass
class RuntimePaths:
    data_file: Path
    kb_dir: Path
    report_dir: Path
    metrics_script: Path
    weekly_script: Path


def resolve_runtime_paths() -> RuntimePaths:
    script_dir = Path(__file__).resolve().parent
    skill_mode = (script_dir.parent / "SKILL.md").is_file()
    workspace = Path(os.environ.get("AOSO_WORKSPACE_DIR", os.getcwd())).resolve()

    if skill_mode:
        data_file_default = workspace / ".agent-loop-data/metrics/task-runs.csv"
        kb_dir_default = workspace / ".agent-loop-data/knowledge-base/errors"
        report_dir_default = workspace / ".agent-loop-data/reports"
    else:
        root_dir = script_dir.parent
        data_file_default = root_dir / "metrics/task-runs.csv"
        kb_dir_default = root_dir / "knowledge-base/errors"
        report_dir_default = root_dir / "reports"

    data_file = Path(os.environ.get("AOSO_DATA_FILE", str(data_file_default))).resolve()
    kb_dir = Path(os.environ.get("AOSO_KB_DIR", str(kb_dir_default))).resolve()
    report_dir = Path(os.environ.get("AOSO_REPORT_DIR", str(report_dir_default))).resolve()

    return RuntimePaths(
        data_file=data_file,
        kb_dir=kb_dir,
        report_dir=report_dir,
        metrics_script=script_dir / "metrics_report.sh",
        weekly_script=script_dir / "weekly_review.sh",
    )


def run_script(command: Sequence[str], env_overrides: Dict[str, str]) -> str:
    env = os.environ.copy()
    env.update(env_overrides)
    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise RuntimeError(output.strip() or f"command failed: {' '.join(command)}")
    return output.strip()


def read_task_rows(data_file: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    if not data_file.exists():
        return [], []
    with data_file.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        fieldnames = reader.fieldnames or []
        rows = [row for row in reader]
    return fieldnames, rows


def filter_rows(
    rows: Sequence[Dict[str, str]], start: str, end: str
) -> List[Dict[str, str]]:
    filtered: List[Dict[str, str]] = []
    for row in rows:
        row_date = row.get("date", "")
        if not _is_date(row_date):
            continue
        if start and row_date < start:
            continue
        if end and row_date > end:
            continue
        filtered.append(row)
    return filtered


def write_filtered_csv(
    fieldnames: Sequence[str], rows: Sequence[Dict[str, str]], tmp_file: Path
) -> None:
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    with tmp_file.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_metrics_output(text: str) -> List[Dict[str, object]]:
    sections: List[Dict[str, object]] = []
    title = None
    metrics: Dict[str, str] = {}

    def flush() -> None:
        nonlocal title, metrics
        if title is not None:
            sections.append({"title": title, "metrics": dict(metrics)})
        title = None
        metrics = {}

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  "):
            clean = line.strip()
            if ": " in clean and title is not None:
                key, value = clean.split(": ", 1)
                metrics[key] = value
            continue
        flush()
        title = line
    flush()
    return sections


def flatten_metrics(sections: Sequence[Dict[str, object]]) -> Dict[str, str]:
    flat: Dict[str, str] = {}
    for section in sections:
        title = str(section.get("title", "section"))
        metrics = section.get("metrics", {})
        if not isinstance(metrics, dict):
            continue
        for key, value in metrics.items():
            if title.startswith("Overall Metrics"):
                flat[key] = str(value)
            elif title.startswith("Pre/Post Metrics"):
                flat[key] = str(value)
            elif title.startswith("Skill: "):
                skill_name = title.replace("Skill: ", "", 1)
                flat[f"{skill_name}.{key}"] = str(value)
    return flat


def collect_skills(rows: Sequence[Dict[str, str]]) -> List[str]:
    skill_set = {
        row.get("skill_name", "").strip()
        for row in rows
        if row.get("used_skill", "").strip().lower() == "true" and row.get("skill_name", "").strip()
    }
    return sorted(skill_set)


def run_weekly_review(
    paths: RuntimePaths, start: str, end: str
) -> str:
    if not paths.kb_dir.exists():
        return "knowledge-base/errors directory not found."

    with tempfile.TemporaryDirectory(prefix="aoso-dashboard-weekly-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        tmp_kb = tmp_root / "kb"
        tmp_report = tmp_root / "reports"
        tmp_kb.mkdir(parents=True, exist_ok=True)
        tmp_report.mkdir(parents=True, exist_ok=True)

        for md in paths.kb_dir.glob("*.md"):
            entry_date = ""
            try:
                with md.open("r", encoding="utf-8") as fp:
                    for raw in fp:
                        if raw.startswith("date: "):
                            entry_date = raw.replace("date: ", "", 1).strip()
                            break
            except UnicodeDecodeError:
                continue
            if not _is_date(entry_date):
                continue
            if start and entry_date < start:
                continue
            if end and entry_date > end:
                continue
            shutil.copy2(md, tmp_kb / md.name)

        output = run_script(
            [str(paths.weekly_script)],
            {
                "AOSO_KB_DIR": str(tmp_kb),
                "AOSO_REPORT_DIR": str(tmp_report),
            },
        )

        report_file = None
        for line in output.splitlines():
            if line.startswith("generated report: "):
                report_file = line.replace("generated report: ", "", 1).strip()
                break
        if not report_file:
            return output
        path = Path(report_file)
        if not path.exists():
            return output
        return path.read_text(encoding="utf-8")


class DashboardHandler(BaseHTTPRequestHandler):
    runtime_paths: RuntimePaths

    def _json(self, payload: Dict[str, object], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _text(self, text: str, status: int = 200, mime: str = "text/plain") -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{mime}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _bad_request(self, message: str) -> None:
        self._json({"error": message}, status=HTTPStatus.BAD_REQUEST)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/":
            self._text(HTML_PAGE, mime="text/html")
            return
        if path == "/api/options":
            self.handle_options()
            return
        if path == "/api/report":
            self.handle_report(query)
            return
        self._bad_request(f"unknown endpoint: {path}")

    def handle_options(self) -> None:
        fieldnames, rows = read_task_rows(self.runtime_paths.data_file)
        dates = sorted(
            {
                row.get("date", "")
                for row in rows
                if row.get("date") and _is_date(row.get("date", ""))
            }
        )
        if dates:
            default_start = dates[0]
            default_end = dates[-1]
        else:
            today = _today()
            default_start = today
            default_end = today

        payload = {
            "fields": fieldnames,
            "skills": collect_skills(rows),
            "default_start": default_start,
            "default_end": default_end,
            "default_cutover": default_start,
            "data_file": str(self.runtime_paths.data_file),
        }
        self._json(payload)

    def handle_report(self, query: Dict[str, List[str]]) -> None:
        start = query.get("start", [""])[0]
        end = query.get("end", [""])[0]
        cutover = query.get("cutover", [""])[0]
        skill = query.get("skill", [""])[0].strip()

        if start and not _is_date(start):
            self._bad_request("invalid start date, expected YYYY-MM-DD")
            return
        if end and not _is_date(end):
            self._bad_request("invalid end date, expected YYYY-MM-DD")
            return
        if cutover and not _is_date(cutover):
            self._bad_request("invalid cutover date, expected YYYY-MM-DD")
            return
        if start and end and start > end:
            self._bad_request("start date must be <= end date")
            return

        fieldnames, rows = read_task_rows(self.runtime_paths.data_file)
        if not fieldnames:
            self._json(
                {
                    "row_count": 0,
                    "sections": [],
                    "flat_metrics": {},
                    "overall_raw": "No data file found or no header row.",
                    "skill_raw": "",
                    "weekly_raw": "",
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "data_file": str(self.runtime_paths.data_file),
                }
            )
            return

        filtered_rows = filter_rows(rows, start, end)

        with tempfile.TemporaryDirectory(prefix="aoso-dashboard-") as tmp_dir:
            tmp_csv = Path(tmp_dir) / "filtered.csv"
            write_filtered_csv(fieldnames, filtered_rows, tmp_csv)

            metrics_cmd: List[str] = [str(self.runtime_paths.metrics_script), "--all"]
            if cutover:
                metrics_cmd.extend(["--cutover", cutover])
            overall_raw = run_script(metrics_cmd, {"AOSO_DATA_FILE": str(tmp_csv)})

            skill_raw = ""
            if skill:
                skill_cmd: List[str] = [
                    str(self.runtime_paths.metrics_script),
                    "--skill",
                    skill,
                ]
                if cutover:
                    skill_cmd.extend(["--cutover", cutover])
                skill_raw = run_script(skill_cmd, {"AOSO_DATA_FILE": str(tmp_csv)})

            weekly_raw = run_weekly_review(self.runtime_paths, start, end)

        sections = parse_metrics_output("\n".join([overall_raw, skill_raw]).strip())
        payload = {
            "row_count": len(filtered_rows),
            "sections": sections,
            "flat_metrics": flatten_metrics(sections),
            "overall_raw": overall_raw,
            "skill_raw": skill_raw,
            "weekly_raw": weekly_raw,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "data_file": str(self.runtime_paths.data_file),
        }
        self._json(payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run local web dashboard for self-optimizing loop."
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host")
    parser.add_argument("--port", type=int, default=8765, help="bind port")
    args = parser.parse_args()

    paths = resolve_runtime_paths()
    if not paths.metrics_script.exists():
        raise SystemExit(f"missing script: {paths.metrics_script}")
    if not paths.weekly_script.exists():
        raise SystemExit(f"missing script: {paths.weekly_script}")

    handler = DashboardHandler
    handler.runtime_paths = paths
    with ThreadingHTTPServer((args.host, args.port), handler) as server:
        print(f"dashboard server listening on http://{args.host}:{args.port}")
        print(f"data_file={paths.data_file}")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
