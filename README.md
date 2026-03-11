# Agent Optsmith

<!-- README_SYNC_VERSION: 2026-03-11 -->

This project provides an Agent Optsmith workflow for measurable AI coding optimization.
This README is the main entry point for installation and daily operation.

Companion docs:

- [中文说明](README_CN.md)
- [Optimization Playbook](docs/optsmith-playbook.md)
- [Measurement Framework](docs/measurement-framework.md)

## 1. Core Capabilities

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
optsmith version
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

1. Top subgraph (`Loop Overview`) is the continuous optimization loop.
2. Bottom-left subgraph (`Scenario A`) is the auto path after task completion.
3. Bottom-right subgraph (`Scenario B`) is the dashboard-triggered optimization path.
4. Cross-subgraph arrows show how loop nodes trigger each scenario and how both scenario outputs return to `Effect Verification`.

## 5. How to Interpret Results Correctly

### 5.1 Effect Validation Strategy (What Is Actually Compared)

1. Skill-level effect:
- Each skill is compared only with no-skill baseline rows from the same `task_type`.
- `token_reduction_pct = (baseline_avg_tokens - skill_avg_tokens) / baseline_avg_tokens`
- `duration_reduction_pct = (baseline_avg_duration - skill_avg_duration) / baseline_avg_duration`
- `success_rate_delta_pp = skill_success_rate - baseline_success_rate`
- `rework_rate_delta = skill_rework_rate - baseline_rework_rate`

2. Process-level pre/post effect (cutover):
- `pre` window: `date < cutover`
- `post` window: `date >= cutover`
- `delta_avg_tokens_pct = (post_avg_tokens - pre_avg_tokens) / pre_avg_tokens`
- `delta_avg_duration_pct = (post_avg_duration - pre_avg_duration) / pre_avg_duration`
- `delta_success_rate_pp = post_success_rate - pre_success_rate`
- `delta_tasks_per_day_pct = (post_tasks_per_day - pre_tasks_per_day) / pre_tasks_per_day`

3. Suggested validation sequence:
- Run `optsmith metrics --workspace "$(pwd)" --skill <skill-name>` for skill-vs-baseline effect.
- Run `optsmith metrics --workspace "$(pwd)" --all --cutover YYYY-MM-DD` for pre/post process effect.
- In dashboard, apply date + skill filter to inspect trend consistency before concluding.

### 5.2 How Same Skill Before/After Optimization Is Distinguished

1. Optimization events are persisted in project files:
- `.agents/optsmith-data/reports/dashboard-optimization-state.json` (`updated_at`, action, score, status).
- `.agents/optsmith-data/reports/optimization-history/<skill>.md` (timestamped optimization log).
- The optimized skill `SKILL.md` auto snapshot block (`updated_at`, status, source report).

2. The recommended cutover is the optimization event date (`updated_at` -> `YYYY-MM-DD`).

3. This is the standard comparison rule:
- `before`: task rows with `date < cutover`.
- `after`: task rows with `date >= cutover`.
- Keep the same `task_type` baseline requirement when interpreting skill deltas.

4. Current data granularity is day-level (`date`), not timestamp-level:
- If multiple optimizations happen on the same day, they share one cutover day window.
- For strict separation, avoid multiple optimizations per day for the same skill, or temporarily version skill names during evaluation.

### 5.3 Rework Definition, Identification, and Formula

1. Task identity contract:
- `task_id` must remain stable when the same business task is reopened.

2. Rework identification contract:
- If a delivered task is reopened (QA fail, requirement miss, rollback fix), log the next completion with the same `task_id` and incremented `rework_count`.
- `rework_count=0` means first-pass completion.
- `rework_count=1/2/...` means reopen rounds occurred before this completion.

3. Current rework metric formula in the toolkit:
- `rework_rate = SUM(rework_count) / COUNT(task_rows)`

4. Important operational note:
- The system does not infer rework across different `task_id` values.
- If your team changes `task_id` on reopen, rework will be undercounted.

### 5.4 Dashboard Discovery Rules (Why Something Is Marked for Optimization)

1. Existing skill opportunity score increases when signals appear:
- insufficient baseline on matching task types
- token or duration regression vs baseline
- success rate drop
- rework rate increase

2. New skill recommendation score increases when signals appear:
- no-skill repeats for a task type (`>=3` samples)
- no-skill token/duration cost is high vs overall
- failure/rework is high
- recurring root cause appears in error KB

3. Trigger timing:
- on every `optsmith run`
- on every dashboard `/api/report` refresh

### 5.5 Anti-Misread Checklist

1. Do not claim skill gains when output says `insufficient baseline`.
2. Read token, success, and rework metrics together.
3. Only compare same `task_type` for skill effect.
4. Ensure both pre and post windows have enough samples before using cutover deltas.
5. Treat optimization as verified only after post-window metrics stay improved, not after one short burst.

## 6. Command Quick Reference

1. Initialize in current project:
- `optsmith install --workspace "$(pwd)"`
2. Record and analyze one completed task:
- `optsmith run --workspace "$(pwd)" ...`
3. Open local dashboard:
- `optsmith dashboard --workspace "$(pwd)" --host 127.0.0.1 --port 8765`
4. Inspect metrics directly:
- `optsmith metrics --workspace "$(pwd)" --all`
- `optsmith metrics --workspace "$(pwd)" --skill <skill-name>`
5. Upgrade or remove project integration:
- `optsmith update --workspace "$(pwd)"`
- `optsmith uninstall --workspace "$(pwd)"`
