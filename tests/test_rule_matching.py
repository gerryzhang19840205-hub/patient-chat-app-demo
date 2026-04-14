from app.models.message import Classification
from app.services.classifier import classify_by_rules, get_rule_matches


def test_single_keyword_tuple_does_not_degrade_to_character_matching() -> None:
    assert classify_by_rules("设否备") == Classification.GENERAL_QUESTION
    assert classify_by_rules("设备坏了") == Classification.DEVICE_ISSUE
    assert get_rule_matches("设备坏了")[0].sub_classification == "device_wont_power_on"


def test_multiple_rule_matches_do_not_pick_first_category() -> None:
    matches = get_rule_matches("我无法登录门户系统，而且账单也有问题。")
    matched_classifications = {match.classification for match in matches}

    assert Classification.ACCOUNT_ISSUE in matched_classifications
    assert Classification.BILLING_ISSUE in matched_classifications
    assert classify_by_rules("我无法登录门户系统，而且账单也有问题。") == Classification.GENERAL_QUESTION
