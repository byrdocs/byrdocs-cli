import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import requests
import json
import hashlib
import pathlib
import argparse
import sys
import os
import argcomplete
from tqdm import tqdm

command_parser = argparse.ArgumentParser(
    prog="byrdocs",
    description=
        "Commands:\n" +
        "  upload <file>    Upload a file. If no command is specified, it defaults to upload.\n" +
        "  login            Authenticate with BYR Docs and obtain a token.\n" +
        "  logout           Remove the locally stored authentication token.\n",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=
        "Examples:\n" +
        f"{' $ byrdocs login'}\n" +
        f"{' $ byrdocs /home/exam_paper.pdf'}\n" +
        f"{' $ byrdocs logout'}\n"
        )
# command_parser.add_argument('--help', '-h', action='help', help='Show this help message and exit')
command_parser.add_argument("command", nargs='?', help="Command to execute")
command_parser.add_argument("file", nargs='?', help="Path to the file to upload").completer = argcomplete.completers.FilesCompleter()
command_parser.add_argument("--token", help="Token for login command")

def interrupt_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)
    return wrapper

def get_file_type(file) -> bool:
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

@interrupt_handler
def upload_progress(chunk, progress_bar: tqdm):
    progress_bar.update(chunk)

@interrupt_handler
def main():
    argcomplete.autocomplete(command_parser)
    args = command_parser.parse_args()

    if args.command not in ['login', 'logout', 'upload']:
        args.file = args.command
        args.command = 'upload'

    if args.file and not args.command:
        args.command = 'upload'

    baseURL = "https://byrdocs.org"

    config_dir = pathlib.Path.home() / ".config" / "byrdocs" 
    if not config_dir.exists():
        config_dir.mkdir(parents=True)

    token_path = config_dir / "token"

    def login(token=None):
        if token:
            with token_path.open("w") as f:
                f.write(token)
            print(f"Token saved to {token_path.absolute()}")
            return

        if token_path.exists():
            print("Token already exists, you can use `byrdocs logout` to remove it.")
            exit(1)

        print("No token found locally, requesting a new one...")
        data = requests.post(f"{baseURL}/api/auth/login").json()
        print("Please visit the following URL to authorize the application:")
        print("\t" + data["loginURL"])
        try:
            r = requests.get(data["tokenURL"], timeout=120)
            r.raise_for_status()
            r = r.json()
        except requests.exceptions.Timeout:
            print("Error: Request timed out while trying to get the token.")
            exit(1)
        except requests.exceptions.RequestException as e:
            print(f"Error: An error occurred while trying to get the token: {e}")
            exit(1)
        if not r.get("success", False):
            print(r)
            exit(1)
        token = r["token"]
        with token_path.open("w") as f:
            f.write(token)
        print(f"Login successful, token saved to {token_path.absolute()}")

    if args.command == 'login':
        login(args.token)
        exit(0)

    if not token_path.exists():
        login()

    if args.command == 'logout':
        os.remove(token_path)
        print(f"Token removed from {token_path.absolute()}.")
        exit(0)

    with token_path.open("r") as f:
        token = f.read().strip()

    if args.command == 'upload' or args.file:
        if not args.file:
            print("Error: No file specified for upload.")
            print("Use `byrdocs -h` for help")
            exit(1)

        file = args.file

        with open(file, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()

        if (file_type := get_file_type(file)) == "unsupported":
            print(f"Error: Unsupported file type of {file}, only PDF and ZIP are supported.")
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
            print(f"Error while trying to upload file: {e}")
            exit(1)

        upload_response_data = response.json()

        if not upload_response_data["success"]:
            try:
                print(f"Error from server: {response.json()['error']}")    # TODO: 优化失败处理
            except:
                print(f"Unknown error: {response.text}")
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
            print("File uploaded successfully")
            print(f"\tFile URL: {baseURL}/files/{new_filename}")
            # print(f"{new_filename} status: `Uploaded`")
        except (NoCredentialsError, PartialCredentialsError) as e:
            progress_bar.close()
            print(f"Credential error: {e}")
        except Exception as e:
            progress_bar.close()
            print(f"Error uploading file: {e}. \nCheck your file tag, login status and Internet connection, then try again.")
