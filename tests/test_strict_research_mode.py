from __future__ import annotations

import importlib.util
from pathlib import Path

from conftest import load_plugin, parse_json, PLUGIN_ROOT


class FakeContext:
    def __init__(self, plugin_name="deepscientist"):
        self.plugin_name = plugin_name
        self.tools = {}
        self.commands = {}
        self.hooks = {}
        self.skills = {}

    def register_tool(self, **kwargs):
        self.tools[kwargs["name"]] = kwargs

    def register_command(self, name, handler, **kwargs):
        self.commands[name] = {"handler": handler, **kwargs}

    def register_hook(self, name, handler):
        self.hooks[name] = handler

    def register_skill(self, name, path):
        if ":" in name:
            raise ValueError("plugin skill names must be bare; namespace is derived from plugin name")
        self.skills[f"{self.plugin_name}:{name}"] = Path(path)


def test_strict_research_tools_and_skills_are_registered():
    plugin = load_plugin()

    ctx = FakeContext()
    plugin.register(ctx)

    for tool_name in {
        "ds_strict_research_prepare",
        "ds_strict_research_record_candidate",
        "ds_strict_research_init_bibliography",
        "ds_paper_reliability_verify",
    }:
        assert tool_name in ctx.tools

    for skill_name in {
        "deepscientist:strict-research",
        "deepscientist:paper-reliability-verifier",
    }:
        assert skill_name in ctx.skills
        assert ctx.skills[skill_name].exists()

    verifier_root = PLUGIN_ROOT / "resources" / "skills" / "paper-reliability-verifier"
    assert (verifier_root / "SKILL.md").exists()
    assert (verifier_root / "scripts" / "verifier.py").exists()
    assert (verifier_root / "paper_ranking" / "conference_ranking.csv").exists()
    assert (verifier_root / "paper_ranking" / "journal_ranking.csv").exists()


def test_strict_research_prepare_creates_reference_workspace_and_candidate_file():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "认真调研 diffusion survey", "quest_id": "strict-research-test"}))["quest"]["quest_id"]
    result = parse_json(
        tools.ds_strict_research_prepare(
            {
                "quest_id": quest_id,
                "intent": "用户要求仔细调研论文并撰写综述",
                "target_count": 12,
            }
        )
    )

    assert result["ok"] is True
    assert result["mode"] == "strict_research"
    assert result["target_count"] == 12
    reference_dir = Path(result["reference_dir"])
    candidate_file = Path(result["candidate_references_path"])
    assert reference_dir.name == "reference"
    assert candidate_file == reference_dir / "candidate_references.md"
    assert candidate_file.exists()
    text = candidate_file.read_text(encoding="utf-8")
    assert "candidate_references" in text
    assert "Title" in text and "DOI" in text and "Link" in text
    assert "paper_reliability_verifier" in text
    assert "预印本论文" in "\n".join(result["selection_rules"])


def test_record_candidate_and_bibliography_init_follow_required_layout():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "strict references", "quest_id": "strict-layout-test"}))["quest"]["quest_id"]
    parse_json(tools.ds_strict_research_prepare({"quest_id": quest_id}))
    recorded = parse_json(
        tools.ds_strict_research_record_candidate(
            {
                "quest_id": quest_id,
                "title": "Attention Is All You Need",
                "doi": "10.48550/arXiv.1706.03762",
                "link": "https://arxiv.org/abs/1706.03762",
                "source": "arxiv",
                "note": "user-specified transformer baseline",
            }
        )
    )
    assert recorded["ok"] is True
    text = Path(recorded["candidate_references_path"]).read_text(encoding="utf-8")
    assert "Attention Is All You Need" in text
    assert "10.48550/arXiv.1706.03762" in text

    bib = parse_json(tools.ds_strict_research_init_bibliography({"quest_id": quest_id}))
    assert bib["ok"] is True
    bibliography_dir = Path(bib["bibliography_dir"])
    assert bibliography_dir == Path(bib["reference_dir"]) / "bibliography"
    expected = {
        "essential_reference_details.md",
        "reference_list.md",
        "priority_reference_materials.md",
    }
    assert expected == {Path(path).name for path in bib["files"]}
    for path in bib["files"]:
        content = Path(path).read_text(encoding="utf-8")
        assert "逐篇阅读" in content or "每篇论文" in content or "引用" in content


def test_paper_reliability_verify_runs_bundled_verifier_into_reference_cards(monkeypatch):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "verify paper", "quest_id": "verify-tool-test"}))["quest"]["quest_id"]

    class FakeVerifier:
        @staticmethod
        def build_card(**kwargs):
            assert kwargs["doi"] == "10.0000/mock"
            assert kwargs["title"] == "Mock Paper"
            return {"title": kwargs["title"], "tier": "strong_evidence"}

    def fake_loader(verifier_root):
        assert str(verifier_root).endswith("resources/skills/paper-reliability-verifier")
        return FakeVerifier

    monkeypatch.setattr(tools, "_load_bundled_verifier", fake_loader)
    result = parse_json(tools.ds_paper_reliability_verify({"quest_id": quest_id, "doi": "10.0000/mock", "title": "Mock Paper"}))

    assert result["ok"] is True
    card_path = Path(result["reliability_card_path"])
    assert card_path.parent.name == "reliability_cards"
    assert result["card"]["tier"] == "strong_evidence"
    assert card_path.exists()


