from dotenv import load_dotenv

load_dotenv()

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from src.ingestion.github_loader import ingest_repo, split_repo
from src.rag.vectorstore import get_vectorstore
from src.rag.reviewer import get_review_chain, review_repo_global
from src.ingestion.filters import filter_documents_l0
from src.ingestion.complexity import filter_documents_l1
from src.ingestion.tree_sitter import extract_skeleton
from src.agent.summarizer import generate_file_summaries
from src.agent.batch_processor import run_batch_review
from src.agent.tree_generator import generate_repo_tree


def main():
    # # repo_url = "msiemens/tinydb"
    # repo_url = "Xheng222/ws-tool"
    # documents = ingest_repo(repo_url, branch="master")
    # # # print(documents[0])

    # # vector_store = get_vectorstore()
    # # vector_store.delete_collection()
    # # vector_store.add_documents(documents=documents)

    # # retriever = vector_store.as_retriever(
    # #     search_type="mmr",
    # #     search_kwargs={"k": 30, "fetch_k": 60, "filter": {"repo_name": repo_url}},
    # # )

    # # chain = get_review_chain(retriever)
    # # for chunk in chain.stream("请讲解这个工具是如何评价代码质量的。"):
    # #     print(chunk, end="", flush=True)
    # # for chunk in chain.stream("生成这个项目的函数关系。"):
    # #     print(chunk, end="", flush=True)

    # print("\n=== 开始全局代码审查 (Map-Reduce) ===")
    # report = review_repo_global(documents)
    # print("\n" + "=" * 30)
    # print(report)
    # print("=" * 30 + "\n")

    repo_url = "msiemens/tinydb"
    branch = "master"
    documents = ingest_repo(repo_url, branch)
    file_tree = generate_repo_tree(repo_url, branch)
    # documents_splitted = split_repo(documents, repo_url, branch="main")
    # L0 过滤文件
    core_docs, context_docs = filter_documents_l0(documents)

    # 对 core_docs 进行切分之后复杂度过滤
    core_chunks = split_repo(core_docs, repo_url, branch)
    context_chunks = split_repo(context_docs, repo_url, branch)

    # 将文档分片存入向量数据库
    docs = []
    docs.extend(core_chunks)
    docs.extend(context_chunks)

    vector_store = get_vectorstore()
    vector_store.add_documents(docs)

    # L1 根据复杂度和正则得到核心代码
    critical_chunks = filter_documents_l1(core_chunks, threshold=10)
    print(f"关键代码块数量: {len(critical_chunks)}")

    # L2 生成全局概括
    critical_file_paths = {doc.metadata.get("source") for doc in critical_chunks}

    # 2. 从 core_docs (完整文件列表) 中筛选出这些文件
    critical_full_files = [
        doc for doc in core_docs if doc.metadata.get("source") in critical_file_paths
    ]

    l2_candidates = critical_full_files + context_docs
    file_summaries = generate_file_summaries(l2_candidates)
    # all_summaries_str = "\n".join([f"[{k}]: {v}" for k, v in file_summaries.items()])

    # L3 启用状态机进行最后审查
    print("\n=== 进入 L3 深度审查阶段 ===")
    final_report = run_batch_review(critical_chunks, file_summaries, file_tree)
    print("\n=== 最终审查报告 ===")
    print(final_report)


def delete_vectorstore():
    vector_store = get_vectorstore()
    vector_store.delete_collection()


if __name__ == "__main__":
    main()
    # delete_vectorstore()
