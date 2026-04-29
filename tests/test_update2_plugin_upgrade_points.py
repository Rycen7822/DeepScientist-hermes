from __future__ import annotations

import json
from pathlib import Path

from conftest import load_plugin, parse_json


def test_new_quest_defaults_to_agent_managed_copilot_without_paper_goal():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    payload = parse_json(tools.ds_new_quest({"goal": "帮我检查这个研究仓库的 baseline 是否合理", "quest_id": "default-copilot-test"}))

    assert payload["ok"] is True
    assert payload["workspace_mode"] == "copilot"
    assert payload["decision_policy"] == "user_gated"
    assert payload["final_goal"] == "open_ended"
    assert payload["startup_contract"]["mode_selected_by"] == "hermes_agent"
    assert payload["startup_contract"]["need_research_paper"] is False
    assert "default_copilot" in payload["startup_contract"]["mode_rationale"]

    state = parse_json(tools.ds_get_quest_state({"quest_id": "default-copilot-test", "full": True}))
    contract = state["snapshot"]["startup_contract"]
    assert contract["workspace_mode"] == "copilot"
    assert contract["decision_policy"] == "user_gated"
    assert contract["need_research_paper"] is False


def test_new_quest_accepts_agent_chosen_autonomous_custom_goal_contract():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    payload = parse_json(
        tools.ds_new_quest(
            {
                "goal": "持续调研这个方向并把 idea 打磨到高质量",
                "quest_id": "autonomous-idea-test",
                "workspace_mode": "autonomous",
                "decision_policy": "autonomous",
                "need_research_paper": False,
                "final_goal": "idea_optimization",
                "delivery_mode": "idea_quality",
                "completion_criteria": [
                    "形成结构化文献地图",
                    "筛选 3 个高质量 idea",
                    "给出最推荐的验证路径",
                ],
                "mode_rationale": "用户希望我主动持续推进 idea 质量，不默认写论文。",
            }
        )
    )

    assert payload["ok"] is True
    assert payload["workspace_mode"] == "autonomous"
    assert payload["decision_policy"] == "autonomous"
    assert payload["final_goal"] == "idea_optimization"
    assert payload["delivery_mode"] == "idea_quality"
    assert payload["startup_contract"]["need_research_paper"] is False
    assert payload["startup_contract"]["completion_criteria"] == [
        "形成结构化文献地图",
        "筛选 3 个高质量 idea",
        "给出最推荐的验证路径",
    ]

    state = parse_json(tools.ds_get_quest_state({"quest_id": "autonomous-idea-test", "full": True}))
    contract = state["snapshot"]["startup_contract"]
    assert contract["workspace_mode"] == "autonomous"
    assert contract["final_goal"] == "idea_optimization"
    assert contract["delivery_mode"] == "idea_quality"
    assert contract["need_research_paper"] is False


def test_new_quest_rejects_invalid_agent_mode_contract():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    payload = parse_json(tools.ds_new_quest({"goal": "Invalid mode smoke", "quest_id": "invalid-mode-test", "workspace_mode": "auto"}))

    assert payload["ok"] is False
    assert "workspace_mode" in payload["error"]


