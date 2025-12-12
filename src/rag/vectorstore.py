import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter



def get_vectorstore() -> Chroma:
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", cache_folder="./notebooks/models")

    client = chromadb.HttpClient(host="localhost", port=8000)

    # 测试数据库是否正确连接
    try:
        heartbeat = client.heartbeat()
        print(f"Chroma Heartbeat: {heartbeat}") 
    except Exception as e:
        print(f"连接失败: {e}")

    vector_store = Chroma(
        collection_name="github_codebase",
        embedding_function=embedding_model,
        client=client
    )
    print("ChromaDB client connected successfully via Docker!")
    return vector_store