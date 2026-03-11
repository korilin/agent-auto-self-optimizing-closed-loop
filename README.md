# Agent Optsmith (User Guide)

<!-- README_SYNC_VERSION: 2026-03-10 -->

This project provides an Agent Optsmith workflow for measurable AI coding optimization.
If your goal is to use the skill in your own repository, this file is the entry point.

If you maintain this repository itself, use [README_ANCHOR.md](README_ANCHOR.md).

Companion docs:

- [中文说明](README_CN.md)
- [Author Anchor Guide](README_ANCHOR.md)
- [Optimization Playbook](docs/optsmith-playbook.md)
- [Measurement Framework](docs/measurement-framework.md)

## 1. What You Get as a User

After setup, you get a repeatable optimization workflow with concrete outputs:

1. Automatic run logging + metrics + weekly review with one command.
2. Skill impact reports (`token_reduction_pct`, `duration_reduction_pct`, etc.).
3. Filterable local web dashboard (date, skill, cutover, metric key filter).
4. Skill optimization discovery with immediate optimize/create actions from dashboard.
5. Clear pre/post comparison around a chosen cutover date.

In your project, data is stored under `.agents/optsmith-data/`:

- `metrics/task-runs.csv`
- `knowledge-base/errors/`
- `reports/`
- `templates/error-entry.md`

## 2. Install `optsmith` CLI

Use either Homebrew or pipx:

```bash
brew tap korilin/optsmith https://github.com/korilin/agent-optsmith
brew install optsmith
```

```bash
pipx install "git+https://github.com/korilin/agent-optsmith.git"
```

Then verify the CLI entrypoint:

```bash
optsmith help
```

## 3. Initialize Your Project Once

Run this in the target project root:

```bash
optsmith install --workspace "$(pwd)"
```

Install parameters:

- `--workspace <path>`: target project directory (default: current directory).
- `--data-dir <path>`: data root used for metrics/KB/reports (default: `.agents/optsmith-data`).
- `--skill-path <path>`: project skill root where `agent-optsmith` is installed (default: `.agents/skills`).
- `--skip-agents`: skip writing/updating the managed `OPTSMITH-SKILL` block in `AGENTS.md`.

Path behavior:

- Relative paths are resolved relative to `--workspace`.
- For safety, `data-dir` and `skill-path` must stay inside the workspace.

Custom path example:

```bash
optsmith install \
  --workspace "$(pwd)" \
  --data-dir ".agents/custom-optsmith-data" \
  --skill-path ".agents/custom-skills"
```

Expected result:

- `.agents/optsmith-data/metrics/task-runs.csv` created (with header).
- `.agents/optsmith-data/knowledge-base/errors/` created.
- `.agents/optsmith-data/reports/` created.
- `.agents/optsmith-data/templates/error-entry.md` created.
- `<workspace>/.agents/skills/agent-optsmith` installed from current CLI version.
- `AGENTS.md` gets/refreshes a managed `OPTSMITH-SKILL` block with `skill_dir` and `data_dir`.

## 4. Daily Workflow (Fully Automated Path)

1. In agent workflow, this command should be auto-executed at task completion (collect + analyze + review):

```bash
optsmith run --workspace "$(pwd)" \
  --task-id TASK-1001 \
  --task-type debug \
  --project my-service \
  --model gpt-5 \
  --used-skill true \
  --skill-name log-analysis-helper \
  --total-tokens 1820 \
  --duration-sec 420 \
  --success true \
  --rework-count 0
```

If telemetry is not passed explicitly, `optsmith run` will try to resolve real values from
local Codex session logs (`$CODEX_HOME/sessions` and `$CODEX_HOME/archived_sessions`, using
`CODEX_THREAD_ID` when available). For non-Codex runners, keep passing `total_tokens` /
`duration_sec` (or set env vars such as `CODEX_TOTAL_TOKENS` and `CODEX_TASK_DURATION_SEC`).

2. Open dashboard for filtering, optimization discovery, and direct optimization:

