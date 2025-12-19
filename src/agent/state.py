from typing import TypedDict, List, Annotated
import operator


class ReviewState(TypedDict):
    """内部审查的状态定义"""

    # 输入
    target_docs: List[str]  # 当前批次的代码块内容列表
    file_source: str  # 当前的文件名及其目录

    # 上下文
    global_context: str  # L2生成的各部分摘要 + 通过README进行的仓库概述（如果有的话
    retrieved_context: Annotated[List[str], operator.add]  # 累计检索到的补充信息

    # 流程控制
    unknown_symbols: List[str]  # LLM 发现的未知符号
    loop_cnt: int  # 循环计数，防止死循环
    final_report: str  # 最终报告
