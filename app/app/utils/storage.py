import asyncio
import logging
from io import BytesIO
from typing import BinaryIO
from app.schemas.image import ImageSaveAs
from app.core.config import settings
from minio import Minio
from minio.error import S3Error
import urllib3

logger = logging.getLogger(__name__)

class MinIOAsync:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_URL,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            http_client=urllib3.PoolManager(cert_reqs="CERT_NONE"),
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME



    async def check_buckt_exist(self, bucket_name: str):
        """
        Checks if the bucket exists and creates it if not.
        """
        return  await asyncio.to_thread(self._sync_check_bucket_exist, bucket_name)

    def _sync_check_bucket_exist(self, bucket_name: str):
        bucket_exist = self.client.bucket_exists(bucket_name)
        if not bucket_exist:
            self.client.make_bucket(bucket_name)
        return bucket_name

    async def upload_files(
        self, content: BytesIO, name: str, size: int, metadata: dict
    ) -> str:
        """
        Upload a file to the MinIO bucket asynchronously.
        """
        try:

            return await asyncio.to_thread(self._sync_upload_file, content, name, size, metadata)
        
        except S3Error as e:
            logger.error("MinIO error in upload file:", e)
            raise e

    def _sync_upload_file(self, content: BytesIO, name: str, size: int, metadata: dict):
        """
        Synchronous upload operation, offloaded for async usage.
        """
        self.client.put_object(
            bucket_name=self.bucket_name,
            data=content,
            object_name=name,
            length=size,
            metadata=metadata,
        )  
        return f"{self.bucket_name}/{name}"
    


    async def download_file(self, bucket_name: str, file_name: str) -> BinaryIO:
        try:
            return await asyncio.to_thread(self._sync_download_file, bucket_name, file_name)
        except S3Error as e:
            logger.error("MinIO error in download file:", e)
            raise e
        
    def _sync_download_file(self, bucket_name: str, file_name: str):
        """
        Synchronous download operation, offloaded for async usage.
        """
        response = self.client.get_object(bucket_name, file_name)
        file = BytesIO()
        for data in response.stream(1024):
            file.write(data)
        response.close()
        response.release_conn()
        file.seek(0)
        return file

    async def generate_presigned_url(self, file_name: str, expiry: int = 3600) -> str:
        """
        Generate a presigned URL for downloading a file asynchronously.
        """
        return await asyncio.to_thread( self.client.presigned_get_object, self.bucket_name, file_name, expiry
        )
    

async def get_client(name: ImageSaveAs):
    """
    Returns an asynchronous MinIO client based on ImageSaveAs input.
    """
    if name.minio:
        return MinIOAsync()