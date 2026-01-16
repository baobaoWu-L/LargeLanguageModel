import json
import redis
from typing import Any

r = redis.Redis(
    host="127.0.0.1",
    port=6379,
    decode_responses=True,
)

TTL_SECONDS = 604800  # 键多久会自动过期，此处是7天


DROP_KEYS = {"docs", "messages", "chat_history", "retrieved_docs"}
# 这是一个集合，集合中放的都是后面要存入redis的时候一些不要的键


def _safe_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)
# 上面是一个辅助函数，将一些对象转为str
# 主要是为了一些复杂对象如果没办法序列化而准备的
# 序列化就是将xx内容变成字节的序列，反序列化就是将字节序列再变回去
# ensure_ascii=False不要将中文等文字变成\0xFF这样的字节序列


def load_session(session_id: str) -> dict | None:
    s = r.get(session_id)  # 从redis中读取session_id这个键对应的值
    return json.loads(s) if s else None


def save_session(session_id: str, state: dict) -> None:
    safe_state = {k: v for k, v in state.items() if k not in DROP_KEYS}
    # 这一行其实是在过滤，去掉一些不想要的键值对，留下想要的存入redis
    r.setex(session_id, TTL_SECONDS, _safe_dumps(safe_state))
    # setex(键，过期时间，值)

save_session('s1', {'NAME':'LoveBreaker1'})
print(load_session('s1'))