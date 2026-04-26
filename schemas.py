
"""JSON schemas for native DeepScientist Hermes tools."""
from __future__ import annotations

from typing import Any


def _schema(name: str, description: str, properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties or {},
            "required": required or [],
            "additionalProperties": True,
        },
    }

MEMORY_KIND_VALUES = [
    "papers", "ideas", "decisions", "episodes", "knowledge", "templates",
    "paper", "idea", "decision", "episode", "template",
    "constraint", "constraints", "context", "observation", "observations", "hypothesis", "hypotheses", "result", "results", "plan", "plans",
]
MEMORY_KIND_FIELD = {
    "type": "string",
    "enum": MEMORY_KIND_VALUES,
    "description": "DeepScientist memory kind. Canonical kinds are papers, ideas, decisions, episodes, knowledge, templates. Singular and semantic aliases such as constraint/context/observation/hypothesis/result/plan are accepted and normalized by the Hermes wrapper.",
}
PAPER_OUTLINE_MODE_FIELD = {
    "type": "string",
    "enum": ["candidate", "select", "revise", "selected"],
    "description": "Paper outline operation. Use candidate, then select, or revise. selected is accepted as a friendly alias for select.",
}

S = {
    "quest_id": {"type": "string", "description": "DeepScientist quest id. Omit to use active quest when supported."},
    "goal": {"type": "string", "description": "Research goal or request."},
    "title": {"type": "string"},
    "stage": {"type": "string"},
    "message": {"type": "string"},
    "limit": {"type": "integer", "default": 20},
    "query": {"type": "string"},
    "scope": {"type": "string", "enum": ["global", "quest", "both"]},
    "kind": {"type": "string"},
    "content": {"type": "string"},
    "body": {"type": "string"},
    "path": {"type": "string"},
    "payload": {"type": "object"},
    "command": {"type": "string"},
}

