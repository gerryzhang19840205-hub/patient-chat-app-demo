from app.models.message import Classification, NextAction


def decide_next_action(
    classification: Classification,
    is_urgent: bool,
    confidence: float,
) -> NextAction:
    if is_urgent:
        return route_to_support_action(classification)
    if confidence > 0.75:
        return NextAction.AUTO_REPLY
    return route_to_support_action(classification)


def route_to_support_action(classification: Classification) -> NextAction:
    if classification == Classification.DEVICE_ISSUE:
        return NextAction.ROUTE_TO_DEVICE_SUPPORT
    if classification == Classification.CLINICAL_QUESTION:
        return NextAction.ROUTE_TO_CLINICAL_TEAM
    if classification == Classification.BILLING_ISSUE:
        return NextAction.ROUTE_TO_BILLING_TEAM
    if classification == Classification.SHIPPING_ISSUE:
        return NextAction.ROUTE_TO_SHIPPING_TEAM
    if classification == Classification.ACCOUNT_ISSUE:
        return NextAction.ROUTE_TO_PORTAL_SUPPORT
    if classification == Classification.INSURANCE_ISSUE:
        return NextAction.ROUTE_TO_INSURANCE_TEAM
    return NextAction.AUTO_REPLY
