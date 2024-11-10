import logging
from io import BytesIO
from typing import BinaryIO
from app.schemas.image import ImageSaveAs
import urllib3
from app.core.config import settings
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class MinIO:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_URL,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            http_client=urllib3.PoolManager(cert_reqs="CERT_NONE"),
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.check_buckt_exist(self.bucket_name)

    def check_buckt_exist(self, bucket_name: str):
        bucket_exist = self.client.bucket_exists(bucket_name)
        if not bucket_exist:
            self.client.make_bucket(bucket_name)
        return bucket_name

    def upload_file(
        self, content: BytesIO, name: str, size: int, metadata: dict
    ) -> str:
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                data=content,
                object_name=name,
                length=size,
                metadata=metadata,
            )
            return f"{self.bucket_name}/{name}"

        except S3Error as e:
            logger.error("MinIO error in upload file:", e)
            raise e

    def download_file(self, bucket_name: str, file_name: str) -> BinaryIO:
        try:
            response = self.client.get_object(bucket_name, file_name)
            file = BytesIO()
            for data in response.stream(1024):  # Read in 1KB chunks
                file.write(data)

            response.close()
            response.release_conn()

            file.seek(0)
            return file

        except S3Error as e:
            logger.error("MinIO error in download file:", e)
            raise e


def get_client(name: ImageSaveAs):
    if name.minio:
        return MinIO()
