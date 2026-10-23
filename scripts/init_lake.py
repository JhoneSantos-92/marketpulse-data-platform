import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

def create_s3_bucket() -> None:
    endpoint = os.getenv("S3_ENDPOINT", "http://localhost:8333")
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    if not access_key or not secret_key:
        raise OSError("S3_ACCESS_KEY and S3_SECRET_KEY must be set in environment.")
    bucket = "marketpulse-lake"

    print(f"Conectando ao S3 ({endpoint}) para criar o bucket '{bucket}'...")
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
    )

    try:
        s3.create_bucket(Bucket=bucket)
        print(f"Bucket '{bucket}' criado com sucesso!")
    except ClientError as e:
        print(f"Nota ao criar bucket (pode já existir): {e}")

if __name__ == "__main__":
    create_s3_bucket()
