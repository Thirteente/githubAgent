import chromadb
from langchain_community.vectorstores import chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import asyncio

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", cache_folder="./models")



async def test_connection():
    # 测试数据库是否正确连接
    client = await chromadb.AsyncHttpClient(host="localhost", port=8000)
    try:
        heartbeat = await client.heartbeat()
        print(f"Chroma Heartbeat: {heartbeat}") 
    except Exception as e:
        print(f"连接失败: {e}")

# test_connection()
asyncio.run(test_connection())