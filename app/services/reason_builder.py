from app.models.message import Classification, NextAction


def build_reason(
    classification: Classification,
    sub_classification: str,
    next_action: NextAction,
    is_urgent: bool,
    source: str,
) -> str:
    if is_urgent:
        return (
            f"识别到高风险或需要尽快人工介入的信号，因此分类为 "
            f"{classification.value}/{sub_classification} 并执行 {next_action.value}。"
        )
    if source == "llm":
        return (
            f"规则未命中或命中歧义，已通过 LLM fallback 识别为 "
            f"{classification.value}/{sub_classification}，当前最合适的处理动作是 {next_action.value}。"
        )
    if source == "rule":
        return (
            f"根据关键词规则识别为 {classification.value}/{sub_classification}，"
            f"当前最合适的处理动作是 {next_action.value}。"
        )
    return (
        f"规则和 LLM 都未明确命中，当前按 {classification.value}/{sub_classification} 处理，"
        f"动作是 {next_action.value}。"
    )
