# src/agent/summarizer.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, List
from langchain_core.documents import Document
from src.ingestion.tree_sitter import extract_skeleton

# 定义摘要 Prompt
SUMMARY_TEMPLATE = """
你是一个代码库导航员。请根据以下代码文件的“骨架”（仅包含签名和注释），用一句话总结该文件的主要职责。

【文件路径】
{filepath}

【代码骨架】
{skeleton}

【要求】
1. 输出格式：`[文件名]: 主要职责描述`
2. 描述要精炼，例如：“处理用户登录和JWT生成”、“定义数据库模型”。
3. 不要包含具体实现细节。
4. 完全基于事实回答，不要进行任何的猜想。
"""


def generate_file_summaries(docs: List[Document]) -> Dict[str, str]:
    """
    L2 层：为每个文件生成摘要。

    Args:
        docs: 需要生成摘要的文档列表 (通常是 context_docs + critical_docs 的原始文件版本)
        注意：这里最好传入未切分的原始文件 Document，或者按文件名聚合后的 Document。
    """
    # 使用便宜的小模型
    llm = ChatOpenAI(model="deepseek-chat", temperature=0)
    # 或者 model="gemini-1.5-flash"

    chain = ChatPromptTemplate.from_template(SUMMARY_TEMPLATE) | llm | StrOutputParser()

    summaries = {}

    # 批处理优化：实际生产中建议使用 llm.batch 或异步处理
    print(f"L2 摘要生成开始: 处理 {len(docs)} 个文件...")

    for doc in docs:
        filepath = doc.metadata.get("source", "unknown")
        ext = "." + filepath.split(".")[-1] if "." in filepath else ""

        # 1. 提取骨架
        skeleton = extract_skeleton(doc.page_content, ext)

        # 2. 生成摘要
        try:
            summary = chain.invoke({"filepath": filepath, "skeleton": skeleton})
            summaries[filepath] = summary
            # print(f"摘要: {summary}")
        except Exception as e:
            print(f"摘要生成失败 ({filepath}): {e}")
            summaries[filepath] = "无法生成摘要"

    return summaries
