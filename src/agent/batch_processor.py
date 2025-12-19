from typing import List, Dict
from langchain_core.documents import Document
from src.agent.recursive_reviewer import build_reviewer_graph

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import uuid
from datetime import datetime

# 定义汇总报告的 Prompt
REDUCE_TEMPLATE = """
你是一个资深技术专家。以下是针对同一个项目的多个代码文件的审查摘要。
请根据这些摘要，生成一份完整的项目代码审查报告。

【审查摘要列表】
{summaries}

【最终报告要求】
1. **项目概览**：总结项目的主要功能和架构风格。
2. **关键风险**：列出发现的最严重的问题（Bug、安全漏洞、性能瓶颈），并指明涉及的文件。
3. **代码质量评分**：根据评分准则给出总体评分 (0-100)。
4. **改进建议**：给出具体的重构或优化建议（如“建议在 auth.py 中增加输入验证”）。
5. 必须使用中文回答，格式清晰，使用 Markdown。

# 【评分准则】
# - 框架设计（30分）：代码结构是否清晰，模块划分是否合理，是否易于扩展和维护。
# - 数据处理（30分）：数据加载、预处理、存储等环节是否高效且符合最佳实践。
# - 代码质量（20分）：代码是否遵循PEP8规范，是否有冗余代码，变量命名是否清晰。
# - 文档和注释（10分）：是否有足够的文档说明和代码注释，帮助理解代码逻辑。
# - 系统安全性（10分）：是否考虑了潜在的安全问题，如输入验证、错误处理等。

【最终报告】
"""


def run_batch_review(critical_docs: List[Document], global_context: str):

    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"=== 本次运行 ID: {batch_id} (可在 LangSmith 中搜索此 Tag) ===")

    # 按文件分组
    docs_by_file: Dict[str, List[str]] = {}
    for doc in critical_docs:
        source = doc.metadata["source"]
        if source not in docs_by_file:
            docs_by_file[source] = []
        docs_by_file[source].append(doc.page_content)

    # 进行审查
    print(f"=== 开始批量审查: 共 {len(docs_by_file)} 个核心文件 ===")

    reviewer_app = build_reviewer_graph()
    file_reports = []

    # TODO 暂时为串行之行，之后可改为并发
    for source, code_chunks in docs_by_file.items():
        print(f"启动审查: {source}")

        initial_state = {
            "target_docs": code_chunks,
            "file_source": source,
            "global_context": global_context,
            "retrieved_context": [],
            "unknown_symbols": [],
            "loop_cnt": 0,
            "final_report": "",
        }

        config = {
            "run_name": f"Review: {source.split('/')[-1]}",
            "tags": [batch_id, "code_review"],
            "metadata": {"source_file": source},
        }

        result = reviewer_app.invoke(initial_state, config=config)
        report = result.get("final_report", "无报告生成")
        file_reports.append(f"### 文件: {source}\n{report}")

    if not file_reports:
        return "未生成任何审查报告（可能是没有核心代码通过了 L1 筛选）。"

    # 汇总
    llm = ChatOpenAI(model="deepseek-chat", temperature=0)
    reduce_prompt = ChatPromptTemplate.from_template(REDUCE_TEMPLATE)
    reduce_chain = reduce_prompt | llm | StrOutputParser()

    combined_summaries = "\n\n".join(file_reports)

    try:
        final_report = reduce_chain.invoke({"summaries": combined_summaries})
        return final_report
    except Exception as e:
        return (
            f"汇总报告生成失败: {str(e)}\n\n以下是原始文件报告:\n{combined_summaries}"
        )
