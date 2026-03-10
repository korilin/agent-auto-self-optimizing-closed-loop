# 跨工程接入说明书（CLI 无 Submodule 版）

## 目标

将本项目“自优化闭环”能力接入任意工程，并做到：

- 流程可复用：任务记录、失败复盘、周报、技能迭代
- 效果可量化：token、时长、成功率、返工率
- 接入成本低：业务仓库不需要引入 submodule

## 接入方式（唯一推荐）

通过 `aoso-skill` CLI 安装与操作，业务仓库只保留本地数据目录 `.agent-loop-data/`。

## 1) 安装 `aoso-skill` CLI

### Homebrew

```bash
brew tap korilin/aoso-skill https://github.com/korilin/agent-auto-self-optimizing-closed-loop
brew install aoso-skill
```

### pipx

```bash
pipx install "git+https://github.com/korilin/agent-auto-self-optimizing-closed-loop.git"
```

## 2) 安装或更新运行时 skill

```bash
aoso-skill update
```

## 3) 在目标工程初始化

在目标工程根目录执行：

```bash
aoso-skill init --workspace "$(pwd)"
```

这会创建：

- `.agent-loop-data/metrics/task-runs.csv`
- `.agent-loop-data/knowledge-base/errors/`
- `.agent-loop-data/reports/`
- `.agent-loop-data/templates/error-entry.md`
- 不会创建 `.agent-loop-data/skills`

同时会更新（或创建）项目根目录 `AGENTS.md` 里的 `AOSO-SKILL` 托管区块。

## 4) 日常命令

启动看板：

```bash
aoso-skill dashboard --workspace "$(pwd)" --host 127.0.0.1 --port 8765
```

任务完成自动记录建议使用 CLI 命令（由 agent 自动执行）：

```bash
aoso-skill run --workspace "$(pwd)" \
  --task-id TASK-1001 \
  --task-type debug \
  --project my-service \
  --model gpt-5 \
  --used-skill true \
  --skill-name log-analysis-helper \
  --total-tokens 1820 \
  --duration-sec 420 \
  --success true
```

补充：如果未显式传 `--total-tokens/--duration-sec`，`aoso-skill run` 会从本地 Codex session 日志自动回填（`$CODEX_HOME/sessions` 与 `$CODEX_HOME/archived_sessions`，有 `CODEX_THREAD_ID` 时按线程匹配）。

## 在目标工程如何真正生效

1. `AGENTS.md` 中声明：任务执行需使用 `agent-self-optimizing-loop`。
2. 每个任务结束自动执行 `aoso-skill run ...`。
3. 每个失败事件写一条 error entry（脚本自动分析会读取这些条目）。
4. 用 dashboard 做日期/skill/指标筛选，并触发优化与新增 skill。
   - 新增或优化后的 skill 默认落在项目根目录 `skills/`。
5. 把确认有效的规则与优化结果回写到 `AGENTS.md` 或 skill。

## 如何评估是否有效

### 单个 skill 的降本效果

- `token_reduction_pct`
- `duration_reduction_pct`
- `success_rate_delta_pp`
- `rework_rate_delta`

### 工程整体效率提升（pre/post）

- `delta_avg_tokens_pct`（越低越好）
- `delta_avg_duration_pct`（越低越好）
- `delta_success_rate_pp`（越高越好）
- `delta_tasks_per_day_pct`（越高越好）

## 统计口径建议

- 单 skill 建议样本量 `n >= 20` 再下结论。
- 仅比较相同 `task_type`。
- 尽量保持模型版本一致，减少干扰变量。
