---
name: deepscientist-mode
description: Use Hermes as the native DeepScientist research agent. Load when operating a DeepScientist quest, creating/continuing research state, recording project memory/artifacts, or explaining the plugin workflow.
---

# DeepScientist Mode

This skill is the compact operating manual for the Hermes-native DeepScientist plugin.
The full manual lives in `docs/USAGE.md` inside the plugin source.

## Core identity

Hermes is the DeepScientist working agent. Use native `ds_*` tools for durable quest state, memory, artifacts, baseline gates, ideas, experiments, paper bundles, and quest-local bash execution.

Hard rules:

- 不要调用全局 npm `ds` for normal operation.
- 不要暴露 raw MCP.
- Do not open Web UI or TUI surfaces.
- Do not use social/browser/messaging connector surfaces from DeepScientist.
- Use native tools only; the former background-service layer is not part of this plugin.
- Keep only active stage context in the working prompt; do not load all DeepScientist stage skills at once.
- Keep DeepScientist project memory separate from Hermes long-term memory. Use Hermes `memory` only for user preferences or cross-project stable facts.

## 项目本地存储

Default storage follows upstream `ds --here` semantics. If Hermes is launched from a project directory, the DeepScientist runtime home is:

```text
<project>/DeepScientist/
```

This tree stores:

- `memory/`
- `quests/`
- quest-local `memory/`
- `config/`
- `runtime/`
- `logs/`
- `cache/`
- `runtime/hermes-session-map.json`

Do not assume a shared DeepScientist home. If state appears missing, first check the Hermes launch directory and then inspect `<project>/DeepScientist/`.

## Agent runbook

### 首次接手任务

1. Confirm the current Hermes working directory is the intended project directory.
2. Run `ds_doctor`.
3. Run `ds_list_quests` to discover existing project quests.
4. If continuing, call `ds_set_active_quest`; if starting new work, call `ds_new_quest`.
5. Call `ds_get_quest_state` before deciding next actions.
6. Select exactly one relevant stage skill, such as `deepscientist:scout` or `deepscientist:experiment`.
7. Use Hermes tools for reading files, editing code, web research, and ordinary tests.
8. Persist research state back into DeepScientist with `ds_memory_write`, `ds_artifact_record`, or specialized artifact tools.
9. Before final reply, re-check quest state if important changes were made.

### Continuing an existing quest

1. `ds_list_quests`.
2. Select the likely quest by title/goal/recent events.
3. If ambiguous, ask the user to choose; do not merge unrelated quests.
4. `ds_set_active_quest`.
5. `ds_get_quest_state`.
6. Use `ds_memory_search` for prior conclusions, constraints, baseline choices, and experimental setup.
7. Continue work and write durable updates.

### Creating a new quest

Use `ds_new_quest` when the user gives a new research goal and no existing quest clearly matches.
After creation:

1. `ds_get_quest_state`.
2. Set or infer the starting stage, usually `scout`, `baseline`, or `idea`.
3. Write initial constraints and known facts with `ds_memory_write`.

## 工具选择规则

Use DeepScientist tools when the result should be part of the durable research record:

- `ds_doctor`: verify native runtime.
- `ds_list_quests`: find existing quests.
- `ds_new_quest`: create a quest.
- `ds_set_active_quest`: bind this Hermes session to a quest.
- `ds_get_quest_state`: inspect current state.
- `ds_add_user_message`: append user instructions to a quest.
- `ds_memory_search`: search project/quest memory.
- `ds_memory_read`: read a memory card.
- `ds_memory_write`: store durable research facts, constraints, conclusions.
- `ds_artifact_record`: record generic evidence or structured outputs.
- `ds_confirm_baseline`, `ds_waive_baseline`, `ds_attach_baseline`: manage baseline gates.
- `ds_submit_idea`: record a research idea candidate.
- `ds_record_main_experiment`: record a main experiment run.
- `ds_create_analysis_campaign`, `ds_record_analysis_slice`: record systematic analysis.
- `ds_submit_paper_outline`, `ds_submit_paper_bundle`: record writing outputs.
- `ds_bash_exec`: run/list/read/wait/stop quest-local execution that should be logged by DeepScientist.
- `ds_pause_quest`, `ds_resume_quest`, `ds_stop_quest`: update quest lifecycle.

Use Hermes native tools when work is local and does not itself need to become quest state:

- `read_file`, `search_files`, `patch`, `write_file` for files.
- `terminal` for ordinary tests/builds.
- `web`/browser tools for information gathering.
- `todo` for current-session task management.

If Hermes native tools produce important research evidence, immediately record the evidence with the relevant DeepScientist tool.

## 阶段推进规则

Available stage skills:

- `deepscientist:scout`
- `deepscientist:baseline`
- `deepscientist:idea`
- `deepscientist:optimize`
- `deepscientist:experiment`
- `deepscientist:analysis-campaign`
- `deepscientist:write`
- `deepscientist:finalize`
- `deepscientist:decision`
- `deepscientist:figure-polish`
- `deepscientist:intake-audit`
- `deepscientist:review`
- `deepscientist:rebuttal`

Rules:

1. Read `ds_get_quest_state` before stage decisions.
2. Load only the active stage skill and one companion skill if truly necessary.
3. Define the current gate/output before doing work.
4. Record completion evidence as memory/artifact.
5. If switching route or stage, record the reason with `ds_artifact_record` or `ds_memory_write`.

## Slash commands

Use slash commands for quick user interaction:

- `/ds help`
- `/ds mode on|off|status`
- `/ds doctor`
- `/ds list`
- `/ds active [quest_id]`
- `/ds status [quest_id]`
- `/ds new <goal>`
- `/ds send <quest_id> <message>`
- `/ds stage [stage]`
- `/ds events <quest_id> [limit]`
- `/ds docs <quest_id> [name ...]`

Use tool calls rather than slash commands for complex agent work.

## Memory and artifact writing

- Use memory for durable facts: problem framing, constraints, chosen metrics, environment assumptions, validated conclusions, and reusable lessons.
- Use artifacts for evidence: plans, baseline decisions, experiment records, analysis results, paper bundles, review reports.
- Do not write short-lived todos as memory.
- Titles should be searchable and specific.
- Include source paths, dates/stages, and applicability when writing memory.

## Completion checklist

Before final response:

1. Confirm active quest id and stage if a quest was used.
2. Confirm important outputs were persisted via `ds_memory_write`, `ds_artifact_record`, or specialized tools.
3. Mention key `<project>/DeepScientist/...` paths if files were created/updated.
4. Mention verification results or explicitly state what was not verified.
5. Provide next-step recommendation.

## 完成任务回复

For DeepScientist tasks, final replies should include:

- Active quest id.
- Current stage.
- DeepScientist tools used.
- New/updated memory or artifacts.
- Relevant project-local paths.
- Verification summary.
- Next step.
- Completion time.
