# DeepScientist Codex Native Adapter

[![Codex Native](https://img.shields.io/badge/Codex-native-4D6A7A)](.codex-plugin/plugin.json)
[![MCP Free](https://img.shields.io/badge/MCP-free-success)](#what-it-deliberately-does-not-provide)
[![Public tools](https://img.shields.io/badge/public_tools-48%20canonical%20ds__%2A-blue)](docs/USAGE.md)
[![Project local](https://img.shields.io/badge/runtime-project--local-purple)](#project-local-runtime)

中文版本: [README.zh-CN.md](README.zh-CN.md)

DeepScientist-codex is a native Codex CLI adapter for the Hermes-native DeepScientist runtime. It packages the headless runtime, curated `ds_*` schemas, Codex skills, and the `scripts/dsctl.py` control surface into one plugin directory.

> Codex does the mechanical work. DeepScientist records the research meaning.

## At a glance

| Area | What you get |
| --- | --- |
| Native transport | `scripts/dsctl.py` returns `transport="codex-native-cli"` and `mcp=false`. |
| Public tool surface | A 48-tool public canonical `ds_*` manifest; legacy `deepscientist_*` names are hidden compatibility aliases only. |
| Research state | Project-local quests, memory, artifacts, baselines, experiments, paper bundles, analysis campaigns, and event reads. |
| Codex skills | `deepscientist-codex` plus stage/support skills for experiments, handoffs, writing plans, paper reliability, and review. |
| Safety boundary | No `.mcp.json`, no FastMCP server, no MCP server transport, and no external ds command for normal operation. |

## Quick start

From this `DeepScientist-codex` directory:

```bash
python scripts/dsctl.py doctor --format json
python scripts/dsctl.py list-tools --format json
```

Install into your normal Codex home:

```bash
bash scripts/install.sh
```

After install, initialize a research project and verify the project-local runtime:

```bash
bash ~/.codex/plugins/deepscientist-codex/scripts/init_project.sh /path/to/project
python ~/.codex/plugins/deepscientist-codex/scripts/dsctl.py --project-root /path/to/project doctor --format json
```

Create a quest from a research project root:

```bash
python ~/.codex/plugins/deepscientist-codex/scripts/dsctl.py call ds_new_quest \
  --json '{"goal":"my research goal","title":"My Quest","workspace_mode":"copilot"}' \
  --format json
```

Then use `scripts/dsctl.py call <ds_tool_name> --json '<object>' --format json` for durable quest, memory, artifact, baseline, experiment, analysis, strict-research, paper-fetch, and paper-bundle operations.

## What it provides

- A Codex plugin manifest at `.codex-plugin/plugin.json`.
- A direct native control script: `scripts/dsctl.py`.
- A self-contained Python package `deepscientist_native/` with the vendored headless DeepScientist runtime, resources, schemas, and curated handlers.
- Codex skills under `skills/`, including `deepscientist-codex`, adapted DeepScientist stage skills, and support skills such as `deepscientist-experiment-execution`, `deepscientist-quest-handoffs`, `deepscientist-writing-plans`, `deepscientist-paper-reliability-verification`, and `deepscientist-review`.
- MCP/event/introspection equivalents including `ds_events`, `ds_memory_list_recent`, `ds_resolve_runtime_refs`, `ds_get_paper_contract_health`, `ds_get_global_status`, `ds_get_method_scoreboard`, `ds_get_optimization_frontier`, `ds_get_conversation_context`, `ds_list_paper_outlines`, `ds_refresh_summary`, and `ds_arxiv`.

## Project-local runtime

When commands run from a research project root, DeepScientist state is stored in:

```text
<project>/DeepScientist/
```

This keeps quests, artifacts, memory, bash provenance, and paper bundles with the research project rather than in global Codex or Hermes state.

## Install details

`scripts/install.sh` performs a local-personal Codex plugin install:

1. Copies this directory to `~/.codex/plugins/deepscientist-codex`.
2. If an installed copy already exists, moves it to `~/.codex/plugins/deepscientist-codex.backup-<timestamp>`.
3. Registers the local marketplace entry in `~/.agents/plugins/marketplace.json`.
4. Enables `[plugins."deepscientist-codex@local-personal"]` in `~/.codex/config.toml`.
5. Runs `scripts/doctor.py`.

For normal Codex use, leave `CODEX_HOME` and `AGENTS_HOME` unset. They are honored for isolated smoke tests or deliberate non-default installs.

See [docs/INSTALL.md](docs/INSTALL.md) and [docs/USAGE.md](docs/USAGE.md) for full details.

## Original Hermes MCP equivalence

This adapter preserves business-workflow effects rather than MCP protocol shape:

| Original DeepScientist/Hermes surface | Codex-native equivalent |
| --- | --- |
| `memory.write/read/search/list_recent` | `ds_memory_write`, `ds_memory_read`, `ds_memory_search`, `ds_memory_list_recent` |
| `artifact.record` and quest artifact flows | `ds_artifact_record` plus specialized `ds_*` artifact tools |
| event reads | `ds_events` |
| `bash_exec` | `ds_bash_exec`, retaining quest-local execution state and logs |
| artifact convenience/introspection helpers | Matching `ds_*` wrappers such as `ds_get_global_status`, `ds_get_method_scoreboard`, `ds_refresh_summary`, and `ds_arxiv` |

The names, CLI entry point, and transport are Codex-native by design. There is no FastMCP server, no `.mcp.json`, and no MCP server transport.

## What it deliberately does not provide

- This is not MCP. There is no `.mcp.json` and `plugin.json` has no server-transport registry field.
- It does not call the external ds command for normal operation.
- It does not expose Web UI, TUI, social connectors, browser connectors, or raw dispatch surfaces.

## Codex-native operation boundary

Use DeepScientist-codex for the research semantic layer: quest state, durable requirements, memory, artifacts, baselines, formal experiment records, analysis campaign state, paper/reliability workflows, and `ds_bash_exec` provenance for formal evidence commands.

Use Codex-native capabilities for routine operation-layer work: file/search/edit, ordinary shell, Git/GitHub mechanics, tests/builds/lint, process monitoring, and local prose editing.
