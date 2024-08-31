from app.parking.schemas.camera import (
    Camera,
    CameraCreate,
    CameraUpdate,
    GetCamera,
)
from app.parking.schemas.spot import (
    GetSpot,
    SpotBase,
    SpotCreate,
    SpotCreateLineInDB,
    SpotInDBBase,
    SpotShowDetailByCamera,
    SpotUpdateStatus,
    ReverseCoordinatesRectangles
)
from app.parking.schemas.zone import *
from app.pricing.schemas import *
from app.users.schemas.token import Token, TokenPayload
from app.users.schemas.user import (
    User,
    UserBase,
    UserCreate,
    UserInDB,
    UserInDBBase,
    UserUpdate,
    ParamsUser,
)

from .image import (
    Image,
    ImageBase64InDB,
    ImageCreateBase64,
    ImageDetails,
    ImageUpdateBase64,
)
from .msg import Msg
from .event import (
    GetEvents,
    Event,
    EventCreate,
    EventUpdate,
    ParamsEvents,
    TypeCamera,
)
from .record import (
    GetRecords,
    Record,
    RecordCreate,
    RecordUpdate,
    ParamsRecord,
    StatusRecord,
)
