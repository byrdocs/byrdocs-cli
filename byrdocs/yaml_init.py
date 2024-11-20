from InquirerPy import inquirer
import InquirerPy.validator
import yaml


# init metadata
data: dict[str, str | dict] = {}

metadata: dict[str, str | dict] = {
    "id": "",
    "url": "",
    "type": "",
    "data": data
}


def format_filename(file_name: str) -> str | None:
    file_name = file_name.strip()
    prefixs = ["https://byrdocs.org/files/", "byrdocs.org/files/", "/files/", "files/", "/"]
    for pre in prefixs:
        file_name = file_name.removeprefix(pre)
    if file_name.endswith('.pdf'):
        surfix = '.pdf'
    elif file_name.endswith('.zip'):
        surfix = '.zip'
    else:
        return None
    file_name = file_name.removesuffix(surfix)
    if len(file_name) == 32:
        return file_name + surfix
    return None

def ask_for_init(file_name: str=None) -> str:
    questions: list[dict[str, str]] = []
    if file_name is None:
        file_name = inquirer.text(
            message="Please enter the file name you got: ",
            validate=lambda ans: format_filename(ans) is not None,
            invalid_message="Invaild file name."
        ).execute()
    file_name = format_filename(file_name)
    # print(file_name)


ask_for_init()