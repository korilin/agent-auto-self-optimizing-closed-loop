# 跨工程接入说明书

## 目标

将本仓库的自优化能力接入到“其他工程”，并做到：

- 流程可复用（skill、错误复盘、周报）
- 数据可量化（token、时长、成功率、返工率）
- 接入成本可控（不要求改动主业务代码）

## 接入方式

1. 直接复制模板到目标工程  
优点：简单直观。  
缺点：后续同步模板更新成本高。

2. Git Submodule（推荐）  
优点：模板统一升级，目标工程只维护本地数据。  
缺点：需要管理 submodule。

3. 平台统一仓聚合  
优点：跨工程统一看板。  
缺点：接入和治理复杂度最高。

## 推荐方案：Submodule + 工程本地数据目录

在目标工程根目录执行：

```bash
git submodule add git@github.com:korilin/agent-auto-self-optimizing-closed-loop.git .agent-loop
git submodule update --init --recursive

mkdir -p .agent-loop-data/metrics .agent-loop-data/knowledge-base/errors .agent-loop-data/reports .agent-loop-data/skills
cp .agent-loop/metrics/task-runs.csv .agent-loop-data/metrics/task-runs.csv
```

### 命令使用（关键）

所有运行数据都写入 `.agent-loop-data/`，不写回 submodule。

```bash
# 记录任务数据
AOSO_DATA_FILE=.agent-loop-data/metrics/task-runs.csv \
  ./.agent-loop/scripts/log_task_run.sh \
  --task-id TASK-1001 \
  --task-type debug \
  --project my-service \
  --model gpt-5 \
  --used-skill true \
  --skill-name log-analysis-helper \
  --total-tokens 1820 \
  --duration-sec 420 \
  --success true

# 输出指标
AOSO_DATA_FILE=.agent-loop-data/metrics/task-runs.csv \
  ./.agent-loop/scripts/metrics_report.sh --all

# 生成每周复盘
AOSO_KB_DIR=.agent-loop-data/knowledge-base/errors \
AOSO_REPORT_DIR=.agent-loop-data/reports \
  ./.agent-loop/scripts/weekly_review.sh

# 在目标工程创建 skill（写到本地数据目录）
./.agent-loop/scripts/create_skill.sh my-project-debug-helper .agent-loop-data/skills
```

## 在目标工程如何“真正用起来”

1. 在目标工程的 `AGENTS.md` 加一条约定：  
当任务命中 `.agent-loop-data/skills/<skill-name>/SKILL.md` 语义范围时，先读取该 skill 再执行。

2. 每次任务结束记录一次 `log_task_run.sh`。

3. 每次失败新增一个错误条目到 `.agent-loop-data/knowledge-base/errors/`。

4. 每周运行一次 `weekly_review.sh`，把有效预防规则沉淀回 `AGENTS.md` 或 skill。

## 如何判断“自优化是否有效”

### 单个 Skill 的 token 降幅

命令：

```bash
AOSO_DATA_FILE=.agent-loop-data/metrics/task-runs.csv \
  ./.agent-loop/scripts/metrics_report.sh --skill log-analysis-helper
```

看指标：

- `token_reduction_pct`
- `duration_reduction_pct`
- `success_rate_delta_pp`
- `rework_rate_delta`

### 工程整体效率提升（pre/post）

命令：

```bash
AOSO_DATA_FILE=.agent-loop-data/metrics/task-runs.csv \
  ./.agent-loop/scripts/metrics_report.sh --all --cutover 2026-03-01
```

看指标：

- `delta_avg_tokens_pct`（越低越好）
- `delta_avg_duration_pct`（越低越好）
- `delta_success_rate_pp`（越高越好）
- `delta_tasks_per_day_pct`（越高越好）

### 统计建议

- 单 skill 建议样本量 `n >= 20` 再下结论。
- 只比较同 `task_type`，避免口径偏差。
- 尽量保持模型版本一致，避免模型升级干扰结论。
