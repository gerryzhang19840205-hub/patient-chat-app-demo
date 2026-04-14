from dataclasses import dataclass

from app.models.message import Classification, RecommendedLink


@dataclass(frozen=True)
class ClassificationRule:
    classification: Classification
    sub_classification: str
    phrases: tuple[str, ...]


CLASSIFICATION_RULES: list[ClassificationRule] = [
    ClassificationRule(
        classification=Classification.ACCOUNT_ISSUE,
        sub_classification="portal_login_issue",
        phrases=("无法登录门户系统", "登录不了门户", "portal登录失败", "无法登录", "账户无法访问"),
    ),
    ClassificationRule(
        classification=Classification.ACCOUNT_ISSUE,
        sub_classification="password_reset",
        phrases=("忘记密码",),
    ),
    ClassificationRule(
        classification=Classification.ACCOUNT_ISSUE,
        sub_classification="password_change",
        phrases=("密码如何修改", "怎么修改密码"),
    ),
    ClassificationRule(
        classification=Classification.ACCOUNT_ISSUE,
        sub_classification="account_locked",
        phrases=("账号被锁定",),
    ),
    ClassificationRule(
        classification=Classification.SHIPPING_ISSUE,
        sub_classification="supply_delivery_eta",
        phrases=("耗材什么时候能送到", "物流什么时候到", "快递什么时候送到", "耗材还没收到"),
    ),
    ClassificationRule(
        classification=Classification.SHIPPING_ISSUE,
        sub_classification="order_tracking",
        phrases=("订单什么时候到", "配送进度怎么查", "包裹状态一直没更新"),
    ),
    ClassificationRule(
        classification=Classification.SHIPPING_ISSUE,
        sub_classification="shipment_not_dispatched",
        phrases=("发货了吗",),
    ),
    ClassificationRule(
        classification=Classification.BILLING_ISSUE,
        sub_classification="billing_error",
        phrases=("账单有问题", "账单", "收费不对"),
    ),
    ClassificationRule(
        classification=Classification.BILLING_ISSUE,
        sub_classification="bill_payment",
        phrases=("如何支付账单", "账单怎么付款", "付款失败"),
    ),
    ClassificationRule(
        classification=Classification.BILLING_ISSUE,
        sub_classification="charge_question",
        phrases=("为什么被扣费", "billing question"),
    ),
    ClassificationRule(
        classification=Classification.BILLING_ISSUE,
        sub_classification="invoice_request",
        phrases=("发票怎么开",),
    ),
    ClassificationRule(
        classification=Classification.INSURANCE_ISSUE,
        sub_classification="insurance_update",
        phrases=("更换了保险", "保险信息怎么更新", "新的保险如何提交", "保险变更"),
    ),
    ClassificationRule(
        classification=Classification.INSURANCE_ISSUE,
        sub_classification="insurance_claim",
        phrases=("保险报销怎么处理",),
    ),
    ClassificationRule(
        classification=Classification.INSURANCE_ISSUE,
        sub_classification="insurance_document_upload",
        phrases=("保单更新", "保险资料上传"),
    ),
    ClassificationRule(
        classification=Classification.INSURANCE_ISSUE,
        sub_classification="insurance_review_status",
        phrases=("保险审核进度",),
    ),
    ClassificationRule(
        classification=Classification.CLINICAL_QUESTION,
        sub_classification="stimulation_discomfort",
        phrases=("刺激感觉更强", "刺激感觉不舒服", "不舒服"),
    ),
    ClassificationRule(
        classification=Classification.CLINICAL_QUESTION,
        sub_classification="skin_redness",
        phrases=("皮肤发红", "使用后皮肤发红"),
    ),
    ClassificationRule(
        classification=Classification.CLINICAL_QUESTION,
        sub_classification="treatment_restart",
        phrases=("今天可以重新开始治疗吗", "中断治疗后可以恢复吗"),
    ),
    ClassificationRule(
        classification=Classification.CLINICAL_QUESTION,
        sub_classification="prescription_status",
        phrases=("医生发了处方", "处方收到了吗"),
    ),
    ClassificationRule(
        classification=Classification.DEVICE_ISSUE,
        sub_classification="device_wont_power_on",
        phrases=("设备坏了", "设备无法开机", "无法开机", "设备故障"),
    ),
    ClassificationRule(
        classification=Classification.DEVICE_ISSUE,
        sub_classification="device_charging",
        phrases=("设备怎么充电", "怎么给设备充电", "设备无法充电"),
    ),
    ClassificationRule(
        classification=Classification.DEVICE_ISSUE,
        sub_classification="device_not_working",
        phrases=("设备无法使用",),
    ),
]

GENERAL_SUB_CLASSIFICATION = "general_inquiry"

