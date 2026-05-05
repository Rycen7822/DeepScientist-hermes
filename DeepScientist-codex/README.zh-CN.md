# DeepScientist Codex 原生适配器

[![Codex Native](https://img.shields.io/badge/Codex-native-4D6A7A)](.codex-plugin/plugin.json)
[![MCP Free](https://img.shields.io/badge/MCP-free-success)](#不提供的内容)
[![Public tools](https://img.shields.io/badge/public_tools-48%20canonical%20ds__%2A-blue)](docs/USAGE.md)
[![Project local](https://img.shields.io/badge/runtime-project--local-purple)](#项目本地-runtime)

English version: [README.md](README.md)

DeepScientist-codex 是给 Codex CLI 使用的 DeepScientist 原生适配器。它把 Hermes-native DeepScientist 的 headless runtime、curated `ds_*` schemas、Codex skills 和 `scripts/dsctl.py` 控制面打包进一个 Codex 插件目录。

> Codex 做机械动作，DeepScientist 记录研究意义。

## 一眼看懂

| 范围 | 内容 |
| --- | --- |
| 原生传输 | `scripts/dsctl.py` 返回 `transport="codex-native-cli"` 和 `mcp=false`。 |
| 公开工具面 | 当前公开 48 个 canonical `ds_*` 工具；历史 `deepscientist_*` 名称只作为隐藏兼容别名保留。 |
| 研究状态 | 项目本地 quest、memory、artifact、baseline、experiment、paper bundle、analysis campaign 和 event 读取。 |
| Codex skills | `deepscientist-codex` 以及实验、handoff、writing plan、paper reliability、review 等 support skills。 |
| 安全边界 | 不创建 `.mcp.json`，不启动 FastMCP，不注册 MCP server transport，正常路径不调用外部 npm `ds` 命令。 |

## 快速开始

在 `DeepScientist-codex` 目录内检查：

```bash
python scripts/dsctl.py doctor --format json
python scripts/dsctl.py list-tools --format json
```

安装到 Codex：

```bash
bash scripts/install.sh
```

安装后在研究项目根目录初始化提示文件，并验证项目本地 runtime：

```bash
bash ~/.codex/plugins/deepscientist-codex/scripts/init_project.sh /path/to/project
python ~/.codex/plugins/deepscientist-codex/scripts/dsctl.py --project-root /path/to/project doctor --format json
```

从研究项目根目录创建 quest：

```bash
python ~/.codex/plugins/deepscientist-codex/scripts/dsctl.py call ds_new_quest \
  --json '{"goal":"my research goal","title":"My Quest","workspace_mode":"copilot"}' \
  --format json
```

之后用 `scripts/dsctl.py call <ds_tool_name> --json '<object>' --format json` 执行持久化 quest、memory、artifact、baseline、experiment、analysis、strict-research、paper-fetch 和 paper-bundle 操作。

## 提供的内容

- Codex 插件 manifest：`.codex-plugin/plugin.json`。
- 原生控制脚本：`scripts/dsctl.py`。
- 自包含 Python 包：`deepscientist_native/`，内含 vendored headless DeepScientist runtime、resources、schemas 和 curated handlers。
- Codex skills：`skills/` 下的 `deepscientist-codex`，以及 adapted DeepScientist stage skills 和 `deepscientist-experiment-execution`、`deepscientist-quest-handoffs`、`deepscientist-writing-plans`、`deepscientist-paper-reliability-verification`、`deepscientist-review` 等 support skills。
- 原 DeepScientist Hermes MCP 业务面里的 event / convenience / introspection 等价工具：`ds_events`、`ds_memory_list_recent`、`ds_resolve_runtime_refs`、`ds_get_paper_contract_health`、`ds_get_global_status`、`ds_get_method_scoreboard`、`ds_get_optimization_frontier`、`ds_get_conversation_context`、`ds_list_paper_outlines`、`ds_refresh_summary`、`ds_arxiv`。

## 项目本地 runtime

从研究项目根目录运行时，DeepScientist 状态保存在：

```text
<project>/DeepScientist/
```

这会把 quests、artifacts、memory、bash provenance 和 paper bundles 留在研究项目里，而不是散落到全局 Codex 或 Hermes 状态中。

## 安装细节

`scripts/install.sh` 执行 local-personal Codex 插件安装：

1. 复制本目录到 `~/.codex/plugins/deepscientist-codex`。
2. 如果目标目录已存在，先备份为 `~/.codex/plugins/deepscientist-codex.backup-<timestamp>`。
3. 注册 `~/.agents/plugins/marketplace.json`。
4. 在 `~/.codex/config.toml` 中启用 `[plugins."deepscientist-codex@local-personal"]`。
5. 运行 `scripts/doctor.py`。

常规 Codex 使用建议保持 `CODEX_HOME` 和 `AGENTS_HOME` 默认值；这两个环境变量主要用于隔离 smoke test 或明确的非默认安装。

更多细节见 [docs/INSTALL.md](docs/INSTALL.md) 和 [docs/USAGE.md](docs/USAGE.md)。

## 与原 Hermes MCP 插件的功能等价边界

这里的“等价”指研究业务效果、状态写入、文件产物和错误语义尽量保持一致，不指 MCP 协议形态一致：

| 原 DeepScientist/Hermes 表面 | Codex-native 等价工具 |
| --- | --- |
| `memory.write/read/search/list_recent` | `ds_memory_write`、`ds_memory_read`、`ds_memory_search`、`ds_memory_list_recent` |
| `artifact.record` 和 quest artifact 流程 | `ds_artifact_record` 以及各类专用 `ds_*` artifact 工具 |
| quest event 读取 | `ds_events` |
| `bash_exec` | `ds_bash_exec`，保留 quest-local execution state 和日志 |
| artifact convenience / introspection helpers | 对应的 `ds_*` wrappers，例如 `ds_get_global_status`、`ds_get_method_scoreboard`、`ds_refresh_summary`、`ds_arxiv` |

因此它是原 DeepScientist Hermes MCP 插件业务能力的 Codex native 功能等价实现，不是 FastMCP / `.mcp.json` / MCP transport 的协议克隆。

## 不提供的内容

- 不使用 MCP：没有 `.mcp.json`，`plugin.json` 没有 server-transport 注册字段。
- 正常路径不调用外部 npm `ds` 命令。
- 不恢复 Web UI、TUI、social/browser connector 或 raw dispatcher。

## Codex 原生操作边界

DeepScientist-codex 负责研究语义层：quest 状态、持久用户需求、memory、artifact、baseline、正式实验记录、analysis campaign 状态、paper/reliability 流程，以及正式证据命令的 `ds_bash_exec` provenance。

常规操作层继续使用 Codex 原生能力：文件读写搜索、普通 shell、Git/GitHub、测试/构建/lint、进程监控和本地文档编辑。
