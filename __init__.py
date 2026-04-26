
"""Hermes-native DeepScientist plugin.

This plugin embeds the retained headless DeepScientist research runtime and
exposes curated ds_* tools. It does not install, start, or invoke the global
npm `ds` command at import time.
"""
from __future__ import annotations

from pathlib import Path

# Local source tests may import this file as top-level __init__.py. Hermes imports
# plugin packages under hermes_plugins.<slug>. Make relative imports work in both.
if not __package__ or __package__ == "__init__" or not str(__package__).startswith("hermes_plugins."):
    import sys
    import types

    _parent_name = "hermes_plugins"
    _pkg_name = "hermes_plugins.deepscientist_native"
    if _parent_name not in sys.modules:
        _parent = types.ModuleType(_parent_name)
        _parent.__path__ = []  # type: ignore[attr-defined]
        _parent.__package__ = _parent_name
        sys.modules[_parent_name] = _parent
    __package__ = _pkg_name
    __path__ = [str(Path(__file__).parent)]  # type: ignore[name-defined]
    if __spec__ is not None:
        __spec__.name = _pkg_name
        __spec__.submodule_search_locations = __path__  # type: ignore[name-defined]
    sys.modules.setdefault(_pkg_name, sys.modules[__name__])

from . import commands, mode, schemas, tools

TOOLSET = "deepscientist"

_TOOL_BINDINGS = [
    (schemas.DS_DOCTOR, tools.ds_doctor),
    (schemas.DS_LIST_QUESTS, tools.ds_list_quests),
    (schemas.DS_GET_QUEST_STATE, tools.ds_get_quest_state),
    (schemas.DS_SET_ACTIVE_QUEST, tools.ds_set_active_quest),
    (schemas.DS_NEW_QUEST, tools.ds_new_quest),
    (schemas.DS_ADD_USER_MESSAGE, tools.ds_add_user_message),
    (schemas.DS_RECORD_USER_REQUIREMENT, tools.ds_record_user_requirement),
    (schemas.DS_READ_QUEST_DOCUMENTS, tools.ds_read_quest_documents),
    (schemas.DS_MEMORY_SEARCH, tools.ds_memory_search),
    (schemas.DS_MEMORY_READ, tools.ds_memory_read),
    (schemas.DS_MEMORY_WRITE, tools.ds_memory_write),
    (schemas.DS_ARTIFACT_RECORD, tools.ds_artifact_record),
    (schemas.DS_CONFIRM_BASELINE, tools.ds_confirm_baseline),
    (schemas.DS_WAIVE_BASELINE, tools.ds_waive_baseline),
    (schemas.DS_ATTACH_BASELINE, tools.ds_attach_baseline),
    (schemas.DS_CREATE_LOCAL_BASELINE, tools.ds_create_local_baseline),
    (schemas.DS_SUBMIT_IDEA, tools.ds_submit_idea),
    (schemas.DS_LIST_RESEARCH_BRANCHES, tools.ds_list_research_branches),
    (schemas.DS_RECORD_MAIN_EXPERIMENT, tools.ds_record_main_experiment),
    (schemas.DS_CREATE_ANALYSIS_CAMPAIGN, tools.ds_create_analysis_campaign),
    (schemas.DS_GET_ANALYSIS_CAMPAIGN, tools.ds_get_analysis_campaign),
    (schemas.DS_RECORD_ANALYSIS_SLICE, tools.ds_record_analysis_slice),
    (schemas.DS_SUBMIT_PAPER_OUTLINE, tools.ds_submit_paper_outline),
    (schemas.DS_SUBMIT_PAPER_BUNDLE, tools.ds_submit_paper_bundle),
    (schemas.DS_BASH_EXEC, tools.ds_bash_exec),
    (schemas.DS_WORKFLOW_SMOKE_REPORT, tools.ds_workflow_smoke_report),
    (schemas.DS_PAUSE_QUEST, tools.ds_pause_quest),
    (schemas.DS_RESUME_QUEST, tools.ds_resume_quest),
    (schemas.DS_STOP_QUEST, tools.ds_stop_quest),
    # Compatibility aliases.
    (schemas.DEEPSCIENTIST_DOCTOR, tools.deepscientist_doctor),
    (schemas.DEEPSCIENTIST_LIST_QUESTS, tools.deepscientist_list_quests),
    (schemas.DEEPSCIENTIST_STATUS, tools.deepscientist_status),
    (schemas.DEEPSCIENTIST_NEW_QUEST, tools.deepscientist_new_quest),
    (schemas.DEEPSCIENTIST_SEND_MESSAGE, tools.deepscientist_send_message),
    (schemas.DEEPSCIENTIST_EVENTS, tools.deepscientist_events),
    (schemas.DEEPSCIENTIST_READ_DOCUMENTS, tools.deepscientist_read_documents),
    (schemas.DEEPSCIENTIST_MEMORY_SEARCH, tools.deepscientist_memory_search),
    (schemas.DEEPSCIENTIST_MEMORY_WRITE, tools.deepscientist_memory_write),
    (schemas.DEEPSCIENTIST_CONFIRM_BASELINE, tools.deepscientist_confirm_baseline),
    (schemas.DEEPSCIENTIST_SUBMIT_IDEA, tools.deepscientist_submit_idea),
    (schemas.DEEPSCIENTIST_RECORD_EXPERIMENT, tools.deepscientist_record_experiment),
    (schemas.DEEPSCIENTIST_SUBMIT_PAPER_BUNDLE, tools.deepscientist_submit_paper_bundle),
    (schemas.DEEPSCIENTIST_PAUSE, tools.deepscientist_pause),
    (schemas.DEEPSCIENTIST_RESUME, tools.deepscientist_resume),
]

_STAGE_SKILLS = ("scout", "baseline", "idea", "optimize", "experiment", "analysis-campaign", "write", "finalize", "decision", "figure-polish", "intake-audit", "review", "rebuttal")


def register(ctx) -> None:
    """Register native tools, /ds command, mode hooks, and namespaced skills."""
    for schema, handler in _TOOL_BINDINGS:
        ctx.register_tool(
            name=schema["name"],
            toolset=TOOLSET,
            schema=schema,
            handler=handler,
            description=schema.get("description", ""),
        )

    ctx.register_command(
        "ds",
        commands.ds_command,
        description="Control Hermes-native DeepScientist research mode.",
        args_hint="help|mode|doctor|list|active|status|new|send|stage|events|docs",
    )

    if hasattr(ctx, "register_hook"):
        ctx.register_hook("pre_llm_call", mode.pre_llm_call)
        ctx.register_hook("on_session_start", mode.on_session_start)
        ctx.register_hook("on_session_end", mode.on_session_end)
        ctx.register_hook("post_tool_call", mode.post_tool_call)

    resources = Path(__file__).parent / "resources" / "skills"
    for skill_id in _STAGE_SKILLS:
        skill_md = resources / skill_id / "SKILL.md"
        if skill_md.exists():
            ctx.register_skill(skill_id, skill_md)

    mode_skill = Path(__file__).parent / "skills" / "deepscientist-mode" / "SKILL.md"
    if mode_skill.exists():
        ctx.register_skill("deepscientist-mode", mode_skill)
