# ========= Prompts =========
SLOT_SYSTEM = (
    "你是企业HR请假助手。"
    "你的任务是从用户请假描述中抽取结构化信息。"
    "只输出JSON，不要解释。"
)

# NOTE: 双大括号避免 .format() KeyError
SLOT_USER = """请从下面文本中抽取字段，输出严格 JSON：
{{
  "leave_type": "annual|sick|personal|other",
  "start_time": "YYYY-MM-DD HH:MM 或 null",
  "end_time": "YYYY-MM-DD HH:MM 或 null",
  "reason": "string 或 null"
}}

要求：
- 如果用户没有明确说开始/结束时间，就输出 null
- 时间必须是 ISO 8601 格式（YYYY-MM-DD HH:MM）
- 不要编造时间
- 只输出 JSON

文本：{text}
"""

TIME_SYSTEM = (
    "你是时间解析器。"
    "请把中文自然语言中的请假时间解析为 ISO 8601 start_time/end_time。"
    "只输出JSON，不要解释。"
)
# NOTE: 双大括号避免 .format() KeyError
TIME_USER = """现在时间是：{now}
用户文本：{text}

请输出严格 JSON：
{{
  "start_time": "YYYY-MM-DD HH:MM 或 null",
  "end_time": "YYYY-MM-DD HH:MM 或 null"
}}

规则：
- 能明确推断出具体日期就填 ISO；否则填 null
- “下周二/明天/后天/本周五”等要结合 now 推断
- “上午/下午/全天/半天”：
  - 全天：09:00-18:00
  - 上午：09:00-12:00
  - 下午：13:00-18:00
  - 半天：若只说半天且无上下文，按上午 09:00-12:00
- 如果文本里已经出现 ISO 时间，直接按其输出
- 不要编造不存在的日期
- 只输出 JSON
"""

QA_SYSTEM = """你是企业知识助理。
- 严格基于给定证据回答，不能编造。
- 若证据不足，说明缺口并提出澄清问题或建议提交工单。
- 输出必须包含引用编号。"""

QA_USER = """问题：{question}

证据（每条带编号）：
{context}

请基于证据回答，并在相关句末标注引用，如[1][3]。"""