DS_DOCTOR = _schema("ds_doctor", "Run native DeepScientist plugin diagnostics without invoking external ds.")
DS_LIST_QUESTS = _schema("ds_list_quests", "List DeepScientist quests from the native runtime home.", {"limit": S["limit"]})
DS_GET_QUEST_STATE = _schema("ds_get_quest_state", "Read compact or full state for a DeepScientist quest.", {"quest_id": S["quest_id"], "full": {"type": "boolean", "default": False}})
DS_SET_ACTIVE_QUEST = _schema("ds_set_active_quest", "Set the active quest for the current Hermes session.", {"quest_id": S["quest_id"], "session_id": {"type": "string"}, "stage": S["stage"]}, ["quest_id"])
DS_NEW_QUEST = _schema("ds_new_quest", "Create a new DeepScientist quest natively.", {"goal": S["goal"], "quest_id": S["quest_id"], "title": S["title"], "session_id": {"type": "string"}}, ["goal"])
DS_ADD_USER_MESSAGE = _schema("ds_add_user_message", "Append a user message/instruction to a quest conversation and queue.", {"quest_id": S["quest_id"], "message": S["message"], "source": {"type": "string"}, "stage": S["stage"]}, ["message"])
DS_READ_QUEST_DOCUMENTS = _schema("ds_read_quest_documents", "List or read quest documents and skill docs.", {"quest_id": S["quest_id"], "names": {"type": "array", "items": {"type": "string"}}, "include_content": {"type": "boolean", "default": True}, "max_chars": {"type": "integer", "default": 12000}})
DS_MEMORY_SEARCH = _schema("ds_memory_search", "Search DeepScientist global/quest memory cards.", {"query": S["query"], "quest_id": S["quest_id"], "scope": S["scope"], "kind": MEMORY_KIND_FIELD, "limit": S["limit"]}, ["query"])
DS_MEMORY_READ = _schema("ds_memory_read", "Read a DeepScientist memory card by id or path.", {"card_id": {"type": "string"}, "path": S["path"], "quest_id": S["quest_id"], "scope": S["scope"]})
DS_MEMORY_WRITE = _schema("ds_memory_write", "Write a DeepScientist memory card. Semantic kind aliases such as constraint/context/observation/hypothesis/result/plan are normalized to knowledge with tags/metadata.", {"title": S["title"], "content": S["content"], "body": S["body"], "markdown": {"type": "string"}, "quest_id": S["quest_id"], "scope": S["scope"], "kind": MEMORY_KIND_FIELD, "tags": {"type": "array", "items": {"type": "string"}}, "metadata": {"type": "object"}}, ["title"])
DS_ARTIFACT_RECORD = _schema("ds_artifact_record", "Record a generic DeepScientist artifact in a quest.", {"quest_id": S["quest_id"], "payload": S["payload"], "kind": S["kind"], "summary": {"type": "string"}, "status": {"type": "string"}, "checkpoint": {"type": "boolean"}}, ["quest_id"])
DS_CONFIRM_BASELINE = _schema("ds_confirm_baseline", "Confirm a baseline gate using native artifact service.", {"quest_id": S["quest_id"], "baseline_path": S["path"], "baseline_id": {"type": "string"}, "variant_id": {"type": "string"}, "summary": {"type": "string"}, "comment": {}, "metric_contract": {"type": "object"}}, ["quest_id", "baseline_path"])
DS_WAIVE_BASELINE = _schema("ds_waive_baseline", "Explicitly waive the baseline gate.", {"quest_id": S["quest_id"], "reason": {"type": "string"}, "comment": {}}, ["quest_id", "reason"])
DS_ATTACH_BASELINE = _schema("ds_attach_baseline", "Attach a registered/imported baseline to the quest workspace.", {"quest_id": S["quest_id"], "baseline_id": {"type": "string"}, "variant_id": {"type": "string"}}, ["quest_id", "baseline_id"])
DS_CREATE_LOCAL_BASELINE = _schema("ds_create_local_baseline", "Create a canonical local baseline stub under baselines/local/<baseline_id>/ and return confirm_args for ds_confirm_baseline.", {"quest_id": S["quest_id"], "baseline_id": {"type": "string"}, "title": S["title"], "summary": {"type": "string"}, "content": S["content"], "source_path": S["path"], "filename": {"type": "string", "default": "baseline.md"}, "variant_id": {"type": "string"}, "metric_contract": {"type": "object"}, "overwrite": {"type": "boolean", "default": False}}, ["quest_id", "baseline_id"])
DS_SUBMIT_IDEA = _schema("ds_submit_idea", "Submit or revise a DeepScientist idea line/candidate.", {"quest_id": S["quest_id"], "title": S["title"], "problem": {"type": "string"}, "hypothesis": {"type": "string"}, "mechanism": {"type": "string"}, "method_brief": {"type": "string"}, "expected_gain": {"type": "string"}, "risks": {"type": "array"}, "decision_reason": {"type": "string"}, "next_target": {"type": "string"}}, ["quest_id", "title"])
DS_LIST_RESEARCH_BRANCHES = _schema("ds_list_research_branches", "List quest research branches/worktrees.", {"quest_id": S["quest_id"]}, ["quest_id"])
DS_RECORD_MAIN_EXPERIMENT = _schema("ds_record_main_experiment", "Record a main experiment run.", {"quest_id": S["quest_id"], "run_id": {"type": "string"}, "title": S["title"], "hypothesis": {"type": "string"}, "setup": {"type": "string"}, "execution": {"type": "string"}, "results": {"type": "string"}, "conclusion": {"type": "string"}, "metric_rows": {"type": "array"}, "metrics_summary": {"type": "object"}, "evidence_paths": {"type": "array"}, "verdict": {"type": "string"}}, ["quest_id", "run_id"])
DS_CREATE_ANALYSIS_CAMPAIGN = _schema("ds_create_analysis_campaign", "Create an analysis campaign.", {"quest_id": S["quest_id"], "campaign_title": S["title"], "campaign_goal": {"type": "string"}, "slices": {"type": "array"}}, ["quest_id", "campaign_title", "campaign_goal", "slices"])
DS_GET_ANALYSIS_CAMPAIGN = _schema("ds_get_analysis_campaign", "Read the active or specified analysis campaign, including pending slice diagnostics.", {"quest_id": S["quest_id"], "campaign_id": {"type": "string", "default": "active", "description": "Use active or omit to inspect the current active campaign."}}, ["quest_id"])
DS_RECORD_ANALYSIS_SLICE = _schema("ds_record_analysis_slice", "Record an analysis slice result.", {"quest_id": S["quest_id"], "campaign_id": {"type": "string"}, "slice_id": {"type": "string"}, "status": {"type": "string"}, "setup": {"type": "string"}, "execution": {"type": "string"}, "results": {"type": "string"}}, ["quest_id", "campaign_id", "slice_id"])
DS_SUBMIT_PAPER_OUTLINE = _schema("ds_submit_paper_outline", "Submit/select/revise a paper outline. selected is accepted as an alias for select.", {"quest_id": S["quest_id"], "mode": PAPER_OUTLINE_MODE_FIELD, "outline_id": {"type": "string"}, "title": S["title"], "note": {"type": "string"}, "story": {"type": "string"}, "ten_questions": {"type": "array"}, "detailed_outline": {"type": "object"}}, ["quest_id"])
DS_SUBMIT_PAPER_BUNDLE = _schema("ds_submit_paper_bundle", "Submit a paper bundle manifest.", {"quest_id": S["quest_id"], "title": S["title"], "summary": {"type": "string"}, "outline_path": S["path"], "draft_path": S["path"], "writing_plan_path": S["path"], "references_path": S["path"], "claim_evidence_map_path": S["path"], "compile_report_path": S["path"], "pdf_path": S["path"], "latex_root_path": S["path"], "prepare_open_source": {"type": "boolean"}}, ["quest_id"])
DS_BASH_EXEC = _schema("ds_bash_exec", "Run/list/read/wait/stop quest-local bash execution sessions natively. By default workdir is limited to the quest; set allow_project_root=true only for administrative project-plugin tasks that must run from <project>.", {"quest_id": S["quest_id"], "command": S["command"], "operation": {"type": "string", "enum": ["run", "list", "status", "read", "wait", "stop"]}, "bash_id": {"type": "string"}, "workdir": {"type": "string"}, "allow_project_root": {"type": "boolean", "default": False}, "env": {"type": "object"}, "timeout_seconds": {"type": "integer"}, "wait": {"type": "boolean"}, "limit": S["limit"]})
DS_PAUSE_QUEST = _schema("ds_pause_quest", "Mark a quest paused.", {"quest_id": S["quest_id"]}, ["quest_id"])
DS_RESUME_QUEST = _schema("ds_resume_quest", "Mark a quest active/resumed.", {"quest_id": S["quest_id"]}, ["quest_id"])
DS_STOP_QUEST = _schema("ds_stop_quest", "Mark a quest stopped.", {"quest_id": S["quest_id"], "reason": {"type": "string"}}, ["quest_id"])

