import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # ChromaDB 配置
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", 8000))
    COLLECTION_NAME: str = "github_codebase"

    # Embedding 配置
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CACHE_FOLDER: str = "./notebooks/models"

    # Splitter 配置
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 200

    # Github 配置
    GITHUB_TOKEN: str = os.getenv("GITHUB_ACCESS_TOKEN", "")


settings = Config()