VALID_SUBCLASSIFICATIONS: dict[Classification, set[str]] = {
    Classification.GENERAL_QUESTION: {GENERAL_SUB_CLASSIFICATION},
}

for rule in CLASSIFICATION_RULES:
    VALID_SUBCLASSIFICATIONS.setdefault(rule.classification, set()).add(rule.sub_classification)

URGENT_KEYWORDS = ("不舒服", "皮肤发红", "发红", "疼痛", "异常", "强很多")

LINKS_BY_CLASSIFICATION: dict[Classification, list[RecommendedLink]] = {
    Classification.ACCOUNT_ISSUE: [
        RecommendedLink(label="门户登录帮助", url="/portal/help/login"),
        RecommendedLink(label="重置密码", url="/portal/reset-password"),
    ],
    Classification.SHIPPING_ISSUE: [
        RecommendedLink(label="订单与物流查询", url="/portal/orders"),
    ],
    Classification.INSURANCE_ISSUE: [
        RecommendedLink(label="保险信息更新", url="/portal/insurance"),
    ],
    Classification.DEVICE_ISSUE: [
        RecommendedLink(label="设备故障排查", url="/portal/device-help"),
        RecommendedLink(label="设备使用说明", url="/portal/device-guide"),
    ],
    Classification.CLINICAL_QUESTION: [
        RecommendedLink(label="治疗与安全说明", url="/portal/treatment-safety"),
    ],
}

FAQ_ANSWERS_BY_SUBCLASSIFICATION: dict[str, str] = {
    "portal_login_issue": "如果你暂时无法登录门户系统，建议先确认账号和密码是否正确，再尝试使用忘记密码功能；如果仍无法访问，可以转给门户支持团队处理。",
    "password_reset": "如果你忘记了密码，可以在登录页点击“忘记密码”，按提示完成身份验证后重设密码。",
    "password_change": "如果你想修改密码，通常可以在账户设置或安全设置中找到修改密码入口；修改后建议重新登录确认是否生效。",
    "account_locked": "如果账号被锁定，通常需要等待短时间后重试，或者联系门户支持团队协助解锁。",
    "supply_delivery_eta": "这类问题通常与耗材配送时间有关，你可以先查看订单或配送状态；如果长时间未更新，可以转给物流支持继续跟进。",
    "order_tracking": "你可以先通过订单或物流查询页面查看当前配送进度；如果状态长期不更新，建议交给物流支持核查。",
    "shipment_not_dispatched": "如果你想确认是否已经发货，建议先查看订单状态；若仍显示未发货，可以由物流支持进一步确认。",
    "billing_error": "如果你认为账单有误，建议先核对最近一次收费明细，再由账单团队进一步确认具体项目。",
    "bill_payment": "这类问题通常与账单支付流程有关，你可以先确认支付方式是否有效；如果付款仍失败，建议转给账单团队处理。",
    "charge_question": "如果你对扣费原因有疑问，建议由账单团队核对收费记录和对应服务项目后再进一步说明。",
    "invoice_request": "如果你需要发票，通常需要先确认账单记录和开票信息是否完整，再由账单团队协助处理。",
    "insurance_update": "如果你更换了保险或需要更新保险信息，建议尽快提交新的保险资料，后续可由保险支持团队继续核对。",
    "insurance_claim": "如果你想了解保险报销流程，通常需要先确认当前保单和理赔要求，再由保险支持团队提供进一步说明。",
    "insurance_document_upload": "如果你需要上传保单或保险资料，建议优先通过 Portal 的保险信息页面提交，避免后续审核延迟。",
    "insurance_review_status": "如果你想确认保险审核进度，建议先查看当前资料是否已完整提交；如进度长时间未更新，可交由保险支持跟进。",
    "stimulation_discomfort": "你提到刺激感觉更强或出现不适，这类情况更适合由临床团队确认；在获得专业建议前，不建议自行大幅调整治疗设置。",
    "skin_redness": "使用设备后出现皮肤发红时，建议先暂停继续刺激并尽快联系临床团队，由专业人员判断是否需要进一步处理。",
    "treatment_restart": "如果你中断治疗后准备重新开始，建议先由临床团队确认当前情况，再决定是否恢复原来的治疗方案。",
    "prescription_status": "如果你想确认处方是否已收到，通常需要由相关团队核对系统记录后再答复。",
    "device_wont_power_on": "如果设备无法开机，建议先检查电量、充电连接和电源状态；如果仍无法恢复，建议转给设备支持团队。",
    "device_charging": "如果你想了解如何给设备充电，建议先参考设备使用说明；如果设备仍无法正常充电，可交由设备支持团队继续处理。",
    "device_not_working": "如果设备无法正常使用，建议先确认电量、连接和基础设置；若问题持续存在，建议转给设备支持团队。",
}