def test_update_quest_mode_switches_existing_quest_without_new_quest():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    created = parse_json(
        tools.ds_new_quest(
            {
                "goal": "先用 copilot 打磨实验方案，后续再自主推进",
                "quest_id": "mode-switch-existing-quest-test",
            }
        )
    )
    quest_id = created["quest"]["quest_id"]
    assert created["workspace_mode"] == "copilot"

    switched = parse_json(
        tools.ds_update_quest_mode(
            {
                "quest_id": quest_id,
                "workspace_mode": "autonomous",
                "decision_policy": "autonomous",
                "final_goal": "quality_result",
                "delivery_mode": "experiment_execution",
                "need_research_paper": False,
                "completion_criteria": ["完成实验执行", "记录主要结果"],
                "mode_rationale": "已有方案打磨完毕，现在由 Hermes 在同一研究项目内自主推进实验。",
            }
        )
    )

    assert switched["ok"] is True
    assert switched["quest"]["quest_id"] == quest_id
    assert switched["workspace_mode"] == "autonomous"
    assert switched["decision_policy"] == "autonomous"
    assert switched["final_goal"] == "quality_result"
    assert switched["startup_contract"]["mode_selected_by"] == "hermes_agent"
    assert switched["startup_contract"]["completion_criteria"] == ["完成实验执行", "记录主要结果"]

    state = parse_json(tools.ds_get_quest_state({"quest_id": quest_id, "full": True}))
    contract = state["snapshot"]["startup_contract"]
    assert state["snapshot"]["quest_id"] == quest_id
    assert contract["workspace_mode"] == "autonomous"
    assert contract["final_goal"] == "quality_result"

    back = parse_json(
        tools.ds_update_quest_mode(
            {
                "quest_id": quest_id,
                "workspace_mode": "copilot",
                "mode_rationale": "实验推进暂停，回到用户门控协作模式。",
            }
        )
    )
    assert back["ok"] is True
    assert back["workspace_mode"] == "copilot"
    assert back["decision_policy"] == "user_gated"
    assert back["quest"]["quest_id"] == quest_id


def test_update_quest_mode_rejects_missing_rationale_for_autonomous():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "Mode switch validation", "quest_id": "mode-switch-invalid-test"}))["quest"]["quest_id"]
    payload = parse_json(tools.ds_update_quest_mode({"quest_id": quest_id, "workspace_mode": "autonomous"}))

    assert payload["ok"] is False
    assert "mode_rationale" in payload["error"]


def test_record_only_user_requirement_does_not_leave_pending_queue():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(
        tools.ds_new_quest(
            {
                "goal": "Record-only requirement upgrade smoke",
                "quest_id": "record-only-requirement-test",
            }
        )
    )["quest"]["quest_id"]

    payload = parse_json(
        tools.ds_add_user_message(
            {
                "quest_id": quest_id,
                "message": "Original user requirement should be durable but not queued.",
                "source": "hermes-test",
                "record_only": True,
            }
        )
    )

    assert payload["ok"] is True
    assert payload["record_only"] is True
    assert payload["message"]["delivery_state"] == "record_only"

    state = parse_json(tools.ds_get_quest_state({"quest_id": quest_id, "full": True}))
    snapshot = state["snapshot"]
    assert snapshot["pending_user_message_count"] == 0
    assert snapshot["counts"]["pending_user_message_count"] == 0

    queue_path = Path(snapshot["paths"]["user_message_queue"])
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    assert queue["pending"] == []

    active_requirements = Path(snapshot["paths"]["active_user_requirements"]).read_text(encoding="utf-8")
    assert "Original user requirement should be durable but not queued." in active_requirements

    explicit = parse_json(
        tools.ds_record_user_requirement(
            {
                "quest_id": quest_id,
                "message": "Second record-only requirement uses the dedicated helper.",
                "source": "hermes-test",
            }
        )
    )
    assert explicit["ok"] is True
    assert explicit["record_only"] is True
    assert explicit["message"]["delivery_state"] == "record_only"


