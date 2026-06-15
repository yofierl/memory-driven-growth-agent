from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.nodes.gap_detection import GapDetectionNode
from app.agent.nodes.intervention_routing import InterventionRoutingNode
from app.agent.nodes.memory_extraction import MemoryExtractionNode
from app.agent.nodes.memory_retrieval import MemoryRetrievalNode
from app.agent.nodes.memory_update import MemoryUpdateNode
from app.agent.nodes.pattern_discovery import PatternDiscoveryNode
from app.agent.nodes.response_generation import ResponseGenerationNode
from app.agent.nodes.response_planner import ResponsePlannerNode
from app.agent.nodes.task_generation import TaskGenerationNode
from app.agent.state import GrowthAgentState
from app.services.intervention_service import InterventionService
from app.services.pattern_service import PatternService
from app.services.task_service import TaskService


class GrowthAgentGraph:
    def __init__(
        self,
        llm_service,
        memory_service,
        pattern_repo=None,
        method_repo=None,
        task_repo=None,
    ) -> None:
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.pattern_repo = pattern_repo
        self.method_repo = method_repo
        self.task_repo = task_repo
        self.memory_retrieval_node = MemoryRetrievalNode(memory_service=memory_service)
        self.gap_detection_node = GapDetectionNode(llm_service=llm_service)
        self.response_planner_node = ResponsePlannerNode(llm_service=llm_service)
        self.response_generation_node = ResponseGenerationNode(llm_service=llm_service)
        self.memory_extraction_node = MemoryExtractionNode(llm_service=llm_service)
        self.memory_update_node = MemoryUpdateNode(memory_service=memory_service)
        if pattern_repo is not None:
            pattern_service = PatternService(pattern_repo=pattern_repo)
            self.pattern_discovery_node = PatternDiscoveryNode(
                llm_service=llm_service,
                memory_service=memory_service,
                pattern_service=pattern_service,
            )
        else:
            self.pattern_discovery_node = None
        if pattern_repo is not None and method_repo is not None and task_repo is not None:
            intervention_service = InterventionService(
                pattern_repo=pattern_repo,
                method_repo=method_repo,
                task_repo=task_repo,
            )
            task_service = TaskService(llm_service=llm_service, task_repo=task_repo)
            self.intervention_routing_node = InterventionRoutingNode(
                llm_service=llm_service,
                memory_service=memory_service,
                intervention_service=intervention_service,
            )
            self.task_generation_node = TaskGenerationNode(task_service=task_service)
        else:
            self.intervention_routing_node = None
            self.task_generation_node = None
        self.graph = self._build_graph()

    @staticmethod
    def _route_after_gap_detection(state: GrowthAgentState) -> str:
        if state.need_follow_up:
            return "follow_up"
        return "normal"

    def _route_after_memory_update(self, state: GrowthAgentState) -> str:
        if self.pattern_discovery_node is None or state.need_follow_up:
            return "end"
        return "pattern_discovery"

    def _route_after_pattern_discovery(self, state: GrowthAgentState) -> str:
        if state.pattern_confirmation_required:
            return "wait_confirmation"
        if self.pattern_repo is None:
            return "end"
        confirmed = self.pattern_repo.list_by_user_id(
            user_id=state.user_id,
            statuses=["confirmed"],
        )
        if not confirmed:
            return "end"
        return "intervention_routing"

    @staticmethod
    def _route_after_intervention(state: GrowthAgentState) -> str:
        if state.recommended_method is None:
            return "end"
        return "task_generation"

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
        workflow.add_conditional_edges(
            "gap_detection",
            self._route_after_gap_detection,
            {
                "follow_up": "response_planner",
                "normal": "response_planner",
            },
        )
        workflow.add_edge("response_planner", "response_generation")
        workflow.add_edge("response_generation", "memory_extraction")
        workflow.add_edge("memory_extraction", "memory_update")

        if self.pattern_discovery_node is not None:
            workflow.add_node("pattern_discovery", self.pattern_discovery_node.run)
            workflow.add_conditional_edges(
                "memory_update",
                self._route_after_memory_update,
                {
                    "pattern_discovery": "pattern_discovery",
                    "end": END,
                },
            )
            if self.intervention_routing_node is not None and self.task_generation_node is not None:
                workflow.add_node("intervention_routing", self.intervention_routing_node.run)
                workflow.add_node("task_generation", self.task_generation_node.run)
                workflow.add_conditional_edges(
                    "pattern_discovery",
                    self._route_after_pattern_discovery,
                    {
                        "wait_confirmation": END,
                        "intervention_routing": "intervention_routing",
                        "end": END,
                    },
                )
                workflow.add_conditional_edges(
                    "intervention_routing",
                    self._route_after_intervention,
                    {
                        "task_generation": "task_generation",
                        "end": END,
                    },
                )
                workflow.add_edge("task_generation", END)
            else:
                workflow.add_conditional_edges(
                    "pattern_discovery",
                    self._route_after_pattern_discovery,
                    {
                        "wait_confirmation": END,
                        "end": END,
                    },
                )
        else:
            workflow.add_edge("memory_update", END)

        return workflow.compile()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        result = self.graph.invoke(state.model_dump())
        return GrowthAgentState.model_validate(result)
