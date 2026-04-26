"""Adapt DeepScientist prompt/skill resources for Hermes-native tool names."""
from __future__ import annotations

import re
from pathlib import Path

from .runtime import resource_root

TOOL_REWRITES = {
    "memory.search": "ds_memory_search",
    "memory.write": "ds_memory_write",
    "memory.read": "ds_memory_read",
    "artifact.record_main_experiment": "ds_record_main_experiment",
    "artifact.record_analysis_slice": "ds_record_analysis_slice",
    "artifact.create_analysis_campaign": "ds_create_analysis_campaign",
    "artifact.submit_paper_outline": "ds_submit_paper_outline",
    "artifact.submit_paper_bundle": "ds_submit_paper_bundle",
    "artifact.submit_idea": "ds_submit_idea",
    "artifact.confirm_baseline": "ds_confirm_baseline",
    "artifact.waive_baseline": "ds_waive_baseline",
    "artifact.attach_baseline": "ds_attach_baseline",
    "artifact.record": "ds_artifact_record",
    "bash_exec": "ds_bash_exec",
}
REMOVED_TERMS = ("connector", "web ui", "browser ui", "tui", "qq", "wechat", "weixin", "whatsapp", "telegram", "artifact" + ".interact", "artifact.complete_quest", "artifact.render_git_graph", "memory.promote_to_global")


def adapt_text(text: str) -> str:
    out = str(text or "")
    # Replace longer names first.
    for old in sorted(TOOL_REWRITES, key=len, reverse=True):
        out = out.replace(old, TOOL_REWRITES[old])
    kept_lines = []
    for line in out.splitlines():
        # Remove only the sentence/fragment that mentions removed Web/TUI/connector/raw-MCP surfaces,
        # rather than dropping a whole line that may also contain valid ds_* guidance.
        fragments = re.split(r"(?<=[.!?。！？])\s+", line)
        kept_fragments = []
        for fragment in fragments:
            lowered = fragment.lower()
            if any(term in lowered for term in REMOVED_TERMS):
                continue
            kept_fragments.append(fragment)
        if kept_fragments:
            kept_lines.append(" ".join(kept_fragments).rstrip())
    out = "\n".join(kept_lines)
    out = re.sub(r"\bCodex runner\b", "Hermes runner", out, flags=re.IGNORECASE)
    out = re.sub(r"\bcodex\b", "Hermes", out, flags=re.IGNORECASE)
    return out.strip() + ("\n" if out.strip() else "")


def skill_path(skill_id: str) -> Path:
    return resource_root() / "skills" / skill_id / "SKILL.md"


def load_skill_excerpt(skill_id: str, *, max_chars: int = 4000) -> str:
    path = skill_path(skill_id)
    if not path.exists():
        return ""
    text = adapt_text(path.read_text(encoding="utf-8", errors="replace"))
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n...[truncated]\n"


def load_prompt_fragment(relative: str, *, max_chars: int = 4000) -> str:
    path = (resource_root() / "prompts" / relative).resolve()
    prompts_root = (resource_root() / "prompts").resolve()
    if prompts_root != path and prompts_root not in path.parents:
        raise ValueError("Prompt fragment path escapes prompt resources")
    if not path.exists():
        return ""
    text = adapt_text(path.read_text(encoding="utf-8", errors="replace"))
    return text if len(text) <= max_chars else text[:max_chars].rstrip() + "\n...[truncated]\n"


def assert_no_removed_terms(text: str) -> list[str]:
    lowered = str(text or "").lower()
    return [term for term in REMOVED_TERMS if term in lowered]
