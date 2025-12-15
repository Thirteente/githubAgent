# src/ingestion/tree_sitter_demo.py
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tree_sitter import Parser, Query, QueryCursor
from src.ingestion.language import get_language_config


def codeSplitter_with_treeSitter(documents: List[Document]):
    split_docs = []

    # 初始化一个通用的 splitter 为 tree-sitter不适用的文件切片
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=200
    )

    for doc in documents:
        file_path = doc.metadata.get("source", "")
        if "." not in file_path:
            # 没有后缀名的文件
            # 如：Makefile Dockerfile LICENSE 以及一些linux下的可执行文件
            ext = ""
        else:
            ext = "." + file_path.split(".")[-1]

        # 获取文件对应的 tree-sitter 的语言设置
        config = get_language_config(ext)
        if config:
            try:
                lang = config["lang"]
                query_scm = config["query"]

                parser = Parser(lang)
                query = Query(lang, query_scm)
                cursor = QueryCursor(query)

                code_bytes = bytes(doc.page_content, "utf8")
                tree = parser.parse(code_bytes)

                # 执行查询
                matches = cursor.matches(tree.root_node)

                # 如果没有匹配到任何东西，则保留原文档
                if not matches:
                    splits = fallback_splitter.split_documents([doc])
                    split_docs.extend(splits)
                    continue

                # 处理匹配结果
                for match_id, capture_dict in matches:
                    for capture_name, nodes in capture_dict.items():
                        for node in nodes:
                            start_byte = node.start_byte
                            end_byte = node.end_byte

                            block_content = code_bytes[start_byte:end_byte].decode(
                                "utf8"
                            )

                            # 创建新文档，保留元数据和上下文
                            new_metadata = doc.metadata.copy()
                            new_metadata.update(
                                {
                                    "type": capture_name,
                                    "start_line": node.start_point[0] + 1,
                                    "end_line": node.end_point[0] + 1,
                                    "parent_source": file_path,
                                }
                            )

                            new_doc = Document(
                                page_content=block_content, metadata=new_metadata
                            )
                            split_docs.append(new_doc)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                # 出错时退回通用切分
                splits = fallback_splitter.split_documents([doc])
                split_docs.extend(splits)
        else:
            splits = fallback_splitter.split_documents([doc])
            split_docs.extend(splits)

    return split_docs
