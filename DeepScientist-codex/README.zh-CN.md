# DeepScientist Codex 原生适配器

本目录是给 Codex CLI 使用的 DeepScientist 原生适配，不是 MCP 形式。它把 Hermes-native DeepScientist 的 headless runtime、schemas、resources 和高层 `ds_*` 操作封装进 Codex 插件目录，通过 `scripts/dsctl.py` 直接调用 Python runtime。

核心约束：

- 不使用 MCP：没有 `.mcp.json`，`plugin.json` 没有 server-transport 注册字段。
- 不调用外部 npm `ds` 命令作为正常路径。
- 不恢复 Web UI、TUI、social/browser connector 或 raw dispatcher。
- 从研究项目根目录运行时，runtime 数据保存在 `<project>/DeepScientist/`。
- `scripts/dsctl.py list-tools --format json` 当前暴露 62 个 Codex-native 工具，返回 `transport="codex-native-cli"`、`mcp=false`。
- 已补齐原 DeepScientist Hermes MCP 业务面里的 convenience/introspection 等价工具：`ds_memory_list_recent`、`ds_resolve_runtime_refs`、`ds_get_paper_contract_health`、`ds_get_global_status`、`ds_get_method_scoreboard`、`ds_get_optimization_frontier`、`ds_get_conversation_context`、`ds_list_paper_outlines`、`ds_refresh_summary`、`ds_arxiv`。

快速检查：

```bash
python scripts/dsctl.py doctor --format json
python scripts/dsctl.py list-tools --format json
```

安装到 Codex：

```bash
bash scripts/install.sh
```

安装后在研究项目根目录使用：

```bash
python ~/.codex/plugins/deepscientist-codex/scripts/dsctl.py doctor --format json
```

## 与原 Hermes MCP 插件的功能等价边界

这里的“等价”指研究业务效果、状态写入、文件产物和错误语义尽量保持一致，不指 MCP 协议形态一致：

- `memory.write/read/search/list_recent` 对应 `ds_memory_write`、`ds_memory_read`、`ds_memory_search`、`ds_memory_list_recent`。
- `artifact.record` 及 quest artifact 流程对应 `ds_artifact_record` 和各类专用 `ds_*` artifact 工具。
- `artifact.resolve_runtime_refs`、`artifact.get_global_status`、`artifact.get_method_scoreboard`、`artifact.get_optimization_frontier`、`artifact.get_conversation_context`、`artifact.get_paper_contract_health`、`artifact.list_paper_outlines`、`artifact.refresh_summary`、`artifact.arxiv` 已有同名语义的 `ds_*` Codex-native wrapper。
- `bash_exec` 对应 `ds_bash_exec`，保留 quest-local bash session、日志和状态记录。

因此它是原 DeepScientist Hermes MCP 插件业务能力的 Codex native 功能等价实现，不是 FastMCP / `.mcp.json` / MCP transport 的协议克隆。
