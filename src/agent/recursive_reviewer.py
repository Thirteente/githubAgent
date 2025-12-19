from typing import List
from pydantic import BaseModel, Field
from src.agent.state import ReviewState
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.rag.vectorstore import get_vectorstore
from langgraph.graph import StateGraph, END
import re


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

【当前状态】
这是第 {loop_cnt} 次审查循环（最大允许 3 次）。

【任务目标】
请对代码进行深度审查，重点关注：潜在Bug、边界条件处理、类型安全和逻辑漏洞。

【决策逻辑】
1. **判断是否需要检索**：
   - 如果代码调用了某个函数/类（如 `self.storage.read()`），且你在【已知上下文】中看不到其源码，你需要判断它是否是**本项目内部定义**的。
   - **如果是标准库或知名第三方库**（如 `json.load`, `requests.get`, `List`, `Dict`, `Optional`等），**请绝对不要检索**，直接基于常识理解。
   - **如果是项目内部逻辑**（如 `utils.process_data`, `User.login`等），且对判断是否存在 Bug 至关重要，请将其加入 `unknown_symbols`。

2. **避免死循环**：
   - 如果这是第 2 次或第 3 次循环，且你之前请求的符号依然没有出现在上下文中（说明检索失败），请**不要再次请求相同的符号**。
   - 在这种情况下，请尝试根据现有信息进行“最佳猜测”并完成审查，将 `is_complete` 设为 True。

3. **完成条件**：
   - 当所有关键的内部依赖都已明确，或者虽然有缺失但不足以阻碍发现主要问题时，请生成详细报告。

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
                "loop_cnt": state["loop_cnt"],
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
        # "definition of X" 能同时匹配 function_definition 和 class_definition
        docs = vector_store.similarity_search(f"definition of {symbol}", k=3)

        target_doc = None

        # 2. 优先筛选：利用 Metadata 中的 type 字段
        # 我们在 tree-sitter 切分时保存了 "function_definition" 或 "class_definition"
        for doc in docs:
            doc_type = doc.metadata.get("type", "")
            if "definition" in doc_type:
                # 双重确认：确保 symbol 真的出现在内容里（防止语义漂移）
                if symbol in doc.page_content:
                    target_doc = doc
                    break

        # 3. 次级筛选：如果 Metadata 没命中，尝试正则匹配内容
        if not target_doc and docs:
            # 匹配 "def symbol" 或 "class symbol"
            pattern = re.compile(rf"(def|class)\s+{re.escape(symbol)}\b")
            for doc in docs:
                if pattern.search(doc.page_content):
                    target_doc = doc
                    break

        # 4. 兜底：如果都没匹配上，取相关性最高的第一个（可能是用法，但也比没有好）
        if not target_doc and docs:
            target_doc = docs[0]

        if target_doc:
            source = target_doc.metadata.get("source", "unknown")
            new_context.append(
                f"--- {symbol} 定义 (from {source}) ---\n{target_doc.page_content}"
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
