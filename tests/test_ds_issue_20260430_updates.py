from __future__ import annotations

import hashlib
import json
from pathlib import Path

from conftest import load_plugin, parse_json


def test_literature_scout_new_quest_uses_strict_research_anchor_and_default_preparing():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    strict = parse_json(
        tools.ds_new_quest(
            {
                "goal": "严格调研 recurrent-depth Transformer 文献",
                "quest_id": "issue-strict-anchor-test",
                "workspace_mode": "autonomous",
                "final_goal": "literature_scout",
                "delivery_mode": "strict_literature_map",
                "mode_rationale": "用户要求严格文献调研，先进入 strict-research。",
            }
        )
    )
    assert strict["ok"] is True
    assert strict["quest"]["active_anchor"] == "strict-research"
    assert strict["state"]["active_stage"] == "strict-research"

    default = parse_json(tools.ds_new_quest({"goal": "先梳理研究项目", "quest_id": "issue-default-preparing-test"}))
    assert default["ok"] is True
    assert default["quest"]["active_anchor"] == "preparing"
    assert default["state"]["active_stage"] == "preparing"

    gitignore = Path(default["quest"]["quest_root"]) / ".gitignore"
    assert "reference/pdfs/*.pdf" in gitignore.read_text(encoding="utf-8")


def test_set_active_quest_stage_syncs_quest_active_anchor():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "Sync anchor smoke", "quest_id": "issue-anchor-sync-test"}))["quest"]["quest_id"]
    payload = parse_json(tools.ds_set_active_quest({"quest_id": quest_id, "stage": "strict-research"}))

    assert payload["ok"] is True
    assert payload["state"]["active_stage"] == "strict-research"
    assert payload["quest"]["active_anchor"] == "strict-research"
    assert payload["stage_anchor_relation"] == "synced"


def test_artifact_record_merges_top_level_kind_and_propagates_inner_failure(tmp_path, monkeypatch):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    home = tmp_path / "ds-home"
    quest_root = home / "quests" / "artifact-kind-test"
    quest_root.mkdir(parents=True)
    (quest_root / "quest.yaml").write_text("quest_id: artifact-kind-test\n", encoding="utf-8")
    captured = {}

    class FakeArtifact:
        def record(self, root, payload, checkpoint=None):
            captured["root"] = root
            captured["payload"] = dict(payload)
            if payload.get("summary") == "fail":
                return {"ok": False, "errors": ["synthetic artifact failure"], "warnings": []}
            return {"ok": True, "artifact_id": "a1", "recorded": payload.get("kind"), "record": dict(payload)}

    class FakeServices:
        def __init__(self):
            self.home = home
            self.artifact = FakeArtifact()

    monkeypatch.setattr(tools, "get_services", lambda: FakeServices())

    ok = parse_json(
        tools.ds_artifact_record(
            {
                "quest_id": "artifact-kind-test",
                "kind": "report",
                "payload": {"summary": "download report", "status": "completed"},
            }
        )
    )
    assert ok["ok"] is True
    assert captured["payload"]["kind"] == "report"
    assert ok["artifact_ok"] is True

    failed = parse_json(
        tools.ds_artifact_record(
            {
                "quest_id": "artifact-kind-test",
                "kind": "report",
                "payload": {"summary": "fail", "status": "completed"},
            }
        )
    )
    assert failed["ok"] is False
    assert failed["artifact_ok"] is False
    assert "synthetic artifact failure" in failed["error"]


def test_paper_reliability_verifier_uses_arxiv_fallbacks_and_marks_unconfirmed_preprint(monkeypatch):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    verifier = tools._load_bundled_verifier(Path(tools.__file__).resolve().parent / "resources" / "skills" / "paper-reliability-verifier")
    calls = {"openalex": [], "s2_arxiv": []}

    def fake_openalex(doi):
        calls["openalex"].append(doi)
        return {
            "display_name": "Universal Transformers",
            "publication_year": 2018,
            "type": "posted-content",
            "cited_by_count": 396,
            "counts_by_year": [],
            "primary_location": {"source": {"display_name": "arXiv"}},
        }

    def fake_s2_arxiv(arxiv_id):
        calls["s2_arxiv"].append(arxiv_id)
        return {
            "title": "Universal Transformers",
            "year": 2018,
            "citationCount": 390,
            "influentialCitationCount": 30,
            "authors": [{"name": "A"}],
        }

    monkeypatch.setattr(verifier, "openalex", fake_openalex)
    monkeypatch.setattr(verifier, "semantic_scholar_arxiv", fake_s2_arxiv)
    monkeypatch.setattr(verifier, "crossref", lambda doi: {"_error": "disabled"})
    monkeypatch.setattr(verifier, "dblp_detect_accepted_publication", lambda **kwargs: {"status": "dblp_preprint_or_unclassified", "venue_name": "CoRR", "venue_type": "preprint", "acronym": "CoRR"})
    monkeypatch.setattr(verifier, "acl_anthology_detect_accepted_publication", lambda **kwargs: {"status": "acl_anthology_not_found_or_ambiguous"})

    card = verifier.build_card(title="Universal Transformers", arxiv_url="https://arxiv.org/abs/1807.03819")

    assert calls["openalex"] == ["10.48550/arXiv.1807.03819"]
    assert calls["s2_arxiv"] == ["1807.03819"]
    assert card["citations"]["openalex"] == 396
    assert card["citations"]["semantic_scholar"] == 390
    assert card["publication_status"]["is_preprint_only"] is True
    assert card["publication_status"]["status"] == "preprint_unconfirmed"
    assert card["tier"] in {"supporting_evidence", "strong_evidence"}


