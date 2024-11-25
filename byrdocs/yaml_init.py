from InquirerPy import inquirer, prompt
from InquirerPy.base.control import Choice
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
import yaml
import pinyin
import isbnlib
import os
import time
from byrdocs.history_manager import UploadHistory


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


def ask_for_confirmation(prompt: str = "确认提交？") -> bool:
    result = inquirer.confirm(prompt, default=True).execute()
    return result


class CollageCompleter(Completer):
    def get_completions(self, document: Document, complete_event):
        lines = document.text.split("\n")
        line = lines[-1]
        suggestions = [
            college
            for college, pinyin_name in colleges_pinyin.items()
            if pinyin_name.replace(" ", "").startswith(
                get_pinyin(line.strip()).replace(" ", "")
            )
        ]
        start_position = -len(line)
        yield from (Completion(s, start_position=start_position) for s in suggestions)


def get_delta_time(upload_time: float) -> str:
    delta = time.time() - upload_time
    if delta < 60:
        return f"{int(delta)} 秒前"
    delta = int(delta / 60)
    if delta < 60:
        return f"{delta} 分钟前"
    delta = int(delta / 60)
    if delta < 24:
        return f"{delta} 小时前"
    delta = int(delta / 24)
    return f"{delta} 天前"


def get_recent_file_choices() -> list[Choice] | None:
    history = UploadHistory()
    history = history.get()
    history.sort(key=lambda x: x[2], reverse=True)
    choices = []
    for line in history:
        choices.append(
            Choice(value=line[1], name=f"{line[0]} ({get_delta_time(float(line[2]))})")
        )
    if choices == []:
        return None
    return choices


def get_recent_file_md5(file_name: str):
    history = UploadHistory()
    history = history.get()
    for line in history:
        if line[0] == file_name:
            return line[1]
    return "Unknown"


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
        for c in file_name:
            if c not in "0123456789abcdef":
                return None
        return file_name + suffix
    return None


def to_clear_list(content: str) -> list[str]:
    # remove duplicate and empty
    content: list = content.strip().split("\n")
    content = [s.strip() for s in content]
    content = list(set(filter(None, content)))
    return content


def cancel(text="操作已取消。") -> None:
    print(f"\033[1;33m{text}\033[0m")
    exit(0)


