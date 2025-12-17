# src/ingestion/filters.py
from typing import List, Tuple
from langchain_core.documents import Document
import re

# 定义噪音模式 (直接丢弃)
IGNORE_PATTERNS = [
    r"node_modules/",
    r"\.git/",
    r"\.idea/",
    r"\.vscode/",
    r"__pycache__/",
    r"dist/",
    r"build/",
    r"venv/",
    r"\.min\.js$",  # 压缩文件
    r"\.svg$",
    r"\.png$",
    r"\.jpg$",
    r"\.jpeg$",
    r"\.gif$",
    r"\.ico$",  # 图片
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"poetry\.lock$",  # 锁文件通常太长且无语义
]

# 定义上下文文件模式 (保留但不做复杂度分析)
CONTEXT_PATTERNS = [
    r"Dockerfile",
    r"docker-compose",
    r"requirements\.txt$",
    r"pyproject\.toml$",
    r"package\.json$",  # 注意：不包含 lock 文件
    r"README",
    r"LICENSE",
    r"\.env\.example$",
    r"Makefile",
]

# 定义测试文件模式 (可选：作为上下文或低优先级审查)
TEST_PATTERNS = [
    r"test/",
    r"tests/",
    r"_test\.py$",
    r"test_\.py$",
    r"\.spec\.js$",
    r"\.test\.js$",
]


def filter_documents_l0(
    documents: List[Document],
) -> Tuple[List[Document], List[Document]]:
    """
    L0 层过滤器：将文档分为 '核心代码' 和 '上下文文件'，并丢弃噪音。

    Returns:
        core_docs: 需要进行后续深度审查（L1/L3）的代码
        context_docs: 仅用于提供环境信息的上下文文件（跳过 L1，直接 L2）
    """
    core_docs = []
    context_docs = []

    print(f"L0 过滤开始: 输入 {len(documents)} 个文件")

    for doc in documents:
        source = doc.metadata.get("source", "")

        # 1. 检查是否为噪音 -> 丢弃
        if any(
            re.search(pattern, source, re.IGNORECASE) for pattern in IGNORE_PATTERNS
        ):
            continue

        # 2. 检查是否为上下文文件 -> 归入 context_docs
        if any(
            re.search(pattern, source, re.IGNORECASE) for pattern in CONTEXT_PATTERNS
        ):
            doc.metadata["category"] = "context"
            context_docs.append(doc)
            continue

        # 3. 检查是否为测试文件 -> 归入 context_docs (或者你可以决定归入 core 但标记低优先级)
        # 这里我们采纳你的建议：作为上下文保留，不深度审查
        if any(re.search(pattern, source, re.IGNORECASE) for pattern in TEST_PATTERNS):
            doc.metadata["category"] = "test"
            context_docs.append(doc)
            continue

        # 4. 剩下的默认为核心代码 -> 归入 core_docs
        doc.metadata["category"] = "core"
        core_docs.append(doc)

    print(
        f"L0 过滤结束: 核心代码 {len(core_docs)} 个, 上下文文件 {len(context_docs)} 个, 丢弃 {len(documents) - len(core_docs) - len(context_docs)} 个"
    )
    return core_docs, context_docs
