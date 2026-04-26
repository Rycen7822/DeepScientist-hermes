# Hermes agent 操作手册：DeepScientist 原生插件

本文是给 Hermes agent 和维护者看的详细使用说明。目标是让 Hermes 在启用 DeepScientist 原生插件后知道什么时候使用插件、怎样建立 quest、怎样记录记忆与 artifacts、怎样推进研究阶段，以及哪些入口已经被有意移除。

## 1. 角色定位

DeepScientist 原生插件不是对外部 `ds` 命令的简单包装。启用后，Hermes agent 本身就是 DeepScientist 的唯一工作入口：

- 通过 Hermes toolset `deepscientist` 暴露 curated `ds_*` 工具。
- 通过 `/ds ...` slash command 提供轻量交互入口。
- 通过 `deepscientist:deepscientist-mode` 和阶段技能提供 agent 操作规范。
- 通过 vendored headless runtime 保存 quest、memory、artifacts、runtime logs 和执行记录。

必须遵守：

- 不要调用全局 npm `ds` 来完成正常工作。
- 不要暴露 raw MCP。
- 不要尝试打开 Web UI。
- 不要尝试打开 TUI。
- 不要使用 social connector、browser connector 或外部消息 connector。
- 不要把 DeepScientist 项目记忆同步进 Hermes 自己的长期记忆，除非用户明确要求记录用户偏好或跨项目长期事实。

## 2. 项目本地存储

默认存储语义等价于原版 `ds --here`：从项目目录启动 Hermes，DeepScientist 相关文件都保存在该目录下的 `DeepScientist/` 树中。

示例：

```text
cd /path/to/example-research
hermes
```

DeepScientist 原生插件默认使用：

```text
/path/to/example-research/DeepScientist/
```

也就是：

```text
<project>/DeepScientist/
├── memory/
├── quests/
│   └── <quest_id>/
│       ├── memory/
│       ├── artifacts/
│       ├── logs/
│       └── ...
├── config/
│   └── hermes-native.yaml
├── runtime/
│   └── hermes-session-map.json
├── logs/
└── cache/
```

含义：

- 一个研究项目对应一个项目本地 DeepScientist 工作区。
- quest、memory、artifact、运行记录、session map 都随项目走。
- Hermes core 目录不会被 DeepScientist runtime 数据污染。
- 默认不会写入共享的 Hermes home 下的 DeepScientist runtime 目录。

高级覆盖：只有在用户明确要求共享或迁移布局时，才使用 `DEEPSCIENTIST_HERMES_CONFIG`、`DEEPSCIENTIST_HERMES_ROOT`、`DEEPSCIENTIST_PROJECT_ROOT` 或 config 中的 `runtime_home` 覆盖默认路径。

## 3. Agent runbook

### 3.1 首次接手任务

当用户提出 DeepScientist、科研 quest、研究计划、实验推进、论文产出、baseline、idea、experiment、analysis、paper bundle 等任务时，Hermes agent 应按下面顺序行动：

1. 确认当前工作目录是否是用户想要的项目目录。
   - 如果用户已经在项目目录启动 Hermes，直接使用该目录。
   - 如果明显不是项目目录，并且会影响存储位置，先提醒用户或切换到正确目录后再开始。
2. 加载/遵循 `deepscientist:deepscientist-mode`。
3. 调用 `ds_doctor` 检查原生 runtime 状态。
4. 调用 `ds_list_quests` 查看是否已有相关 quest。
5. 如果已有 quest，调用 `ds_set_active_quest` 绑定当前 Hermes session。
6. 如果没有 quest，调用 `ds_new_quest` 创建新 quest。
7. 调用 `ds_get_quest_state` 获取当前 stage、文档、memory 摘要和 artifact 状态。
8. 根据阶段选择一个阶段技能，例如 `deepscientist:scout` 或 `deepscientist:experiment`。
9. 工作过程中把关键事实写入 DeepScientist memory，把证据、实验、计划、结论写入 artifacts。
10. 最终回复用户时说明本轮做了什么、写入了哪些 quest 文件/记忆/artifacts，以及建议下一步。

### 3.2 已有 quest 的续作

如果用户说“继续之前的 DeepScientist 任务”“接着上次 quest”“继续这个研究项目”：

1. `ds_list_quests` 找候选 quest。
2. 根据标题、goal、最近事件选择最可能的 quest。
3. 不确定时向用户给出候选，不要擅自合并不同 quest。
4. `ds_set_active_quest` 绑定。
5. `ds_get_quest_state` 读取 compact state。
6. 必要时用 `ds_memory_search` 查找旧结论、实验配置、baseline 约束。
7. 继续推进，并把新决策写回 `ds_memory_write` 或对应 artifact 工具。

