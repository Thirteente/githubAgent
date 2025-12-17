import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from src.ingestion.github_loader import ingest_repo, split_repo
from src.rag.vectorstore import get_vectorstore
from src.rag.reviewer import get_review_chain, review_repo_global
from src.ingestion.filters import filter_documents_l0
from src.ingestion.complexity import filter_documents_l1
from src.ingestion.tree_sitter import extract_skeleton
from src.agent.summarizer import generate_file_summaries


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

    repo_url = "Thirteente/githubAgent"
    documents = ingest_repo(repo_url, branch="main")
    # documents_splitted = split_repo(documents, repo_url, branch="main")

    core_docs, context_docs = filter_documents_l0(documents)
    # print(f"核心文件：\n {core_docs[:2]}")
    # print(f"上下文文件：\n {context_docs[:2]}")
    critical_docs = filter_documents_l1(core_docs, threshold=5)
    print(f"关键代码块数量: {len(critical_docs)}")

    l2_candidates = critical_docs + context_docs

    file_summaries = generate_file_summaries(l2_candidates)

    # 打印地图看看
    print("\n=== 项目地图 (L2 Summary) ===")
    for path, summary in file_summaries.items():
        print(summary)

    # 临时测试：看看过滤效果
    # print(f"Context Docs: {[d.metadata['source'] for d in context_docs[:2]]}")
    # print(
    #     f"Critical Docs: {[d.metadata['source'] for d in critical_docs[:2]]}\n {[d.metadata['keep_reason']for d in critical_docs[:2]]}"
    # )
    # 提取骨架


if __name__ == "__main__":
    main()
