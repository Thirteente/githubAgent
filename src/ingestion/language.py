from tree_sitter import Language
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_java
import tree_sitter_go
import tree_sitter_ruby
import tree_sitter_cpp
import tree_sitter_c
import tree_sitter_c_sharp
import tree_sitter_rust

# 定义通用的查询模式
# 注意：不同语言的节点名称可能不同，需要针对性调整
# 例如：Python用 function_definition, Java用 method_declaration

LANGUAGE_CONFIG = {
    ".py": {
        "lang": Language(tree_sitter_python.language()),
        "query": """
            (class_definition) @class
            (function_definition) @function
        """,
    },
    ".js": {
        "lang": Language(tree_sitter_javascript.language()),
        "query": """
            (class_declaration) @class
            (function_declaration) @function
            (method_definition) @function
            (arrow_function) @function
        """,
    },
    ".ts": {
        "lang": Language(tree_sitter_typescript.language_typescript()),
        "query": """
            (class_declaration) @class
            (function_declaration) @function
            (method_definition) @function
            (arrow_function) @function
            (interface_declaration) @interface
        """,
    },
    ".java": {
        "lang": Language(tree_sitter_java.language()),
        "query": """
            (class_declaration) @class
            (interface_declaration) @interface
            (method_declaration) @function
            (constructor_declaration) @function
        """,
    },
    ".go": {
        "lang": Language(tree_sitter_go.language()),
        "query": """
            (type_declaration) @class
            (function_declaration) @function
            (method_declaration) @function
        """,
    },
    ".rb": {
        "lang": Language(tree_sitter_ruby.language()),
        "query": """
            (class) @class
            (module) @module
            (method) @function
        """,
    },
    ".cpp": {
        "lang": Language(tree_sitter_cpp.language()),
        "query": """
            (class_specifier) @class
            (struct_specifier) @class
            (function_definition) @function
        """,
    },
    ".c": {
        "lang": Language(tree_sitter_c.language()),
        "query": """
            (struct_specifier) @class
            (function_definition) @function
        """,
    },
    ".cs": {
        "lang": Language(tree_sitter_c_sharp.language()),
        "query": """
            (class_declaration) @class
            (interface_declaration) @interface
            (method_declaration) @function
            (constructor_declaration) @function
        """,
    },
    ".rs": {
        "lang": Language(tree_sitter_rust.language()),
        "query": """
            (struct_item) @class
            (enum_item) @class
            (trait_item) @interface
            (function_item) @function
            (impl_item) @impl
        """,
    },
}


def get_language_config(file_extension: str):
    """获取指定文件后缀的语言配置"""
    return LANGUAGE_CONFIG.get(file_extension)
