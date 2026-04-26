"""Heuristic DeepScientist stage router."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STAGE_SKILLS = ("scout", "baseline", "idea", "optimize", "experiment", "analysis-campaign", "write", "finalize", "decision")
COMPANION_SKILLS = ("figure-polish", "intake-audit", "review", "rebuttal")

_KEYWORDS = {
    "scout": ["论文", "文献", "调研", "survey", "paper", "arxiv", "related work", "查找"],
    "baseline": ["baseline", "基线", "复现", "reproduce", "复现实验", "确认基线"],
    "idea": ["创新", "idea", "方法", "提出", "hypothesis", "new method", "路线"],
    "optimize": ["优化", "改进", "ablation", "消融", "tune", "调参"],
    "experiment": ["实验", "跑", "run", "训练", "evaluate", "评估", "结果"],
    "analysis-campaign": ["分析", "多组", "campaign", "统计", "对比", "归因"],
    "write": ["写", "论文", "draft", "paper", "manuscript", "整理成文", "摘要", "引言"],
    "finalize": ["收尾", "打包", "检查", "final", "finalize", "投稿", "release"],
    "decision": ["判断", "决策", "是否", "选择", "路线", "取舍", "decision"],
}
_COMPANION_KEYWORDS = {
    "review": ["审稿", "review", "评审", "修改意见", "aigc", "润色"],
    "rebuttal": ["rebuttal", "反驳", "回复审稿", "response"],
    "figure-polish": ["图", "figure", "画图", "可视化", "plot"],
    "intake-audit": ["审计", "检查输入", "需求梳理", "intake"],
}
_AMBIGUOUS = {"继续", "下一步", "go on", "continue", "接着", "继续做"}

@dataclass(frozen=True)
class Route:
    stage: str
    companion: str | None = None
    confidence: float = 0.5
    reason: str = "heuristic"


def _score(text: str, words: list[str]) -> int:
    return sum(1 for word in words if word.lower() in text)


def route(user_message: str, *, active_stage: str | None = None, snapshot: dict[str, Any] | None = None) -> Route:
    text = " ".join(str(user_message or "").lower().split())
    state_stage = str((snapshot or {}).get("active_anchor") or active_stage or "").strip()
    if text in _AMBIGUOUS and state_stage in STAGE_SKILLS:
        return Route(state_stage, confidence=0.7, reason="active_stage_continuation")
    best_stage = state_stage if state_stage in STAGE_SKILLS else "scout"
    best_score = 0
    for stage, words in _KEYWORDS.items():
        score = _score(text, words)
        if score > best_score:
            best_score = score
            best_stage = stage
    companion = None
    companion_score = 0
    for skill, words in _COMPANION_KEYWORDS.items():
        score = _score(text, words)
        if score > companion_score:
            companion_score = score
            companion = skill
    if best_score == 0 and state_stage in STAGE_SKILLS:
        best_stage = state_stage
    confidence = 0.85 if best_score else 0.55
    return Route(best_stage, companion=companion, confidence=confidence, reason="keyword_match" if best_score else "default_or_active")


def route_payload(user_message: str, *, active_stage: str | None = None, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    r = route(user_message, active_stage=active_stage, snapshot=snapshot)
    return {"stage": r.stage, "companion": r.companion, "confidence": r.confidence, "reason": r.reason}
