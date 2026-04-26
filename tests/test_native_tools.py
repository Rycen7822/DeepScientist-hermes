from __future__ import annotations

from conftest import load_plugin, parse_json


def test_native_quest_memory_artifact_and_bash_smoke():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools
    new_payload = parse_json(tools.ds_new_quest({"goal": "Study native plugin testing", "quest_id": "native-test", "title": "Native Test"}))
    assert new_payload["ok"] is True
    quest_id = new_payload["quest"]["quest_id"]
    assert quest_id == "native-test"

    state = parse_json(tools.ds_get_quest_state({"quest_id": quest_id}))
    assert state["ok"] is True
    assert state["snapshot"]["quest_id"] == quest_id

    message = parse_json(tools.ds_add_user_message({"quest_id": quest_id, "message": "Continue scouting papers."}))
    assert message["ok"] is True
    assert message["message"]["role"] == "user"

    card = parse_json(tools.ds_memory_write({"quest_id": quest_id, "kind": "knowledge", "title": "Smoke memory", "content": "native memory search token"}))
    assert card["ok"] is True
    assert card["card"]["metadata"]["scope"] == "quest"

    search = parse_json(tools.ds_memory_search({"quest_id": quest_id, "query": "native memory search token", "scope": "both"}))
    assert search["ok"] is True
    assert search["count"] >= 1

    artifact = parse_json(tools.ds_artifact_record({"quest_id": quest_id, "kind": "report", "summary": "Native artifact record smoke."}))
    assert artifact["ok"] is True
    assert artifact["artifact"]["ok"] is True

    bash = parse_json(tools.ds_bash_exec({"quest_id": quest_id, "command": "printf native-bash-token", "wait": True, "timeout_seconds": 20, "limit": 20}))
    assert bash["ok"] is True
    assert bash["session"]["status"] in {"completed", "failed", "terminated"}
    rendered = "\\n".join(str(item) for item in bash.get("entries", []))
    assert "native-bash-token" in rendered


def test_native_status_controls_and_compatibility_aliases():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools
    quest_id = parse_json(tools.ds_new_quest({"goal": "Control status smoke", "quest_id": "status-test"}))["quest"]["quest_id"]
    paused = parse_json(tools.deepscientist_pause({"quest_id": quest_id}))
    assert paused["ok"] is True
    resumed = parse_json(tools.deepscientist_resume({"quest_id": quest_id}))
    assert resumed["ok"] is True
    listed = parse_json(tools.deepscientist_list_quests({}))
    assert listed["ok"] is True
    assert any(item["quest_id"] == quest_id for item in listed["quests"])
