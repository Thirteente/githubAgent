import os
from github import Github, Auth
from src.config import settings


def generate_repo_tree(repo_name: str, branch: str = "main") -> str:
    """
    使用 GitHub API 直接获取文件树结构（不下载文件内容）。
    """

    token = settings.GITHUB_TOKEN
    auth = Auth.Token(token)
    github = Github(auth)
    repo = github.get_repo(repo_name)

    # recursive = True 表示递归获取所有子目录
    try:
        tree = repo.get_git_tree(sha=branch, recursive=True)
    except Exception as e:
        return f"Error fetching tree: {e}"

    file_structure = {}
    for element in tree.tree:
        # print(element.path)
        path_parts = element.path.split("/")
        current_level = file_structure
        for part in path_parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

    # tree_str = f"Project Structure ({repo_name} @ {branch}):\n"

    # for element in tree.tree:
    #     type_marker = "[DIR]" if element.type == "tree" else ""
    #     tree_str += f"- {type_marker}{element.path}\n"

    tree_lines = _build_tree(file_structure)
    # print(file_structure)

    return f"Project Structure ({repo_name} @ {branch}):\n" + "\n".join(tree_lines)


def _build_tree(structure, prefix=""):
    lines = []
    items = list(structure.keys())
    items.sort()

    for i, name in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└──" if is_last else "├──"

        annotation = ""
        # if name == "main.go" or "main.py":
        #     annotation = "  [Entry Point]"
        # elif name == "Dockerfile":
        #     annotation = "  [Config]"

        lines.append(f"{prefix}{connector}{name}{annotation}")

        # 递归处理子目录
        if structure[name]:
            extension = "   " if is_last else "│   "
            lines.extend(_build_tree(structure[name], prefix + extension))

    return lines


if __name__ == "__main__":
    print(generate_repo_tree("Thirteente/githubAgent", "main"))
