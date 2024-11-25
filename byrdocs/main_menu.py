from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator
from byrdocs.resources import title
from pathlib import Path

class Command:
    def __init__(self, command: str, file: str = None):
        self.command = command
        self.file = file

def main_menu() -> Command:
    print(f"\033[1;94m{title}\033[0m")
    command = inquirer.rawlist(
        message="请选择操作",
        choices=[
            Choice("upload_2", "上传文件"),   # 交互式上传
            Choice("login", "登录到 BYR Docs"),
            Choice("logout", "登出"),
            Choice("init", "交互式生成文件元信息文件"),
            Choice("validate", "(待实现) 验证元信息文件的合法性"),
            Choice("exit", "退出"),
        ],
        default=1,
        mandatory=True
    ).execute()
    
    if command == "upload_2":
        file_path = inquirer.filepath(
            message="选择上传的文件路径",
            long_instruction="支持拖拽文件到终端。或直接输入，Tab 补全，Enter 确定。",
            validate=PathValidator(is_file=True, message="请选定一个正确的文件"),
            only_files=False
        ).execute()
        return Command(command, Path(file_path).expanduser().absolute())
    
    if command == "exit":
        exit(0)
        
    return Command(command)