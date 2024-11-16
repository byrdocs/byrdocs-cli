import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import requests
import json
import hashlib
import pathlib
import sys
import os

baseURL = "https://byrdocs.org"

config_dir = pathlib.Path.home() / ".config" / "byrdocs"  # Optimized path
if not config_dir.exists():
    config_dir.mkdir(parents=True)

token_path = config_dir / "token"
if not token_path.exists():
    data = requests.post(f"{baseURL}/api/auth/login").json()
    print("Please visit the following URL to authorize the application:")
    print("\t" + data["loginURL"])
    r = requests.get(data["tokenURL"]).json()  # TODO: 优化请求与超时
    if not r.get("success", False):
        print(r)
        exit(1)
    token = r["token"]
    with token_path.open("w") as f:
        f.write(token)
    print(f"Login successful, token saved to {token_path.absolute()}")

with token_path.open("r") as f:
    token = f.read().strip()

file = sys.argv[1]  # TODO: 命令行参数优化

with open(file, "rb") as f:
    md5 = hashlib.md5(f.read()).hexdigest()

print(f"Uploading {md5}.pdf ...")

payload = json.dumps(
    {
        "key": md5 + ".pdf",    # TODO: 多类型文件上传支持
    }
)
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

response = requests.request(
    "POST", f"{baseURL}/api/s3/upload", headers=headers, data=payload
)

data = response.json()

if not data["success"]:
    print(response.text)    # TODO: 优化失败处理
    exit(1)

print(f"{md5}.pdf status: `Pending`")
input("Press Enter to continue uploading...")

temporary_credentials = {
    "AccessKeyId": data["credentials"]["access_key_id"],
    "SecretAccessKey": data["credentials"]["secret_access_key"],
    "SessionToken": data["credentials"]["session_token"],
}

s3_client = boto3.client(
    "s3",
    aws_access_key_id=temporary_credentials["AccessKeyId"],
    aws_secret_access_key=temporary_credentials["SecretAccessKey"],
    aws_session_token=temporary_credentials["SessionToken"],
    region_name="us-east-1",
    endpoint_url="https://s3.byrdocs.org",
)

bucket_name = "test"
file_name = file
object_name = data["key"]

try:
    s3_client.upload_file(
        file_name,
        bucket_name,
        object_name,
        ExtraArgs={
            "Tagging": "&".join(
                [f"{key}={value}" for key, value in data["tags"].items()]
            )
        },
    )
    print("File uploaded successfully")
    print(f"\tFile URL: {baseURL}/files/{md5}.pdf")
    print(f"{md5}.pdf status: `Uploaded`")
except (NoCredentialsError, PartialCredentialsError) as e:
    print(f"Credential error: {e}")
except Exception as e:
    print(f"Error uploading file: {e}")
