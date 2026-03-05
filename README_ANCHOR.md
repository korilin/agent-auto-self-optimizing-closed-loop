# README_ANCHOR（作者维护说明）

本文档只面向本仓库作者/维护者。  
`README.md` / `README_CN.md` 已改为“用户使用说明”，作者流程统一收敛到这里。

## 1. 你作为作者的目标

1. 保证闭环可持续运行：记录任务、复盘失败、沉淀规则。
2. 保证优化可量化：token、时长、成功率、返工率可追踪。
3. 保证能力可复用：runtime 脚本与可安装 skill 始终一致。
4. 保证文档可执行：用户文档和维护文档职责清晰、入口明确。

## 2. 文档职责分层（避免再混乱）

- `README.md` / `README_CN.md`：只讲“用户怎么用 skill”。
- `README_ANCHOR.md`（本文件）：只讲“作者怎么维护仓库”。
- `AGENTS.md`：治理规则与门禁策略。
- `docs/measurement-framework.md`：指标定义与口径。
- `docs/closed-loop-playbook.md`：日常/每周操作节奏。

执行原则：用户文档不塞维护细节，维护细节不散落在多个入口页。

## 3. 触发维护流程的条件

任一条件满足，都走完整维护流程：

1. 修改 `scripts/`。
2. 修改 `skills/`。
3. 修改 CI 配置。
4. 修改流程文档（含 README、操作手册、工作流说明）。

推荐直接使用本仓库维护 skill：`skills/aoso-repo-maintainer/`。

## 4. 提交前必做流程（强制）

### Step A：如果改了 runtime 脚本，先做脚本同步

```bash
skills/aoso-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh
```

用途：把 `scripts/` 的 runtime 实现同步到 `skills/agent-self-optimizing-loop/scripts/`。

### Step B：同步中英文 README 并保持版本号一致

要求：

1. 同时更新 `README.md` 与 `README_CN.md`。
2. 两个文件中的 `README_SYNC_VERSION` 日期必须完全一致。
3. 两个 README 都必须保留 `## 1.` 到 `## 6.` 结构。

校验命令：

```bash
skills/aoso-repo-maintainer/scripts/check_readme_sync.sh
```

### Step C：跑仓库级总校验

```bash
skills/aoso-repo-maintainer/scripts/validate_repo_workflow.sh
```

该命令会覆盖：

1. Shell 语法检查。
2. runtime 与 installable scripts 一致性检查。
3. README 中英文同步检查。
4. root toolkit smoke test。
5. installable skill smoke test。

只有看到 `repository workflow validation passed` 才允许提交。

### Step D：自动提交（通过校验后）

```bash
skills/aoso-repo-maintainer/scripts/auto_commit.sh --message "<commit-message>"
```

说明：

1. 脚本会执行 `git add -A`。
2. 若无变更会直接退出，不会创建空提交。
3. 若有变更会创建一次非交互提交。

## 5. 作者日常运行节奏（建议）

1. 每个任务完成后运行 `./scripts/auto_run_loop.sh` 自动执行记录+分析+周报。
2. 用 `./scripts/dashboard_server.sh` 查看可筛选看板并验证趋势。
3. 对新增失败在 `knowledge-base/errors/` 建立标准条目。
4. 当重复工作流 >= 3 次/7天，或高成本/重复失败出现时，新增或重构 skill。
5. 仅在有事故证据或指标收益时，修改 `AGENTS.md` 规则。

## 6. 变更映射速查（改哪里，补哪里）

- 改 `scripts/`：
  - 同步到 installable skill
  - 跑 `validate_repo_workflow.sh`
  - 若行为变化，更新 README / docs
- 改 `skills/agent-self-optimizing-loop/`：
  - 跑 `validate_repo_workflow.sh`
  - 确认命令示例与文档一致
- 改 README：
  - 同步中英文
  - 更新 `README_SYNC_VERSION`
  - 跑 `check_readme_sync.sh`
- 改流程或校验规则：
  - 更新 `AGENTS.md`
  - 必要时更新 `README_ANCHOR.md`
  - 记录变更原因（incident 或 measurable gain）

## 7. 常见失败与快速排查

1. `README sync version mismatch`
   - 原因：中英文 README 日期不同。
   - 处理：对齐 `README_SYNC_VERSION`，再跑同步检查。

2. `runtime script out of sync`
   - 原因：改了 `scripts/` 但没同步到 installable skill。
   - 处理：先跑 `sync_runtime_to_installable_skill.sh`，再总校验。

3. Smoke test 失败
   - 原因：命令示例、参数约束或默认路径改动后未同步文档/脚本。
   - 处理：按失败步骤回溯，先修脚本，再修文档，再跑总校验。

## 8. 维护者提交门禁（最终版）

提交前确认：

1. 相关脚本和文档已同步。
2. `check_readme_sync.sh` 通过。
3. `validate_repo_workflow.sh` 通过。
4. 若有新增失败案例，已写入 `knowledge-base/errors/YYYY-MM-DD-*.md`。
5. 如果规则发生变化，`AGENTS.md` 与本文件已更新。
6. 使用 `auto_commit.sh` 完成提交并确认 commit message 合理。
