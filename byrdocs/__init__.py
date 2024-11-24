import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import requests
import json
import hashlib
import pathlib
import argparse
import sys
import os
from time import sleep
import argcomplete
from tqdm import tqdm
from byrdocs.yaml_init import ask_for_init, ask_for_confirmation, cancel    # TODO: 进行模块拆分便于维护，而不是全从这里导入进来

info = lambda s: f"\033[1;94m{s}\033[0m"
error = lambda s: f"\033[1;31m{s}\033[0m"
warn = lambda s: f"\033[1;33m{s}\033[0m"
quote = lambda s: f"\033[37m{s}\033[0m"

command_parser = argparse.ArgumentParser(
    prog="byrdocs",
    description=
        "可用的命令:\n" +
        "  upload <file>    上传文件，默认命令即为上传\n" +
        "  login            请求登录到 BYR Docs 并在本地保存登录凭证\n" +
        "  logout           删除本地保存的登录凭证，退出 BYR Docs 的登录\n"+
        "  init             交互式地生成文件元信息 yaml 文件\n"+
        "  validate         (施工中) 判断 yaml 元信息文件的合法性\n",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=
        "示例命令:\n" +
        f"{' $ byrdocs login'}\n" +
        f"{' $ byrdocs /home/exam_paper.pdf'}\n" +
        f"{' $ byrdocs logout'}\n"
        f"{' $ byrdocs init'}\n"
        )
# command_parser.add_argument('--help', '-h', action='help', help='Show this help message and exit')
command_parser.add_argument("command", nargs='?', help="执行的操作")
command_parser.add_argument("file", nargs='?', help="上传的文件路径").completer = argcomplete.completers.FilesCompleter()
command_parser.add_argument("--token", help="手动登录时传入的 token ")

baseURL = "https://byrdocs.org"

def interrupt_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            cancel()
            sys.exit(0)
    return wrapper

