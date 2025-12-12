from langchain_community.document_loaders import GithubFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
from typing import List, Dict
from src.config import settings
import os
from dotenv import load_dotenv
load_dotenv()


# 1. 定义支持的文件后缀
SUPPORTED_EXTENSIONS = (".py", ".js", ".java", ".go", ".rb", ".cpp", ".c", ".cs", ".ts")

# 2. 建立 后缀 -> Language 的映射关系
EXTENSION_TO_LANGUAGE: Dict[str, Language] = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".ts": Language.TS,
    ".java": Language.JAVA,
    ".go": Language.GO,
    ".rb": Language.RUBY,
    ".cpp": Language.CPP,
    ".c": Language.C,
    ".cs": Language.CSHARP,
}



def ingest_repo(repo_name: str, branch:str = "main") -> List[Document]:
    """
    加载 GitHub 仓库并按语言切分文件。

    Args:
        repo_name: 仓库全名，例如 "langchain-ai/langchain"
        branch: 分支名称，默认为 "main"

    Returns:
        List[Document]: 切分后的文档列表

    Raises:
        ValueError: 当 Token 缺失或仓库名格式错误时抛出
    """
    token = settings.GITHUB_TOKEN
    if not token:
        raise ValueError("未找到 GITHUB_ACCESS_TOKEN。请在 .env 文件中配置该变量以避免速率限制。")

    if '/' not in repo_name:
        raise ValueError(f"无效的仓库名 '{repo_name}'。格式应为 'owner/repo'。")

    loader = GithubFileLoader(
        repo=repo_name, 
        access_token=settings.GITHUB_TOKEN,
        github_api_url="https://api.github.com",
        file_filter=lambda file_path: file_path.endswith(SUPPORTED_EXTENSIONS), # 只读指定类型的文件
        branch=branch,
    )

    documents = loader.load()
    print(f"Loaded {len(documents)} documents")

    # 创建不同语言的 TextSplitter 实例
    splitters: Dict[Language, RecursiveCharacterTextSplitter] = {}
    for ext, lang in EXTENSION_TO_LANGUAGE.items():
        if lang not in splitters:
            splitters[lang] = RecursiveCharacterTextSplitter.from_language(
                language=lang,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )

    splitters['default'] = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    # 按语言拆分文档
    split_docs: List[Document] = []
    for doc in documents:
        file_path = doc.metadata.get("source", "")
        file_ext = os.path.splitext(file_path)[1]

        lang = EXTENSION_TO_LANGUAGE.get(file_ext)
        if lang in splitters:
            splitter = splitters[lang]
        else:
            splitter = splitters["default"]

        splits = splitter.split_documents([doc])
        split_docs.extend(splits)

    for split in split_docs:
        split.metadata["repo_name"] = repo_name
        split.metadata["branch"] = branch

    print(f"Total splits generated: {len(split_docs)}")
    return split_docs
