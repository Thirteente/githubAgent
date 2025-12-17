import lizard
import re
from typing import List
from langchain_core.documents import Document

# --- 安全启发式规则 (Security Heuristics) ---
# 如果代码包含这些模式，无论复杂度多低，都必须保留
SENSITIVE_PATTERNS = [
    # 危险函数
    r"eval\(",
    r"exec\(",
    r"os\.system\(",
    r"subprocess\.call",
    r"pickle\.load",
    r"yaml\.load",
    r"input\(",
    # 数据库/SQL 相关
    r"SELECT.*FROM",
    r"INSERT.*INTO",
    r"UPDATE.*SET",
    r"DELETE.*FROM",
    r"cursor\.execute",
    r"raw_sql",
    # 密钥/凭证 (简单的正则，更复杂的建议用 Gitleaks)
    r"api_key",
    r"secret",
    r"password",
    r"token",
    r"auth",
    r"credential",
    r"private_key",
    # 网络/请求
    r"requests\.get",
    r"requests\.post",
    r"urllib",
    r"socket",
    # 文件操作
    r"open\(",
    r"write\(",
    r"read\(",
    # 常见漏洞点
    r"noqa",  # 试图绕过 lint 的地方通常有猫腻
    r"TODO",
    r"FIXME",  # 开发者留下的坑
]


def check_security_heuristics(code: str) -> bool:
    """
    检查代码是否包含敏感模式。
    Returns: True if sensitive pattern found.
    """
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return True
    return False


def filter_documents_l1(docs: List[Document], threshold: int = 5) -> List[Document]:
    """
    L1 层过滤器：基于复杂度 + 安全启发式规则。

    保留条件 (满足任一即可):
    1. 圈复杂度 (CCN) >= threshold (逻辑复杂)
    2. 命中敏感关键词 (可能存在安全风险)
    """
    kept_docs = []
    dropped_count = 0

    print(f"L1 过滤开始: 输入 {len(docs)} 个代码块 (CCN阈值: {threshold})")

    for doc in docs:
        code = doc.page_content
        source = doc.metadata.get("source", "unknown")

        # 1. 安全旁路检查 (Security Bypass)
        if check_security_heuristics(code):
            doc.metadata["keep_reason"] = "security_heuristic"
            kept_docs.append(doc)
            continue

        # 2. 复杂度检查 (Complexity Check)
        try:
            # lizard 分析需要文件名（用于推断语言）和代码内容
            analysis = lizard.analyze_file.analyze_source_code(source, code)

            # 如果没有函数（全是全局变量或类属性），lizard 返回空列表
            if not analysis.function_list:
                # 如果代码很长但没函数，可能是一大坨配置或脚本，保留
                if len(code) > 500:
                    doc.metadata["keep_reason"] = "length"
                    kept_docs.append(doc)
                else:
                    dropped_count += 1
                continue

            # 获取最大复杂度
            max_ccn = max(
                [func.cyclomatic_complexity for func in analysis.function_list]
            )

            if max_ccn >= threshold:
                doc.metadata["complexity"] = max_ccn
                doc.metadata["keep_reason"] = "high_complexity"
                kept_docs.append(doc)
            else:
                dropped_count += 1

        except Exception as e:
            # 分析出错（可能是片段不完整），保守起见保留
            print(f"Lizard 分析失败 ({source}): {e}")
            doc.metadata["keep_reason"] = "analysis_error"
            kept_docs.append(doc)

    print(
        f"L1 过滤结束: 保留 {len(kept_docs)} 个, 丢弃 {dropped_count} 个 (保留率 {len(kept_docs)/len(docs):.1%})"
    )
    return kept_docs