def retry_handler(error_description: str, max_retries: int=10, interval: int=0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # print(f"{error_description}: {e}")
                    if i < max_retries - 1:
                        # print(f"Retrying... ({i+1}/{max_retries})")
                        sleep(interval)
                    else:
                        print(error(f"{error_description} 在 {max_retries} 次重试后失败: {e}"))
                        sys.exit(1)
        return wrapper
    return decorator

def get_file_type(file) -> str:
    # https://en.wikipedia.org/wiki/List_of_file_signatures
    # use magic number to check file type
    with open(file, "rb") as f:
        magic_number = f.read(4)
        if magic_number == b"%PDF":
            return "pdf"
        elif magic_number == b"PK\x03\x04":
            return "zip"
        else:
            return "unsupported"

@retry_handler("请求登录时出现错误。", interval=1)    # decorator
def request_login_data() -> dict[str, str]:
    return requests.post(f"{baseURL}/api/auth/login").json()

@retry_handler("获取登录状态时出现错误")
def request_token(data: dict[str, str]) -> str:
    try:
        r = requests.get(data["tokenURL"], timeout=120)
        r.raise_for_status()
        r = r.json()
    except requests.exceptions.Timeout:
        raise Exception("获取登录凭证时超时。")  # raise to retry_handler
    except requests.exceptions.RequestException as e:
        raise Exception(f"请求登录凭证时出现网络错误: {e}")
    if not r.get("success", False):
        raise Exception(f"未知错误: {r}")
    return r["token"]

@interrupt_handler
def upload_progress(chunk, progress_bar: tqdm):
    progress_bar.update(chunk)
    
@interrupt_handler
def _ask_for_init(file_name: str=None) -> str:
    ask_for_init(file_name)

@interrupt_handler
def main():
    argcomplete.autocomplete(command_parser)
    args = command_parser.parse_args()

    if args.command not in ['login', 'logout', 'upload', 'init', 'validate']:
        args.file = args.command
        args.command = 'upload'

    if args.file and not args.command:
        args.command = 'upload'
    
    if args.command == 'init':
        _ask_for_init()
        exit(0)
        
    if args.command == 'validate':
        print(warn("该功能正在施工中..."))
        exit(0)


    config_dir = pathlib.Path.home() / ".config" / "byrdocs" 
    if not config_dir.exists():
        config_dir.mkdir(parents=True)

    token_path = config_dir / "token"

    def login(token=None):
        if token:
            with token_path.open("w") as f:
                f.write(token)
            print(info(f"登录凭证已保存到 {token_path.absolute()} 。"))
            return

        if token_path.exists():
            print(warn("已登录，输入 byrdocs logout 命令以退出登录。"))
            exit(1)

        print(info("尚未登录，正在请求登录..."))
        # token = request_token()
        login_data = request_login_data()
        print(info("请在浏览器中访问以下链接进行登录:"))
        print("\t" + login_data["loginURL"])
        token = request_token(login_data)
        
        with token_path.open("w") as f:
            f.write(token)
        print(info(f"登录成功，凭证已保存到 {token_path.absolute()} 。"))

    if args.command == 'login':
        login(args.token)
        exit(0)

    if not token_path.exists():
        login()

    if args.command == 'logout':
        os.remove(token_path)
        print(info(f"已移除 {token_path.absolute()} 处的登录凭证。"))
        exit(0)

    with token_path.open("r") as f:
        token = f.read().strip()

    if args.command == 'upload' or args.file:
        if not args.file:
            print(error("错误：请指定一个需要上传的文件。"))
            print(warn("输入 byrdocs -h 命令以获取帮助。"))
            exit(1)

        file = args.file

        try:
            with open(file, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()
        except FileNotFoundError:
            print(error(f"未找到文件: {file}"))
            exit(1)
        except Exception as e:
            print(error(f"读取文件时出现错误: {e}"))
            exit(1)

        if (file_type := get_file_type(file)) == "unsupported":
            print(error(f"错误：暂不支持文件格式 `{file_type}`，当前仅支持上传 PDF 或 ZIP 文件。"))
            exit(1)

        payload = json.dumps(
            {
                "key": (new_filename := f"{md5}.{file_type}"),
            }
        )
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        try:
            response = requests.request(
                "POST", f"{baseURL}/api/s3/upload", headers=headers, data=payload
            )
        except Exception as e:
            print(error(f"上传文件时出现错误: {e}"))
            exit(1)

        upload_response_data = response.json()

        if not upload_response_data["success"]:
            try:
                print(error(f"文件存储服务器出现错误: {response.json()['error']}"))    # TODO: 优化失败处理
            except:
                print(error(f"未知错误: {response.text}"))
            exit(1)

        # print(f"{new_filename} status: `Pending`")
        # input("Press Enter to continue uploading...")

        temporary_credentials = {
            "AccessKeyId": upload_response_data["credentials"]["access_key_id"],
            "SecretAccessKey": upload_response_data["credentials"]["secret_access_key"],
            "SessionToken": upload_response_data["credentials"]["session_token"],
        }
        # print(temporary_credentials)

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=temporary_credentials["AccessKeyId"],
            aws_secret_access_key=temporary_credentials["SecretAccessKey"],
            aws_session_token=temporary_credentials["SessionToken"],
            region_name="us-east-1",
            endpoint_url="https://s3.byrdocs.org",
        )

        bucket_name = upload_response_data["bucket"]
        file_name = file
        object_name = upload_response_data["key"]

        # Initialize progress bar
        file_size = os.path.getsize(file)
        progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc="Uploading")

        # https://blog.csdn.net/weixin_44123540/article/details/118492260
        GB = 1024**3
        upload_config = boto3.s3.transfer.TransferConfig(multipart_threshold=2*GB)

        try:
            s3_client.upload_file(
                file_name,
                bucket_name,
                object_name,
                Callback=(lambda chunk: upload_progress(chunk, progress_bar)),
                ExtraArgs={
                    "Tagging": "&".join(
                        [f"{key}={value}" for key, value in upload_response_data["tags"].items()]
                    )
                },
                Config=upload_config
            )
            progress_bar.close()
            print(info("文件上传成功！"))
            print(f"\t文件地址: {baseURL}/files/{new_filename}")
            
            try:
                if ask_for_confirmation("是否直接对该文件进行元信息录入？"):
                    _ask_for_init(new_filename)
                else:
                    cancel()
            except KeyboardInterrupt:
                cancel()
            # print(f"{new_filename} status: `Uploaded`")
        except (NoCredentialsError, PartialCredentialsError) as e:
            progress_bar.close()
            print(error(f"证书错误: {e}"))
        except Exception as e:
            progress_bar.close()
            print(error(f"上传文件时出现错误: {e}"))
            print(warn("请检查你的文件标签、登录状态及网络连接，再尝试重新上传，这或许能解决问题。"))
