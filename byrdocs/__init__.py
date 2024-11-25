import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import requests
import json
import hashlib
import pathlib
import argparse
import sys
import os
from time import sleep, time
import argcomplete
from tqdm import tqdm
from byrdocs.yaml_init import ask_for_init, ask_for_confirmation, cancel    # TODO: 进行模块拆分便于维护，而不是全从这里导入进来
from byrdocs.history_manager import UploadHistory
from byrdocs.main_menu import main_menu

info = lambda s: f"\033[1;94m{s}\033[0m"
error = lambda s: f"\033[1;31m{s}\033[0m"
warn = lambda s: f"\033[1;33m{s}\033[0m"
quote = lambda s: f"\033[37m{s}\033[0m"

command_parser = argparse.ArgumentParser(
    prog="byrdocs",
    description=
        "命令：\n" +
        "  upload <文件路径>    上传文件 [默认命令]\n" +
        "  login               登录到 BYR Docs\n" +
        "  logout              退出登录\n"+
        "  init                交互式生成文件元信息文件\n"+
        "  validate            (待实现) 验证元信息文件的合法性\n",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=
        "示例：\n" +
        "  $ byrdocs login\n" +
        "  $ byrdocs /home/exam_paper.pdf\n" +
        "  $ byrdocs logout\n" +
        "  $ byrdocs init\n"
    )
# command_parser.add_argument('--help', '-h', action='help', help='Show this help message and exit')
command_parser.add_argument("command", nargs='?', help="要执行的命令")
command_parser.add_argument("file", nargs='?', help="要上传的文件路径").completer = argcomplete.completers.FilesCompleter()
command_parser.add_argument("--token", help="指定登录时使用的 token")

baseURL = "https://byrdocs.org"

def interrupt_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            cancel()
            sys.exit(0)
    return wrapper

def retry_handler(error_description: str, max_retries: int=10, interval=0.1):
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
                        print(error(f"{error_description}。 在 {max_retries} 次重试后失败: {e}"))
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

@retry_handler("登录请求错误", interval=1)    # decorator
def request_login_data() -> dict[str, str]:
    return requests.post(f"{baseURL}/api/auth/login").json()

@interrupt_handler
@retry_handler("登录错误")
def request_token(data: dict[str, str]) -> str:
    try:
        r = requests.get(data["tokenURL"], timeout=120)
        r.raise_for_status()
        r = r.json()
    except requests.exceptions.Timeout:
        raise Exception("登录超时")  # raise to retry_handler
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络错误: {e}")
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
    
    if not args.command and not args.file:
        menu_command = main_menu()  
        if menu_command.command == 'upload_2':
            args.command = 'upload'
            args.file = menu_command.file
        else:
            args.command = menu_command.command
        
    if args.command not in ['login', 'logout', 'upload', 'init', 'validate']:
        args.file = args.command
        args.command = 'upload'

    if args.file and not args.command:
        args.command = 'upload'
    
    if args.command == 'init':
        _ask_for_init()
        exit(0)
        
    if args.command == 'validate':
        print(warn("该功能尚未实现"))
        exit(0)


    config_dir = pathlib.Path.home() / ".config" / "byrdocs" 
    if not config_dir.exists():
        config_dir.mkdir(parents=True)

    token_path = config_dir / "token"

    def login(token=None):
        if token:
            with token_path.open("w") as f:
                f.write(token)
            print(info(f"登录凭证已保存到 {token_path.absolute()}"))
            return

        if token_path.exists():
            print(warn("已登录，byrdocs logout 以退出登录"))
            exit(1)

        print(info("未检测到登录信息，正在请求登录..."))
        # token = request_token()
        login_data = request_login_data()
        print(info("请在浏览器中访问以下链接进行登录:"))
        print("\t" + login_data["loginURL"])
        token = request_token(login_data)
        
        with token_path.open("w") as f:
            f.write(token)
        print(info(f"登录成功，凭证已保存到 {token_path.absolute()}"))

    if args.command == 'login':
        login(args.token)
        exit(0)

    if not token_path.exists():
        login()

    if args.command == 'logout':
        if ask_for_confirmation("确认登出？"):
            os.remove(token_path)
            print(info(f"登出成功"))
        exit(0)

    with token_path.open("r") as f:
        token = f.read().strip()

    if args.command == 'upload' or args.file:
        if not args.file:
            print(error("错误：未指定要上传的文件"))
            print(warn("使用 byrdocs -h 获取帮助"))
            exit(1)

        file = args.file

        try:
            with open(file, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()
        except FileNotFoundError:
            print(error(f"未找到文件: {file}"))
            exit(1)
        except Exception as e:
            print(error(f"读取文件出错: {e}"))
            exit(1)

        if (file_type := get_file_type(file)) == "unsupported":
            print(error(f"错误：不支持的文件格式 `{str(file).split('.')[-1]}` 或文件损坏，仅支持上传 PDF 或 ZIP 文件。"))
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
                print(error(f"服务器错误: {response.json()['error']}"))    # TODO: 优化失败处理
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
            UploadHistory().add(file, md5, time())
            print(info("文件上传成功！"))
            print(f"\t文件地址: {baseURL}/files/{new_filename}")
            
            try:
                if ask_for_confirmation("是否立即为该文件录入元信息？"):
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
            print(error(f"上传文件出错: {e}"))
            print(warn("请稍后重试。"))
