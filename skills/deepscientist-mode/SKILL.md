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
- Plugin skills are namespaced resources. Always load them with `deepscientist:<skill>` (for example `deepscientist:scout`, `deepscientist:strict-research`, `deepscientist:paper-fetch`); bare names such as `scout` or `paper-fetch` may not appear in ordinary `skills_list` and should not be used with `skill_view`.
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
7. If the same research project moves from user-gated planning to autonomous execution, or back to review, call `ds_update_quest_mode` on the existing quest. Do not create a new quest just to change modes.
8. Continue work and write durable updates.

### Creating a new quest

Use `ds_new_quest` when the user gives a new research goal and no existing quest clearly matches.
Hermes chooses the mode contract; do not make the user type a mode command for normal use.

Defaults and overrides:

- Default is `workspace_mode="copilot"`, `decision_policy="user_gated"`, `need_research_paper=false`, `final_goal="open_ended"`.
- Choose `workspace_mode="autonomous"` only when the task should be owned across multiple steps without stopping after the current request unit.
- Keep `workspace_mode` separate from `final_goal`: autonomous does not imply paper writing.
- For autonomous non-paper tasks, explicitly set `final_goal` such as `idea_optimization`, `literature_scout`, `baseline_reproduction`, `analysis_report`, or `quality_result`, plus `delivery_mode`, `completion_criteria`, and `mode_rationale`.
- Set `final_goal="paper"` or `need_research_paper=true` only for explicit paper/posting/paper-bundle goals.

After creation:

1. `ds_get_quest_state`.
2. Set or infer the starting stage, usually `scout`, `baseline`, or `idea`.
3. Write initial constraints and known facts with `ds_memory_write`.

### Switching mode inside the same quest

A quest is the research-project boundary, not a single question and not a fixed execution mode. For follow-up requests inside the same research project, keep the same quest and switch its mode when the phase changes.

Use `ds_update_quest_mode` when:

- Copilot planning/doc editing/experiment design has converged and Hermes should start autonomous experiment execution.
- Autonomous execution should pause and return to user-gated review or plan revision.
- The terminal goal for the next phase changes while the project identity stays the same.

Rules:

- Do not create a new quest merely to switch between `copilot` and `autonomous`.
- Switching to autonomous requires `mode_rationale`; also provide `final_goal`, `delivery_mode`, and concrete `completion_criteria` whenever possible.
- Autonomous still does not imply paper writing. For experiment execution use `final_goal="quality_result"`, `delivery_mode="experiment_execution"`, and `need_research_paper=false` unless the user explicitly asks for a paper.
- Switching back to copilot defaults to `decision_policy="user_gated"` and should preserve the same quest id.

## 工具选择规则

Use DeepScientist tools when the result should be part of the durable research record:

- `ds_doctor`: verify native runtime.
- `ds_list_quests`: find existing quests.
- `ds_new_quest`: create a quest.
- `ds_set_active_quest`: bind this Hermes session to a quest.
- `ds_get_quest_state`: inspect current state.
- `ds_update_quest_mode`: switch an existing quest between copilot/autonomous without changing quest identity; use for phase transitions inside the same research project.
- `ds_add_user_message`: append user instructions to a quest. Use `record_only=true` when the instruction should be durable context but should not wake/queue a pending user message.
- `ds_record_user_requirement`: record durable user requirements into quest conversation and `active-user-requirements.md` without leaving `pending_user_message_count > 0`.
- `ds_memory_search`: search project/quest memory.
- `ds_memory_read`: read a memory card.
- `ds_memory_write`: store durable research facts, constraints, conclusions.
- `ds_artifact_record`: record generic evidence or structured outputs.
- `ds_confirm_baseline`, `ds_waive_baseline`, `ds_attach_baseline`, `ds_create_local_baseline`: manage baseline gates. Prefer `ds_create_local_baseline` for local stubs under `baselines/local/<baseline_id>/baseline.md` before calling `ds_confirm_baseline`.
- `ds_submit_idea`: record a research idea candidate.
- `ds_record_main_experiment`: record a main experiment run.
- `ds_create_analysis_campaign`, `ds_get_analysis_campaign`, `ds_record_analysis_slice`: record and diagnose systematic analysis. Before writing/paper bundle work, inspect active analysis campaign state and finish or close pending slices.
- `ds_submit_paper_outline`, `ds_submit_paper_bundle`: record writing outputs. Use `candidate -> select` for outline selection; `selected` is only a compatibility alias for `select`. Markdown-only bundles are supported; the Hermes wrapper counts `##` sections and aligns returned guidance with the latest quest anchor.
- `ds_bash_exec`: run/list/read/wait/stop quest-local execution that should be logged by DeepScientist. Set `allow_project_root=true` only when project-root workdir is required; set `summary_mode=true` for compact provenance output; complex Python should be written to a `.py` file before execution instead of large inline heredoc.
- `ds_workflow_smoke_report`: produce a non-mutating Hermes-only checklist for dataset inspection, baseline, experiment, analysis, paper bundle, and final report handoff.
- Strict research tools: when the user asks for careful/strict literature investigation or a survey, the router may recommend strict research but must not force it. The Hermes agent decides from the full user intent whether to enable strict research; if yes, use `ds_strict_research_prepare`, `ds_strict_research_record_candidate`, `ds_paper_reliability_verify`, and `ds_strict_research_init_bibliography` to enforce broad candidate scouting, reliability verification, conservative filtering, quest-local PDF/reference storage, and bibliography updates before writing.
- `ds_pause_quest`, `ds_resume_quest`, `ds_stop_quest`: update quest lifecycle.

Load `deepscientist:paper-fetch` when a DeepScientist quest needs arXiv/OpenReview/PDF retrieval or official paper-resource verification. Do not load note-taking `clip` for this case unless the user explicitly asks to archive the paper into `llm-wiki`.

Use Hermes native tools when work is local and does not itself need to become quest state:

- `read_file`, `search_files`, `patch`, `write_file` for files.
- `terminal` for ordinary tests/builds.
- `web`/browser tools for information gathering.
- `todo` for current-session task management.

If Hermes native tools produce important research evidence, immediately record the evidence with the relevant DeepScientist tool.

## 阶段推进规则

Available stage skills:

- `deepscientist:scout`
- `deepscientist:strict-research`
- `deepscientist:paper-reliability-verifier`
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
- memory kind canonical values are `papers`, `ideas`, `decisions`, `episodes`, `knowledge`, `templates`; semantic aliases such as `constraint`, `context`, `observation`, `hypothesis`, `result`, and `plan` are normalized by the Hermes wrapper and retained as tags/metadata.
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
