# 跨工程接入说明书

## 目标

将本项目的“自优化闭环”能力接入任意工程，并做到：

- 流程可复用：任务记录、失败复盘、周报、技能迭代
- 效果可量化：token、时长、成功率、返工率
- 接入成本低：尽量不改业务代码

## 接入模式

1. 仅安装 Skill（推荐默认）
- 适用：只想快速获得自优化能力，不想引入 submodule。
- 特点：所有能力通过已安装 skill 的脚本完成，数据写入项目本地 `.agent-loop-data/`。

2. Submodule 引入整仓
- 适用：希望在项目中共用完整模板仓（文档、模板、脚本）。
- 特点：版本管理更清晰，但接入稍重。

## 方案 A：仅安装 Skill（推荐）

### 1) 安装 skill

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo korilin/agent-auto-self-optimizing-closed-loop \
  --path skills/agent-self-optimizing-loop
```

安装后重启 Codex。

### 2) 在目标工程初始化数据目录

在目标工程根目录执行：

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/setup_loop_workspace.sh" --workspace "$(pwd)"
```

这会创建：

- `.agent-loop-data/metrics/task-runs.csv`
- `.agent-loop-data/knowledge-base/errors/`
- `.agent-loop-data/reports/`
- `.agent-loop-data/skills/`
- `.agent-loop-data/templates/error-entry.md`

### 3) 日常运行命令（自动模式）

建议在你的 agent 结束任务时自动触发以下命令，而不是让用户手动执行。

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"

# 自动执行：记录 + 指标分析 + 周报
"${SKILL_HOME}/scripts/auto_run_loop.sh" \
  --task-id TASK-1001 \
  --task-type debug \
  --project my-service \
  --model gpt-5 \
  --used-skill true \
  --skill-name log-analysis-helper \
  --total-tokens 1820 \
  --duration-sec 420 \
  --success true

# 打开本地看板（日期/skill/cutover/指标筛选）
"${SKILL_HOME}/scripts/dashboard_server.sh" --host 127.0.0.1 --port 8765

# 可选：CLI 原始输出
"${SKILL_HOME}/scripts/metrics_report.sh" --all
"${SKILL_HOME}/scripts/metrics_report.sh" --skill log-analysis-helper
"${SKILL_HOME}/scripts/metrics_report.sh" --all --cutover 2026-03-01
```

## 方案 B：Submodule 引入整仓

在目标工程根目录执行：

```bash
git submodule add git@github.com:korilin/agent-auto-self-optimizing-closed-loop.git .agent-loop
git submodule update --init --recursive

mkdir -p .agent-loop-data/metrics .agent-loop-data/knowledge-base/errors .agent-loop-data/reports .agent-loop-data/skills
cp .agent-loop/metrics/task-runs.csv .agent-loop-data/metrics/task-runs.csv
```

命令示例：

```bash
# 自动执行：记录 + 指标分析 + 周报
AOSO_DATA_FILE=.agent-loop-data/metrics/task-runs.csv \
  ./.agent-loop/scripts/auto_run_loop.sh --task-id TASK-1001 --task-type debug --project my-service --model gpt-5 --used-skill true --skill-name log-analysis-helper --total-tokens 1820 --duration-sec 420 --success true

# 启动看板
./.agent-loop/scripts/dashboard_server.sh --host 127.0.0.1 --port 8765
```

## 在目标工程如何真正生效

1. 在工程 `AGENTS.md` 加约定：命中 `.agent-loop-data/skills/<skill>/SKILL.md` 时先用对应 skill。
2. 每个任务结束执行 `auto_run_loop.sh`，由脚本自动采集和分析。
3. 每个失败事件写一条 error entry（脚本自动分析会读取这些条目）。
4. 用 dashboard 做日期/skill/指标筛选，再把有效规则回写到 `AGENTS.md` 或 skill。

## 如何评估是否有效

### 单个 skill 的降本效果

查看：

- `token_reduction_pct`
- `duration_reduction_pct`
- `success_rate_delta_pp`
- `rework_rate_delta`

### 工程整体效率提升

查看 pre/post：

- `delta_avg_tokens_pct`（越低越好）
- `delta_avg_duration_pct`（越低越好）
- `delta_success_rate_pp`（越高越好）
- `delta_tasks_per_day_pct`（越高越好）

## 统计口径建议

- 单 skill 建议样本量 `n >= 20` 再下结论。
- 仅比较相同 `task_type`。
- 尽量保持模型版本一致，减少干扰变量。
