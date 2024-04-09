from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.image import Image
from app.schemas.image import (
    ImageBase64,
    ImageBase64InDB,
    ImageCreateBinary,
    ImageCreateBase64,
    ImageUpdateBinary,
    ImageUpdateBase64,
)
import base64
from typing import Any, Optional, List, Dict, Union, Awaitable
from fastapi.encoders import jsonable_encoder


class CRUDImage(
    CRUDBase[
        Image,
        ImageCreateBinary,
        ImageUpdateBinary,
    ]
):
    def create(
        self,
        db: Session | AsyncSession,
        *,
        obj_in: ImageCreateBinary | dict[str, Any]
    ) -> Image | Awaitable[Image]:
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
            db_obj = Image(**obj_in_data)  # type: ignore
            print(db_obj)
        else:
            db_obj = obj_in
        db.add(db_obj)
        return self._commit_refresh(db=db, db_obj=db_obj)

    def update(
        self,
        db: Session,
        *,
        db_obj: Image,
        obj_in: Union[ImageUpdateBinary, Dict[str, Any]]
    ) -> Image:
        img = db_obj.image
        del db_obj.image
        obj_data = jsonable_encoder(db_obj)
        obj_data["image"] = img
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        return super().update(db=db, db_obj=db_obj)

    def remove(self, db: Session, *, id: int) -> Image:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def get_image(self, db: Session, *, id: int) -> bytes:
        return db.query(self.model).get(id).image

    async def get_base64(
        self, db: AsyncSession, id: int
    ) -> Optional[ImageBase64InDB]:
        obj = await self.get(db=db, id=id)
        if obj is None:
            return None
        img = obj.image
        del obj.image
        obj = jsonable_encoder(obj)
        if obj:
            obj["image"] = base64.b64encode(img).decode()

        obj = ImageBase64InDB(**obj)
        return obj

    def get_multi_base64(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ImageBase64InDB]:
        images = (
            db.query(self.model)
            .order_by(self.model.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        images = [jsonable_encoder(image) for image in images]
        if images:
            for img in images:
                if "image" in img:
                    img["image"] = (
                        base64.b64encode(img["image"]).decode()
                        if img
                        else None
                    )

        return [ImageBase64InDB(**obj) for obj in images]

    async def create_base64(
        self, db: AsyncSession, *, obj_in: ImageCreateBase64
    ) -> ImageBase64InDB:
        obj_in = jsonable_encoder(obj_in)
        if "image" in obj_in:
            obj_in["image"] = base64.b64decode(obj_in["image"].encode())
            print('obj_in["image"]:', type(obj_in["image"]))

        db_obj = await self.create(db=db, obj_in=obj_in)
        db_obj = ImageBase64InDB(
            image=(
                base64.b64encode(db_obj.image).decode()
                if db_obj.image
                else None
            ),
            created=db_obj.created,
            modified=db_obj.modified,
            image_metadata=db_obj.image_metadata,
            id=db_obj.id,
        )

        return db_obj

    async def update_base64(
        self,
        db: AsyncSession,
        *,
        db_obj: ImageUpdateBase64,
        obj_in: Union[ImageUpdateBase64, Dict[str, Any]]
    ) -> ImageBase64InDB:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        update_data = jsonable_encoder(update_data)
        if "image" in update_data:
            update_data["image"] = base64.b64decode(
                update_data["image"].encode()
            )

        db_obj = jsonable_encoder(db_obj)
        if "image" in db_obj:
            db_obj["image"] = base64.b64decode(db_obj["image"].encode())

        db_obj = ImageUpdateBinary(**db_obj)

        db_obj = await self.update(db=db, db_obj=db_obj, obj_in=update_data)

        img = db_obj.image
        del db_obj.image
        db_obj = jsonable_encoder(db_obj)
        if db_obj:
            db_obj["image"] = base64.b64encode(img).decode()
        db_obj = ImageBase64InDB(**db_obj)
        return db_obj

    def remove_base64(self, db: Session, *, id: int) -> ImageBase64InDB:
        obj = self.remove(db=db, id=id)
        img = obj.image
        del obj.image
        obj = jsonable_encoder(obj)
        if obj:
            obj["image"] = base64.b64encode(img).decode()

        obj = ImageBase64InDB(**obj)
        return obj


image = CRUDImage(Image)
