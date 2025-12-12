import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from src.ingestion.github_loader import ingest_repo
from src.rag.vectorstore import get_vectorstore
from src.rag.reviewer import get_review_chain   

def main():
    repo_url = "Thirteente/githubAgent"
    # documents = ingest_repo(repo_url, branch="main")
    # # print(documents[0])

    vector_store = get_vectorstore()
    # # vector_store.delete_collection()
    # vector_store.add_documents(documents=documents)

    retriever = vector_store.as_retriever(
        search_type="mmr", 
        search_kwargs={
            "k": 20, 
            "fetch_k": 40,
            "filter":{"repo_name": repo_url}
        }
    )

    chain = get_review_chain(retriever)
    for chunk in chain.stream("评价这个项目。"):
        print(chunk, end="", flush=True)
    



if __name__ == "__main__":
    main()  