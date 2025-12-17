# src/ingestion/tree_sitter_demo.py
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tree_sitter import Parser, Query, QueryCursor
from src.ingestion.language import get_language_config


def Splitter_with_treeSitter(documents: List[Document]):
    """
    使用 tree-sitter 按语言结构切分代码文件。
    Args:
        documents (List[Document]): 待切分的文档列表
    Returns:
        List[Document]: 切分后的文档列表
    """
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


def extract_skeleton(code: str, extension: str) -> str:
    """
    使用 tree-sitter 提取代码骨架(移除函数体和类体)。
    Args:
        code (str): 代码内容
        extension (str): 代码文件后缀名
    Returns:
        str: 提取的代码骨架
    """
    config = get_language_config(extension)
    if not config or "skeleton_query" not in config:
        # 如果不支持这种语言，则截取前2000个字符
        return code[:2000] + "/n...(truncated)..." if len(code) > 2000 else code

    lang = config["lang"]
    query_scm = config["skeleton_query"]

    parser = Parser(lang)
    query = Query(lang, query_scm)
    cursor = QueryCursor(query)

    code_bytes = bytes(code, "utf8")
    tree = parser.parse(code_bytes)

    # 查询找到所有 body 节点
    captures = cursor.captures(tree.root_node)

    # 收集 @body 节点的范围
    ranges_to_move = []
    for name, nodes in captures.items():
        for node in nodes:
            if name == "body":
                # ranges_to_move.append((node.start_byte, node.end_byte))
                start_byte = node.start_byte
                end_byte = node.end_byte

                # --- Python 特化处理：保留 Docstring ---
                if extension == ".py":
                    # 检查 body 的第一个子节点
                    # Python 的 body 通常是一个 block
                    # block -> expression_statement -> string (Docstring)
                    if node.child_count > 0:
                        first_child = node.children[0]
                        if first_child.type == "expression_statement":
                            # 进一步检查是否是字符串
                            if (
                                first_child.child_count > 0
                                and first_child.children[0].type == "string"
                            ):
                                # 找到了 Docstring！
                                # 只移除 Docstring 之后的部分
                                # 如果 Docstring 是 body 的唯一内容，则不移除任何东西
                                if node.child_count > 1:
                                    # 从第二个子节点的开始，到 body 的结束
                                    second_child = node.children[1]
                                    start_byte = second_child.start_byte
                                    # end_byte 保持不变
                                else:
                                    continue  # 只有 Docstring，保留原样

                ranges_to_move.append((start_byte, end_byte))

    # 从后往前替换，避免索引偏移
    ranges_to_move.sort(key=lambda x: x[0], reverse=True)

    skeleton_bytes = bytearray(code_bytes)

    for start, end in ranges_to_move:
        if end - start < 20:
            continue

        replacement = b"\n   ... (impl hidden) ...\n"
        skeleton_bytes[start:end] = replacement

    return skeleton_bytes.decode("utf8")