### 3.3 新 quest 的创建标准

使用 `ds_new_quest` 的情况：

- 用户提出一个新的研究目标。
- 当前项目没有可复用 quest。
- 旧 quest 与新任务目标不同，复用会混淆状态。

创建后立即：

1. 用 `ds_get_quest_state` 读取初始状态。
2. 根据任务设置 active stage，通常从 `scout`、`baseline` 或 `idea` 开始。
3. 用 `ds_memory_write` 写入初始背景、用户约束、数据/代码路径、评价标准。

## 4. 何时使用 DeepScientist 工具，何时使用 Hermes 原生工具

### 4.1 使用 DeepScientist `ds_*` 工具

当信息需要成为 DeepScientist quest 的持久状态时，用 `ds_*` 工具：

- quest 创建、绑定、暂停、恢复、停止。
- 研究阶段和 quest state 读取。
- 项目记忆和 quest 记忆。
- baseline gate、idea、experiment、analysis campaign、paper bundle。
- 需要被 DeepScientist 记录的 quest-local bash 执行。
- 需要在后续 DeepScientist 阶段被检索/复用的证据。

### 4.2 使用 Hermes 原生工具

当任务是普通文件、代码、检索、浏览、调试，且不需要自动成为 DeepScientist 状态时，用 Hermes 原生工具：

- `read_file` / `search_files` / `patch` / `write_file`：读写项目文件。
- `terminal`：常规命令、测试、构建。
- `web` / browser 工具：查询当前资料。
- `todo`：本轮会话内任务拆解。
- `memory`：只记录用户长期偏好或跨项目稳定事实，不记录普通 DeepScientist 项目记忆。

### 4.3 同步规则

如果 Hermes 原生工具产生了对研究重要的结果，应再用 DeepScientist 工具登记：

- 读论文得到关键结论：`ds_memory_write`。
- 跑实验得到指标：`ds_record_main_experiment`。
- 生成分析表格：`ds_create_analysis_campaign` + `ds_record_analysis_slice`。
- 完成 baseline 对齐：`ds_confirm_baseline` 或 `ds_waive_baseline`。
- 完成论文草稿或 bundle：`ds_submit_paper_outline` / `ds_submit_paper_bundle`。

## 5. Slash command 快速入口

Slash command 主要面向用户交互和快速检查。复杂工作仍应优先使用工具调用。

| 命令 | 用途 |
| --- | --- |
| `/ds help` | 查看命令概览 |
| `/ds mode on` | 启用 DeepScientist mode |
| `/ds mode off` | 关闭 DeepScientist mode |
| `/ds mode status` | 查看 mode 状态 |
| `/ds doctor` | 检查原生 runtime 状态 |
| `/ds list` | 列出本项目 DeepScientist quests |
| `/ds active [quest_id]` | 查看或设置当前 active quest |
| `/ds status [quest_id]` | 查看 quest 状态 |
| `/ds new <goal>` | 新建 quest |
| `/ds send <quest_id> <message>` | 给 quest 追加用户消息 |
| `/ds stage [stage]` | 查看或设置当前 active stage |
| `/ds events <quest_id> [limit]` | 查看 quest 最近事件 |
| `/ds docs <quest_id>` | 查看 quest 文档 |
| `/ds docs <quest_id> <name ...>` | 读取指定 quest 文档 |

## 6. 工具索引

优先使用 `ds_*` 工具名；`deepscientist_*` 兼容别名只用于过渡。

### 6.1 诊断与 quest 控制

| 工具 | 用途 | 何时调用 |
| --- | --- | --- |
| `ds_doctor` | 检查原生插件/runtime 状态 | 开始 DeepScientist 工作前 |
| `ds_list_quests` | 列出本项目 quests | 续作、查找已有任务 |
| `ds_new_quest` | 新建 quest | 新研究目标 |
| `ds_set_active_quest` | 绑定当前 Hermes session 到 quest | 续作或切换 quest |
| `ds_get_quest_state` | 读取 compact/full quest 状态 | 每轮关键操作前后 |
| `ds_add_user_message` | 向 quest 追加用户指令 | 用户给已有 quest 新指令 |
| `ds_pause_quest` | 标记 quest 暂停 | 等待外部资源或用户决定 |
| `ds_resume_quest` | 恢复 quest | 暂停后继续 |
| `ds_stop_quest` | 标记 quest 停止 | 任务结束或废弃 |

### 6.2 记忆与文档

| 工具 | 用途 | 何时调用 |
| --- | --- | --- |
| `ds_memory_search` | 检索 global/quest memory | 续作、查找背景、查实验约束 |
| `ds_memory_read` | 读取指定 memory card | 需要完整细节时 |
| `ds_memory_write` | 写入 memory card | 保存长期研究事实、约束、结论 |
| `ds_read_quest_documents` | 读取 quest 文档和 skill docs | 阶段切换、恢复上下文 |

