from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.nodes.gap_detection import GapDetectionNode
from app.agent.nodes.memory_extraction import MemoryExtractionNode
from app.agent.nodes.memory_retrieval import MemoryRetrievalNode
from app.agent.nodes.memory_update import MemoryUpdateNode
from app.agent.nodes.response_generation import ResponseGenerationNode
from app.agent.nodes.response_planner import ResponsePlannerNode
from app.agent.state import GrowthAgentState


class GrowthAgentGraph:
    def __init__(self, llm_service, memory_service) -> None:
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.memory_retrieval_node = MemoryRetrievalNode(memory_service=memory_service)
        self.gap_detection_node = GapDetectionNode(llm_service=llm_service)
        self.response_planner_node = ResponsePlannerNode(llm_service=llm_service)
        self.response_generation_node = ResponseGenerationNode(llm_service=llm_service)
        self.memory_extraction_node = MemoryExtractionNode(llm_service=llm_service)
        self.memory_update_node = MemoryUpdateNode(memory_service=memory_service)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(GrowthAgentState)
        workflow.add_node("memory_retrieval", self.memory_retrieval_node.run)
        workflow.add_node("gap_detection", self.gap_detection_node.run)
        workflow.add_node("response_planner", self.response_planner_node.run)
        workflow.add_node("response_generation", self.response_generation_node.run)
        workflow.add_node("memory_extraction", self.memory_extraction_node.run)
        workflow.add_node("memory_update", self.memory_update_node.run)

        workflow.add_edge(START, "memory_retrieval")
        workflow.add_edge("memory_retrieval", "gap_detection")
        workflow.add_edge("gap_detection", "response_planner")
        workflow.add_edge("response_planner", "response_generation")
        workflow.add_edge("response_generation", "memory_extraction")
        workflow.add_edge("memory_extraction", "memory_update")
        workflow.add_edge("memory_update", END)
        return workflow.compile()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        result = self.graph.invoke(state.model_dump())
        return GrowthAgentState.model_validate(result)
