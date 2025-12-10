from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import settings


def get_llm():  # 配置一个大语言模型，此处用的是deepseek
    return ChatTongyi(
        model=settings.model_name,
        api_key=settings.qianwen_api_key,
        temperature=0.2,
        streaming=True,
    )

def get_embeddings():  # 此处配置的是千问的嵌入式模型
    return DashScopeEmbeddings(  # 此处这个类是千问的，所以不用url，默认就连接到千问
        model=settings.qianwen_embedding_model_name,
        dashscope_api_key=settings.qianwen_api_key,
    )

if __name__ == "__main__":
    resp = get_llm().invoke('你是谁？你的版本是什么？')
    print(resp.content)


