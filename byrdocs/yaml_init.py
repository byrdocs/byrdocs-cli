from InquirerPy import inquirer, prompt
from InquirerPy.base.control import Choice
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
import yaml
import pinyin
import isbnlib
import os


# init metadata
data: dict[str, str | dict] = {}

metadata: dict[str, str | dict] = {
    "id": "", "url": "", "type": "", "data": data}


def get_pinyin(text):
    return pinyin.get(text, format="strip", delimiter=" ")


colleges = ["信息与通信工程学院", "电子工程学院", "计算机学院（国家示范性软件学院）",
            "网络空间安全学院", "人工智能学院", "智能工程与自动化学院", "集成电路学院",
            "经济管理学院", "理学院", "未来学院", "人文学院", "数字媒体与设计艺术学院",
            "马克思主义学院", "国际学院", "应急管理学院", "网络教育学院（继续教育学院）",
            "玛丽女王海南学院", "体育部", "卓越工程师学院"]
colleges_pinyin = {c: get_pinyin(c) for c in colleges}
college_completer = {s: None for s in colleges}


def college_validate(content):
    content = content.strip()
    if content == "":
        return True  # 可留空
    inputs = to_clear_list(content)
    for s in inputs:
        if s not in colleges:
            return False
    return True

def ask_for_confirmation(prompt: str="确定提交？") -> bool:
    result = inquirer.confirm(prompt, default=True).execute()
    return result


class CollageCompleter(Completer):
    def get_completions(self, document: Document, complete_event):
        input_pinyin = get_pinyin(document.text)
        input_pinyin = input_pinyin.replace(" ", "")
        suggestions = [college for college, pinyin_name in colleges_pinyin.items(
        ) if pinyin_name.replace(" ", "").startswith(input_pinyin)]
        for suggestion in suggestions:
            yield Completion(suggestion, start_position=-len(input_pinyin))


def not_empty(content: str | list):
    if type(content) is str:
        return content.strip() != ""
    if type(content) is list:
        return content != []
    return bool(content)


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
        汉字 = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", "二十一", "二十二", "二十三", "二十四", "二十五", "二十六", "二十七", "二十八", "二十九", "三十", "三十一", "三十二", "三十三", "三十四", "三十五", "三十六", "三十七", "三十八", "三十九", "四十", "四十一", "四十二", "四十三", "四十四", "四十五", "四十六", "四十七", "四十八", "四十九", "五十", "五十一", "五十二",
              "五十三", "五十四", "五十五", "五十六", "五十七", "五十八", "五十九", "六十", "六十一", "六十二", "六十三", "六十四", "六十五", "六十六", "六十七", "六十八", "六十九", "七十", "七十一", "七十二", "七十三", "七十四", "七十五", "七十六", "七十七", "七十八", "七十九", "八十", "八十一", "八十二", "八十三", "八十四", "八十五", "八十六", "八十七", "八十八", "八十九", "九十", "九十一", "九十二", "九十三", "九十四", "九十五", "九十六", "九十七", "九十八", "九十九", "一百"]
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


def valid_year_period(start: str, end: str) -> bool:
    if start == "" or end == "":
        return False
    try:
        start = int(start)
        end = int(end)
    except ValueError:
        return False
    return end - start in [0, 1]


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
    # remove duplicate and empty
    content: list = content.strip().split("\n")
    content = [s.strip() for s in content]
    content = list(set(filter(None, content)))
    return content


def cancel(text="已取消。") -> None:
    print(f"\033[1;33m{text}\033[0m")
    exit(0)


