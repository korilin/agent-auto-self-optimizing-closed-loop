# Agent 自动自优化闭环（用户手册）

<!-- README_SYNC_VERSION: 2026-03-06 -->

这个项目用于在你的工程里落地“可量化”的 AI 编码自优化闭环。
如果你的目标是“作为 skill 使用者快速上手”，请从这份 README 开始。

如果你是维护本仓库的作者，请看 [README_ANCHOR.md](README_ANCHOR.md)。

配套文档：

- [English Guide](README.md)
- [作者锚点说明](README_ANCHOR.md)
- [闭环运行手册](docs/closed-loop-playbook.md)
- [指标评估方法](docs/measurement-framework.md)

## 1. 作为用户你能得到什么

初始化完成后，你会得到一套稳定循环和清晰产物：

1. 一条命令自动完成记录 + 分析 + 周报。
2. skill 效果评估（`token_reduction_pct`、`duration_reduction_pct` 等）。
3. 本地可筛选 Web 看板（日期、skill、cutover、指标关键字）。
4. skill 优化机会自动发现，并支持在看板中立即执行优化/创建。
5. 指定切换日期后的 pre/post 对比结果。

数据默认在你的项目目录 `.agent-loop-data/` 下：

- `metrics/task-runs.csv`
- `knowledge-base/errors/`
- `reports/`
- `templates/error-entry.md`

## 2. 安装 skill

先安装跨工程可复用的主 skill（用户日常使用这个）：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo korilin/agent-auto-self-optimizing-closed-loop \
  --path skills/agent-self-optimizing-loop
```

仅当你要维护本仓库时，再安装维护者 skill：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo korilin/agent-auto-self-optimizing-closed-loop \
  --path skills/aoso-repo-maintainer
```

安装后重启 Codex。

## 3. 在你的项目里做一次初始化

在目标项目根目录运行：

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/setup_loop_workspace.sh" --workspace "$(pwd)"
```

预期结果：

- 自动创建 `.agent-loop-data/metrics/task-runs.csv`（含表头）。
- 自动创建 `.agent-loop-data/knowledge-base/errors/`。
- 自动创建 `.agent-loop-data/reports/`。
- 自动创建 `.agent-loop-data/templates/error-entry.md`。

## 4. 日常使用路径（全自动）

1. 在 agent 工作流中，任务完成后应自动执行此命令（采集 + 分析 + 周报）：

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/auto_run_loop.sh" \
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

如果运行时能提供真实遥测，请传入 `total_tokens` / `duration_sec`
（或设置 `CODEX_TOTAL_TOKENS`、`CODEX_TASK_DURATION_SEC`），避免写入占位 0 值。

2. 打开看板做筛选、优化发现和直接执行：

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/dashboard_server.sh" --host 127.0.0.1 --port 8765
```

然后访问 `http://127.0.0.1:8765`。
在 `Skill Optimization Discovery` 区域可对现有 skill 立即执行优化。
在 `New Skill Recommendations` 区域可一键创建并优化新增 skill。

3. 如需原始命令输出（可选）：

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/metrics_report.sh" --all
"${SKILL_HOME}/scripts/metrics_report.sh" --skill log-analysis-helper
"${SKILL_HOME}/scripts/metrics_report.sh" --all --cutover YYYY-MM-DD
```

## 5. 如何正确解读输出

避免误判时，按这 5 条看：

1. 只有同 `task_type` 存在 no-skill baseline，skill 对比才可靠。
2. 出现 `insufficient baseline` 说明样本不足，先补 baseline。
3. 不要只看 token，需结合 `success_rate_delta_pp` 和 `rework_rate_delta`。
4. `--cutover` 对比需要 pre/post 都有足够样本。
5. 在看板中先做日期和 skill 筛选，再比较指标趋势。

## 6. 作者/维护者入口

所有作者维护说明已集中到 [README_ANCHOR.md](README_ANCHOR.md)，包括：

1. 仓库变更流程。
2. 必跑校验脚本。
3. README 中英文同步规则。
4. 提交前门禁与发布检查。

如果你只是 skill 使用者，按 1-5 节执行即可。
