# from fastapi import FastAPI
# from pydantic import BaseModel
# from app.router_graph import router_graph


from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel

from app.router_graph import router_graph
from app.deps import get_vs
from rag_docs.loader import load_single_file, split_with_visibility, load_docs, split_docs
from app.config import settings
import time
import uuid
from pathlib import Path
from typing import Optional
import chromadb

from api.rbac_api import router as rbac_router
from db.redis_session import load_session, save_session
from auth.auth import router as auth_router, UserInDB, get_current_user_optional, get_current_user
# from app.db.rbac_db import get_user_roles, get_user_permissions
from db.rbac import get_user_roles,get_user_permissions
from rbac.perm import require_permission

SESSIONS: dict[str, dict] = {}  # # ⚠️加这一行

app = FastAPI(title="Enterprise KB Assistant")
app.include_router(auth_router)
app.include_router(rbac_router)

DATA_DOCS_DIR = Path("./data/docs")
DATA_DOCS_DIR.mkdir(parents=True, exist_ok=True)

class ChatReq(BaseModel):
    text: str
    user_role: str = "public"
    requester: str = "anonymous"
    session_id: Optional[str] = None  # ⚠️加这一行

class ChatResp(BaseModel):
    answer: str
    session_id: Optional[str] = None    # ⚠️添加
    active_route: Optional[str] = None  # ⚠️添加

@app.get("/whoami") # ‼️测试一下而已
def whoami(current_user: UserInDB = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "roles": get_user_roles(current_user.id),
        "permissions": sorted(list(get_user_permissions(current_user.id))),
        "is_super_admin": current_user.is_super_admin,
    }
@app.post("/chat", response_model=ChatResp)
def chat(
    req: ChatReq,
    current_user: UserInDB | None = Depends(get_current_user_optional), # ‼️
):
    payload = req.model_dump()
    text = payload.get("text") or ""

    # 0) 统一构造可信身份上下文
    if current_user:
        payload["requester"] = current_user.username
        payload["user_id"] = current_user.id

        roles = get_user_roles(current_user.id)
        perms = sorted(list(get_user_permissions(current_user.id)))

        payload["roles"] = roles
        payload["permissions"] = perms
        payload["user_role"] = roles[0] if roles else "public"

        # ‼️ /chat基础门槛：至少能看公共KB（这个后续也可以改成必须登录，看情况吧）
        require_permission(current_user, "kb.view_public")
    else:
        # ‼️ 匿名：绝不信任客户端传的任何角色/用户
        payload["requester"] = "anonymous"
        payload["user_id"] = None
        payload["roles"] = ["anonymous"]
        payload["permissions"] = ["kb.view_public"]
        payload["user_role"] = "anonymous"

    # 1) session id
    sid = payload.get("session_id") or f"sid-{uuid.uuid4().hex[:10]}"
    payload["session_id"] = sid

    # 2) load previous state from redis and merge
    prev_state = load_session(sid)
    if prev_state:
        merged = {**prev_state, **payload}
        merged["text"] = text
        payload = merged

    # 3) run router graph
    out = router_graph.invoke(payload)

    # 4) save new state to redis
    new_state = {**payload, **out}
    save_session(sid, new_state)

    return {
        "answer": out.get("answer", ""),
        "session_id": sid,
        "active_route": new_state.get("active_route"),
    }


@app.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    visibility: str = Form("public"),
    doc_id: Optional[str] = Form(None),
    current_user: UserInDB = Depends(get_current_user),  # ‼️ 必须登录
):
    # ‼️ 只有有权限的人才能上传
    require_permission(current_user, "kb.manage_docs")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")

    visibility = (visibility or "public").strip().lower()
    suffix = Path(file.filename).suffix
    safe_name = f"{int(time.time())}_{uuid.uuid4().hex}{suffix}"
    save_path = DATA_DOCS_DIR / safe_name

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    save_path.write_bytes(content)

    docs = load_single_file(save_path)
    if not docs:
        raise HTTPException(status_code=400, detail=f"Unsupported or empty file type: {suffix}")

    chunks = split_with_visibility(docs, visibility=visibility, doc_id=doc_id)

    vs = get_vs()
    vs.add_documents(chunks)
    try:
        vs.persist()
    except Exception:
        pass

    return {
        "saved_as": str(save_path),
        "visibility": visibility,
        "doc_id": doc_id,
        "chunks": len(chunks),
    }


