from __future__ import annotations

from langgraph.graph import END, StateGraph

from xtractor.pipeline.nodes.file_understanding import file_understanding
from xtractor.pipeline.nodes.multimodal_extract import multimodal_extract
from xtractor.pipeline.nodes.postprocess import postprocess
from xtractor.pipeline.nodes.prompt_builder import prompt_builder
from xtractor.pipeline.nodes.prompt_merge import prompt_merge
from xtractor.pipeline.nodes.symbol_agent import symbol_agent
from xtractor.pipeline.nodes.symbol_router import symbol_router
from xtractor.pipeline.state import DXState


def build_graph() -> StateGraph[DXState]:
    builder: StateGraph[DXState] = StateGraph(DXState)
    builder.add_node("file_understanding", file_understanding)
    builder.add_node("prompt_builder", prompt_builder)
    builder.add_node("symbol_agent", symbol_agent)
    builder.add_node("prompt_merge", prompt_merge)
    builder.add_node("multimodal_extract", multimodal_extract)
    builder.add_node("postprocess", postprocess)

    builder.set_entry_point("file_understanding")
    builder.add_edge("file_understanding", "prompt_builder")
    builder.add_conditional_edges(
        "prompt_builder",
        symbol_router,
        {
            "symbol_needed": "symbol_agent",
            "skip": "prompt_merge",
        },
    )
    builder.add_edge("symbol_agent", "prompt_merge")
    builder.add_edge("prompt_merge", "multimodal_extract")
    builder.add_edge("multimodal_extract", "postprocess")
    builder.add_edge("postprocess", END)
    return builder


def compile_graph() -> any:
    """Compile the LangGraph workflow with in-memory checkpoints."""

    builder = build_graph()
    return builder.compile()


__all__ = ["build_graph", "compile_graph"]
