
"""Hermes-native DeepScientist tool handlers.

Handlers call vendored DeepScientist services directly. They do not shell out to
or require the global npm `ds` command.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from .redaction import dumps_json
from .runtime import compact_snapshot, doctor as native_doctor, get_services
from .state import StateStore


def _payload(data: dict[str, Any]) -> str:
    return dumps_json(data)


def _error(message: str, **extra: Any) -> str:
    return _payload({"ok": False, "error": message, **extra})


def _guard(fn: Callable[[dict[str, Any]], dict[str, Any]]):
    @wraps(fn)
    def wrapper(args: dict | None = None, **kwargs: Any) -> str:
        try:
            payload = fn(dict(args or {}))
            if "ok" not in payload:
                payload = {"ok": True, **payload}
            return _payload(payload)
        except Exception as exc:
            return _error(str(exc), error_type=exc.__class__.__name__)
    return wrapper


def _require(args: dict[str, Any], *names: str) -> str | None:
    missing = [name for name in names if not str(args.get(name) or "").strip()]
    return f"Missing required value(s): {', '.join(missing)}" if missing else None


def _limit(args: dict[str, Any], default: int = 20, maximum: int = 200) -> int:
    try:
        value = int(args.get("limit") or default)
    except Exception:
        value = default
    return max(1, min(value, maximum))


ALLOWED_MEMORY_KINDS = ("papers", "ideas", "decisions", "episodes", "knowledge", "templates")
MEMORY_KIND_ALIASES = {
    "paper": "papers",
    "idea": "ideas",
    "decision": "decisions",
    "episode": "episodes",
    "template": "templates",
}
SEMANTIC_MEMORY_KIND_ALIASES = {
    "constraint": "constraint",
    "constraints": "constraint",
    "context": "context",
    "observation": "observation",
    "observations": "observation",
    "hypothesis": "hypothesis",
    "hypotheses": "hypothesis",
    "result": "result",
    "results": "result",
    "plan": "plan",
    "plans": "plan",
}


def _normalize_tags(tags: Any) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        raw = tags.strip()
        if not raw:
            return []
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                values = parsed
            else:
                values = [part.strip() for part in raw.split(",")]
        else:
            values = [part.strip() for part in raw.split(",")]
    elif isinstance(tags, (list, tuple, set)):
        values = list(tags)
    else:
        values = [tags]
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _memory_kind_aliases_payload() -> dict[str, str]:
    aliases = dict(MEMORY_KIND_ALIASES)
    aliases.update({key: "knowledge" for key in SEMANTIC_MEMORY_KIND_ALIASES})
    return aliases


def _normalize_memory_kind(value: Any, *, default: str = "knowledge") -> dict[str, Any]:
    requested = str(value or default).strip().lower().replace("-", "_") or default
    if requested in ALLOWED_MEMORY_KINDS:
        normalized = requested
        semantic_tag = None
    elif requested in MEMORY_KIND_ALIASES:
        normalized = MEMORY_KIND_ALIASES[requested]
        semantic_tag = None
    elif requested in SEMANTIC_MEMORY_KIND_ALIASES:
        normalized = "knowledge"
        semantic_tag = SEMANTIC_MEMORY_KIND_ALIASES[requested]
    else:
        raise ValueError(
            "Unknown memory kind: "
            f"{requested}. Allowed memory kinds: {', '.join(ALLOWED_MEMORY_KINDS)}. "
            "Supported aliases: "
            + ", ".join(f"{key}->{value}" for key, value in sorted(_memory_kind_aliases_payload().items()))
        )
    return {
        "requested": requested,
        "normalized": normalized,
        "semantic_tag": semantic_tag,
        "alias_applied": requested != normalized,
    }


def _memory_kind_error_payload(exc: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "error": str(exc),
        "error_type": exc.__class__.__name__,
        "allowed_memory_kinds": list(ALLOWED_MEMORY_KINDS),
        "memory_kind_aliases": _memory_kind_aliases_payload(),
    }


def _safe_slug(value: Any, default: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("._-")
    return text or default


def _coerce_env(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    env: dict[str, str] = {}
    for key, item in value.items():
        key_text = str(key or "").strip()
        if not key_text or item is None:
            continue
        env[key_text] = str(item)
    return env


def _active_analysis_campaign_payload(services, root: Path, message: str) -> dict[str, Any]:
    campaign: dict[str, Any] = {}
    try:
        campaign = services.artifact.get_analysis_campaign(root, "active")
        if not isinstance(campaign, dict):
            campaign = {}
    except Exception:
        campaign = {}
    active_id = str(campaign.get("campaign_id") or "").strip() or None
    next_pending = str(campaign.get("next_pending_slice_id") or "").strip() or None
    pending_count = campaign.get("pending_slice_count")
    guidance = "Finish or close the active analysis campaign before selecting an outline or submitting a paper bundle."
    details = []
    if active_id:
        details.append(f"active_analysis_campaign_id={active_id}")
    if next_pending:
        details.append(f"next_pending_slice_id={next_pending}")
    if pending_count is not None:
        details.append(f"pending_slice_count={pending_count}")
    enhanced = message
    if details:
        enhanced = f"{message} ({'; '.join(details)}). {guidance}"
    return {
        "ok": False,
        "error": enhanced,
        "error_type": "ActiveAnalysisCampaignError",
        "active_analysis_campaign_id": active_id,
        "next_pending_slice_id": next_pending,
        "pending_slice_count": pending_count,
        "campaign": campaign or None,
        "guidance": guidance,
    }


def _is_active_analysis_campaign_error(exc: Exception) -> bool:
    return "analysis campaign is active" in str(exc).lower()


def _session_id(args: dict[str, Any]) -> str:
    return str(args.get("session_id") or "local").strip() or "local"


def _active_or_latest_quest_id(args: dict[str, Any], services=None) -> str | None:
    qid = str(args.get("quest_id") or "").strip()
    if qid:
        return qid
    store = StateStore()
    qid = store.active_quest_id(_session_id(args)) or ""
    if qid:
        return qid
    services = services or get_services()
    quests = services.quest.list_quests()
    if quests:
        return str(quests[0].get("quest_id") or "").strip() or None
    return None


def _quest_root(services, quest_id: str) -> Path:
    qid = str(quest_id or "").strip()
    if not qid:
        raise ValueError("quest_id is required")
    root = services.home / "quests" / qid
    if not (root / "quest.yaml").exists():
        raise FileNotFoundError(f"Unknown quest `{qid}`")
    return root


@_guard
def ds_doctor(args: dict[str, Any]) -> dict[str, Any]:
    return native_doctor()


@_guard
def ds_list_quests(args: dict[str, Any]) -> dict[str, Any]:
    services = get_services()
    items = services.quest.list_quests()[: _limit(args, default=50, maximum=500)]
    return {"quests": items, "count": len(items), "runtime_home": str(services.home)}


@_guard
def ds_get_quest_state(args: dict[str, Any]) -> dict[str, Any]:
    services = get_services()
    quest_id = _active_or_latest_quest_id(args, services)
    if not quest_id:
        return {"ok": False, "error": "No quest_id supplied and no active quest exists.", "quests": []}
    snapshot = services.quest.snapshot(quest_id)
    return {"quest_id": quest_id, "snapshot": snapshot if args.get("full") else compact_snapshot(snapshot)}


@_guard
def ds_set_active_quest(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    snapshot = services.quest.snapshot(str(args["quest_id"]))
    state = StateStore().set_active_quest(str(args["quest_id"]), _session_id(args), active_stage=str(args.get("stage") or snapshot.get("active_anchor") or "") or None)
    return {"state": state, "quest": compact_snapshot(snapshot)}


@_guard
def ds_new_quest(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "goal"):
        return {"ok": False, "error": err}
    services = get_services()
    snapshot = services.quest.create(
        str(args.get("goal") or ""),
        quest_id=str(args.get("quest_id") or "").strip() or None,
        runner="hermes",
        title=str(args.get("title") or "").strip() or None,
    )
    state = StateStore().set_active_quest(str(snapshot.get("quest_id")), _session_id(args), active_stage=str(snapshot.get("active_anchor") or "scout"))
    return {"quest": compact_snapshot(snapshot), "state": state}


@_guard
def ds_add_user_message(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "message"):
        return {"ok": False, "error": err}
    services = get_services()
    quest_id = _active_or_latest_quest_id(args, services)
    if not quest_id:
        return {"ok": False, "error": "quest_id is required when no active quest exists"}
    record = services.quest.append_message(
        quest_id,
        role="user",
        content=str(args.get("message") or ""),
        source=str(args.get("source") or "hermes"),
        skill_id=str(args.get("stage") or "").strip() or None,
    )
    if args.get("stage"):
        try:
            services.quest.update_settings(quest_id, active_anchor=str(args.get("stage")))
            StateStore().set_active_stage(str(args.get("stage")), _session_id(args))
        except Exception:
            pass
    return {"quest_id": quest_id, "message": record, "snapshot": compact_snapshot(services.quest.snapshot(quest_id))}


def _read_events_payload(args: dict[str, Any]) -> dict[str, Any]:
    services = get_services()
    quest_id = _active_or_latest_quest_id(args, services)
    if not quest_id:
        return {"ok": False, "error": "quest_id is required"}
    root = _quest_root(services, quest_id)
    path = root / ".ds" / "events.jsonl"
    events = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-_limit(args, 20, 200):]:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                events.append({"raw": line})
    return {"quest_id": quest_id, "events": events, "count": len(events), "path": str(path)}


@_guard
def deepscientist_events(args: dict[str, Any]) -> dict[str, Any]:
    return _read_events_payload(args)


@_guard
def ds_read_quest_documents(args: dict[str, Any]) -> dict[str, Any]:
    services = get_services()
    quest_id = _active_or_latest_quest_id(args, services)
    if not quest_id:
        return {"ok": False, "error": "quest_id is required"}
    docs = services.quest.list_documents(quest_id)
    names = args.get("names") or []
    if isinstance(names, str):
        names = [names]
    names = [str(x) for x in names if str(x).strip()]
    if not names:
        return {"quest_id": quest_id, "documents": docs, "count": len(docs)}
    max_chars = max(100, min(int(args.get("max_chars") or 12000), 200000))
    selected = []
    for name in names:
        hit = next((d for d in docs if name in {str(d.get("document_id")), str(d.get("title")), Path(str(d.get("path") or "")).name}), None)
        if not hit:
            selected.append({"name": name, "ok": False, "error": "document not found"})
            continue
        item = dict(hit)
        if args.get("include_content", True):
            path = Path(str(hit.get("path") or ""))
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                item["content"] = text[:max_chars]
                item["truncated"] = len(text) > max_chars
            except Exception as exc:
                item["read_error"] = str(exc)
        selected.append(item)
    return {"quest_id": quest_id, "documents": selected, "count": len(selected)}


@_guard
def ds_memory_search(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "query"):
        return {"ok": False, "error": err}
    services = get_services()
    quest_id = _active_or_latest_quest_id(args, services)
    scope = str(args.get("scope") or ("both" if quest_id else "global"))
    quest_root = _quest_root(services, quest_id) if quest_id and scope in {"quest", "both"} else None
    kind_info = None
    kind_arg = str(args.get("kind") or "").strip()
    if kind_arg:
        try:
            kind_info = _normalize_memory_kind(kind_arg)
        except ValueError as exc:
            return _memory_kind_error_payload(exc)
    requested_limit = _limit(args)
    service_limit = 500 if kind_info and kind_info.get("semantic_tag") else requested_limit
    matches = services.memory.search(
        str(args.get("query") or ""),
        scope=scope,
        quest_root=quest_root,
        limit=service_limit,
        kind=str(kind_info["normalized"]) if kind_info else None,
    )
    if kind_info and kind_info.get("semantic_tag"):
        semantic_tag = str(kind_info["semantic_tag"])
        filtered = []
        for match in matches:
            tags = {str(tag) for tag in (match.get("tags") or [])}
            if not tags:
                try:
                    card = services.memory.read_card(
                        path=str(match.get("path") or ""),
                        scope=str(match.get("scope") or scope),
                        quest_root=quest_root,
                    )
                    tags = {str(tag) for tag in (card.get("metadata", {}).get("tags") or [])}
                except Exception:
                    tags = set()
            if semantic_tag in tags:
                filtered.append(match)
        matches = filtered[:requested_limit]
    payload = {"matches": matches, "count": len(matches), "scope": scope, "quest_id": quest_id}
    if kind_info:
        payload["memory_kind_alias"] = kind_info
    return payload


@_guard
def ds_memory_read(args: dict[str, Any]) -> dict[str, Any]:
    services = get_services()
    quest_id = _active_or_latest_quest_id(args, services)
    scope = str(args.get("scope") or ("quest" if quest_id else "global"))
    quest_root = _quest_root(services, quest_id) if quest_id and scope == "quest" else None
    card = services.memory.read_card(card_id=str(args.get("card_id") or "").strip() or None, path=str(args.get("path") or "").strip() or None, scope=scope, quest_root=quest_root)
    return {"card": card}


@_guard
def ds_memory_write(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "title"):
        return {"ok": False, "error": err}
    services = get_services()
    quest_id = _active_or_latest_quest_id(args, services)
    scope = str(args.get("scope") or ("quest" if quest_id else "global"))
    quest_root = _quest_root(services, quest_id) if quest_id and scope == "quest" else None
    try:
        kind_info = _normalize_memory_kind(args.get("kind") or "knowledge")
    except ValueError as exc:
        return _memory_kind_error_payload(exc)
    tags = _normalize_tags(args.get("tags"))
    semantic_tag = kind_info.get("semantic_tag")
    if semantic_tag and semantic_tag not in tags:
        tags.append(str(semantic_tag))
    metadata = args.get("metadata") if isinstance(args.get("metadata"), dict) else {}
    metadata = dict(metadata or {})
    metadata["requested_kind"] = kind_info["requested"]
    metadata["normalized_kind"] = kind_info["normalized"]
    if kind_info.get("alias_applied"):
        metadata["kind_alias"] = {"requested": kind_info["requested"], "normalized": kind_info["normalized"]}
    card = services.memory.write_card(
        scope=scope,
        kind=str(kind_info["normalized"]),
        title=str(args.get("title") or ""),
        body=str(args.get("body") if args.get("body") is not None else args.get("content") or ""),
        markdown=str(args.get("markdown") or "") or None,
        quest_root=quest_root,
        quest_id=quest_id,
        tags=tags,
        metadata=metadata,
    )
    return {"card": card, "quest_id": quest_id, "scope": scope, "memory_kind_alias": kind_info}


@_guard
def ds_artifact_record(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    payload = args.get("payload") if isinstance(args.get("payload"), dict) else {}
    if not payload:
        payload = {
            "kind": str(args.get("kind") or "report"),
            "status": str(args.get("status") or "completed"),
            "summary": str(args.get("summary") or "Hermes-native artifact record."),
            "source": {"kind": "hermes", "role": "native-plugin"},
        }
    record = services.artifact.record(root, payload, checkpoint=args.get("checkpoint") if isinstance(args.get("checkpoint"), bool) else None)
    return {"artifact": record, "quest_id": str(args["quest_id"])}


@_guard
def ds_confirm_baseline(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id", "baseline_path"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    return services.artifact.confirm_baseline(
        root,
        baseline_path=str(args.get("baseline_path") or ""),
        comment=args.get("comment"),
        baseline_id=str(args.get("baseline_id") or "").strip() or None,
        variant_id=str(args.get("variant_id") or "").strip() or None,
        summary=str(args.get("summary") or "").strip() or None,
        metric_contract=args.get("metric_contract") if isinstance(args.get("metric_contract"), dict) else None,
    )


@_guard
def ds_waive_baseline(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id", "reason"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    return services.artifact.waive_baseline(root, reason=str(args.get("reason") or ""), comment=args.get("comment"))


@_guard
def ds_attach_baseline(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id", "baseline_id"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    return services.artifact.attach_baseline(root, str(args.get("baseline_id") or ""), variant_id=str(args.get("variant_id") or "").strip() or None)


@_guard
def ds_create_local_baseline(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id", "baseline_id"):
        return {"ok": False, "error": err}
    services = get_services()
    quest_id = str(args["quest_id"])
    root = _quest_root(services, quest_id)
    baseline_id = _safe_slug(args.get("baseline_id"), "local_baseline")
    filename = _safe_slug(args.get("filename") or "baseline.md", "baseline.md")
    if not filename.endswith(".md"):
        filename = f"{filename}.md"
    baseline_root = root / "baselines" / "local" / baseline_id
    baseline_root.mkdir(parents=True, exist_ok=True)
    baseline_path = baseline_root / filename
    overwrite = bool(args.get("overwrite", False))
    if baseline_path.exists() and not overwrite:
        return {
            "ok": False,
            "error": f"Local baseline already exists: {baseline_path}. Pass overwrite=true to replace it.",
            "baseline_path": str(baseline_path),
            "baseline_id": baseline_id,
        }
    source_path = str(args.get("source_path") or "").strip()
    if source_path:
        source = Path(source_path).expanduser()
        if not source.exists():
            return {"ok": False, "error": f"source_path not found: {source}", "baseline_id": baseline_id}
        if source.is_dir():
            if any(baseline_root.iterdir()) and not overwrite:
                return {
                    "ok": False,
                    "error": f"Local baseline directory already has files: {baseline_root}. Pass overwrite=true to replace it.",
                    "baseline_root": str(baseline_root),
                    "baseline_id": baseline_id,
                }
            if overwrite and baseline_root.exists():
                for child in baseline_root.iterdir():
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
            shutil.copytree(source, baseline_root, dirs_exist_ok=True)
            if not baseline_path.exists():
                readme = baseline_root / "README.md"
                baseline_path = readme if readme.exists() else next((p for p in baseline_root.glob("*.md") if p.is_file()), baseline_path)
        else:
            shutil.copy2(source, baseline_path)
    else:
        content = str(args.get("content") or "").strip()
        if not content:
            title = str(args.get("title") or baseline_id).strip() or baseline_id
            summary = str(args.get("summary") or "Local baseline contract created by Hermes-native DeepScientist.").strip()
            content = f"# {title}\n\n{summary}\n"
        baseline_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    confirm_args = {
        "quest_id": quest_id,
        "baseline_path": str(baseline_path),
        "baseline_id": baseline_id,
    }
    if args.get("variant_id"):
        confirm_args["variant_id"] = str(args.get("variant_id"))
    if args.get("summary"):
        confirm_args["summary"] = str(args.get("summary"))
    if isinstance(args.get("metric_contract"), dict):
        confirm_args["metric_contract"] = args.get("metric_contract")
    return {
        "quest_id": quest_id,
        "baseline_id": baseline_id,
        "baseline_root": str(baseline_root),
        "baseline_path": str(baseline_path),
        "confirm_args": confirm_args,
        "next_tool": "ds_confirm_baseline",
        "guidance": "Pass confirm_args to ds_confirm_baseline when this local baseline is ready to open the baseline gate.",
    }


@_guard
def ds_submit_idea(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id", "title"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    keys = ["mode","submission_mode","idea_id","lineage_intent","title","problem","hypothesis","mechanism","method_brief","selection_scores","mechanism_family","change_layer","source_lens","expected_gain","evidence_paths","risks","decision_reason","foundation_ref","foundation_reason","next_target","draft_markdown","source_candidate_id"]
    kwargs = {k: args[k] for k in keys if k in args}
    return services.artifact.submit_idea(root, **kwargs)


@_guard
def ds_list_research_branches(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    return services.artifact.list_research_branches(_quest_root(services, str(args["quest_id"])))


@_guard
def ds_record_main_experiment(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id", "run_id"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    keys = ["run_id","title","hypothesis","setup","execution","results","conclusion","metric_rows","metrics_summary","metric_contract","evidence_paths","changed_files","config_paths","notes","dataset_scope","verdict","status","baseline_id","baseline_variant_id","evaluation_summary","strict_metric_contract"]
    kwargs = {k: args[k] for k in keys if k in args}
    return services.artifact.record_main_experiment(root, **kwargs)


@_guard
def ds_create_analysis_campaign(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id", "campaign_title", "campaign_goal", "slices"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    keys = ["campaign_title","campaign_goal","parent_run_id","slices","campaign_origin","selected_outline_ref","research_questions","experimental_designs","todo_items"]
    kwargs = {k: args[k] for k in keys if k in args}
    return services.artifact.create_analysis_campaign(root, **kwargs)


@_guard
def ds_get_analysis_campaign(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    quest_id = str(args["quest_id"])
    root = _quest_root(services, quest_id)
    campaign_id = str(args.get("campaign_id") or "active").strip() or "active"
    campaign = services.artifact.get_analysis_campaign(root, campaign_id)
    return {"quest_id": quest_id, "campaign_id": campaign_id, "campaign": campaign}


@_guard
def ds_record_analysis_slice(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id", "campaign_id", "slice_id"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    keys = ["campaign_id","slice_id","status","setup","execution","results","evidence_paths","metric_rows","deviations","claim_impact","reviewer_resolution","manuscript_update_hint","next_recommendation","dataset_scope","subset_approval_ref","comparison_baselines","evaluation_summary"]
    kwargs = {k: args[k] for k in keys if k in args}
    return services.artifact.record_analysis_slice(root, **kwargs)


@_guard
def ds_submit_paper_outline(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    keys = ["mode","outline_id","title","note","story","ten_questions","detailed_outline","review_result","selected_reason"]
    kwargs = {k: args[k] for k in keys if k in args}
    if "mode" in kwargs:
        mode = str(kwargs.get("mode") or "candidate").strip().lower() or "candidate"
        if mode == "selected":
            mode = "select"
        if mode not in {"candidate", "select", "revise"}:
            return {
                "ok": False,
                "error": "submit_paper_outline mode must be `candidate`, `select`, or `revise` (`selected` is accepted as an alias for `select`).",
                "allowed_modes": ["candidate", "select", "revise"],
                "mode_aliases": {"selected": "select"},
            }
        kwargs["mode"] = mode
    try:
        return services.artifact.submit_paper_outline(root, **kwargs)
    except ValueError as exc:
        if _is_active_analysis_campaign_error(exc):
            return _active_analysis_campaign_payload(services, root, str(exc))
        raise


@_guard
def ds_submit_paper_bundle(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    root = _quest_root(services, str(args["quest_id"]))
    keys = ["title","summary","outline_path","draft_path","writing_plan_path","references_path","claim_evidence_map_path","compile_report_path","pdf_path","latex_root_path","prepare_open_source"]
    kwargs = {k: args[k] for k in keys if k in args}
    try:
        return services.artifact.submit_paper_bundle(root, **kwargs)
    except ValueError as exc:
        if _is_active_analysis_campaign_error(exc):
            return _active_analysis_campaign_payload(services, root, str(exc))
        raise


@_guard
def ds_bash_exec(args: dict[str, Any]) -> dict[str, Any]:
    services = get_services()
    quest_id = _active_or_latest_quest_id(args, services)
    if not quest_id:
        return {"ok": False, "error": "quest_id is required"}
    root = _quest_root(services, quest_id)
    operation = str(args.get("operation") or ("run" if args.get("command") else "list")).strip().lower()
    if operation == "list":
        return {"quest_id": quest_id, "sessions": services.bash.list_sessions(root, limit=_limit(args, 20, 200)), "summary": services.bash.summary(root)}
    bash_id = str(args.get("bash_id") or "").strip()
    if operation in {"status", "read", "wait", "stop"}:
        if not bash_id:
            bash_id = services.bash.resolve_session_id(root)
        if operation == "stop":
            session = services.bash.request_stop(root, bash_id, reason=str(args.get("reason") or "hermes_native_stop"), force=bool(args.get("force")))
        elif operation == "wait":
            session = services.bash.wait_for_session(root, bash_id, timeout_seconds=int(args.get("timeout_seconds") or 30))
        else:
            session = services.bash.get_session(root, bash_id)
        entries, meta = services.bash.read_log_entries(root, bash_id, limit=_limit(args, 40, 500), prefer_visible=True)
        return {"quest_id": quest_id, "session": session, "entries": entries, "log_meta": meta}
    if operation != "run":
        return {"ok": False, "error": f"Unknown ds_bash_exec operation: {operation}"}
    if err := _require(args, "command"):
        return {"ok": False, "error": err}
    from deepscientist.mcp.context import McpContext
    project_root = services.home.parent.resolve()
    allow_project_root = bool(args.get("allow_project_root"))
    context_worktree_root = project_root if allow_project_root else root
    requested_workdir = str(args.get("workdir") or "").strip() or None
    if allow_project_root and requested_workdir is None:
        requested_workdir = str(root)
    env_payload = _coerce_env(args.get("env"))
    if allow_project_root:
        env_payload.setdefault("HERMES_ENABLE_PROJECT_PLUGINS", "true")
        env_payload.setdefault("DEEPSCIENTIST_PROJECT_ROOT", str(project_root))
        env_payload.setdefault("DEEPSCIENTIST_HERMES_PROJECT_ROOT", str(project_root))
        existing_pythonpath = env_payload.get("PYTHONPATH") or os.environ.get("PYTHONPATH", "")
        pythonpath_parts = [part for part in existing_pythonpath.split(os.pathsep) if part]
        project_plugins = project_root / ".hermes" / "plugins"
        if project_plugins.exists():
            plugin_parent = str(project_plugins.resolve())
            if plugin_parent not in pythonpath_parts:
                pythonpath_parts.insert(0, plugin_parent)
        if pythonpath_parts:
            env_payload["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    context = McpContext(home=services.home, quest_id=quest_id, quest_root=root, run_id=None, active_anchor=None, conversation_id=f"hermes:{quest_id}", agent_role="hermes", worker_id=None, worktree_root=context_worktree_root, team_mode=None)
    session = services.bash.start_session(context, command=str(args.get("command") or ""), mode="exec", workdir=requested_workdir, env=env_payload, timeout_seconds=int(args.get("timeout_seconds") or 120), comment=args.get("comment"))
    if args.get("wait", True):
        session = services.bash.wait_for_session(root, str(session.get("bash_id")), timeout_seconds=int(args.get("timeout_seconds") or 120))
    entries, meta = services.bash.read_log_entries(root, str(session.get("bash_id")), limit=_limit(args, 40, 500), prefer_visible=True)
    return {"quest_id": quest_id, "session": session, "entries": entries, "log_meta": meta}


@_guard
def ds_pause_quest(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    return {"quest": compact_snapshot(services.quest.set_status(str(args["quest_id"]), "paused"))}


@_guard
def ds_resume_quest(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    return {"quest": compact_snapshot(services.quest.set_status(str(args["quest_id"]), "active"))}


@_guard
def ds_stop_quest(args: dict[str, Any]) -> dict[str, Any]:
    if err := _require(args, "quest_id"):
        return {"ok": False, "error": err}
    services = get_services()
    snap = services.quest.set_status(str(args["quest_id"]), "stopped")
    return {"quest": compact_snapshot(snap), "reason": str(args.get("reason") or "stopped_by_hermes")}

# Compatibility aliases.
deepscientist_doctor = ds_doctor
deepscientist_list_quests = ds_list_quests
deepscientist_status = ds_get_quest_state
deepscientist_new_quest = ds_new_quest
deepscientist_send_message = ds_add_user_message
deepscientist_read_documents = ds_read_quest_documents
deepscientist_memory_search = ds_memory_search
deepscientist_memory_write = ds_memory_write
deepscientist_confirm_baseline = ds_confirm_baseline
deepscientist_submit_idea = ds_submit_idea
deepscientist_record_experiment = ds_record_main_experiment
deepscientist_submit_paper_bundle = ds_submit_paper_bundle
deepscientist_pause = ds_pause_quest
deepscientist_resume = ds_resume_quest
