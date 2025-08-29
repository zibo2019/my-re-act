import ast
import inspect
import os
import re
from string import Template
from typing import List, Callable, Optional, Tuple

import click
from dotenv import load_dotenv
from openai import OpenAI
import platform

from prompt_template import react_system_prompt_template


class ReActAgent:
    def __init__(self, tools: List[Callable], model: str, project_directory: str, base_url: Optional[str] = None):
        self.tools = { func.__name__: func for func in tools }
        self.model = model
        self.project_directory = project_directory

        # 如果没有指定 base_url，则从环境变量获取，默认使用 OpenAI 官方
        if base_url is None:
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        self.client = OpenAI(
            base_url=base_url,
            api_key=ReActAgent.get_api_key(),
        )

    def run(self, user_input: str):
        messages = [
            {"role": "system", "content": self.render_system_prompt(react_system_prompt_template)},
            {"role": "user", "content": f"<question>{user_input}</question>"}
        ]

        while True:

            # 请求模型
            content = self.call_model(messages)

            # 检测 Thought
            thought_match = re.search(r"<thought>(.*?)</thought>", content, re.DOTALL)
            if thought_match:
                thought = thought_match.group(1)
                print(f"\n\n💭 Thought: {thought}")

            # 检测模型是否输出 Final Answer，如果是的话，直接返回
            if "<final_answer>" in content:
                final_answer = re.search(r"<final_answer>(.*?)</final_answer>", content, re.DOTALL)
                return final_answer.group(1)

            # 检测 Action
            action_match = re.search(r"<action>(.*?)</action>", content, re.DOTALL)
            if not action_match:
                raise RuntimeError("模型未输出 <action>")
            action = action_match.group(1)
            tool_name, args = self.parse_action(action)

            print(f"\n\n🔧 Action: {tool_name}({', '.join(args)})")
            # 只有终端命令才需要询问用户，其他的工具直接执行
            should_continue = input(f"\n\n是否继续？（Y/N）") if tool_name == "run_terminal_command" else "y"
            if should_continue.lower() != 'y':
                print("\n\n操作已取消。")
                return "操作被用户取消"

            try:
                observation = self.tools[tool_name](*args)
            except Exception as e:
                observation = f"工具执行错误：{str(e)}"
            print(f"\n\n🔍 Observation：{observation}")
            obs_msg = f"<observation>{observation}</observation>"
            messages.append({"role": "user", "content": obs_msg})


    def get_tool_list(self) -> str:
        """生成工具列表字符串，包含函数签名和简要说明"""
        tool_descriptions = []
        for func in self.tools.values():
            name = func.__name__
            signature = str(inspect.signature(func))
            doc = inspect.getdoc(func)
            tool_descriptions.append(f"- {name}{signature}: {doc}")
        return "\n".join(tool_descriptions)

    def render_system_prompt(self, system_prompt_template: str) -> str:
        """渲染系统提示模板，替换变量"""
        tool_list = self.get_tool_list()
        file_list = ", ".join(
            os.path.abspath(os.path.join(self.project_directory, f))
            for f in os.listdir(self.project_directory)
        )
        return Template(system_prompt_template).substitute(
            operating_system=self.get_operating_system_name(),
            tool_list=tool_list,
            file_list=file_list
        )

    @staticmethod
    def get_api_key() -> str:
        """Load the API key from an environment variable."""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("未找到 OPENAI_API_KEY 环境变量，请在 .env 文件中设置。")
        return api_key

    def call_model(self, messages):
        print("\n\n正在请求模型，请稍等...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})
        return content

    def parse_action(self, code_str: str) -> Tuple[str, List[str]]:
        match = re.match(r'(\w+)\((.*)\)', code_str, re.DOTALL)
        if not match:
            raise ValueError("Invalid function call syntax")

        func_name = match.group(1)
        args_str = match.group(2).strip()

        # 手动解析参数，特别处理包含多行内容的字符串
        args = []
        current_arg = ""
        in_string = False
        string_char = None
        i = 0
        paren_depth = 0
        
        while i < len(args_str):
            char = args_str[i]
            
            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                    current_arg += char
                elif char == '(':
                    paren_depth += 1
                    current_arg += char
                elif char == ')':
                    paren_depth -= 1
                    current_arg += char
                elif char == ',' and paren_depth == 0:
                    # 遇到顶层逗号，结束当前参数
                    args.append(self._parse_single_arg(current_arg.strip()))
                    current_arg = ""
                else:
                    current_arg += char
            else:
                current_arg += char
                if char == string_char and (i == 0 or args_str[i-1] != '\\'):
                    in_string = False
                    string_char = None
            
            i += 1
        
        # 添加最后一个参数
        if current_arg.strip():
            args.append(self._parse_single_arg(current_arg.strip()))
        
        return func_name, args
    
    def _parse_single_arg(self, arg_str: str):
        """解析单个参数"""
        arg_str = arg_str.strip()
        
        # 如果是字符串字面量
        if (arg_str.startswith('"') and arg_str.endswith('"')) or \
           (arg_str.startswith("'") and arg_str.endswith("'")):
            # 移除外层引号并处理转义字符
            inner_str = arg_str[1:-1]
            # 处理常见的转义字符
            inner_str = inner_str.replace('\\"', '"').replace("\\'", "'")
            inner_str = inner_str.replace('\\n', '\n').replace('\\t', '\t')
            inner_str = inner_str.replace('\\r', '\r').replace('\\\\', '\\')
            return inner_str
        
        # 尝试使用 ast.literal_eval 解析其他类型
        try:
            return ast.literal_eval(arg_str)
        except (SyntaxError, ValueError):
            # 如果解析失败，返回原始字符串
            return arg_str

    def get_operating_system_name(self):
        os_map = {
            "Darwin": "macOS",
            "Windows": "Windows",
            "Linux": "Linux"
        }

        return os_map.get(platform.system(), "Unknown")


class ProjectTools:
    """项目工具类，包含项目目录上下文"""
    def __init__(self, project_directory):
        self.project_directory = project_directory

    def read_file(self, file_path):
        """用于读取文件内容"""
        # 如果是绝对路径，直接使用；否则相对于项目目录
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.project_directory, file_path)

        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_to_file(self, file_path, content):
        """将指定内容写入指定文件"""
        # 如果是绝对路径，直接使用；否则相对于项目目录
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.project_directory, file_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.replace("\\n", "\n"))
        return "写入成功"

    def run_terminal_command(self, command):
        """用于执行终端命令"""
        import subprocess
        # 在项目目录下执行命令
        run_result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=self.project_directory)
        return "执行成功" if run_result.returncode == 0 else run_result.stderr

    def list_directory_structure(self, directory_path=None, max_depth=3):
        """读取目录结构

        Args:
            directory_path: 要读取的目录路径，如果为None则使用项目根目录
            max_depth: 最大递归深度，默认为3层

        Returns:
            str: 格式化的目录结构字符串
        """
        if directory_path is None:
            target_path = self.project_directory
        elif os.path.isabs(directory_path):
            target_path = directory_path
        else:
            target_path = os.path.join(self.project_directory, directory_path)

        if not os.path.exists(target_path):
            return f"目录不存在: {target_path}"

        def _build_tree(path, prefix="", current_depth=0):
            if current_depth >= max_depth:
                return ""

            result = ""
            try:
                items = sorted(os.listdir(path))
                # 分离文件和目录
                dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
                files = [item for item in items if os.path.isfile(os.path.join(path, item))]

                # 先显示目录
                for i, dirname in enumerate(dirs):
                    is_last_dir = (i == len(dirs) - 1) and len(files) == 0
                    connector = "└── " if is_last_dir else "├── "
                    result += f"{prefix}{connector}{dirname}/\n"

                    # 递归显示子目录
                    next_prefix = prefix + ("    " if is_last_dir else "│   ")
                    result += _build_tree(os.path.join(path, dirname), next_prefix, current_depth + 1)

                # 再显示文件
                for i, filename in enumerate(files):
                    is_last = i == len(files) - 1
                    connector = "└── " if is_last else "├── "
                    result += f"{prefix}{connector}{filename}\n"

            except PermissionError:
                result += f"{prefix}[权限不足]\n"

            return result

        tree_structure = f"{os.path.basename(target_path) or target_path}/\n"
        tree_structure += _build_tree(target_path)

        return tree_structure

    def get_project_path(self):
        """获取当前项目的绝对路径

        Returns:
            str: 项目的绝对路径
        """
        return os.path.abspath(self.project_directory)

@click.command()
@click.argument('project_directory',
                type=click.Path(exists=True, file_okay=False, dir_okay=True))
def main(project_directory):
    project_dir = os.path.abspath(project_directory)

    # 创建项目工具实例
    project_tools = ProjectTools(project_dir)
    tools = [project_tools.read_file, project_tools.write_to_file, project_tools.run_terminal_command, project_tools.list_directory_structure, project_tools.get_project_path]
    agent = ReActAgent(tools=tools, model="gemini-2.5-pro", project_directory=project_dir)

    task = input("请输入任务：")

    final_answer = agent.run(task)

    print(f"\n\n✅ Final Answer：{final_answer}")

if __name__ == "__main__":
    main()