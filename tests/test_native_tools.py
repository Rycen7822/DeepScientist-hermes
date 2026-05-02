from __future__ import annotations

import json
import shutil
from pathlib import Path

from conftest import load_plugin, parse_json


def test_auto_quest_creation_resyncs_numeric_state_from_actual_directories():
    load_plugin()
    from hermes_plugins.deepscientist_native import config, tools

    first = parse_json(tools.ds_new_quest({"goal": "First auto quest"}))
    assert first["ok"] is True
    assert first["quest"]["quest_id"] == "001"

    second = parse_json(tools.ds_new_quest({"goal": "Second auto quest"}))
    assert second["ok"] is True
    assert second["quest"]["quest_id"] == "002"

    cfg = config.load_config()
    second_root = Path(second["quest"]["quest_root"])
    shutil.rmtree(second_root)
    state_path = cfg.runtime_home / "runtime" / "quest_id_state.json"
    assert json.loads(state_path.read_text(encoding="utf-8"))["next_numeric_id"] == 3

    recycled = parse_json(tools.ds_new_quest({"goal": "Recycled auto quest after deletion"}))

    assert recycled["ok"] is True
    assert recycled["quest"]["quest_id"] == "002"
    assert json.loads(state_path.read_text(encoding="utf-8"))["next_numeric_id"] == 3


def test_named_quest_creation_resyncs_numeric_state_before_scaffold():
    load_plugin()
    from hermes_plugins.deepscientist_native import config, tools

    first = parse_json(tools.ds_new_quest({"goal": "First auto quest"}))
    second = parse_json(tools.ds_new_quest({"goal": "Second auto quest"}))
    assert first["quest"]["quest_id"] == "001"
    assert second["quest"]["quest_id"] == "002"

    cfg = config.load_config()
    shutil.rmtree(Path(second["quest"]["quest_root"]))
    state_path = cfg.runtime_home / "runtime" / "quest_id_state.json"
    assert json.loads(state_path.read_text(encoding="utf-8"))["next_numeric_id"] == 3

    named = parse_json(tools.ds_new_quest({"goal": "Named quest after deletion", "quest_id": "named-after-delete"}))

    assert named["ok"] is True
    assert named["quest"]["quest_id"] == "named-after-delete"
    assert json.loads(state_path.read_text(encoding="utf-8"))["next_numeric_id"] == 2


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


def test_memory_kind_aliases_preserve_constraint_semantics():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "Memory alias smoke", "quest_id": "memory-alias-test"}))["quest"]["quest_id"]
    card = parse_json(
        tools.ds_memory_write(
            {
                "quest_id": quest_id,
                "kind": "constraint",
                "title": "Dataset constraint",
                "content": "shared semantic alias token: use an offline fixture when network downloads are unavailable.",
                "tags": ["full-test"],
            }
        )
    )
    parse_json(
        tools.ds_memory_write(
            {
                "quest_id": quest_id,
                "kind": "context",
                "title": "Dataset context",
                "content": "shared semantic alias token: CIFAR downloads may be slow in CI.",
            }
        )
    )

    assert card["ok"] is True
    metadata = card["card"]["metadata"]
    assert metadata["type"] == "knowledge"
    assert metadata["requested_kind"] == "constraint"
    assert metadata["normalized_kind"] == "knowledge"
    assert "constraint" in metadata["tags"]
    assert card["memory_kind_alias"]["requested"] == "constraint"
    assert card["memory_kind_alias"]["normalized"] == "knowledge"

    search = parse_json(tools.ds_memory_search({"quest_id": quest_id, "query": "shared semantic alias token", "scope": "quest", "kind": "constraint"}))
    assert search["ok"] is True
    assert search["count"] == 1
    assert search["matches"][0]["title"] == "Dataset constraint"