```bash
optsmith dashboard --workspace "$(pwd)" --host 127.0.0.1 --port 8765
```

Then open `http://127.0.0.1:8765`.
Use the `Skill Optimization Discovery` section to optimize one skill immediately.
Use `New Skill Recommendations` to create-and-optimize a new skill immediately.
New or optimized skill files are written under project `.agents/skills/` by default
(Codex auto-readable project skill directory).
Legacy fallback scan for project `skills/` is disabled. If you need a custom path,
set `OPTSMITH_LOCAL_SKILLS_DIR`.

3. Optional direct report commands (if you need raw CLI output):

```bash
optsmith metrics --workspace "$(pwd)" --all
optsmith metrics --workspace "$(pwd)" --skill log-analysis-helper
optsmith metrics --workspace "$(pwd)" --all --cutover YYYY-MM-DD
optsmith optimize --workspace "$(pwd)" --skill log-analysis-helper
```

4. Update project-installed skill to current CLI version:

```bash
optsmith update --workspace "$(pwd)"
```

5. Uninstall project integration when needed:

```bash
optsmith uninstall --workspace "$(pwd)"
```

### Complete Agent Optsmith Flow

![Agent Optsmith workflow map](docs/assets/agent-optsmith-workflow-flow.png)

How to read this flow:

1. Discovery timing:
- On every completed task (`optsmith run`) and every dashboard refresh (`/api/report`), opportunities are recalculated from latest local data.
2. Discovery mechanism:
- `optsmith metrics` + weekly review + opportunity scoring + new-skill recommendation logic drive optimization candidates.
3. Where records are saved:
- Run data: `.agents/optsmith-data/metrics/task-runs.csv`
- Error KB: `.agents/optsmith-data/knowledge-base/errors/*.md`
- Optimization reports: `.agents/optsmith-data/reports/skill-optimization/*`
4. Where optimization status is saved:
- `.agents/optsmith-data/reports/dashboard-optimization-state.json`
- This file is shared by the project, so different browsers can see the same optimized/created status.
5. Status transition:
- `DISCOVERED -> TRIGGERED -> APPLIED -> VERIFIED -> PROMOTED`
- Only `VERIFIED` improvements should be promoted to `AGENTS.md` / stable skills.

## 5. How to Interpret Results Correctly

Comparison method used by this toolkit:

1. Compare each skill only against no-skill baseline rows on the same `task_type`.
2. For skill-level effect:
- `token_reduction_pct = (baseline_avg_tokens - skill_avg_tokens) / baseline_avg_tokens`
- `duration_reduction_pct = (baseline_avg_duration - skill_avg_duration) / baseline_avg_duration`
- `success_rate_delta_pp = skill_success_rate - baseline_success_rate`
- `rework_rate_delta = skill_rework_rate - baseline_rework_rate`
3. For cutover pre/post effect:
- `delta_avg_tokens_pct = (post_avg_tokens - pre_avg_tokens) / pre_avg_tokens`
- `delta_avg_duration_pct = (post_avg_duration - pre_avg_duration) / pre_avg_duration`
- `delta_success_rate_pp = post_success_rate - pre_success_rate`
- `delta_tasks_per_day_pct = (post_tasks_per_day - pre_tasks_per_day) / pre_tasks_per_day`

Use these rules to avoid false conclusions:

1. Trust skill comparison only when there is no-skill baseline on the same `task_type`.
2. If output says `insufficient baseline`, collect more baseline samples first.
3. Read `success_rate_delta_pp` and `rework_rate_delta` together with token reduction.
4. Use `--cutover` only when both pre and post windows have enough samples.
5. In dashboard, use date range + skill filter before comparing metric trends.

## 6. Author/Maintainer Entry

All maintainer-facing instructions were moved to [README_ANCHOR.md](README_ANCHOR.md), including:

1. Repository change workflow.
2. Required validation scripts.
3. README synchronization rules.
4. Commit gates and release checks.

If your role is user only, you can stop at Sections 1-5.
