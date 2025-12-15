from typing import TypedDict, List, Any

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

from app.rag.prompts import QA_SYSTEM, QA_USER
from app.deps import get_llm, get_vs

class QAState(TypedDict, total=False):
    question: str
    text: str          # 兼容 /chat 传 text
    user_role: str
    docs: List[Any]
    answer: str
    messages: List[Any]


def decide_retrieve(state: QAState) -> str:
    """
    条件函数：决定走检索还是直答
    返回值必须对应 add_conditional_edges 的 key
    """
    # 简化版：永远检索
    return "retrieve"  # 跳到下一个叫做retrieve的节点


def decide_retrieve_node(state: QAState) -> dict:
    """
    节点 runnable：必须返回 dict
    这里只是一个 no-op 节点，真正路由在 decide_retrieve() 里完成
    """
    return {} # 当一个节点返回空字典，表示什么也不做。


# ---------- retrieval / generation ----------

def retrieve(state: QAState) -> dict:
    """从 Chroma 检索相关文档。

    先按 visibility 做过滤；如果元数据里没有该字段导致检索为空，则回退到无过滤检索。
    """
    vs = get_vs()
    role = state.get("user_role", "public")
    query = state.get("question") or state.get("text") or ""

    # 1) filtered retrieval first
    retriever = vs.as_retriever(  # as_retriever用于构造一个要检索的需求
        search_kwargs={
            "k": 8,  # 最多查8个结果
            "filter": {"visibility": {"$in": ["public", role]}},
            # 只查询向量数据库中那些public的文档
        }
    )
    docs = retriever.invoke(query) # invoke就是真的去向量数据库查询
    # docs表示从向量数据库中查出来的文档

    # 2) fallback to unfiltered if empty (common when metadata doesn't contain `visibility`)
    if not docs: # 如果docs查出东西，下面就不执行了
        retriever2 = vs.as_retriever(search_kwargs={"k": 8})
        docs = retriever2.invoke(query)
        return {"docs": docs, "question": query, "debug": "fallback_unfiltered"}

    return {"docs": docs, "question": query, "debug": "filtered"}


def grade_evidence(state: QAState) -> str:
    """检索后判断是否有证据。"""
    return "good" if state.get("docs") else "bad"


def generate_answer(state: QAState) -> dict:
    """带引用生成答案。"""
    llm = get_llm()
    docs = state.get("docs", [])

    context = "\n\n".join(
        f"[{i+1}] {d.page_content}\n(source={d.metadata.get('source')}, page={d.metadata.get('page')})"
        for i, d in enumerate(docs[:6])
    )  # 将我检索出的内容拼接成一个大的字符串

    prompt = QA_USER.format(question=state["question"], context=context)
    messages = [
        AIMessage(content=QA_SYSTEM),
        HumanMessage(content=prompt)
    ]
    ans = llm.invoke(messages).content  # content表示大模型返回的结果
    return {"answer": ans}


def refuse_or_clarify(state: QAState) -> dict:
    """无证据兜底。"""
    return {
        "answer": "我没有在当前可见知识库中找到足够证据回答。请提供更具体的关键词/文档来源。"
    }


def build_qa_graph():
    g = StateGraph(QAState)

    # 注意：节点注册用 runnable（返回 dict）
    g.add_node("decide_retrieve", decide_retrieve_node)
    g.add_node("retrieve", retrieve)
    g.add_node("generate", generate_answer)
    g.add_node("refuse", refuse_or_clarify)

    # START -> decide_retrieve
    g.add_edge(START, "decide_retrieve")

    # decide_retrieve 的条件路由（用 decide_retrieve 条件函数）
    g.add_conditional_edges(
        "decide_retrieve",
        decide_retrieve,
        {
            "retrieve": "retrieve",
            "direct": "generate",
        },
    )

    # retrieve 后根据证据充分性路由
    g.add_conditional_edges(
        "retrieve",
        grade_evidence,
        {
            "good": "generate",
            "bad": "refuse",
        },
    )

    g.add_edge("generate", END)
    g.add_edge("refuse", END)

    return g.compile()