def ask_for_init(file_name: str = None) -> str:  # 若需要传入 file_name，需要带上后缀名
    global metadata
    if (recent_file_choices := get_recent_file_choices()) is not None:
        if file_name is None:
            file_name = inquirer.fuzzy(
                message="选择最近上传的文件:",
                long_instruction="输入文件名或使用上下键选择，按回车确定，按 ESC 跳过。",
                choices=recent_file_choices,
                validate=format_filename,
                transformer=lambda name: f"{name}: {get_recent_file_md5(name)}",
                keybindings={"skip": [{"key": "escape"}]},
                mandatory=False,
                invalid_message="请选择一个有效的文件。"
            ).execute()
    if file_name is None:
        file_name = inquirer.text(
            message="输入文件名或链接:",
            long_instruction="例如 <md5>.pdf 或 https://byrdocs.org/files/<md5>.pdf",
            validate=format_filename,
            mandatory_message="此项为必填项",
            invalid_message="文件名格式错误，应为 MD5 值加文件后缀 (.pdf/.zip)"
        ).execute()
    file_name = format_filename(file_name)
    metadata["id"] = file_name[:-4]
    metadata["url"] = f"https://byrdocs.org/files/{file_name}"
    if os.path.exists(metadata["id"]+".yml"):
        continued = inquirer.confirm(
            message=f"当前目录下已存在该文件的元信息文件，是否继续并覆盖？",
            long_instruction=f"{os.path.realpath(metadata['id']+'.yml')}",
            default=False,
            confirm_letter="y",
            reject_letter="n",
        ).execute()
        if not continued:
            cancel()

    type: str = inquirer.select(
        mandatory_message="此项为必填项",
        message="选择文件类型:",
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
                "mandatory_message": "此项为必填项",
                "invalid_message": "此项为必填项",
            },
            {
                "type": "input",
                "multiline": True,
                "message": "输入作者:",
                "long_instruction": "每行输入一位作者，按 Enter 换行，按 ESC + Enter 提交",
                "validate": not_empty,
                "mandatory_message": "此项为必填项",
                "transformer": to_clear_list,
                "invalid_message": "请至少填写一位作者",
            },
            {
                "type": "input",
                "multiline": True,
                "instruction": " ",
                "long_instruction": "每行输入一位译者，可选。按 Enter 换行，按 ESC + Enter 提交",
                "message": "输入译者:",
                "mandatory": False,
                "transformer": to_clear_list,
            },
            {
                "type": "input",
                "message": "输入版次:",
                "mandatory": False,
                "long_instruction": "阿拉伯数字，可选",
                "validate": lambda e: to_vaild_edition(e) is not None,
                "invalid_message": "请输入有效的版次",
            },
            {
                "type": "input",
                "mandatory": False,
                "message": "输入出版社:",
                "long_instruction": "可选",
            },
            {
                "type": "input",
                "message": "输入出版年份:",
                "mandatory": False,
                "validate": is_vaild_year,
                "long_instruction": "可选",
                "invalid_message": "请输入有效的年份",
            },
            {
                "type": "input",
                "multiline": True,
                "message": "输入 ISBN:",
                "long_instruction": "每行输入一个 ISBN，按 Enter 换行，按 ESC + Enter 提交",
                "instruction": " ",
                "validate": to_isbn13,
                "mandatory_message": "此项为必填项",
                "transformer": to_clear_list,
                "invalid_message": "请至少填写一个有效的 ISBN-10 或 ISBN-13",
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
                "message": "输入考试学院:",
                "long_instruction": "请确认学院实际考过此试卷，无法确认可留空。每行输入一个学院，按 Tab 补全，按 Enter 换行，按 ESC + Enter 提交",
                "completer": CollageCompleter(),
                "multiline": True,
                "mandatory": False,
                "validate": college_validate,
                "invalid_message": "请填写有效的学院全称",
                "transformer": lambda content: to_clear_list(content)
            },
            {
                "name": "course_type",
                "type": "list",
                "message": "选择考试学段:",
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
                "message": "输入考试课程全称:",
                "long_instruction": "需要包括字母和括号中的内容，例如「高等数学A（上）」",
                "validate": not_empty,
                "mandatory_message": "此项为必填项",
                "invalid_message": "此项为必填项"
            }
        ]
        result1 = prompt(questions1)
        time_start = inquirer.text(
            message="输入考试学年开始年份:",
            long_instruction="例如 2023-2024 学年，应填写 2023。如果只能精确到某一年，填写该年份即可",
            validate=lambda y: is_vaild_year(y) and not_empty(y),
            mandatory_message="此项为必填项",
            invalid_message="请输入有效的年份，完全不知道年份的试题不应被收录",
        ).execute()
        time_end = inquirer.text(
            message="输入考试学年结束年份:",
            long_instruction="例如 2023-2024 学年，应填写 2024。如果只能精确到某一年，填写该年份即可",
            validate=lambda y: valid_year_period(time_start, y),
            mandatory_message="此项为必填项",
            invalid_message=f"只能填写 {time_start} 或 {int(time_start) + 1}",
        ).execute()
        questions2 = [
            {
                "name": "semester",
                "type": "list",
                "message": "选择考试所在学期:",
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
                "message": "选择考试阶段:",
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
                "message": "选择文件内容类型:",
                "long_instruction": "多选，使用空格选择，回车提交。\n如果只有答案而没有题面，不能算作「原题」。\n如果答案不能涵盖绝大多数题目，不能算作「答案」。\n如果题目、答案都显著不全，这样的文件不应被收录。",
                "choices": [
                    Choice(value="原题", name="原题"),
                    Choice(value="答案", name="答案"),
                ],
                "validate": not_empty,
                "invalid_message": "此项为必填项"
            }
        ]
        result2: dict = prompt(questions2)
        result = {**result1, **result2}
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
                "message": "输入标题:",
                "long_instruction": "请自行总结一个合适的标题",
                "validate": not_empty,
                "invalid_message": "此项为必填项",
                "mandatory_message": "此项为必填项",
            },
            {
                "name": "course_type",
                "type": "rawlist",
                "message": "选择资料适用的学段:",
                "choices": ["本科", "研究生", Choice(value=None, name="未知")],
                "mandatory": False,
            },
            {
                "name": "course_name",
                "type": "input",
                "message": "输入资料对应课程全称:",
                "long_instruction": "需要包括字母和括号中的内容，例如「高等数学A（上）」",
                "validate": not_empty,
                "invalid_message": "请填写课程全称",
                "mandatory_message": "此项为必填项",
            },
            {
                "name": "content",
                "type": "checkbox",
                "message": "选择资料类型:",
                "long_instruction": "多选，使用空格选择，回车提交",
                "choices": ["思维导图", "题库", "答案", "知识点", "课件"],
                "validate": not_empty,
                "invalid_message": "此项为必填项",
            }
        ]
        result = prompt(questions)
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
    print(f"\n\033[1;32m✔ 已成功写入 {metadata['id']}.yml\033[0m")