记忆与 artifacts 的写入规范：

- memory 写事实、约束、结论、可复用经验。
- artifact 写证据、结构化产物、实验记录、bundle、gate 决策。
- 不要把临时 todo 或一次性状态写成 memory；这类内容可放 artifacts 或当前回复。
- 写 memory 时标题要可检索，正文要包含来源、日期/阶段、适用范围。

### 6.3 Baseline / idea / experiment / paper

| 工具 | 用途 |
| --- | --- |
| `ds_confirm_baseline` | 确认 baseline gate |
| `ds_waive_baseline` | 明确豁免 baseline gate，并记录理由 |
| `ds_attach_baseline` | 把 baseline 附着到 quest 工作区 |
| `ds_submit_idea` | 提交或修订研究 idea |
| `ds_list_research_branches` | 查看 quest research branches/worktrees |
| `ds_record_main_experiment` | 记录主实验 run |
| `ds_create_analysis_campaign` | 创建分析 campaign |
| `ds_record_analysis_slice` | 记录单个分析 slice |
| `ds_submit_paper_outline` | 提交/选择/修订论文 outline |
| `ds_submit_paper_bundle` | 提交论文 bundle manifest |
| `ds_artifact_record` | 记录通用 artifact |

### 6.4 Quest-local execution

`ds_bash_exec` 用于需要被 DeepScientist 记录的 quest-local shell 执行。它支持：

- `operation=run`
- `operation=list`
- `operation=status`
- `operation=read`
- `operation=wait`
- `operation=stop`

使用规则：

- 如果只是普通项目测试，可用 Hermes `terminal`。
- 如果执行结果属于 quest 证据链，优先使用 `ds_bash_exec`，并在结束后记录 artifact 或 experiment。
- 长命令要设置合理 timeout，避免无边界等待。

## 7. 阶段推进规则

DeepScientist 原生插件注册了阶段技能。每次只加载与当前阶段相关的技能，避免上下文过大。

| Stage | 技能 | 目标 | 典型工具 |
| --- | --- | --- | --- |
| `scout` | `deepscientist:scout` | 文献/方向侦察，形成候选 baseline 与 eval contract | `ds_memory_write`, `ds_artifact_record` |
| `baseline` | `deepscientist:baseline` | 确认比较对象、环境、指标与可复现实验 | `ds_confirm_baseline`, `ds_attach_baseline`, `ds_waive_baseline` |
| `idea` | `deepscientist:idea` | 生成、筛选、固化研究 idea | `ds_submit_idea`, `ds_memory_search` |
| `optimize` | `deepscientist:optimize` | 优化方法、超参、实现路线 | `ds_artifact_record`, `ds_bash_exec` |
| `experiment` | `deepscientist:experiment` | 运行主实验和补充实验 | `ds_record_main_experiment`, `ds_bash_exec` |
| `analysis-campaign` | `deepscientist:analysis-campaign` | 系统分析误差、消融、可视化 | `ds_create_analysis_campaign`, `ds_record_analysis_slice` |
| `write` | `deepscientist:write` | 组织论文结构、证据矩阵、草稿 | `ds_submit_paper_outline`, `ds_submit_paper_bundle` |
| `finalize` | `deepscientist:finalize` | 收尾、复现包、最终检查 | `ds_submit_paper_bundle`, `ds_artifact_record` |
| `decision` | `deepscientist:decision` | 多路线决策或停走判断 | `ds_artifact_record`, `ds_memory_write` |
| `figure-polish` | `deepscientist:figure-polish` | 图表润色 | `ds_artifact_record` |
| `intake-audit` | `deepscientist:intake-audit` | 接手已有项目、审计状态 | `ds_get_quest_state`, `ds_memory_search` |
| `review` | `deepscientist:review` | 审稿意见/自查修订 | `ds_artifact_record`, `ds_submit_paper_bundle` |
| `rebuttal` | `deepscientist:rebuttal` | rebuttal 证据组织与回复 | `ds_artifact_record`, `ds_memory_write` |

阶段推进的最低标准：

1. 进入新阶段前读取 `ds_get_quest_state`。
2. 加载对应阶段技能。
3. 明确当前阶段的 gate 或输出物。
4. 完成阶段后写入 memory/artifact。
5. 如果阶段切换会影响路线，先解释理由并记录 decision artifact。

## 8. 典型工作流

### 8.1 新研究项目

