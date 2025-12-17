from langchain_community.document_loaders import GithubFileLoader
from langchain_core.documents import Document
from typing import List, Dict
from src.ingestion.tree_sitter import Splitter_with_treeSitter
from src.config import settings


# 1. 定义支持的文件后缀
SUPPORTED_EXTENSIONS = (
    ".py",
    ".js",
    ".java",
    ".go",
    ".rb",
    ".cpp",
    ".c",
    ".cs",
    ".ts",
    ".rst",
    ".rs",
    ".md",
    ".txt",
    ".json",
)


def ingest_repo(repo_name: str, branch: str = "main") -> List[Document]:
    """
    加载 GitHub 仓库并按语言使用 tree-sitter 切分文件。

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
        raise ValueError(
            "未找到 GITHUB_ACCESS_TOKEN。请在 .env 文件中配置该变量以避免速率限制。"
        )

    if "/" not in repo_name:
        raise ValueError(f"无效的仓库名 '{repo_name}'。格式应为 'owner/repo'。")

    loader = GithubFileLoader(
        repo=repo_name,
        access_token=settings.GITHUB_TOKEN,
        github_api_url="https://api.github.com",
        file_filter=lambda file_path: file_path.endswith(
            SUPPORTED_EXTENSIONS
        ),  # 只读指定类型的文件
        branch=branch,
    )

    documents = loader.load()
    print(f"Loaded {len(documents)} documents")
    return documents


def split_repo(
    documents: List[Document], repo_name: str, branch: str
) -> List[Document]:
    """
    使用 tree-sitter 按语言结构切分代码文件。
    Args:
        documents (List[Document]): 待切分的文档列表
    Returns:
        List[Document]: 切分后的文档列表
    """

    split_docs = Splitter_with_treeSitter(documents)

    for split in split_docs:
        split.metadata["repo_name"] = repo_name
        split.metadata["branch"] = branch

    print(f"Total splits generated: {len(split_docs)}")
    return split_docs
