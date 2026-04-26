"""DeepScientist native mode hooks for Hermes."""
from __future__ import annotations

from typing import Any

from . import prompt_adapter, stage_router
from .runtime import compact_snapshot, get_services
from .state import StateStore, session_id_from_context

AVAILABLE_TOOLS = "ds_doctor, ds_list_quests, ds_get_quest_state, ds_new_quest, ds_add_user_message, ds_memory_search, ds_memory_write, ds_artifact_record, ds_confirm_baseline, ds_submit_idea, ds_record_main_experiment, ds_submit_paper_bundle, ds_bash_exec"


def _extract_user_message(context: Any = None, **kwargs: Any) -> str:
    for key in ("user_message", "message", "prompt", "input"):
        if kwargs.get(key):
            return str(kwargs[key])
    if isinstance(context, dict):
        for key in ("user_message", "message", "prompt", "input"):
            if context.get(key):
                return str(context[key])
        messages = context.get("messages")
        if isinstance(messages, list):
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    return str(msg.get("content") or "")
    for attr in ("user_message", "message", "prompt", "input"):
        if context is not None and getattr(context, attr, None):
            return str(getattr(context, attr))
    return ""


def build_mode_context(user_message: str, *, session_id: str = "local") -> str:
    store = StateStore()
    if not store.mode_enabled(session_id):
        return ""
    services = get_services()
    active_quest_id = store.active_quest_id(session_id)
    snapshot = None
    if active_quest_id:
        try:
            snapshot = compact_snapshot(services.quest.snapshot(active_quest_id))
        except Exception:
            snapshot = None
    if not active_quest_id:
        quests = services.quest.list_quests()
        if quests:
            active_quest_id = str(quests[0].get("quest_id") or "").strip() or None
            if active_quest_id:
                store.set_active_quest(active_quest_id, session_id)
                try:
                    snapshot = compact_snapshot(services.quest.snapshot(active_quest_id))
                except Exception:
                    snapshot = None
    active_stage = store.active_stage(session_id)
    route = stage_router.route_payload(user_message, active_stage=active_stage, snapshot=snapshot)
    if route.get("stage"):
        store.set_active_stage(str(route["stage"]), session_id)
    skill_excerpt = prompt_adapter.load_skill_excerpt(str(route.get("stage") or "scout"), max_chars=2500)
    lines = [
        "<DeepScientist mode context>",
        "mode: enabled",
        f"session_id: {session_id}",
        f"active_quest_id: {active_quest_id or 'none'}",
        f"active_stage: {route.get('stage')}",
        f"companion_skill: {route.get('companion') or 'none'}",
        f"route_reason: {route.get('reason')} confidence={route.get('confidence')}",
        f"available_native_tools: {AVAILABLE_TOOLS}",
        "rules: Hermes is the DeepScientist runner; do not call external ds; use ds_* tools for durable quest state/artifacts/memory/bash; no Web UI, TUI, or social connectors.",
    ]
    if snapshot:
        lines.extend(["quest_snapshot:", repr(snapshot)])
    else:
        lines.append("quest_snapshot: none; for research workflows create or ask to create a quest with ds_new_quest according to user intent.")
    if skill_excerpt:
        lines.extend(["active_stage_skill_excerpt:", skill_excerpt])
    lines.append("</DeepScientist mode context>")
    return "\n".join(lines)


def pre_llm_call(context: Any = None, **kwargs: Any) -> dict[str, Any]:
    session_id = session_id_from_context(context, **kwargs)
    user_message = _extract_user_message(context, **kwargs)
    block = build_mode_context(user_message, session_id=session_id)
    return {"context": block} if block else {"context": ""}


def on_session_start(context: Any = None, **kwargs: Any) -> dict[str, Any]:
    session_id = session_id_from_context(context, **kwargs)
    store = StateStore()
    store.set_session(session_id)
    return {"ok": True, "session_id": session_id, "mode_enabled": store.mode_enabled(session_id)}


def on_session_end(context: Any = None, **kwargs: Any) -> dict[str, Any]:
    return {"ok": True, "session_id": session_id_from_context(context, **kwargs)}


def post_tool_call(context: Any = None, **kwargs: Any) -> dict[str, Any]:
    return {"ok": True}