def test_paper_bundle_result_repairs_anchor_and_markdown_section_counts(tmp_path, monkeypatch):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    home = tmp_path / "ds-home"
    quest_root = home / "quests" / "paper-upgrade-test"
    quest_root.mkdir(parents=True)
    (quest_root / "quest.yaml").write_text("quest_id: paper-upgrade-test\n", encoding="utf-8")
    draft = tmp_path / "PAPER.md"
    draft.write_text(
        "# Demo paper\n\n"
        "## Abstract\n\ntext\n\n"
        "## Method\n\ntext\n\n"
        "## Results\n\ntext\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "paper_bundle_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "title": "Demo paper",
                "draft_path": str(draft),
                "evidence_gate": {"section_count": 0, "ready_section_count": 0},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    artifact_path = tmp_path / "artifact.json"
    artifact_record = {
        "artifact_id": "artifact-paper-1",
        "kind": "report",
        "flow_type": "paper_bundle",
        "protocol_step": "submit",
        "guidance_vm": {"current_anchor": "baseline", "recommended_skill": "decision"},
        "details": {"section_count": 0, "ready_section_count": 0},
    }
    artifact_path.write_text(json.dumps(artifact_record, ensure_ascii=False), encoding="utf-8")

    class FakeQuest:
        def snapshot(self, quest_id):
            return {"quest_id": quest_id, "active_anchor": "finalize"}

    class FakeArtifact:
        def submit_paper_bundle(self, root, **kwargs):
            return {
                "ok": True,
                "manifest_path": str(manifest_path),
                "manifest": json.loads(manifest_path.read_text(encoding="utf-8")),
                "artifact": {
                    "ok": True,
                    "artifact_path": str(artifact_path),
                    "path": str(artifact_path),
                    "guidance_vm": {"current_anchor": "baseline", "recommended_skill": "decision"},
                    "record": dict(artifact_record),
                },
            }

    class FakeServices:
        def __init__(self):
            self.home = home
            self.quest = FakeQuest()
            self.artifact = FakeArtifact()

    monkeypatch.setattr(tools, "get_services", lambda: FakeServices())

    payload = parse_json(
        tools.ds_submit_paper_bundle(
            {
                "quest_id": "paper-upgrade-test",
                "title": "Demo paper",
                "draft_path": str(draft),
            }
        )
    )

    assert payload["ok"] is True
    assert payload["artifact"]["guidance_vm"]["current_anchor"] == "finalize"
    assert payload["artifact"]["guidance_vm"]["recommended_skill"] == "finalize"
    assert payload["manifest"]["section_count"] == 3
    assert payload["manifest"]["ready_section_count"] == 3
    assert [item["title"] for item in payload["manifest"]["markdown_sections"]] == ["Abstract", "Method", "Results"]

    persisted_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert persisted_manifest["section_count"] == 3
    assert persisted_manifest["evidence_gate"]["section_count"] == 3

    persisted_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert persisted_artifact["guidance_vm"]["current_anchor"] == "finalize"
    assert persisted_artifact["details"]["section_count"] == 3


def test_workflow_smoke_helper_reports_canonical_sequence(tmp_path):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(
        tools.ds_new_quest(
            {
                "goal": "Workflow helper smoke",
                "quest_id": "workflow-helper-test",
            }
        )
    )["quest"]["quest_id"]
    dataset = tmp_path / "tiny-dataset.tar.gz"
    dataset.write_bytes(b"not a real dataset; only path-existence smoke")
    paper = tmp_path / "PAPER.md"
    paper.write_text("# Paper\n\n## Abstract\n\nSmoke.\n", encoding="utf-8")

    payload = parse_json(
        tools.ds_workflow_smoke_report(
            {
                "quest_id": quest_id,
                "dataset_path": str(dataset),
                "paper_path": str(paper),
            }
        )
    )

    assert payload["ok"] is True
    assert payload["checks"]["dataset"]["exists"] is True
    assert payload["checks"]["paper"]["exists"] is True
    assert [step["id"] for step in payload["recommended_sequence"]] == [
        "dataset_inspection",
        "baseline",
        "experiment",
        "analysis",
        "paper_bundle",
        "report_summary",
    ]
    assert "ds_artifact_record" in {step["tool"] for step in payload["recommended_sequence"]}
    assert "paper_bundle" in payload["summary"]


def test_ds_bash_exec_summary_mode_omits_full_entries():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(
        tools.ds_new_quest(
            {
                "goal": "Bash summary mode smoke",
                "quest_id": "bash-summary-mode-test",
            }
        )
    )["quest"]["quest_id"]

    payload = parse_json(
        tools.ds_bash_exec(
            {
                "quest_id": quest_id,
                "command": "printf summary-mode-token",
                "wait": True,
                "timeout_seconds": 20,
                "limit": 20,
                "summary_mode": True,
            }
        )
    )

    assert payload["ok"] is True
    assert payload["summary_mode"] is True
    assert "entries" not in payload
    assert payload["session"]["status"] == "completed"
    assert "summary-mode-token" in payload["output_tail"]
