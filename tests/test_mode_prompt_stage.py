from __future__ import annotations

from conftest import load_plugin, parse_json


def test_stage_router_representative_requests():
    load_plugin()
    from hermes_plugins.deepscientist_native import stage_router
    assert stage_router.route("帮我找相关论文和文献").stage == "scout"
    assert stage_router.route("确认 baseline 并做复现实验").stage == "baseline"
    assert stage_router.route("提出一个新的创新方法").stage == "idea"
    assert stage_router.route("跑实验并记录结果").stage == "experiment"
    assert stage_router.route("开始写论文初稿").stage == "write"
    strict_route = stage_router.route("请认真调研相关论文，谨慎确认后撰写综述")
    # Strict-research is an agent-managed mode: heuristics may recommend it,
    # but must not silently switch the active stage and override agent judgment.
    assert strict_route.stage == "scout"
    assert strict_route.suggested_stage == "strict-research"
    assert strict_route.requires_agent_decision is True
    assert stage_router.route("继续", active_stage="optimize").stage == "optimize"
    assert stage_router.route("回复审稿人 rebuttal").companion == "rebuttal"


def test_stage_router_keeps_existing_strict_research_on_strict_request():
    load_plugin()
    from hermes_plugins.deepscientist_native import stage_router

    route = stage_router.route("请认真调研相关论文，谨慎确认后撰写综述", active_stage="strict-research")

    assert route.stage == "strict-research"
    assert route.requires_agent_decision is False

    search_route = stage_router.route("继续查找论文", active_stage="strict-research")
    assert search_route.stage == "strict-research"
    assert search_route.requires_agent_decision is False


def test_prompt_adapter_rewrites_and_filters_removed_surfaces():
    load_plugin()
    from hermes_plugins.deepscientist_native import prompt_adapter
    text = "Use memory.search(...) then artifact.record(...). Never call artifact.interact. Open Web UI connector. bash_exec('x')"
    adapted = prompt_adapter.adapt_text(text)
    assert "ds_memory_search" in adapted
    assert "ds_artifact_record" in adapted
    assert "ds_bash_exec" in adapted
    assert "artifact.interact" not in adapted
    assert "connector" not in adapted.lower()
    assert "web ui" not in adapted.lower()


def test_mode_context_is_compact_and_active_stage_only():
    load_plugin()
    from hermes_plugins.deepscientist_native import mode, tools
    quest_id = parse_json(tools.ds_new_quest({"goal": "Mode context smoke", "quest_id": "mode-test"}))["quest"]["quest_id"]
    result = mode.pre_llm_call({"session_id": "s1", "user_message": "帮我找相关论文"})
    ctx = result["context"]
    assert "DeepScientist mode context" in ctx
    assert "active_quest_id:" in ctx
    assert "active_stage: scout" in ctx
    assert "ds_memory_search" in ctx
    assert len(ctx) < 12000
    # Active stage excerpt should be present, but all stage headings should not be dumped wholesale.
    assert ctx.count("active_stage_skill_excerpt") == 1


def test_mode_context_exposes_strict_research_as_agent_decision_not_forced_stage():
    load_plugin()
    from hermes_plugins.deepscientist_native import mode, tools

    parse_json(tools.ds_new_quest({"goal": "Mode context strict smoke", "quest_id": "mode-strict-test"}))
    result = mode.pre_llm_call({"session_id": "s-strict", "user_message": "请认真调研相关论文，谨慎确认后撰写综述"})
    ctx = result["context"]

    assert "active_stage: scout" in ctx
    assert "agent_decision_required: strict_research_mode" in ctx
    assert "recommended_stage: strict-research" in ctx
    assert "do not auto-enter strict-research solely from keyword heuristics" in ctx