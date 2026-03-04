# Agent 自动自优化闭环

这是一个可落地的模板，用于让 AI 编码 Agent 持续自优化，包含：

- `AGENTS.md` 治理规则
- 基于脚本的 Skill 脚手架自动化
- 错误知识库模板
- 周期复盘与反馈闭环
- 可量化的 token 与工程效率评估

## 仓库结构

- `AGENTS.md`：运行期治理规则与质量门禁。
- `docs/closed-loop-playbook.md`：日常与每周执行手册。
- `docs/measurement-framework.md`：token 与效率收益的量化方法。
- `scripts/create_skill.sh`：按规范名称创建 skill 骨架。
- `scripts/weekly_review.sh`：基于错误知识库生成周报。
- `scripts/log_task_run.sh`：向指标 CSV 追加一条标准任务记录。
- `scripts/metrics_report.sh`：输出整体、按 skill、以及 pre/post 指标对比。
- `metrics/task-runs.csv`：任务执行数据集（用于效果分析）。
- `templates/skill/SKILL.md.template`：最小 skill 模板。
- `templates/knowledge-base/error-entry.md`：错误条目模板。
- `templates/reports/weekly-self-optimization-report.md`：周报模板。
- `knowledge-base/errors/`：错误条目目录（每次事故一文件）。
- `reports/`：自动生成的周报目录。

## 快速开始

```bash
git clone git@github.com:<user>/agent-auto-self-optimizing-closed-loop.git
cd agent-auto-self-optimizing-closed-loop

# 1) 创建一个新 skill 骨架
./scripts/create_skill.sh log-analysis-helper

# 2) 在 knowledge-base/errors/ 下记录错误条目
# 参考 templates/knowledge-base/error-entry.md

# 3) 生成周报
./scripts/weekly_review.sh

# 4) 查看优化效果
./scripts/metrics_report.sh --all

# 5) 记录一条任务执行数据
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

## 推荐工作流

1. 保持 `AGENTS.md` 简短且可执行，只引入有证据支持的规则。
2. 对重复任务及时创建或更新 skill。
3. 每次失败都写入错误知识库，明确根因与预防规则。
4. 每周运行复盘脚本，把稳定有效的改进沉淀到 `AGENTS.md` 或 skill。
5. 持续记录 `metrics/task-runs.csv`，用数据评估优化收益。

## 发布检查清单

1. 初始化 git 并完成首个提交。
2. 本地验证脚本可运行。
3. 配置远端：`git@github.com:<user>/agent-auto-self-optimizing-closed-loop.git`。
4. 推送 `main` 分支。
