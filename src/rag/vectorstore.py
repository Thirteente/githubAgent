import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import settings


def get_vectorstore() -> Chroma:
    """
    初始化并返回 ChromaDB 向量库客户端。
    
    Returns:
        Chroma: 已初始化的 ChromaDB 向量库实例
    """
    embedding_model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL, cache_folder=settings.CACHE_FOLDER)

    client = chromadb.HttpClient(settings.CHROMA_HOST, settings.CHROMA_PORT)

    # 测试数据库是否正确连接
    try:
        heartbeat = client.heartbeat()
    except Exception as e:
        raise ConnectionError(f"无法连接到 ChromaDB ({settings.CHROMA_HOST}:{settings.CHROMA_PORT})。请确保 Docker 容器已启动。错误信息: {e}")

    vector_store = Chroma(
        collection_name=settings.COLLECTION_NAME,
        embedding_function=embedding_model,
        client=client
    )
    print("ChromaDB client connected successfully via Docker!")
    return vector_store