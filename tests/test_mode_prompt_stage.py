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
    assert stage_router.route("继续", active_stage="optimize").stage == "optimize"
    assert stage_router.route("回复审稿人 rebuttal").companion == "rebuttal"


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
