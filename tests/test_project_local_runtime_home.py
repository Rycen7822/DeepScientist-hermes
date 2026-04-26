from __future__ import annotations

from pathlib import Path

from conftest import load_plugin, parse_json


def test_default_runtime_files_follow_hermes_launch_workdir(tmp_path, monkeypatch):
    project_root = tmp_path / "research-project"
    project_root.mkdir()
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.chdir(project_root)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("DEEPSCIENTIST_HERMES_ROOT", raising=False)
    monkeypatch.delenv("DEEPSCIENTIST_HERMES_CONFIG", raising=False)
    monkeypatch.delenv("DEEPSCIENTIST_HOME", raising=False)
    monkeypatch.delenv("DS_HOME", raising=False)

    load_plugin()
    from hermes_plugins.deepscientist_native import config, runtime, tools
    from hermes_plugins.deepscientist_native.state import StateStore

    expected_home = project_root / "DeepScientist"
    cfg = config.load_config()
    assert cfg.runtime_home == expected_home
    assert cfg.config_root == expected_home
    assert cfg.config_path == expected_home / "config" / "hermes-native.yaml"
    assert cfg.session_map_path == expected_home / "runtime" / "hermes-session-map.json"

    services = runtime.get_services(cfg)
    assert services.home == expected_home.resolve()

    created = parse_json(tools.ds_new_quest({"goal": "Keep all state in this project", "quest_id": "local-state"}))
    assert created["ok"] is True
    quest_root = Path(created["quest"]["quest_root"])
    assert quest_root == expected_home / "quests" / "local-state"
    assert quest_root.exists()

    quest_card = parse_json(tools.ds_memory_write({
        "quest_id": "local-state",
        "kind": "knowledge",
        "title": "Quest local card",
        "content": "quest scoped project-local token",
    }))
    assert quest_card["ok"] is True
    quest_card_path = Path(quest_card["card"]["path"])
    assert quest_card_path.is_relative_to(quest_root / "memory")

    global_card = parse_json(tools.ds_memory_write({
        "scope": "global",
        "kind": "knowledge",
        "title": "Project global card",
        "content": "global scoped project-local token",
    }))
    assert global_card["ok"] is True
    global_card_path = Path(global_card["card"]["path"])
    assert global_card_path.is_relative_to(expected_home / "memory")

    store = StateStore(cfg)
    assert store.path == expected_home / "runtime" / "hermes-session-map.json"
    assert store.path.exists()

    assert (expected_home / "config").exists()
    assert (expected_home / "runtime").exists()
    assert (expected_home / "quests").exists()
    assert (expected_home / "memory").exists()
    assert not (fake_home / ".hermes" / "deepscientist").exists()