# Compatibility aliases for one transition cycle.
DEEPSCIENTIST_DOCTOR = {**DS_DOCTOR, "name": "deepscientist_doctor"}
DEEPSCIENTIST_LIST_QUESTS = {**DS_LIST_QUESTS, "name": "deepscientist_list_quests"}
DEEPSCIENTIST_STATUS = {**DS_GET_QUEST_STATE, "name": "deepscientist_status"}
DEEPSCIENTIST_NEW_QUEST = {**DS_NEW_QUEST, "name": "deepscientist_new_quest"}
DEEPSCIENTIST_SEND_MESSAGE = {**DS_ADD_USER_MESSAGE, "name": "deepscientist_send_message"}
DEEPSCIENTIST_EVENTS = _schema("deepscientist_events", "Read quest events directly from native quest files.", {"quest_id": S["quest_id"], "limit": S["limit"]}, ["quest_id"])
DEEPSCIENTIST_READ_DOCUMENTS = {**DS_READ_QUEST_DOCUMENTS, "name": "deepscientist_read_documents"}
DEEPSCIENTIST_MEMORY_SEARCH = {**DS_MEMORY_SEARCH, "name": "deepscientist_memory_search"}
DEEPSCIENTIST_MEMORY_WRITE = {**DS_MEMORY_WRITE, "name": "deepscientist_memory_write"}
DEEPSCIENTIST_CONFIRM_BASELINE = {**DS_CONFIRM_BASELINE, "name": "deepscientist_confirm_baseline"}
DEEPSCIENTIST_SUBMIT_IDEA = {**DS_SUBMIT_IDEA, "name": "deepscientist_submit_idea"}
DEEPSCIENTIST_RECORD_EXPERIMENT = {**DS_RECORD_MAIN_EXPERIMENT, "name": "deepscientist_record_experiment"}
DEEPSCIENTIST_SUBMIT_PAPER_BUNDLE = {**DS_SUBMIT_PAPER_BUNDLE, "name": "deepscientist_submit_paper_bundle"}
DEEPSCIENTIST_PAUSE = {**DS_PAUSE_QUEST, "name": "deepscientist_pause"}
DEEPSCIENTIST_RESUME = {**DS_RESUME_QUEST, "name": "deepscientist_resume"}

