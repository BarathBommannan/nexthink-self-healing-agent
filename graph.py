import logging

try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    from langgraph_compat import StateGraph, START, END, MemorySaver

from state import SelfHealingState
from nodes import (
    telemetry_diagnostic_agent,
    guardrail_decision_agent,
    decision_router,
    safe_automation_snow_incident,
    human_approval_snow_incident,
    wait_for_human_approval,
    approval_router,
    escalation_node,
    escalation_snow_incident,
    remediation_execution_agent,
    reset_demo_http_node,
    post_healing_validation_agent
)

logger = logging.getLogger(__name__)

def create_workflow(checkpointer=None):
    """Constructs the LangGraph matching the Lyzr 'Nexthink Self Healing - PIF' workflow."""
    builder = StateGraph(SelfHealingState)

    # Add Nodes
    builder.add_node("telemetry_diagnostic_agent", telemetry_diagnostic_agent)
    builder.add_node("guardrail_decision_agent", guardrail_decision_agent)
    builder.add_node("safe_automation_snow_incident", safe_automation_snow_incident)
    builder.add_node("human_approval_snow_incident", human_approval_snow_incident)
    builder.add_node("wait_for_human_approval", wait_for_human_approval)
    builder.add_node("escalation_node", escalation_node)
    builder.add_node("escalation_snow_incident", escalation_snow_incident)
    builder.add_node("remediation_execution_agent", remediation_execution_agent)
    builder.add_node("reset_demo_http_node", reset_demo_http_node)
    builder.add_node("post_healing_validation_agent", post_healing_validation_agent)

    # Main flow edges
    builder.add_edge(START, "telemetry_diagnostic_agent")
    builder.add_edge("telemetry_diagnostic_agent", "guardrail_decision_agent")

    # Decision conditional routing
    builder.add_conditional_edges(
        "guardrail_decision_agent",
        decision_router,
        {
            "safe_automation_snow_incident": "safe_automation_snow_incident",
            "human_approval_snow_incident": "human_approval_snow_incident",
            "escalation_node": "escalation_node"
        }
    )

    # Safe branch
    builder.add_edge("safe_automation_snow_incident", "remediation_execution_agent")

    # Human approval branch
    builder.add_edge("human_approval_snow_incident", "wait_for_human_approval")
    builder.add_conditional_edges(
        "wait_for_human_approval",
        approval_router,
        {
            "remediation_execution_agent": "remediation_execution_agent",
            "escalation_snow_incident": "escalation_snow_incident"
        }
    )

    # Escalation branch
    builder.add_edge("escalation_node", "escalation_snow_incident")
    builder.add_edge("escalation_snow_incident", END)

    # Remediation -> Demo Reset -> Post Validation -> END
    builder.add_edge("remediation_execution_agent", "reset_demo_http_node")
    builder.add_edge("reset_demo_http_node", "post_healing_validation_agent")
    builder.add_edge("post_healing_validation_agent", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)

app = create_workflow()