1. `ds_doctor`
2. `ds_new_quest(goal=...)`
3. `ds_get_quest_state`
4. `/ds stage scout` 或 `ds_set_active_quest(..., stage="scout")`
5. 加载 `deepscientist:scout`
6. 搜集资料，用 Hermes web/file 工具读取来源。
7. 用 `ds_memory_write` 保存关键结论和约束。
8. 用 `ds_artifact_record` 保存 literature scout 表、baseline shortlist、eval contract。
9. 进入 `baseline` 或 `idea`。

### 8.2 接手已有代码和实验

1. `ds_list_quests`
2. `ds_set_active_quest`
3. `ds_get_quest_state(full=false)`
4. 加载 `deepscientist:intake-audit`
5. 用 Hermes `search_files` / `read_file` 审计代码、日志、配置。
6. 若发现稳定事实，用 `ds_memory_write` 保存。
7. 若形成审计报告，用 `ds_artifact_record` 保存。
8. 若需要跑实验，进入 `experiment`。

### 8.3 记录一次主实验

1. 确认 active quest 和 stage 为 `experiment`。
2. 用 `ds_bash_exec` 或 Hermes `terminal` 执行实验。
3. 读取日志、指标和输出文件。
4. 调用 `ds_record_main_experiment`，至少记录：
   - `run_id`
   - hypothesis
   - setup
   - execution
   - results
   - conclusion
   - evidence_paths
5. 如果结论影响后续路线，再调用 `ds_memory_write`。

### 8.4 论文写作

1. 确认 baseline、idea、experiment、analysis 已有足够 artifact。
2. 进入 `write`。
3. 加载 `deepscientist:write`。
4. 用 `ds_submit_paper_outline` 固化 outline。
5. 写作时用 Hermes 文件工具编辑草稿。
6. 用 `ds_submit_paper_bundle` 记录 draft、references、claim-evidence map、compile report、PDF 路径。
7. 进入 `review` 或 `finalize`。

## 9. 安装后验证

正式安装后，新开 Hermes session 或重启入口，然后检查：

1. `/plugins` 或 Hermes 插件列表能看到 `deepscientist` 已启用。
2. `/ds help` 能显示 native command 帮助。
3. `/ds doctor` 返回 ok。
4. 从项目目录启动 Hermes 后，`/ds new <goal>` 会创建 `<project>/DeepScientist/quests/...`。
5. `ds_doctor` 不依赖全局 npm `ds`。
6. Web UI、TUI、raw MCP、social connector 入口不可用。
7. 插件不会在 Hermes core 目录写入 DeepScientist runtime 文件。

## 10. 故障处理

### 10.1 找不到 quest

- 先确认 Hermes 是否从正确项目目录启动。
- 检查 `<project>/DeepScientist/quests/` 是否存在。
- 使用 `ds_list_quests`，不要跨项目猜测。

### 10.2 memory 搜不到

- 确认 scope：`global`、`quest`、`both`。
- 确认 `quest_id` 是否正确。
- 先用 `ds_memory_read` 读取已知 card。
- 如果是本轮刚生成的临时内容，可能还没写入；用 `ds_memory_write` 固化。

### 10.3 存储位置不对

- 检查 Hermes 启动目录。
- 检查是否设置了 `DEEPSCIENTIST_PROJECT_ROOT`。
- 检查是否设置了 `DEEPSCIENTIST_HERMES_ROOT` 或 `DEEPSCIENTIST_HERMES_CONFIG`。
- 检查 config 中是否显式写了 `runtime_home`。

### 10.4 不知道下一步阶段

- `ds_get_quest_state`。
- 读取 quest docs：`ds_read_quest_documents`。
- 检索 memory：`ds_memory_search(query="current stage next action", scope="both")`。
- 如果仍不确定，写 decision artifact，向用户给出 2-3 个可选路线。

## 11. 完成任务回复

每次完成 DeepScientist 相关任务时，回复用户应包含：

- 当前 active quest id。
- 当前 stage。
- 本轮调用了哪些关键 DeepScientist 工具。
- 新增/更新的 memory 或 artifact 摘要。
- 关键文件路径，尤其是 `<project>/DeepScientist/...` 下的路径。
- 验证结果或未验证项。
- 下一步建议。
- 完成时间。

## 12. 维护者备注

- 原生插件源目录：本仓库根目录，也就是包含 `plugin.yaml` 的目录。
- 当前目录只是源码，不代表已安装。
- 正式安装前不要修改 Hermes core。
- 推荐项目级安装方式见 `docs/AGENT_PROJECT_INSTALL.md`：复制到 `<target-project>/.hermes/plugins/deepscientist/`，并从目标项目目录设置 `HERMES_ENABLE_PROJECT_PLUGINS=true` 启动 Hermes。
- 修改文档后运行文档测试和完整插件测试，确保说明没有回退到外部 CLI、raw MCP、Web UI、TUI 或外部 connector 语义。