def test_reliability_verifier_demotes_non_main_track_top_venue():
    verifier_path = PLUGIN_ROOT / "resources" / "skills" / "paper-reliability-verifier" / "scripts" / "verifier.py"
    spec = importlib.util.spec_from_file_location("paper_reliability_verifier", verifier_path)
    verifier = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(verifier)

    warnings = verifier.non_main_track("Some Workshop Paper", "AAAI Conference on Artificial Intelligence Workshop")
    assert "workshop_or_colocated_event" in warnings
    card = {
        "paper": {"year": 2024},
        "citations": {"openalex": None, "semantic_scholar": None, "crossref": None},
        "venue": {
            "ccf_rank": "A",
            "core_rank": "A*",
            "is_main_track_full_paper": None,
        },
        "journal": None,
        "publication_status": {"is_retracted": False},
        "warnings": warnings,
    }

    tier, _flags, updated_warnings = verifier.classify(card)

    assert tier != "strong_evidence"
    assert "not_main_track_full_paper" in updated_warnings


def test_reliability_verifier_requires_confirmed_acceptance_for_top_venue_tier():
    verifier_path = PLUGIN_ROOT / "resources" / "skills" / "paper-reliability-verifier" / "scripts" / "verifier.py"
    spec = importlib.util.spec_from_file_location("paper_reliability_verifier", verifier_path)
    verifier = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(verifier)

    def classify_with_status(status):
        card = {
            "paper": {"year": 2024},
            "citations": {"openalex": None, "semantic_scholar": None, "crossref": None},
            "venue": {
                "ccf_rank": "A",
                "core_rank": "A*",
                "is_main_track_full_paper": True,
            },
            "journal": None,
            "publication_status": {"is_retracted": False},
            "warnings": [],
        }
        if status is not None:
            card["accepted_publication"] = {"status": status}
        return verifier.classify(card)

    for status in ("metadata_inferred_unconfirmed", None):
        tier, _flags, updated_warnings = classify_with_status(status)

        assert tier != "strong_evidence"
        assert "accepted_publication_not_independently_confirmed" in updated_warnings


def test_acl_anthology_findings_can_be_strong_evidence():
    verifier_path = PLUGIN_ROOT / "resources" / "skills" / "paper-reliability-verifier" / "scripts" / "verifier.py"
    spec = importlib.util.spec_from_file_location("paper_reliability_verifier", verifier_path)
    verifier = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(verifier)

    card = {
        "paper": {"year": 2024},
        "citations": {"openalex": None, "semantic_scholar": None, "crossref": None},
        "venue": {
            "ccf_rank": "A",
            "core_rank": "A*",
            "is_main_track_full_paper": None,
        },
        "journal": None,
        "accepted_publication": {
            "status": "acl_anthology_confirmed",
            "acl_anthology": {
                "venue_id": "findings",
                "venue_acronym": "Findings",
                "volume_title": "Findings of the Association for Computational Linguistics: ACL 2024",
            },
        },
        "publication_status": {"is_retracted": False},
        "warnings": ["findings_or_non_main_track"],
    }

    tier, flags, updated_warnings = verifier.classify(card)

    assert tier == "strong_evidence"
    assert "top_venue" in flags
    assert "acl_anthology_findings_confirmed" in flags
    assert "findings_or_non_main_track" not in updated_warnings
    assert "not_main_track_full_paper" not in updated_warnings


def test_build_card_maps_acl_anthology_findings_to_parent_venue_rank(monkeypatch):
    verifier_path = PLUGIN_ROOT / "resources" / "skills" / "paper-reliability-verifier" / "scripts" / "verifier.py"
    spec = importlib.util.spec_from_file_location("paper_reliability_verifier", verifier_path)
    verifier = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(verifier)

    monkeypatch.setattr(verifier, "openalex_title_search", lambda **kwargs: {"results": []})
    monkeypatch.setattr(verifier, "choose_openalex_work", lambda result, title=None, year=None: None)
    monkeypatch.setattr(verifier, "acl_anthology_detect_accepted_publication", lambda **kwargs: {
        "status": "acl_anthology_confirmed",
        "venue_name": "Findings of the Association for Computational Linguistics: ACL 2024",
        "venue_type": "conference",
        "acronym": "Findings",
        "evidence_source": "ACL Anthology local metadata: title_match",
        "interface_version": "accepted-publication-v1",
        "acl_anthology": {
            "venue_id": "findings",
            "venue_acronym": "Findings",
            "venue_name": "Findings of the Association for Computational Linguistics",
            "volume_title": "Findings of the Association for Computational Linguistics: ACL 2024",
        },
    })

    card = verifier.build_card(title="Mock ACL Findings Paper", year=2024, use_openreview=False, use_dblp=False, use_crossref=False)

    assert card["accepted_publication"]["status"] == "acl_anthology_confirmed"
    assert card["tier"] == "strong_evidence"
    assert card["venue"]["normalized_name"] == "Annual Meeting of the Association for Computational Linguistics"
    assert "acl_anthology_findings_confirmed" in card["quality_flags"]
    assert "findings_or_non_main_track" not in card["warnings"]
    assert "not_main_track_full_paper" not in card["warnings"]