NATIVE_SCHEMAS = [
    DS_DOCTOR, DS_LIST_QUESTS, DS_GET_QUEST_STATE, DS_SET_ACTIVE_QUEST, DS_NEW_QUEST,
    DS_ADD_USER_MESSAGE, DS_READ_QUEST_DOCUMENTS, DS_MEMORY_SEARCH, DS_MEMORY_READ,
    DS_MEMORY_WRITE, DS_ARTIFACT_RECORD, DS_CONFIRM_BASELINE, DS_WAIVE_BASELINE,
    DS_ATTACH_BASELINE, DS_CREATE_LOCAL_BASELINE, DS_SUBMIT_IDEA, DS_LIST_RESEARCH_BRANCHES, DS_RECORD_MAIN_EXPERIMENT,
    DS_CREATE_ANALYSIS_CAMPAIGN, DS_GET_ANALYSIS_CAMPAIGN, DS_RECORD_ANALYSIS_SLICE, DS_SUBMIT_PAPER_OUTLINE,
    DS_SUBMIT_PAPER_BUNDLE, DS_BASH_EXEC, DS_PAUSE_QUEST, DS_RESUME_QUEST, DS_STOP_QUEST,
]
ALIAS_SCHEMAS = [
    DEEPSCIENTIST_DOCTOR, DEEPSCIENTIST_LIST_QUESTS, DEEPSCIENTIST_STATUS,
    DEEPSCIENTIST_NEW_QUEST, DEEPSCIENTIST_SEND_MESSAGE, DEEPSCIENTIST_EVENTS,
    DEEPSCIENTIST_READ_DOCUMENTS, DEEPSCIENTIST_MEMORY_SEARCH, DEEPSCIENTIST_MEMORY_WRITE,
    DEEPSCIENTIST_CONFIRM_BASELINE, DEEPSCIENTIST_SUBMIT_IDEA, DEEPSCIENTIST_RECORD_EXPERIMENT,
    DEEPSCIENTIST_SUBMIT_PAPER_BUNDLE, DEEPSCIENTIST_PAUSE, DEEPSCIENTIST_RESUME,
]
ALL_SCHEMAS = NATIVE_SCHEMAS + ALIAS_SCHEMAS
