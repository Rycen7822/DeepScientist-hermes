# DeepScientist Codex Native Adapter

This directory is a complete native Codex CLI adapter for the Hermes-native DeepScientist runtime. It is generated as a sibling package inside `DeepScientist-hermes/DeepScientist-codex`.

## What it provides

- A Codex plugin manifest at `.codex-plugin/plugin.json`.
- Codex skills under `skills/`, including `deepscientist-codex`, adapted DeepScientist stage skills, and support skills such as `deepscientist-experiment-execution`, `deepscientist-quest-handoffs`, `deepscientist-writing-plans`, `deepscientist-paper-reliability-verification`, and `deepscientist-review`.
- A direct native control script: `scripts/dsctl.py`.
- A self-contained Python package `deepscientist_native/` with the vendored headless DeepScientist runtime, resources, schemas, and curated handlers.
- Project-local runtime semantics: when run from a project root, DeepScientist state is stored in `<project>/DeepScientist/`.
- Codex-native functional equivalents for the original DeepScientist Hermes MCP business surface. `scripts/dsctl.py list-tools --format json` currently reports 62 tools with `transport="codex-native-cli"` and `mcp=false`.
- MCP convenience/introspection equivalents including `ds_memory_list_recent`, `ds_resolve_runtime_refs`, `ds_get_paper_contract_health`, `ds_get_global_status`, `ds_get_method_scoreboard`, `ds_get_optimization_frontier`, `ds_get_conversation_context`, `ds_list_paper_outlines`, `ds_refresh_summary`, and `ds_arxiv`.

## What it deliberately does not provide

- This is not MCP. There is no `.mcp.json` and `plugin.json` has no server-transport registry field.
- It does not call the external ds command for normal operation.
- It does not expose Web UI, TUI, social connectors, browser connectors, or raw dispatch surfaces.

## Quick smoke

From this directory:

```bash
python scripts/dsctl.py doctor --format json
python scripts/dsctl.py list-tools --format json
```

From a research project root:

```bash
python /path/to/DeepScientist-codex/scripts/dsctl.py call ds_new_quest   --json '{"goal":"my research goal","title":"My Quest","workspace_mode":"copilot"}'   --format json
```

Then use `scripts/dsctl.py call <ds_tool_name> --json '<object>' --format json` for durable quest, memory, artifact, baseline, experiment, analysis, strict-research, paper-fetch, and paper-bundle operations.

## Original Hermes MCP equivalence

This adapter preserves business-workflow effects rather than MCP protocol shape:

- `memory.write/read/search/list_recent` -> `ds_memory_write`, `ds_memory_read`, `ds_memory_search`, `ds_memory_list_recent`.
- `artifact.record` and quest artifacts -> `ds_artifact_record` plus specialized `ds_*` artifact tools.
- `artifact.resolve_runtime_refs`, `artifact.get_global_status`, `artifact.get_method_scoreboard`, `artifact.get_optimization_frontier`, `artifact.get_conversation_context`, `artifact.get_paper_contract_health`, `artifact.list_paper_outlines`, `artifact.refresh_summary`, and `artifact.arxiv` -> matching `ds_*` Codex-native wrappers.
- `bash_exec` -> `ds_bash_exec`, retaining quest-local execution state and logs.

The names, CLI entry point, and transport are Codex-native by design. There is no FastMCP server, no `.mcp.json`, and no MCP server transport.

## Install into Codex

```bash
bash scripts/install.sh
```

The installer copies this directory to `~/.codex/plugins/deepscientist-codex`, registers the local marketplace entry in `~/.agents/plugins/marketplace.json`, and enables `[plugins."deepscientist-codex@local-personal"]` in `~/.codex/config.toml`.

See `docs/INSTALL.md` and `docs/USAGE.md` for full details.