@app.post("/reindex")
def reindex(
    visibility_default: str = Form("public"),
    current_user: UserInDB = Depends(get_current_user),  # ‼️必须登录
):
    # ‼️只有有权限的人才能重建索引
    require_permission(current_user, "kb.manage_docs")

    visibility_default = (visibility_default or "public").strip().lower()

    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    try:
        client.delete_collection(settings.collection_name)
    except Exception:
        pass
    client.get_or_create_collection(settings.collection_name)

    vs = get_vs()
    raw_docs = load_docs(str(DATA_DOCS_DIR))
    if not raw_docs:
        return {"chunks": 0, "docs": 0, "message": "No documents found in data/docs"}

    chunks = split_docs(raw_docs)
    for c in chunks:
        c.metadata = dict(c.metadata or {})
        c.metadata.setdefault("visibility", visibility_default)

    vs.add_documents(chunks)
    try:
        vs.persist()
    except Exception:
        pass

    return {"docs": len(raw_docs), "chunks": len(chunks), "visibility_default": visibility_default}


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}

# class1 ChatReq(BaseModel):
# uvicorn app.main:app --reload --port 8002 启动服务器
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
# curl -X POST http://127.0.0.1:8002/chat \
#   -H "Content-Type: application/json" \
# 测试4个cutl
# curl -X POST http://127.0.0.1:8002/chat \
#   -H "Content-Type: application/json" \
#   -d '{"text":"我下周二想请一天年假","user_role":"public","requester":"LoveBreaker"}'
# 得到下面json
# {"answer":"请确认你的请假信息：\n- 类型：annual\n- 开始：2025-11-28 09:00\n- 结束：2025-11-28 18:00\n- 时长：1.12 天\n- 原因：无\n回复“确认”提交，或直接回复修改后的信息。","session_id":"sid-52bdc79daf","active_route":"leave"}%
#
# 确认
# curl -X POST http://127.0.0.1:8002/chat \
#   -H "Content-Type: application/json" \
#   -d '{"text":"确认","user_role":"public","requester":"LoveBreaker","session_id":"sid-52bdc79daf"}'
#
# 叉状态
# curl -X POST http://127.0.0.1:8002/chat \
#   -H "Content-Type: application/json" \
#   -d '{"text":"查我的请假状态 LV-c4eda0c8","user_role":"public","requester":"LoveBreaker"}'
#
# 取消
# curl -X POST http://127.0.0.1:8002/chat \
#   -H "Content-Type: application/json" \
#   -d '{"text":"取消请假申请 LV-c4eda0c8","user_role":"public","requester":"LoveBreaker"}'
#
# 再查一次状态
# curl -X POST http://127.0.0.1:8002/chat \
#   -H "Content-Type: application/json" \
#   -d '{"text":"查我的请假状态 LV-c4eda0c8","user_role":"public","requester":"LoveBreaker"}'



# TOKEN =$(curl - s - X POST http: // 127.0.0.1:8002 / auth / login \
#     -H 'Content-Type: application/json' \
#     -d '{"username":"LoveBreaker","password":"123456"}' | jq -r.access_token)
# echo $TOKEN


# ADMIN_TOKEN =$(curl - s - X POST http: // 127.0.0.1:8002 / auth / login \
#     -H 'Content-Type: application/json' \
#     -d '{"username":"admin","password":"123456"}' | jq -r.access_token)
# echo $ADMIN_TOKEN

#
#
#
# curl - s
# http: // 127.0
# .0
# .1: 8002 / rbac / roles \
#     - H
# "Authorization: Bearer $TOKEN" | jq
#
# curl - s
# http: // 127.0
# .0
# .1: 8002 / rbac / roles \
#     - H
# "Authorization: Bearer $ADMIN_TOKEN" | jq