# Agent 自动自优化闭环（作者手册）

这是一个用于 AI 编码 Agent 的“自优化基础设施”项目。  
你可以把它理解为两层：

1. `Toolkit` 层：脚本 + 模板 + 指标口径（可执行）
2. `Skill` 层：可被 Codex 触发的工作流（可复用）

如果你是本项目作者，最核心目标是三件事：

1. 让自优化流程持续运行（记录、复盘、迭代）
2. 让流程结果可量化（token、时长、成功率、返工率）
3. 让能力可分发（跨工程安装 skill）

配套文档：

- [跨工程接入说明书](docs/project-integration-guide-cn.md)
- [指标评估方法](docs/measurement-framework.md)
- [本仓库专用 skill](skills/aoso-repo-maintainer/SKILL.md)

## 1. 仓库中每个内容的作用、怎么用、结果是什么

### 核心治理与说明

| 路径 | 作用 | 你什么时候用 | 使用方式 | 结果/产物 |
|---|---|---|---|---|
| `AGENTS.md` | 定义项目治理规则和质量门禁 | 改流程、加规则、复盘后沉淀规则 | 编辑文档 | 形成可执行规范，指导后续 agent 行为 |
| `README.md` / `README_CN.md` | 面向使用者的入口说明 | 发布、引导新成员 | 编辑文档 | 明确项目定位、接入与操作路径 |
| `docs/closed-loop-playbook.md` | 日常/每周操作手册 | 日常运行闭环时 | 按文档执行 | 稳定执行节奏（daily/weekly） |
| `docs/measurement-framework.md` | 指标定义与统计口径 | 解释“优化是否有效”时 | 按公式与命令统计 | 得到可比的指标结果 |

### Runtime 脚本（仓库内直接运行）

| 路径 | 作用 | 使用命令 | 典型输出 | 你得到什么 |
|---|---|---|---|---|
| `scripts/log_task_run.sh` | 记录一条任务执行数据 | `./scripts/log_task_run.sh ...` | `logged: task_id=...` | `metrics/task-runs.csv` 增加一行 |
| `scripts/metrics_report.sh` | 计算指标（总体/单 skill/pre-post） | `./scripts/metrics_report.sh --all` | `Overall Metrics ...` | 当前效率、质量、skill 效果数据 |
| `scripts/weekly_review.sh` | 从错误知识库生成周报 | `./scripts/weekly_review.sh` | `generated report: ...` | `reports/YYYY-MM-DD-weekly-...md` |
| `scripts/create_skill.sh` | 快速创建 skill 骨架 | `./scripts/create_skill.sh xxx skills` | `created skill: ...` | 新 skill 目录结构 |

### 模板与数据目录

| 路径 | 作用 | 你什么时候用 | 结果/产物 |
|---|---|---|---|
| `templates/knowledge-base/error-entry.md` | 错误条目模板 | 新增事故记录 | 标准化 error KB |
| `templates/reports/weekly-self-optimization-report.md` | 周报模板 | 调整报告格式 | 报告结构一致 |
| `templates/skill/SKILL.md.template` | skill 模板 | 创建新 skill | 统一 skill 最小结构 |
| `metrics/task-runs.csv` | 任务执行数据集 | 每个任务结束记录 | 指标可计算 |
| `knowledge-base/errors/` | 错误知识库 | 每次失败后记录 | 复盘输入数据 |
| `reports/` | 周报输出目录 | 每周生成周报 | 复盘输出结果 |

### Skill 层

| 路径 | 作用 | 适用范围 | 结果 |
|---|---|---|---|
| `skills/agent-self-optimizing-loop/` | 对外可安装的自优化 skill | 其他工程、通用场景 | 让任意工程快速获得闭环能力 |
| `skills/aoso-repo-maintainer/` | 本仓库专用维护 skill | 仅本仓库 | 保证脚本同步、流程校验、发布一致性 |

## 2. 作为作者，你日常怎么用

### 路径 A：日常记录与看效果

1. 记录任务（每个任务完成后）：