def test_paper_fetch_writes_pdf_hash_and_ledger(monkeypatch):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "Fetch paper smoke", "quest_id": "issue-paper-fetch-test"}))["quest"]["quest_id"]
    pdf_bytes = b"%PDF-1.4\n1 0 obj <</Type /Page>>\nendobj\n%%EOF\n"
    monkeypatch.setattr(tools, "_download_url_to_bytes", lambda url: pdf_bytes)

    payload = parse_json(
        tools.ds_paper_fetch(
            {
                "quest_id": quest_id,
                "title": "Demo Paper",
                "arxiv_id": "2401.00001",
                "output_name": "demo-paper",
            }
        )
    )

    assert payload["ok"] is True
    assert payload["canonical_url"] == "https://arxiv.org/pdf/2401.00001.pdf"
    assert Path(payload["pdf_path"]).read_bytes() == pdf_bytes
    assert payload["sha256"] == hashlib.sha256(pdf_bytes).hexdigest()
    assert payload["page_count"] == 1
    assert Path(payload["ledger_path"]).exists()


def test_paper_fetch_retries_extensionless_arxiv_pdf_when_dot_pdf_fails(monkeypatch):
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "Fetch paper fallback smoke", "quest_id": "issue-paper-fetch-arxiv-fallback-test"}))["quest"]["quest_id"]
    pdf_bytes = b"%PDF-1.5\n1 0 obj <</Type /Page>>\nendobj\n%%EOF\n"
    calls = []

    def fake_download(url):
        calls.append(url)
        if url.endswith(".pdf"):
            raise RuntimeError("HTTP Error 500: Internal Server Error")
        return pdf_bytes

    monkeypatch.setattr(tools, "_download_url_to_bytes", fake_download)

    payload = parse_json(
        tools.ds_paper_fetch(
            {
                "quest_id": quest_id,
                "title": "Fallback Paper",
                "arxiv_id": "2410.20672v2",
                "output_name": "fallback-paper",
            }
        )
    )

    assert payload["ok"] is True
    assert calls == ["https://arxiv.org/pdf/2410.20672v2.pdf", "https://arxiv.org/pdf/2410.20672v2"]
    assert payload["canonical_url"] == "https://arxiv.org/pdf/2410.20672v2.pdf"
    assert payload["retrieval_url"] == "https://arxiv.org/pdf/2410.20672v2"
    assert payload["attempted_urls"] == calls
    assert Path(payload["pdf_path"]).read_bytes() == pdf_bytes


def test_candidate_upsert_updates_existing_row_without_duplicates():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "Candidate upsert smoke", "quest_id": "issue-candidate-upsert-test"}))["quest"]["quest_id"]
    tools.ds_strict_research_prepare({"quest_id": quest_id, "target_count": 2})
    first = parse_json(tools.ds_strict_research_upsert_candidate({"quest_id": quest_id, "title": "Universal Transformers", "link": "https://arxiv.org/abs/1807.03819"}))
    updated = parse_json(
        tools.ds_strict_research_upsert_candidate(
            {
                "quest_id": quest_id,
                "key": "Universal Transformers",
                "status": "verified-retained",
                "evidence_card": "reference/reliability_cards/universal.json",
                "retain_reject_reason": "high citation and foundational recurrent-depth baseline",
                "note": "keep",
            }
        )
    )

    assert first["action"] == "inserted"
    assert updated["action"] == "updated"
    path = Path(updated["candidate_references_path"])
    body = path.read_text(encoding="utf-8")
    assert body.count("Universal Transformers") == 1
    assert "verified-retained" in body
    assert "reference/reliability_cards/universal.json" in body


def test_record_literature_reading_note_writes_note_ledger_and_bibliography_update():
    load_plugin()
    from hermes_plugins.deepscientist_native import tools

    quest_id = parse_json(tools.ds_new_quest({"goal": "Reading note smoke", "quest_id": "issue-reading-note-test"}))["quest"]["quest_id"]
    tools.ds_strict_research_init_bibliography({"quest_id": quest_id})
    payload = parse_json(
        tools.ds_record_literature_reading_note(
            {
                "quest_id": quest_id,
                "paper_id": "universal-transformers",
                "title": "Universal Transformers",
                "pdf_path": "reference/pdfs/universal.pdf",
                "surfaces_read": ["abstract", "method", "experiments"],
                "sections_read": ["3 Model", "4 Experiments"],
                "note": "Weight sharing plus adaptive recurrence is a foundational baseline.",
                "claim_routes": ["background/recurrent-depth", "method/adaptive-depth"],
                "status": "read",
                "bibliography_updates": {
                    "essential_reference_details": "Universal Transformers: shared-depth Transformer with ACT.",
                    "reference_list": "Use for recurrent-depth and adaptive computation background.",
                    "priority_reference_materials": "Read Section 3 and ACT discussion before writing method background.",
                },
            }
        )
    )

    assert payload["ok"] is True
    assert Path(payload["note_path"]).exists()
    assert Path(payload["ledger_path"]).exists()
    assert payload["completion"]["status_counts"]["read"] == 1
    bibliography_dir = Path(payload["bibliography_dir"])
    assert "shared-depth Transformer" in (bibliography_dir / "essential_reference_details.md").read_text(encoding="utf-8")
