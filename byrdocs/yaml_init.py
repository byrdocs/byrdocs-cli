from InquirerPy import inquirer, prompt
import InquirerPy.validator
from InquirerPy.base.control import Choice
import yaml


# init metadata
data: dict[str, str | dict] = {}

metadata: dict[str, str | dict] = {
    "id": "",
    "url": "",
    "type": "",
    "data": data
}


def not_empty(content):
    return content.strip() != ""

def format_filename(file_name: str) -> str | None:
    file_name = file_name.strip()
    prefixs = ["https://byrdocs.org/files/", "byrdocs.org/files/", "/files/", "files/", "/"]
    for pre in prefixs:
        file_name = file_name.removeprefix(pre)
    if file_name.endswith('.pdf'):
        suffix = '.pdf'
    elif file_name.endswith('.zip'):
        suffix = '.zip'
    else:
        return None
    file_name = file_name.removesuffix(suffix)
    if len(file_name) == 32:
        return file_name + suffix
    return None

def ask_for_init(file_name: str=None) -> str:   # 若需要传入 file_name，需要带上后缀名
    if file_name is None:
        file_name = inquirer.text(
            message="Please enter the file name you got: ",
            validate=lambda ans: format_filename(ans) is not None,
            invalid_message="Invaild file name."
        ).execute()
    file_name = format_filename(file_name)
    metadata["id"] = file_name[:-4]
    metadata["url"] = f"https://byrdocs.org/files/{file_name}"
    
    type: str = inquirer.select(
        message="Select a file type:",
        choices=[
            Choice(value='book', name="书籍"),
            Choice(value='test', name="试题"),
            Choice(value='doc', name="资料")
        ]).execute()
    metadata['type'] = type
    
    if type == 'book':
        questions = [
            {"type": "input", "message": "输入书籍标题:", "validate": not_empty, "invalid_message": "请填写一个书籍标题"},
            {"type": "input", "multiline": True, "message": "输入书籍作者，可输入多个:", "instruction": "可输入多个作者，一行一个，Enter换行，ESC+Enter提交。", "validate": not_empty, "invalid_message": "请填写至少一个作者"},
            {"type": "input", "multiline": True, "message": "输入译者，可输入多个:", "instruction": "可输入多个译者，一行一个，如没有/未知译者，可省略。Enter换行，ESC+Enter提交。"},
        ]
        result = prompt(questions)


ask_for_init()