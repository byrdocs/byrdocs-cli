from InquirerPy import inquirer, prompt
from InquirerPy.base.control import Choice
import yaml
import isbnlib


# init metadata
data: dict[str, str | dict] = {}

metadata: dict[str, str | dict] = {"id": "", "url": "", "type": "", "data": data}


def not_empty(content):
    return content.strip() != ""


def is_vaild_year(year: str) -> bool:
    if year == "":
        return True  # 可留空
    try:
        year = int(year)
    except ValueError:
        return False
    return 1000 <= year <= 2100


def to_vaild_edition(edition: str) -> str | None:
    edition = edition.strip()
    if edition == "":
        return ""  # 可留空
    try:
        edition = int(edition)
    except ValueError:
        # 转化汉字
        edition = edition.removeprefix("第")
        edition = edition.removesuffix("版")
        edition = edition.strip()
        汉字 = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", "二十一", "二十二", "二十三", "二十四", "二十五", "二十六", "二十七", "二十八", "二十九", "三十", "三十一", "三十二", "三十三", "三十四", "三十五", "三十六", "三十七", "三十八", "三十九", "四十", "四十一", "四十二", "四十三", "四十四", "四十五", "四十六", "四十七", "四十八", "四十九", "五十", "五十一", "五十二", "五十三", "五十四", "五十五", "五十六", "五十七", "五十八", "五十九", "六十", "六十一", "六十二", "六十三", "六十四", "六十五", "六十六", "六十七", "六十八", "六十九", "七十", "七十一", "七十二", "七十三", "七十四", "七十五", "七十六", "七十七", "七十八", "七十九", "八十", "八十一", "八十二", "八十三", "八十四", "八十五", "八十六", "八十七", "八十八", "八十九", "九十", "九十一", "九十二", "九十三", "九十四", "九十五", "九十六", "九十七", "九十八", "九十九", "一百"]
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
    isbns = isbns.split("\n")
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
    prefixs = [
        "https://byrdocs.org/files/",
        "byrdocs.org/files/",
        "/files/",
        "files/",
        "/",
    ]
    for pre in prefixs:
        file_name = file_name.removeprefix(pre)
    if file_name.endswith(".pdf"):
        suffix = ".pdf"
    elif file_name.endswith(".zip"):
        suffix = ".zip"
    else:
        return None
    file_name = file_name.removesuffix(suffix)
    if len(file_name) == 32:
        return file_name + suffix
    return None


def to_clear_list(content: str) -> list[str]:
    content = content.strip().split("\n")
    result = []
    for element in content:
        element = element.strip()
        if element != "":
            result.append(element)
    return result


def ask_for_init(file_name: str = None) -> str:  # 若需要传入 file_name，需要带上后缀名
    global metadata
    if file_name is None:
        file_name = inquirer.text(
            message="Please enter the file name you got: ",
            validate=format_filename,
            invalid_message="文件名错误，应为32位的十六进制md5文件名加上文件后缀名 (.pdf/.zip)",
        ).execute()
    file_name = format_filename(file_name)
    metadata["id"] = file_name[:-4]
    metadata["url"] = f"https://byrdocs.org/files/{file_name}"

    type: str = inquirer.select(
        message="Select a file type:",
        choices=[
            Choice(value="book", name="书籍"),
            Choice(value="test", name="试题"),
            Choice(value="doc", name="资料"),
        ],
    ).execute()
    metadata["type"] = type

    if type == "book":
        questions = [
            {
                "type": "input",
                "message": "输入书籍标题:",
                "validate": not_empty,
                "invalid_message": "请填写一个书籍标题",
            },
            {
                "type": "input",
                "multiline": True,
                "message": "输入书籍作者，可输入多个:",
                "instruction": "可输入多个作者，一行一个，Enter换行，ESC+Enter提交。",
                "validate": not_empty,
                "invalid_message": "请填写至少一个作者",
            },
            {
                "type": "input",
                "multiline": True,
                "message": "输入译者，可输入多个:",
                "instruction": "可输入多个译者，一行一个，如没有/未知译者，可省略。Enter换行，ESC+Enter提交。",
            },
            {
                "type": "input",
                "message": "输入书籍的版本: ",
                "instruction": "一个数字，如未知版次，可留空。",
                "validate": lambda e: to_vaild_edition(e) is not None,
                "invalid_message": "请填写合法的版次。",
            },
            {
                "type": "input",
                "message": "输入出版社: ",
                "instruction": "如未知出版社，可留空。",
            },
            {
                "type": "input",
                "message": "输入出版年份: ",
                "validate": is_vaild_year,
                "instruction": "",
                "invalid_message": "请填写合法的年份。",
            },
            {
                "type": "input",
                "multiline": True,
                "message": "输入书籍的 ISBN: ",
                "instruction": "可输入多个 ISBN，一行一个，Enter换行，ESC+Enter提交。",
                "validate": to_isbn13,
                "invalid_message": "请填写至少一个合法的 ISBN10 或 ISBN13 编号。",
            },
            {"type": "confirm", "message": "是否确认提交 (Enter) ?", "default": True},
        ]
        result = prompt(questions)
        result = [str(s).strip() for s in result.values()]
        data = {"title": result[0], "authors": to_clear_list(result[1])}
        if not_empty(result[2]):
            data["translators"] = to_clear_list(result[2])
        if not_empty(result[3]):
            data["edition"] = to_vaild_edition(result[3])
        if not_empty(result[4]):
            data["publisher"] = result[4]
        if not_empty(result[5]):
            data["publish_year"] = result[5]
        data["isbn"] = to_clear_list(result[6])
        data["filetype"] = file_name[-3:]

    elif type == "test":
        pass

    else:  # doc
        pass

    metadata["data"] = data

    yaml_content = (
        "# yaml-language-server: $schema=https://byrdocs.org/schema/book.yaml\n\n"
    )
    yaml_content += yaml.dump(metadata, indent=2, sort_keys=False, allow_unicode=True)
    with open(f"{metadata['id']}.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"\033[1;94m\n以下的文件元信息已经存储到 {metadata['id']}.yaml 中。\n\033[0m")
    print(yaml_content)


# print(to_isbn13("978-7-04-023069-7"))
# ask_for_init()
