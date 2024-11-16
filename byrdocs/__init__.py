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

command_parser = argparse.ArgumentParser(
    prog="byrdocs",
    description="BYR Docs file uploader CLI")
command_parser.add_argument('--version', '-v', action='version', version='version dev-1.0.0')
# command_parser.add_argument('--help', '-h', action='help', help='Show this help message and exit')
command_parser.add_argument("command", nargs='?', help="Command to execute")
command_parser.add_argument("file", nargs='?', help="Path to the file to upload").completer = argcomplete.completers.FilesCompleter()
command_parser.add_argument("--token", help="Token for login command")


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

        response = requests.request(
            "POST", f"{baseURL}/api/s3/upload", headers=headers, data=payload
        )

        upload_response_data = response.json()

        if not upload_response_data["success"]:
            try:
                print(f"Error from server: {response.json()['error']}")    # TODO: 优化失败处理
            except:
                print(f"Unknown error: {response.text}")
            exit(1)

        print(f"{new_filename} status: `Pending`")
        # input("Press Enter to continue uploading...")

        temporary_credentials = {
            "AccessKeyId": upload_response_data["credentials"]["access_key_id"],
            "SecretAccessKey": upload_response_data["credentials"]["secret_access_key"],
            "SessionToken": upload_response_data["credentials"]["session_token"],
        }
        print(temporary_credentials)

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
        

        try:
            s3_client.upload_file(
                file_name,
                bucket_name,
                object_name,
                ExtraArgs={
                    "Tagging": "&".join(
                        [f"{key}={value}" for key, value in upload_response_data["tags"].items()]
                    )
                },
            )
            print("File uploaded successfully")
            print(f"\tFile URL: {baseURL}/files/{new_filename}")
            print(f"{new_filename} status: `Uploaded`")
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"Credential error: {e}")
        except Exception as e:
            print(f"Error uploading file: {e}. \nCheck your file tag, logging status and Internet connection, then try again.")
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

command_parser = argparse.ArgumentParser(
    prog="byrdocs",
    description="BYR Docs file uploader CLI")
command_parser.add_argument('--version', '-v', action='version', version='version dev-1.0.0')
# command_parser.add_argument('--help', '-h', action='help', help='Show this help message and exit')
command_parser.add_argument("command", nargs='?', help="Command to execute")
command_parser.add_argument("file", nargs='?', help="Path to the file to upload").completer = argcomplete.completers.FilesCompleter()
command_parser.add_argument("--token", help="Token for login command")


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

if __name__ == "__main__":
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

        response = requests.request(
            "POST", f"{baseURL}/api/s3/upload", headers=headers, data=payload
        )

        upload_response_data = response.json()

        if not upload_response_data["success"]:
            try:
                print(f"Error from server: {response.json()['error']}")    # TODO: 优化失败处理
            except:
                print(f"Unknown error: {response.text}")
            exit(1)

        print(f"{new_filename} status: `Pending`")
        # input("Press Enter to continue uploading...")

        temporary_credentials = {
            "AccessKeyId": upload_response_data["credentials"]["access_key_id"],
            "SecretAccessKey": upload_response_data["credentials"]["secret_access_key"],
            "SessionToken": upload_response_data["credentials"]["session_token"],
        }
        print(temporary_credentials)

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
        

        try:
            s3_client.upload_file(
                file_name,
                bucket_name,
                object_name,
                ExtraArgs={
                    "Tagging": "&".join(
                        [f"{key}={value}" for key, value in upload_response_data["tags"].items()]
                    )
                },
            )
            print("File uploaded successfully")
            print(f"\tFile URL: {baseURL}/files/{new_filename}")
            print(f"{new_filename} status: `Uploaded`")
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"Credential error: {e}")
        except Exception as e:
            print(f"Error uploading file: {e}. \nCheck your file tag, logging status and Internet connection, then try again.")
