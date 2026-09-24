"""Bounded conversation context shared by all providers and action modes."""


def context_history(state):
    messages = state.get("conversation", [])
    # The final user turn is already supplied as the current request.
    if messages and messages[-1].get("role") == "user":
        messages = messages[:-1]
    result, budget = [], 24000
    for message in reversed(messages[-16:]):
        if message.get("role") not in ("user", "assistant", "system"):
            continue
        content = str(message.get("content", ""))[:6000]
        if len(content) > budget:
            break
        budget -= len(content)
        result.append({"role": message["role"], "content": content, "mode": message.get("mode", 0)})
    return list(reversed(result))
