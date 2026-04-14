# 设计说明

## 1. 项目目标

这个项目实现的是一个面向患者的消息助手，目标是完成三个核心任务：

- 对患者消息做分类
- 生成可解释、可执行的回复
- 决定下一步动作，并在需要时支持会话追踪
  
---

## 2. 接口设计

### 2.1 消息分析接口

- `POST /api/messages/analyze`

这个接口同时支持两种输入方式：

- `application/json`：直接传文本
- `multipart/form-data`：上传 `mp3` 文件，先转写成文本再进入主流程

请求字段：

- `sessionId`
- `id`
- `transcript`
- `inputMode`：`text` 或 `audio`
- `sourceAudioFilename`：当输入是语音时，保存原始文件名

响应字段：

- `sessionId`
- `id`
- `transcript`
- `inputMode`
- `sourceAudioFilename`
- `classification`
- `sub_classification`
- `reply`
- `next_action`
- `confidence`
- `reason`
- `recommended_links`
- `replyAudioFilename`
- `replyAudioUrl`

其中：

- `transcript` 是最终参与分类和回复生成的文本
- `replyAudioUrl` 是系统生成的语音回复文件下载地址

### 2.2 会话查询接口

- `GET /api/messages/sessions/{session_id}`

这个接口返回某个会话下所有已保存的输入和输出记录，方便：

- 回看对话过程
- 后续接入 Portal/App 会话历史

---

## 3. 分类策略

### 3.1 主分类和子分类

当前分类不只是一个主分类，而是两层结构：

- 主分类，例如 `account_issue`
- 子分类，例如 `portal_login_issue`

子分类是更贴近 FAQ 的粒度，也更适合后续做回复模板、统计和路由分析。

代码里当前的分类如下：

| 主分类 | 子分类 |
| --- | --- |
| `device_issue` | `device_wont_power_on`, `device_charging`, `device_not_working` |
| `clinical_question` | `stimulation_discomfort`, `skin_redness`, `treatment_restart`, `prescription_status` |
| `billing_issue` | `billing_error`, `bill_payment`, `charge_question`, `invoice_request` |
| `shipping_issue` | `supply_delivery_eta`, `order_tracking`, `shipment_not_dispatched` |
| `account_issue` | `portal_login_issue`, `password_reset`, `password_change`, `account_locked` |
| `insurance_issue` | `insurance_update`, `insurance_claim`, `insurance_document_upload`, `insurance_review_status` |
| `general_question` | `general_inquiry` |

### 3.2 规则优先，歧义走 LLM

规则引擎的实现方式不是简单的“找到第一个关键词就返回”，而是：

1. 先收集所有命中的规则
2. 如果只命中一个规则，直接返回规则结果
3. 如果没有命中，或者命中了多个不同规则，就交给 LLM 判断
4. 如果 LLM 不可用或返回无效结果，再退回到 `general_question / general_inquiry`

这样做的原因是避免“前面的规则抢先命中”导致误分类。

### 3.3 LLM 输出约束

LLM fallback 的输出要求非常严格，只允许返回 JSON：

```json
{
  "classification": "account_issue",
  "sub_classification": "portal_login_issue"
}
```

返回后会做白名单校验：

- 主分类必须在允许范围内
- 子分类必须属于这个主分类

这样可以避免模型随意输出文本破坏主流程。

---

## 4. 回复策略

回复的生成采用分层策略：

1. 如果是紧急场景，先返回保守型安全提醒
2. 如果 `sub_classification` 能命中 FAQ 配置，直接返回 FAQ answer
3. 如果 FAQ 没命中，再交给 LLM 生成回复
4. 如果 LLM 也不可用，最后返回一个保守模板

这样设计的好处是：

- 常见问题走确定性回复，成本低、稳定性高
- 长尾问题由 LLM 补足
- 高风险问题不让模型自由发挥
- LLM 生成回复时会带上最近 5 轮会话历史，增强多轮对话连贯性

---

## 5. 下一步动作策略

当前的动作策略是：

1. 如果 `is_urgent = true`，直接路由到对应主分类支持团队
2. 如果不是紧急场景且 `confidence > 0.75`，则使用 `auto_reply`
3. 如果置信度不够，则路由到对应支持团队

支持团队映射为：

- `device_issue` -> `route_to_device_support`
- `clinical_question` -> `route_to_clinical_team`
- `billing_issue` -> `route_to_billing_team`
- `shipping_issue` -> `route_to_shipping_team`
- `account_issue` -> `route_to_portal_support`
- `insurance_issue` -> `route_to_insurance_team`

这套策略的核心目标是让系统在“自动回复”和“人工支持”之间做出可解释的分流。

---

## 6. 置信度策略

置信度是“可解释的决策信号”，不是严格统计意义上的真实概率。

当前规则是：

- 规则唯一命中时，`confidence = 1.0`
- LLM 分类时，优先使用模型返回的 `confidence`
- 如果 LLM 没有给出 `confidence`，才回退到本地启发式估算
- 通用 fallback 时，给一个较低的基线值
- 紧急信号或更强的命中场景会提高置信度

这么做的原因是：

- 足够简单，便于解释
- 能直接配合动作策略使用
- 规则命中和模型命中的置信度来源一致，便于调试和回放
- 不需要额外训练或评估流程

---

## 7. 会话持久化

每次调用分析接口时，我都会把两条事件写入 SQLite：

- 一条 `inbound`，保存请求内容
- 一条 `outbound`，保存响应内容

存储字段包括：

- `session_id`
- `message_id`
- `direction`
- `payload_json`
- `created_at`

这样做的价值是：

- 可以回放完整会话
- 方便调试和演示
- 后续可以自然扩展成 Portal/App 的历史记录功能

---

## 8. 为什么这样取舍

它的优势是：

- 规则层稳定，适合处理高频问题
- LLM 只作为补充，不会强行接管关键决策
- 主分类和子分类都保留，方便后续扩展 FAQ
- 会话历史已经落库，体现了工程完整性

---

## 9. 局限
- 规则短语覆盖有限
- 没有做更复杂的中文分词或语义检索
- 置信度不是校准后的真实概率
- 没有数据保留、脱敏、审计等生产级治理能力

---

## 10. 后续迭代方向

如果继续做，我会优先考虑：

1. 把规则和 FAQ 配置拆成独立 JSON/YAML 文件
2. 增加会话查询的分页和过滤能力
3. 增加更完整的评测集，验证分类和动作策略
4. 增加 LLM 调用的重试和降级策略
5. 增加更细粒度的会话状态管理
6. prompt根据benchmark进行优化

---

## 11. 总结

这个设计的核心思想是：

- 主流程尽量确定性
- FAQ 命中优先于模型生成
- 模型只处理规则无法覆盖或存在歧义的场景
- 会话级持久化为后续产品化保留扩展空间

这样既能满足题目要求，也能体现对工程边界和产品取舍的理解。
