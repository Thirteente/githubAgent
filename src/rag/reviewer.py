from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.vectorstores import VectorStoreRetriever



# 定义 Prompt 模板
# 技巧：在 System Prompt 中明确设定角色和语言要求
REVIEW_TEMPLATE = """
你是一个精通 Python 严格的资深代码审查者。请根据以下检索到的代码片段（Context）回答用户的问题。

【要求】
1. 必须使用**中文**回答。
2. 回答时可以使用激进的语言风格，但必须专业且有理有据。
3. 回答应简洁明了，避免冗长。
4. 最后根据评分准则，输出对这个代码库的评分，分数格式"1/100"。

【评分准则】
- 框架设计（30分）：代码结构是否清晰，模块划分是否合理，是否易于扩展和维护。
- 数据处理（30分）：数据加载、预处理、存储等环节是否高效且符合最佳实践。
- 代码质量（20分）：代码是否遵循PEP8规范，是否有冗余代码，变量命名是否清晰。
- 文档和注释（10分）：是否有足够的文档说明和代码注释，帮助理解代码逻辑。
- 系统安全性（10分）：是否考虑了潜在的安全问题，如输入验证、错误处理等。

【代码片段】
{context}

【用户问题】
{question}
"""



# 格式化文档的辅助函数
def format_docs(docs):
    return "\n\n".join([
        f"--- 文件: {doc.metadata['source']} ---\n{doc.page_content}" 
        for doc in docs
    ])

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
        temperature=0, # 代码问题建议低温度，更严谨
        streaming=True
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
