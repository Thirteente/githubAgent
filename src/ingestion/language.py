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
# "skeleton_query" 为用于骨架提取的查询模式

LANGUAGE_CONFIG = {
    ".py": {
        "lang": Language(tree_sitter_python.language()),
        "query": """
            (class_definition) @class
            (function_definition) @function
        """,
        "skeleton_query": """
            (function_definition body: (block) @body)
            (class_definition body: (block) @body)
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
        "skeleton_query": """
            (function_declaration body: (statement_block) @body)
            (class_declaration body: (class_block) @body)
            (arrow_function body: (statement_block) @body)
            (method_definition body: (statement_block) @body)
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
        "skeleton_query": """
            (class_declaration body: (class_body) @body)
            (interface_declaration body: (object_type) @body)
            (method_declaration body: (statement_block) @body)
            (function_declaration body: (statement_block) @body)
            (arrow_function body: (statement_block) @body)
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
        "skeleton_query": """
            (class_declaration body: (class_body) @body)
            (interface_declaration body: (interface_body) @body)
            (method_declaration body: (block) @body)
            (constructor_declaration body: (block) @body)
        """,
    },
    ".go": {
        "lang": Language(tree_sitter_go.language()),
        "query": """
            (type_declaration) @class
            (function_declaration) @function
            (method_declaration) @function
        """,
        "skeleton_query": """
            (func_literal body: (block) @body)
            (function_declaration body: (block) @body)
            (method_declaration body: (block) @body)
        """,
    },
    ".rb": {
        "lang": Language(tree_sitter_ruby.language()),
        "query": """
            (class) @class
            (module) @module
            (method) @function
        """,
        "skeleton_query": """
            (class body: (_) @body)
            (module body: (_) @body)
            (method body: (_) @body)
            (singleton_method body: (_) @body)
        """,
    },
    ".cpp": {
        "lang": Language(tree_sitter_cpp.language()),
        "query": """
            (class_specifier) @class
            (struct_specifier) @class
            (function_definition) @function
        """,
        "skeleton_query": """
            (function_definition body: (compound_statement) @body)
            (class_specifier body: (field_declaration_list) @body)
            (struct_specifier body: (field_declaration_list) @body)
            (lambda_expression body: (compound_statement) @body)
        """,
    },
    ".c": {
        "lang": Language(tree_sitter_c.language()),
        "query": """
            (struct_specifier) @class
            (function_definition) @function
        """,
        "skeleton_query": """
            (function_definition body: (compound_statement) @body)
            (struct_specifier body: (field_declaration_list) @body)
            (enum_specifier body: (enumerator_list) @body)
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
        "skeleton_query": """
            (class_declaration body: (body) @body)
            (constructor_declaration body: (block) @body)
            (class_declaration body: (declaration_list) @body)
            (struct_declaration body: (declaration_list) @body)
            (interface_declaration body: (declaration_list) @body)
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
        "skeleton_query": """
            (function_item body: (block) @body)
            (impl_item body: (declaration_list) @body)
            (trait_item body: (declaration_list) @body)
            (mod_item body: (declaration_list) @body)
        """,
    },
}


def get_language_config(file_extension: str):
    """获取指定文件后缀的语言配置"""
    return LANGUAGE_CONFIG.get(file_extension)
