from graph.config import PlanExecuteState


def route_by_intent(state: PlanExecuteState):
    route = state.get("route")
    return route if route in {"planner", "direct_answer"} else "planner"


def should_end(state: PlanExecuteState):
    """判断流程是否需要结束"""
    if state.get('response'):
        return True
    else:
        return False