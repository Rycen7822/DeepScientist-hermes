from __future__ import annotations

from conftest import load_plugin, parse_json


def test_ds_command_help_mode_new_status_stage():
    load_plugin()
    from hermes_plugins.deepscientist_native import commands

    help_text = commands.ds_command("help")
    assert "/ds new <goal>" in help_text
    assert "global npm ds" in help_text
    assert "daemon" not in help_text.lower()

    mode_on = parse_json(commands.ds_command("mode on"))
    assert mode_on["ok"] is True
    assert mode_on["state"]["mode_enabled"] is True

    created = parse_json(commands.ds_command("new Investigate command smoke"))
    assert created["ok"] is True
    quest_id = created["quest"]["quest_id"]

    active = parse_json(commands.ds_command("active"))
    assert active["active_quest_id"] == quest_id

    stage = parse_json(commands.ds_command("stage scout"))
    assert stage["ok"] is True
    assert stage["state"]["active_stage"] == "scout"

    status = parse_json(commands.ds_command(f"status {quest_id}"))
    assert status["ok"] is True
    assert status["snapshot"]["quest_id"] == quest_id

    sent = parse_json(commands.ds_command(f"send {quest_id} keep going"))
    assert sent["ok"] is True
    assert sent["message"]["content"] == "keep going"

    events = parse_json(commands.ds_command(f"events {quest_id} 5"))
    assert events["ok"] is True
    assert events["count"] >= 1

    docs = parse_json(commands.ds_command(f"docs {quest_id} plan.md"))
    assert docs["ok"] is True


def test_ds_command_daemon_is_removed():
    load_plugin()
    from hermes_plugins.deepscientist_native import commands

    removed = parse_json(commands.ds_command("daemon status"))
    assert removed["ok"] is False
    assert "unknown" in removed["error"].lower()

    unknown = parse_json(commands.ds_command("not-a-command"))
    assert unknown["ok"] is False
