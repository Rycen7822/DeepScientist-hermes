---
name: deepscientist-codex
description: Use DeepScientist from Codex CLI through the native dsctl adapter. Load when a task needs DeepScientist quests, memory, artifacts, experiments, strict literature workflow, or paper/resource operations. This adapter is not MCP and does not call external ds.
---

# DeepScientist Codex Native

This skill is the Codex CLI operating manual for the native DeepScientist adapter.

## Core rules

- Use `scripts/dsctl.py` as the native control surface.
- Do not use MCP for DeepScientist. This plugin intentionally has no `.mcp.json` and no server-transport registry manifest entry.
- Do not call the external npm `ds` command for normal operation.
- Do not open removed Web surface, removed terminal UI, social connectors, browser connectors, or raw internal dispatchers.
- Launch or operate from the research project root whenever possible. Runtime state lives in `<project>/DeepScientist/`.
- Persist important research facts through DeepScientist memory/artifact tools, not only through ordinary files.
- Treat this adapter as a Codex-native functional equivalent of the original DeepScientist Hermes MCP business surface, not as an MCP protocol clone. `list-tools` should report `transport="codex-native-cli"` and `mcp=false`.

## First actions in a project

From the target project root:

```bash
python /path/to/DeepScientist-codex/scripts/dsctl.py doctor --format json
python /path/to/DeepScientist-codex/scripts/dsctl.py list-tools --format json
python /path/to/DeepScientist-codex/scripts/dsctl.py call ds_list_quests --format json
```

If no relevant quest exists, create one:

```bash
python /path/to/DeepScientist-codex/scripts/dsctl.py call ds_new_quest   --json '{"goal":"...","title":"...","workspace_mode":"copilot"}'   --format json
```

## Calling native tools

General form:

```bash
python /path/to/DeepScientist-codex/scripts/dsctl.py call <ds_tool_name> --json '<JSON object>' --format json
```

Examples:

```bash
python /path/to/DeepScientist-codex/scripts/dsctl.py call ds_get_quest_state --json '{"quest_id":"001"}' --format json
python /path/to/DeepScientist-codex/scripts/dsctl.py call ds_memory_write --json '{"quest_id":"001","scope":"quest","kind":"constraint","title":"Constraint","content":"..."}' --format json
python /path/to/DeepScientist-codex/scripts/dsctl.py call ds_artifact_record --json '{"quest_id":"001","kind":"milestone","summary":"...","payload":{"verdict":"pass"}}' --format json
python /path/to/DeepScientist-codex/scripts/dsctl.py call ds_bash_exec --json '{"quest_id":"001","operation":"run","command":"python script.py","wait":true,"summary_mode":true}' --format json
```

## Tool selection

Use DeepScientist tools when the result should become durable research state:

- `ds_doctor`, `ds_list_quests`, `ds_get_quest_state`, `ds_set_active_quest`, `ds_new_quest`, `ds_update_quest_mode`.
- `ds_record_user_requirement`, `ds_add_user_message` with `record_only=true` when needed.
- `ds_memory_search`, `ds_memory_read`, `ds_memory_write`, `ds_memory_list_recent`.
- `ds_artifact_record`, `ds_resolve_runtime_refs`, `ds_get_global_status`, `ds_get_method_scoreboard`, `ds_get_optimization_frontier`, `ds_get_conversation_context`, `ds_get_paper_contract_health`, `ds_list_paper_outlines`, `ds_refresh_summary`, `ds_arxiv`, `ds_confirm_baseline`, `ds_waive_baseline`, `ds_attach_baseline`, `ds_create_local_baseline`.
- `ds_submit_idea`, `ds_record_main_experiment`, analysis campaign tools, paper bundle tools.
- `ds_bash_exec` for quest-local execution that must be logged as evidence.
- strict research and paper tools: `ds_strict_research_prepare`, `ds_strict_research_record_candidate`, `ds_strict_research_upsert_candidate`, `ds_paper_fetch`, `ds_record_literature_reading_note`, `ds_strict_research_init_bibliography`, `ds_paper_reliability_verify`.

Use ordinary Codex file editing and shell commands for local code changes that do not need to become DeepScientist state. If the result matters to the research record, follow up with a `ds_*` memory/artifact call.

## Stage skills

This plugin also ships adapted stage skills such as `deepscientist-experiment`, `deepscientist-strict-research`, `deepscientist-paper-fetch`, and `deepscientist-write`. Load only the active stage skill plus at most one companion skill.

## Bundled support skills

For DeepScientist-specific subtasks, load the adapted Codex skills instead of generic global skills:

- `deepscientist-experiment-execution`
- `deepscientist-quest-handoffs`
- `deepscientist-writing-plans`
- `deepscientist-paper-reliability-verification`
- `deepscientist-review`

Use only one companion support skill alongside the active stage skill. Continue to call durable operations through `scripts/dsctl.py call ds_* ... --format json`; do not use MCP or the external `ds` command.

## Final reply checklist

When completing a DeepScientist task, report:

- quest id and stage if used;
- dsctl commands/tools used;
- files created or modified;
- new/updated DeepScientist memory/artifacts;
- verification results;
- next recommended action.
