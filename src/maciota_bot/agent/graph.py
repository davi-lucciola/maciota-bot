from langgraph.graph import END, START, StateGraph

from maciota_bot.agent.nodes import make_nodes
from maciota_bot.agent.state import BotState


def route_after_trigger(state: BotState) -> str:
    if state['approved']:
        return 'persona_router'
    return END


def build_graph(checkpointer: object, light_model: object, reply_model: object):
    evaluate_trigger, persona_router, generate_response = make_nodes(
        light_model,
        reply_model,
    )
    graph = StateGraph(BotState)
    graph.add_node('evaluate_trigger', evaluate_trigger)
    graph.add_node('persona_router', persona_router)
    graph.add_node('generate_response', generate_response)
    graph.add_edge(START, 'evaluate_trigger')
    graph.add_conditional_edges('evaluate_trigger', route_after_trigger)
    graph.add_edge('persona_router', 'generate_response')
    graph.add_edge('generate_response', END)
    return graph.compile(checkpointer=checkpointer)
