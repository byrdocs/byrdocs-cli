from InquirerPy import inquirer, prompt
import InquirerPy.validator
from InquirerPy.base.control import Choice
import yaml
import isbnlib


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

def is_vaild_year(year: str) -> bool:
    try:
        year = int(year)
    except ValueError:
        return False
    return 1000 <= year <= 2100

def to_vaild_edition(edition: str) -> str | None:
    edition = edition.strip()
    if edition == "":
        return None
    try:
        edition = int(edition)
    except ValueError:
        # 转化汉字
        edition = edition.removeprefix("第")
        edition = edition.removesuffix("版")
        edition = edition.strip()
        汉字 = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        try: 
            edition = int(edition)
        except ValueError:
            if edition in 汉字:
                edition = 汉字.index(edition) + 1
            else:
                return None
    return str(edition)

def to_isbn13(isbns) -> list[str] | None:
    isbns = isbns.strip()
    isbns = isbns.split('\n')
    result: list[str] = []
    for isbn in isbns:
        isbn = isbn.strip()
        if isbnlib.is_isbn10(isbn) or isbnlib.is_isbn13(isbn):
            result.append(isbnlib.mask(isbnlib.to_isbn13(isbn)))
        else:
            return None
    return result

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
            validate=format_filename,
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
            {"type": "input", "message": "输入书籍的版本: ", "instruction": "一个数字，如未知版次，可留空。", "validate": to_vaild_edition, "invalid_message": "请填写合法的版次。"},
            {"type": "input", "message": "输入出版社: ", "instruction": "如未知出版社，可留空。"},
            {"type": "input", "message": "输入出版年份: ", "validate": is_vaild_year, "instruction": "", "invalid_message": "请填写合法的年份。"},
            {"type": "input", "multiline": True, "message": "输入书籍的 ISBN: ", "instruction": "可输入多个 ISBN，一行一个，Enter换行，ESC+Enter提交。", "validate": to_isbn13, "invalid_message": "请填写合法的 ISBN10 或 ISBN13 编号。"},
        ]
        result = prompt(questions)

# print(to_isbn13("978-7-04-023069-7"))
ask_for_init()