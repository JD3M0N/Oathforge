"""Deterministic achievement conditions; no persistence or presentation."""

from copy import deepcopy


def event_types(condition) -> set[str]:
    return {condition.event} if condition.event else set().union(*(event_types(c) for c in condition.children))


def advance(condition, previous: dict, event: str, data: dict) -> dict:
    state = deepcopy(previous)
    if condition.kind in ("all", "any"):
        state["children"] = [
            advance(c, s, event, data)
            for c, s in zip(condition.children, state.get("children", [{} for _ in condition.children]))
        ]
        return state
    if condition.kind == "sequence":
        index = state.get("index", 0)
        if index < len(condition.children):
            child = advance(condition.children[index], state.get("current", {}), event, data)
            if progress(condition.children[index], child)[0] >= progress(condition.children[index], child)[1]:
                state.update(index=index + 1, current={})
            else:
                state["current"] = child
        return state
    if event != condition.event or any(data.get(k) != v for k, v in condition.match.items()):
        return state
    value = data.get(condition.field) if condition.field else None
    if condition.values and value not in condition.values:
        return state
    if condition.kind == "distinct":
        if value is not None:
            state["values"] = sorted(set(state.get("values", [])) | {str(value)})
    elif condition.kind == "threshold":
        if isinstance(value, (int, float)):
            state["value"] = max(state.get("value", 0), value)
    else:
        state["value"] = min(condition.target, state.get("value", 0) + 1)
    return state


def progress(condition, state: dict) -> tuple[int, int]:
    if condition.kind == "sequence":
        return state.get("index", 0), len(condition.children)
    if condition.kind in ("all", "any"):
        children = state.get("children", [{} for _ in condition.children])
        done = sum(progress(c, s)[0] >= progress(c, s)[1] for c, s in zip(condition.children, children))
        return min(done, 1) if condition.kind == "any" else done, 1 if condition.kind == "any" else len(children)
    value = len(state.get("values", [])) if condition.kind == "distinct" else state.get("value", 0)
    return min(int(value), condition.target), condition.target
