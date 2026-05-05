# DeepScientist Codex Native Usage

This manual tells Codex CLI how to operate DeepScientist through the native adapter. The adapter is not MCP and does not call external ds.

## Architecture

Codex loads this as a normal Codex plugin via `.codex-plugin/plugin.json`. The plugin contributes skills only. Actual DeepScientist operations are performed by `scripts/dsctl.py`, which imports `deepscientist_native.tools` and calls the curated `ds_*` handlers directly.

Runtime path semantics follow upstream `ds --here` style:

```text
<project>/DeepScientist/
```

This tree stores quests, memory, artifacts, logs, bash execution state, config, cache, and the Codex session map.

## Start of work

1. Work from the target project root.
2. Load the `deepscientist-codex` skill.
3. Run:

```bash
python /path/to/DeepScientist-codex/scripts/dsctl.py doctor --format json
python /path/to/DeepScientist-codex/scripts/dsctl.py call ds_list_quests --format json
```

4. Select an existing quest with `ds_set_active_quest`, or create a new quest with `ds_new_quest`.
5. Load one stage skill if needed, for example `deepscientist-experiment`.
6. Persist key evidence through `ds_memory_write`, `ds_artifact_record`, or specialized tools.

## Command reference

List tools. The output is the Codex-native tool manifest and should report `transport="codex-native-cli"`, `mcp=false`, and the current tool count:

```bash
python scripts/dsctl.py list-tools --format json
```

Show schema:

```bash
python scripts/dsctl.py schema ds_record_main_experiment --format json
```

Call a tool:

```bash
python scripts/dsctl.py call ds_get_quest_state --json '{"quest_id":"001"}' --format json
```

Shortcut form:

```bash
python scripts/dsctl.py ds_get_quest_state --arg quest_id=001 --format json
```

Project override:

```bash
python scripts/dsctl.py --project-root /path/to/project doctor --format json
```

## Important tools

- Quest control: `ds_doctor`, `ds_list_quests`, `ds_get_quest_state`, `ds_set_active_quest`, `ds_new_quest`, `ds_update_quest_mode`, `ds_pause_quest`, `ds_resume_quest`, `ds_stop_quest`.
- Durable requirements: `ds_record_user_requirement`, `ds_add_user_message` with `record_only=true`.
- Memory: `ds_memory_search`, `ds_memory_read`, `ds_memory_write`, `ds_memory_list_recent`.
- Artifacts and baselines: `ds_artifact_record`, `ds_resolve_runtime_refs`, `ds_get_global_status`, `ds_get_method_scoreboard`, `ds_get_optimization_frontier`, `ds_get_conversation_context`, `ds_get_paper_contract_health`, `ds_refresh_summary`, `ds_arxiv`, `ds_create_local_baseline`, `ds_confirm_baseline`, `ds_waive_baseline`, `ds_attach_baseline`.
- Experiment/analysis: `ds_submit_idea`, `ds_record_main_experiment`, `ds_create_analysis_campaign`, `ds_get_analysis_campaign`, `ds_record_analysis_slice`, `ds_bash_exec`.
- Strict research/papers: `ds_strict_research_prepare`, `ds_strict_research_record_candidate`, `ds_strict_research_upsert_candidate`, `ds_paper_fetch`, `ds_record_literature_reading_note`, `ds_strict_research_init_bibliography`, `ds_paper_reliability_verify`, `ds_submit_paper_outline`, `ds_list_paper_outlines`, `ds_submit_paper_bundle`.

## Original Hermes MCP equivalence map

The original Hermes plugin exposed these business capabilities through MCP. In this adapter, use the Codex-native wrappers instead:

- `memory.write`, `memory.read`, `memory.search`, `memory.list_recent`: `ds_memory_write`, `ds_memory_read`, `ds_memory_search`, `ds_memory_list_recent`.
- `artifact.record`: `ds_artifact_record` or the specialized artifact tool for the workflow stage.
- `artifact.resolve_runtime_refs`: `ds_resolve_runtime_refs`.
- `artifact.get_global_status`: `ds_get_global_status`.
- `artifact.get_method_scoreboard`: `ds_get_method_scoreboard`.
- `artifact.get_optimization_frontier`: `ds_get_optimization_frontier`.
- `artifact.get_conversation_context`: `ds_get_conversation_context`.
- `artifact.get_paper_contract_health`: `ds_get_paper_contract_health`.
- `artifact.list_paper_outlines`: `ds_list_paper_outlines`.
- `artifact.refresh_summary`: `ds_refresh_summary`.
- `artifact.arxiv`: `ds_arxiv`.
- `bash_exec`: `ds_bash_exec`.

Equivalence is defined at the research workflow layer: durable quest state, memory/artifact writes, generated files, logs, status payloads, and recoverable error payloads. It intentionally does not preserve MCP protocol objects, FastMCP server behavior, `.mcp.json`, or MCP transport naming.

## Safety boundaries

- no MCP transport;
- no external ds command;
- no Web UI/TUI/connectors;
- no raw shell exposure beyond curated `ds_bash_exec` for quest-local evidence logging;
- keep research memory in DeepScientist state unless the user asks for another store.
