from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

import aiofiles
import boto3

from src.core.config import settings


class BackendStorge(ABC):

    @abstractmethod
    async def upload(self, filename: str, file_obj: BinaryIO) -> str:
        """返回文件的访问 URL 或 key"""

    @abstractmethod
    async def download(self, key: str) -> BinaryIO:
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        ...


class LocalStorage(BackendStorge):

    def __init__(self, base_dir: Path):
        self.base = base_dir
        self.base.mkdir(parents=True, exist_ok=True)

    async def download(self, key: str) -> BinaryIO:
        pass

    async def upload(self, filename: str, file_obj: BinaryIO) -> str:
        dest = self.base / filename
        async with aiofiles.open(dest, "wb") as f:
            while chunk := file_obj.read(1024 * 1024):
                await f.write(chunk)
        return str(dest)

    async def delete(self, key: str) -> bool:
        pass


class S3Storage(BackendStorge):
    def __init__(self, endpoint_url: str | None, access_key: str,
                 secret_key: str, bucket: str, region: str):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,  # Ceph 就填 RGW 地址
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    async def upload(self, filename: str, file_obj: BinaryIO) -> str:
        self.client.upload_fileobj(file_obj, self.bucket, filename)
        return f"{self.bucket}/{filename}"

    async def download(self, key: str) -> BinaryIO:
        pass

    async def delete(self, key: str) -> bool:
        pass


def get_storage() -> BackendStorge:
    settings: Settings = get_settings()
    match settings.backend_storge:
        case "local":
            return LocalStorage(settings.local_upload_dir)
        case "s3":
            return S3Storage(None, settings.s3_access_key,
                             settings.s3_secret_key,
                             settings.s3_bucket,
                             settings.s3_region)
        case "ceph":
            return S3Storage(settings.s3_endpoint_url,
                             settings.s3_access_key,
                             settings.s3_secret_key,
                             settings.s3_bucket,
                             settings.s3_region)
