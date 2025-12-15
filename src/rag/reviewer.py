from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.vectorstores import VectorStoreRetriever
from typing import List
from langchain_core.documents import Document


# 定义 Prompt 模板
# 技巧：在 System Prompt 中明确设定角色和语言要求
REVIEW_TEMPLATE = """
你是一个精通 Python 严格的资深代码审查者。请根据以下检索到的代码片段（Context）回答用户的问题。

【代码片段】
{context}

【用户问题】
{question}
"""

MAP_TEMPLATE = """
你是一个代码审查助手。请分析以下一组代码片段（可能来自不同文件），指出其中的关键功能、潜在问题（Bug、安全漏洞、性能问题）以及代码质量评价。

【代码片段集合】
{context_bundle}

【分析结果】
"""

REDUCE_TEMPLATE = """
你是一个资深技术专家。以下是针对同一个项目的多个代码片段的审查摘要。
请根据这些摘要，生成一份完整的项目代码审查报告。

【审查摘要列表】
{summaries}

【最终报告要求】
1. 项目概览：总结项目的主要功能和架构。
2. 关键问题：列出发现的最严重的问题。
3. 代码质量评分：根据评分准则，给出总体评分 (0-100)。
4. 改进建议：给出具体的重构或优化建议。
5. 必须使用中文回答。

# 【评分准则】
# - 框架设计（30分）：代码结构是否清晰，模块划分是否合理，是否易于扩展和维护。
# - 数据处理（30分）：数据加载、预处理、存储等环节是否高效且符合最佳实践。
# - 代码质量（20分）：代码是否遵循PEP8规范，是否有冗余代码，变量命名是否清晰。
# - 文档和注释（10分）：是否有足够的文档说明和代码注释，帮助理解代码逻辑。
# - 系统安全性（10分）：是否考虑了潜在的安全问题，如输入验证、错误处理等。

【最终报告】
"""
# REVIEW_TEMPLATE = """
# 你是一个精通 Python 严格的资深代码审查者。请根据以下检索到的代码片段（Context）回答用户的问题。

# 【要求】
# 1. 必须使用**中文**回答。
# 2. 回答时可以使用激进的语言风格，但必须专业且有理有据。
# 3. 回答应简洁明了，避免冗长。
# 4. 最后根据评分准则，输出对这个代码库的评分，分数格式"1/100"。

# 【评分准则】
# - 框架设计（30分）：代码结构是否清晰，模块划分是否合理，是否易于扩展和维护。
# - 数据处理（30分）：数据加载、预处理、存储等环节是否高效且符合最佳实践。
# - 代码质量（20分）：代码是否遵循PEP8规范，是否有冗余代码，变量命名是否清晰。
# - 文档和注释（10分）：是否有足够的文档说明和代码注释，帮助理解代码逻辑。
# - 系统安全性（10分）：是否考虑了潜在的安全问题，如输入验证、错误处理等。

# 【代码片段】
# {context}

# 【用户问题】
# {question}
# """


# 格式化文档的辅助函数
def format_docs(docs):
    return "\n\n".join(
        [f"--- 文件: {doc.metadata['source']} ---\n{doc.page_content}" for doc in docs]
    )


def get_review_chain(retriever: VectorStoreRetriever) -> Runnable:
    """
    构建并返回代码审查的 RAG Chain。

    Args:
        retriever: 已经初始化好的向量库检索器

    Returns:
        Runnable: 可执行的 LangChain 对象
    """

    llm = ChatOpenAI(
        model="gemini-2.5-flash-lite",
        temperature=0,  # 代码问题建议低温度，更严谨
        streaming=True,
    )

    prompt = ChatPromptTemplate.from_template(REVIEW_TEMPLATE)

    # 流程：检索 -> 格式化文档 -> 填充 Prompt -> 调用 LLM -> 解析输出
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def review_repo_global(docs: List[Document]) -> str:

    # llm = ChatOpenAI(
    #     model="gemini-2.5-flash-lite",
    #     temperature=0,
    # )
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
    )

    # 1. 预处理：将文档分批 (Batching)
    # 假设每个 chunk 约 500-1000 tokens，Gemini 上下文很大，可以一次处理多个。
    # 设置为 10，意味着 332 个片段只需要约 34 次请求，大幅节省 API 调用次数。
    BATCH_SIZE = 10
    doc_batches = [docs[i : i + BATCH_SIZE] for i in range(0, len(docs), BATCH_SIZE)]

    map_inputs = []
    for batch in doc_batches:
        # 拼接该批次的所有代码
        bundle_text = "\n".join(
            [
                f"### 文件: {doc.metadata.get('source', 'unknown')} ###\n{doc.page_content}\n"
                for doc in batch
            ]
        )
        map_inputs.append({"context_bundle": bundle_text})

    print(f"优化策略: 将 {len(docs)} 个片段合并为 {len(map_inputs)} 个批次进行分析...")

    # 2. map阶段，并发分析每个片段
    map_prompt = ChatPromptTemplate.from_template(MAP_TEMPLATE)
    map_chain = map_prompt | llm | StrOutputParser()

    # summaries = []
    # for i, inp in enumerate(map_inputs):
    #     print(f"正在分析批次 {i+1}/{len(map_inputs)} ...")
    #     try:
    #         res = map_chain.invoke(inp)
    #         summaries.append(res)
    #     except Exception as e:
    #         print(f"重试失败，跳过该批次: {e}")

    summaries = map_chain.batch(map_inputs, config={"max_concurrency": 10})

    # 2. Reduce 阶段：汇总结果
    print("正在汇总分析结果 (Reduce Phase)...")

    # 拼接摘要
    combined_summaries = "\n\n".join(
        [
            f"--- 批次 {i+1} 分析摘要 ---\n{summary}"
            for i, summary in enumerate(summaries)
        ]
    )

    reduce_prompt = ChatPromptTemplate.from_template(REDUCE_TEMPLATE)
    reduce_chain = reduce_prompt | llm | StrOutputParser()
    final_report = reduce_chain.invoke({"summaries": combined_summaries})

    return final_report
