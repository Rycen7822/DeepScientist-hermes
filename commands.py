"""Native /ds slash command handler."""
from __future__ import annotations

import shlex

from . import tools
from .redaction import dumps_json
from .state import StateStore

HELP = """DeepScientist native Hermes commands:
  /ds help                         Show this help.
  /ds mode on|off|status           Toggle/check compact DeepScientist mode context.
  /ds doctor                       Check the native runtime without global npm ds.
  /ds list                         List quests under the project-local DeepScientist home.
  /ds active [quest_id]            Show or bind the active quest for this Hermes session.
  /ds status [quest_id]            Read compact quest state.
  /ds new <goal>                   Create a new quest in <project>/DeepScientist/.
  /ds send <quest_id> <message>    Append user instruction to a quest.
  /ds stage [stage]                Show or set active stage.
  /ds events <quest_id> [limit]    Read recent quest events.
  /ds docs <quest_id> [name ...]   List/read quest documents.

Agent guide: load deepscientist:deepscientist-mode and follow docs/USAGE.md.
Native mode does not call the global npm ds command. Web UI, TUI, raw MCP,
social connectors, and the former DeepScientist background service are intentionally unavailable.
Default storage follows ds --here style: <project>/DeepScientist/.
""".strip()


def _err(message: str) -> str:
    return dumps_json({"ok": False, "error": message})


def ds_command(raw_args: str) -> str:
    raw_args = (raw_args or "").strip()
    if not raw_args or raw_args in {"help", "-h", "--help"}:
        return HELP
    try:
        parts = shlex.split(raw_args)
    except ValueError as exc:
        return _err(str(exc))
    if not parts:
        return HELP
    action, rest = parts[0].lower(), parts[1:]
    if action == "mode":
        store = StateStore()
        if not rest or rest[0].lower() == "status":
            return dumps_json({"ok": True, "mode_enabled": store.mode_enabled("local")})
        if rest[0].lower() in {"on", "enable", "enabled"}:
            return dumps_json({"ok": True, "state": store.set_mode_enabled(True, "local")})
        if rest[0].lower() in {"off", "disable", "disabled"}:
            return dumps_json({"ok": True, "state": store.set_mode_enabled(False, "local")})
        return _err("Usage: /ds mode on|off|status")
    if action == "doctor":
        return tools.ds_doctor({})
    if action == "list":
        return tools.ds_list_quests({})
    if action == "active":
        if not rest:
            return dumps_json({"ok": True, "active_quest_id": StateStore().active_quest_id("local")})
        return tools.ds_set_active_quest({"quest_id": rest[0]})
    if action == "status":
        return tools.ds_get_quest_state({"quest_id": rest[0] if rest else ""})
    if action == "new":
        if not rest:
            return _err("Usage: /ds new <goal>")
        return tools.ds_new_quest({"goal": " ".join(rest)})
    if action == "send":
        if len(rest) < 2:
            return _err("Usage: /ds send <quest_id> <message>")
        return tools.ds_add_user_message({"quest_id": rest[0], "message": " ".join(rest[1:])})
    if action == "stage":
        store = StateStore()
        if not rest:
            return dumps_json({"ok": True, "active_stage": store.active_stage("local")})
        return dumps_json({"ok": True, "state": store.set_active_stage(rest[0], "local")})
    if action == "events":
        if not rest:
            return _err("Usage: /ds events <quest_id> [limit]")
        limit = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 20
        return tools.deepscientist_events({"quest_id": rest[0], "limit": limit})
    if action == "docs":
        if not rest:
            return _err("Usage: /ds docs <quest_id> [name ...]")
        return tools.ds_read_quest_documents({"quest_id": rest[0], "names": rest[1:]})
    return _err(f"Unknown /ds action: {action}")