```bash
./scripts/log_task_run.sh \
  --task-id TASK-1001 \
  --task-type debug \
  --project core-service \
  --model gpt-5 \
  --used-skill true \
  --skill-name log-analysis-helper \
  --total-tokens 1820 \
  --duration-sec 420 \
  --success true
```

2. 看全局指标：

```bash
./scripts/metrics_report.sh --all
```

3. 看单个 skill 效果：

```bash
./scripts/metrics_report.sh --skill log-analysis-helper
```

你会看到关键字段：

- `token_reduction_pct`
- `duration_reduction_pct`
- `success_rate_delta_pp`
- `rework_rate_delta`

### 路径 B：每周复盘并沉淀规则

1. 每周生成周报：

```bash
./scripts/weekly_review.sh
```

2. 打开 `reports/` 下最新周报，做三件事：
- 识别高频根因
- 决定新增/重构 skill
- 把稳定有效的规则写回 `AGENTS.md`

### 路径 C：维护本仓库自身（关键）

当你修改了 `scripts/`、`skills/`、CI 或流程文档时，使用本仓库专用 skill 的脚本：

1. 同步 runtime 脚本到可安装 skill：

```bash
skills/aoso-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh
```

2. 执行仓库级校验（语法 + 一致性 + 双路径 smoke test）：

```bash
skills/aoso-repo-maintainer/scripts/validate_repo_workflow.sh
```

典型成功输出：

```text
[1/5] shell syntax checks
[2/5] runtime/script parity checks
[3/5] root toolkit smoke test
[4/5] installable skill smoke test
[5/5] done
repository workflow validation passed
```

这一步通过后再提交代码。

## 3. 你能期待的“使用结果/效果”是什么样

### 单个 skill 的效果（微观）

命令：

```bash
./scripts/metrics_report.sh --skill <skill-name>
```

预期输出特征：

- 有同 task_type 的 baseline 时，出现 `token_reduction_pct` 等比较结果
- 无 baseline 时，会提示 `insufficient baseline`

你可以据此回答：
- 这个 skill 是否真的减少 token？
- 是否降低任务时长？
- 是否提升成功率并降低返工？

### 工程整体效果（宏观）

命令：

```bash
./scripts/metrics_report.sh --all --cutover YYYY-MM-DD
```

预期输出特征：

- 有 pre/post 数据时，出现 `delta_*` 指标
- 如果 pre 或 post 缺样本，对应指标显示 `n/a`

你可以据此回答：
- 模型使用后整体效率是否提升？
- 优化策略是否带来真实收益而不是偶然波动？

### 每周治理效果（流程）

命令：

```bash
./scripts/weekly_review.sh
```

预期输出特征：

- 生成周报文件路径
- 周报包含：高频根因、高成本任务类型、下周行动项

你可以据此形成持续迭代闭环，而不是一次性优化。

## 4. 安装与分发（作者常用）

### 安装通用 skill（给其他工程）

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo korilin/agent-auto-self-optimizing-closed-loop \
  --path skills/agent-self-optimizing-loop
```

### 安装本仓库专用 skill（本地维护本仓库）

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo korilin/agent-auto-self-optimizing-closed-loop \
  --path skills/aoso-repo-maintainer
```

安装后重启 Codex。

## 5. 作者最小工作清单（建议照这个执行）

1. 修改代码/脚本
2. 运行 `sync_runtime_to_installable_skill.sh`（若改了 runtime 脚本）
3. 运行 `validate_repo_workflow.sh`
4. 必要时更新 `README/README_CN` 与 `docs/`
5. 提交并推送
6. 记录关键任务数据，观察指标趋势

## 6. 当前项目状态（你可以直接复用）

- 已有对外 skill：`skills/agent-self-optimizing-loop`
- 已有项目内专用 skill：`skills/aoso-repo-maintainer`
- 已接入 CI 校验 skill 工作流
- 已具备 token/效率可量化能力

这意味着该仓库已经从“模板”升级为“可自维护、可自验证、可自衡量”的自优化系统。
