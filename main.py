import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from src.ingestion.github_loader import ingest_repo
from src.rag.vectorstore import get_vectorstore
from src.rag.reviewer import get_review_chain, review_repo_global


def main():
    # repo_url = "msiemens/tinydb"
    repo_url = "Xheng222/ws-tool"
    documents = ingest_repo(repo_url, branch="master")
    # # print(documents[0])

    # vector_store = get_vectorstore()
    # vector_store.delete_collection()
    # vector_store.add_documents(documents=documents)

    # retriever = vector_store.as_retriever(
    #     search_type="mmr",
    #     search_kwargs={"k": 30, "fetch_k": 60, "filter": {"repo_name": repo_url}},
    # )

    # chain = get_review_chain(retriever)
    # for chunk in chain.stream("请讲解这个工具是如何评价代码质量的。"):
    #     print(chunk, end="", flush=True)
    # for chunk in chain.stream("生成这个项目的函数关系。"):
    #     print(chunk, end="", flush=True)

    print("\n=== 开始全局代码审查 (Map-Reduce) ===")
    report = review_repo_global(documents)
    print("\n" + "=" * 30)
    print(report)
    print("=" * 30 + "\n")


if __name__ == "__main__":
    main()