def test_create_local_baseline_helper_writes_canonical_stub():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "Baseline helper smoke", "quest_id": "baseline-helper-test"}))["quest"]["quest_id"]
    created = parse_json(
        tools.ds_create_local_baseline(
            {
                "quest_id": quest_id,
                "baseline_id": "random_majority_balanced_binary",
                "content": "# Random majority baseline\n\nAccuracy: 0.50\n",
            }
        )
    )

    assert created["ok"] is True
    baseline_path = Path(created["baseline_path"])
    assert baseline_path.exists()
    assert baseline_path.name == "baseline.md"
    assert baseline_path.parts[-4:] == ("baselines", "local", "random_majority_balanced_binary", "baseline.md")
    assert created["confirm_args"]["baseline_path"] == str(baseline_path)
    assert created["next_tool"] == "ds_confirm_baseline"


def test_ds_bash_exec_allows_project_root_only_when_opted_in():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    project_root = Path.cwd().resolve()
    quest_id = parse_json(tools.ds_new_quest({"goal": "Project-root bash smoke", "quest_id": "bash-project-root-test"}))["quest"]["quest_id"]

    denied = parse_json(
        tools.ds_bash_exec(
            {
                "quest_id": quest_id,
                "command": "pwd",
                "workdir": str(project_root),
                "wait": True,
                "timeout_seconds": 20,
                "limit": 20,
            }
        )
    )
    assert denied["ok"] is False
    assert denied["error_type"] == "ValueError"
    assert "workdir_outside_quest" in denied["error"]

    allowed = parse_json(
        tools.ds_bash_exec(
            {
                "quest_id": quest_id,
                "command": "pwd",
                "workdir": str(project_root),
                "allow_project_root": True,
                "wait": True,
                "timeout_seconds": 20,
                "limit": 20,
            }
        )
    )
    assert allowed["ok"] is True
    assert allowed["session"]["status"] == "completed"
    assert allowed["session"]["cwd"] == str(project_root)
    assert "HERMES_ENABLE_PROJECT_PLUGINS" in allowed["session"]["env_keys"]
    rendered = "\n".join(str(item) for item in allowed.get("entries", []))
    assert str(project_root) in rendered


def test_paper_outline_selected_alias_is_normalized(tmp_path, monkeypatch):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    home = tmp_path / "ds-home"
    quest_root = home / "quests" / "outline-alias-test"
    quest_root.mkdir(parents=True)
    (quest_root / "quest.yaml").write_text("quest_id: outline-alias-test\n", encoding="utf-8")

    class FakeArtifact:
        def __init__(self):
            self.kwargs = None

        def submit_paper_outline(self, root, **kwargs):
            self.kwargs = kwargs
            return {"ok": True, "mode": kwargs.get("mode"), "root": str(root)}

    artifact = FakeArtifact()

    class FakeServices:
        def __init__(self):
            self.home = home
            self.artifact = artifact

    monkeypatch.setattr(tools, "get_services", lambda: FakeServices())
    payload = parse_json(tools.ds_submit_paper_outline({"quest_id": "outline-alias-test", "mode": "selected"}))

    assert payload["ok"] is True
    assert artifact.kwargs["mode"] == "select"
    assert payload["mode"] == "select"


def test_get_analysis_campaign_reports_active_pending_slice(tmp_path, monkeypatch):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    home = tmp_path / "ds-home"
    quest_root = home / "quests" / "analysis-campaign-test"
    quest_root.mkdir(parents=True)
    (quest_root / "quest.yaml").write_text("quest_id: analysis-campaign-test\n", encoding="utf-8")

    class FakeArtifact:
        def get_analysis_campaign(self, root, campaign_id=None):
            return {
                "campaign_id": campaign_id or "analysis-1",
                "pending_slice_count": 1,
                "completed_slice_count": 1,
                "next_pending_slice_id": "scope_caveat",
                "slices": [
                    {"slice_id": "metric_contract", "status": "completed"},
                    {"slice_id": "scope_caveat", "status": "pending"},
                ],
            }

    class FakeServices:
        def __init__(self):
            self.home = home
            self.artifact = FakeArtifact()

    monkeypatch.setattr(tools, "get_services", lambda: FakeServices())
    payload = parse_json(tools.ds_get_analysis_campaign({"quest_id": "analysis-campaign-test", "campaign_id": "active"}))

    assert payload["ok"] is True
    assert payload["campaign"]["pending_slice_count"] == 1
    assert payload["campaign"]["next_pending_slice_id"] == "scope_caveat"
