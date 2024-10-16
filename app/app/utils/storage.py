import logging
from io import BytesIO
from typing import BinaryIO
from app.schemas.image import ImageSaveAs
import urllib3
from app.crud.crud_image import CRUDImage
from app.core.config import settings
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class MinIO:
    def init(self):
        # self.client = Minio(
        #     endpoint=settings.MINIO_SERVER_ADDRESS,
        #     access_key=settings.MINIO_ACCESS_KEY,
        #     secret_key=settings.MINIO_SECRET_KEY,
        #     http_client=urllib3.PoolManager(cert_reqs="CERT_NONE"),
        #     secure=True,
        # )
        self.client = Minio(
            endpoint="188.121.103.3:9000",
            access_key="EVpeLRcQYOqxqtQ2qEiX",
            secret_key="YOeUTTOeQvRu4gJnUlf0artfW6hzVhJlqb8zL1Zf",
            http_client=urllib3.PoolManager(cert_reqs="CERT_NONE"),
            secure=False,
        )
        self.folder_path = settings.MINIO_FOLDER_ADDRESS
        self.bucket_name = settings.MINIO_BUCKET_NAME

    def upload_file(self, content: BytesIO, name: str, size: int) -> str:
        try:
            path = self.folder_path + name
            self.client.put_object(
                bucket_name=self.bucket_name,
                data=content,
                object_name=path,
                length=size,
            )
            return path

        except S3Error as e:
            logger.error("MinIO error in upload file:", e)
            raise e

    def download_file(self, file_name: str) -> BinaryIO:
        try:
            file_path = self.folder_path + file_name
            response = self.client.get_object(self.bucket_name, file_path)

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
    


# # file: UploadFile = File()  # API input
# # file.file.seek(0)

# minio_client = get_client()
# path = minio_client.upload_file(
#     content=io.BytesIO(file.file.read()), name=file_name, size=file.size
# )
