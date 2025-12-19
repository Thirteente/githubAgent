from typing import List
from pydantic import BaseModel, Field
from src.agent.state import ReviewState
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.rag.vectorstore import get_vectorstore
from langgraph.graph import StateGraph, END


class ReviewOutput(BaseModel):
    """第一阶段审查的输出格式"""

    is_complete: bool = Field(description="是否获得足够的信息完成审查")
    unknown_symbols: List[str] = Field(
        description="需要查阅定义的未知函数", default_factory=list
    )
    report: str = Field(description="审查报考内容", default="")


# --- Prompt ---
ANALYZER_PROMPT = """
你是一个严谨的代码审查员。正在审查仓库中的一个重要文件: {file_source}

【待审查代码】
{target_code}

【已知上下文】
{context}

请分析代码。如果你遇到**关键的**未知函数/类定义，请在 `unknown_symbols` 中列出它们的名字（不要列出标准库函数）。
如果信息足够，请将 `is_complete` 设为 True 并输出详细报告。

【输出格式要求】
请务必输出合法的 JSON 格式，不要包含 Markdown 代码块标记（如 ```json）。
{format_instructions}
"""

# --- 节点函数 ---


def analyzer_node(state: ReviewState) -> dict:
    """分析节点，生成对应的审查报告。如果过程中发现了未知的符号（函数名、类名等）会转向信息检索节点寻找相关信息。

    Args:
        state (ReviewState): 审查的状态

    Returns:
        dict: final_report 或是 unknown_symbols 和 loop_cnt
    """
    llm = ChatOpenAI(model="deepseek-chat", temperature=0)
    parser = PydanticOutputParser(pydantic_object=ReviewOutput)
    format_instructions = parser.get_format_instructions()

    # 拼接上下文
    full_context = (
        state["global_context"] + "\n\n" + "\n".join(state.get("retrieved_context", []))
    )
    target_code = "\n---\n".join(state["target_docs"])

    prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)
    chain = prompt | llm | parser

    try:
        result = chain.invoke(
            {
                "file_source": state["file_source"],
                "target_code": target_code,
                "context": full_context,
                "format_instructions": format_instructions,  # 注入指令
            }
        )

        if result.is_complete:
            return {"final_report": result.report}
        else:
            return {
                "unknown_symbols": result.unknown_symbols,
                "loop_cnt": state["loop_cnt"] + 1,
            }
    except Exception as e:
        return {"final_report": f"审查过程中发生错误: {str(e)}"}


def retriever_node(state: ReviewState):
    """信息检索节点，检索审查节点当中发现的未知符号。

    Args:
        state (ReviewState): 审查的状态

    Returns:
        dict: 检索到的上下文
    """
    vector_store = get_vectorstore()
    new_context = []

    print(f"   [Retriever] 正在查找: {state['unknown_symbols']}")

    for symbol in state["unknown_symbols"]:
        # 首先查向量库
        docs = vector_store.similarity_search(f"def {symbol}", k=1)
        if docs:
            new_context.append(
                f"--- {symbol} 定义 (from {docs[0].metadata['source']}) ---\n{docs[0].page_content}"
            )
        else:
            # 如果查不到，可以尝试查 L2
            new_context.append(f"--- {symbol} --- \n(未在核心代码库中找到定义)")

    return {"retrieved_context": new_context}


def build_reviewer_graph():
    """构智能体建状态机。

    Returns:
        StateGraph: 设置完成的状态机
    """
    workflow = StateGraph(ReviewState)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("retriever", retriever_node)

    workflow.set_entry_point("analyzer")

    def route(state):
        if state.get("final_report"):
            return END
        if state["loop_cnt"] > 2:  # 限制递归深度为 2，防止死循环
            return END
        return "retriever"

    workflow.add_conditional_edges(
        "analyzer", route, {"retriever": "retriever", END: END}
    )
    workflow.add_edge("retriever", "analyzer")

    return workflow.compile()