def ask_for_init(file_name: str = None) -> str:  # 若需要传入 file_name，需要带上后缀名
    global metadata
    if file_name is None:
        file_name = inquirer.text(
            message="文件名或链接:",
            long_instruction="例如 <md5>.pdf 或 https://byrdocs.org/files/<md5>.pdf",
            validate=format_filename,
            mandatory_message="必填",
            invalid_message="文件名错误，应为十六进制 md5 值加文件后缀 (.pdf/.zip)"
        ).execute()
    file_name = format_filename(file_name)
    metadata["id"] = file_name[:-4]
    metadata["url"] = f"https://byrdocs.org/files/{file_name}"
    if os.path.exists(metadata["id"]+".yml"):
        continued = inquirer.confirm(
            message=f"当前路径下存在该文件的元信息文件，是否继续并覆盖此文件?",
            long_instruction=f"{os.path.realpath(metadata["id"]+".yml")}",
            default=False,
            confirm_letter="y",
            reject_letter="n",
        ).execute()
        if not continued:
            cancel()

    type: str = inquirer.select(
        mandatory_message="必填",
        message="文件类型:",
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
                "message": "标题:",
                "validate": not_empty,
                "mandatory_message": "必填",
                "invalid_message": "必填",
            },
            {
                "type": "input",
                "multiline": True,
                "message": "作者:",
                "long_instruction": "一行一个\nEnter 换行；ESC + Enter 提交",
                "validate": not_empty,
                "mandatory_message": "必填",
                "transformer": to_clear_list,
                "invalid_message": "填写至少一个作者",
            },
            {
                "type": "input",
                "multiline": True,
                "instruction": " ",
                "long_instruction": "一行一个，可选\nEnter 换行；ESC + Enter 提交",
                "message": "译者:",
                "mandatory": False,
                "transformer": to_clear_list,
            },
            {
                "type": "input",
                "message": "版次:",
                "mandatory": False,
                "long_instruction": "阿拉伯数字，可选",
                "validate": lambda e: to_vaild_edition(e) is not None,
                "invalid_message": "请填写合法的版次",
            },
            {
                "type": "input",
                "mandatory": False,
                "message": "出版社:",
                "long_instruction": "可选",
            },
            {
                "type": "input",
                "message": "出版年份:",
                "mandatory": False,
                "validate": is_vaild_year,
                "long_instruction": "可选",
                "invalid_message": "请填写合法的年份",
            },
            {
                "type": "input",
                "multiline": True,
                "message": "ISBN:",
                "long_instruction": "一行一个\nEnter 换行；ESC + Enter 提交",
                "instruction": " ",
                "validate": to_isbn13,
                "mandatory_message": "必填",
                "transformer": to_clear_list,
                "invalid_message": "请填写至少一个合法的 ISBN-10 或 ISBN-13",
            },
        ]
        result = prompt(questions)
        if ask_for_confirmation():
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
        else:
            cancel()

    elif type == "test":
        questions1 = [
            {
                "name": "college",
                "type": "input",
                "instruction": " ",
                "message": "考试学院:",
                "long_instruction": "确认学院实际考过此考卷才填写，无法确认可留空\n一行一个，可选\nTab 补全；Enter 换行；ESC + Enter 提交",
                "completer": CollageCompleter(),
                "multiline": True,
                "mandatory": False,
                "validate": college_validate,
                "invalid_message": "请填写合法的学院全名",
                "transformer": lambda content: to_clear_list(content)
            },
            {
                "name": "course_type",
                "type": "list",
                "message": "考试学段:",
                "mandatory": False,
                "choices": [
                    "本科",
                    "研究生",
                    Choice(value=None, name="未知")
                ]
            },
            {
                "name": "course_name",
                "type": "input",
                "message": "考试课程全称:",
                "long_instruction": "需要包括字母和括号中的内容，比如「高等数学A（上）」",
                "validate": not_empty,
                "mandatory_message": "必填",
                "invalid_message": "必填"
            }
        ]
        result1 = prompt(questions1)
        time_start = inquirer.text(
            message="考试学年开始年份:",
            long_instruction="例如 2023-2024 学年，应当填写 2023。如果只能精确到某一年，填写该年份即可",
            validate=lambda y: is_vaild_year(y) and not_empty(y),
            mandatory_message="必填",
            invalid_message="请填写合法的年份，完全不知道年份的试题是不应该收录的",
        ).execute()
        time_end = inquirer.text(
            message="考试学年结束年份:",
            long_instruction="例如 2023-2024 学年，应当填写 2024。如果只能精确到某一年，填写该年份即可",
            validate=lambda y: valid_year_period(time_start, y),
            mandatory_message="必填",
            invalid_message=f"仅能填写 {time_start} 或 {int(time_start) + 1}",
        ).execute()
        questions2 = [
            {
                "name": "semester",
                "type": "list",
                "message": "考试所在的学期:",
                "mandatory": False,
                "choices": [
                    Choice(value="First", name="第一学期"),
                    Choice(value="Second", name="第二学期"),
                    Choice(value=None, name="未知")
                ]
            },
            {
                "name": "stage",
                "type": "list",
                "message": "是期中还是期末考试？",
                "mandatory": False,
                "choices": [
                    Choice(value="期中", name="期中"),
                    Choice(value="期末", name="期末"),
                    Choice(value=None, name="未知")
                ]
            },
            {
                "name": "content",
                "type": "checkbox",
                "message": "是原题还是答案, 还是均有？",
                "long_instruction": "空格以选择，回车以提交\n如果只有答案而没有题面，不能算作「原题」。\n如果答案不能涵盖绝大多数题目，不能算作「答案」。\n如果题目、答案都显著不全，这样的文件不应当被收录。",
                "choices": [
                    Choice(value="原题", name="原题"),
                    Choice(value="答案", name="答案"),
                ],
                "validate": not_empty,
                "invalid_message": "必填"
            }
        ]
        result2: dict = prompt(questions2)
        result = {**result1, **result2}
        # print(result)
        # result = [str(s).strip() for s in result.values()]
        # result = {k: str(v).strip() for k, v in result.items()}
        if ask_for_confirmation():
            data = {}
            if not_empty(result['college']):
                data['college'] = to_clear_list(result['college'])
            data['course'] = {}
            data['time'] = {}
            if result['course_type'] is not None:
                data['course']['type'] = result['course_type']
            data['course']['name'] = result['course_name'].strip()
            data['time']['start'] = time_start.strip()
            data['time']['end'] = time_end.strip()
            if result['semester'] is not None:
                data['time']['semester'] = result['semester']
            if result['stage'] is not None:
                data['time']['stage'] = result['stage']
            data['filetype'] = file_name[-3:]
            data['content'] = result['content']
        else:
            cancel()

    else:  # doc
        questions = [
            {
                "name": "title",
                "type": "input",
                "message": "标题:",
                "long_instruction": "自行总结一个合适的标题",
                "validate": not_empty,
                "invalid_message": "必填",
                "mandatory_message": "必填",
            },
            {
                "name": "course_type",
                "type": "rawlist",
                "message": "资料适用的学段:",
                "choices": ["本科", "研究生", Choice(value=None, name="未知")],
                "mandatory": False,
            },
            {
                "name": "course_name",
                "type": "input",
                "message": "资料对应课程的全称:",
                "long_instruction": "需要包括字母和括号中的内容，比如「高等数学A（上）」",
                "validate": not_empty,
                "invalid_message": "请填写课程全称",
                "mandatory_message": "必填",
            },
            {
                "name": "content",
                "type": "checkbox",
                "message": "选择一个或多个资料类型：",
                "long_instruction": "空格以选择，回车以提交",
                "choices": ["思维导图", "题库", "答案", "知识点", "课件"],
                "validate": not_empty,
                "invalid_message": "必填",
            }
        ]
        result = prompt(questions)
        # result = {k: str(v).strip() for k, v in result.items()}
        if ask_for_confirmation():
            data = {
                "title": result["title"].strip(),
                "filetype": file_name[-3:],
                "course": [{}],      # 格式要求为数组，可能有多项，但此处暂时只支持用户输入单项
                "content": result["content"],
            }
            if result['course_type'] is not None:
                data['course'][0]['type'] = result['course_type']
            data['course'][0]['name'] = result['course_name'].strip()
        else:
            cancel()

    metadata["data"] = data

    yaml_content = (
        f"# yaml-language-server: $schema=https://byrdocs.org/schema/{type}.yaml\n\n"
    )
    yaml_content += yaml.dump(metadata, indent=2,
                              sort_keys=False, allow_unicode=True)
    with open(f"{metadata['id']}.yml", "w", encoding="utf-8") as f:
        f.write(yaml_content)
    # print()
    print(yaml_content)
    print(f"\n\033[1;32m✔ 已写入 {metadata['id']}.yml\033[0m")
