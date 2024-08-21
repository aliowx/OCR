from sqlalchemy import Boolean, Integer, String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base

from app.acl.role import UserRoles


class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(50), nullable=True)
    username: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean(), default=True, nullable=True
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean(), default=False, nullable=True
    )

    # after migration add to file beacuse not found role
    # def upgrade() -> None:
    #   op.execute(
    #    "CREATE TYPE userroles AS ENUM ('ADMINISTRATOR', 'PARKING_MANAGER', 'TECHNICAL_SUPPORT', 'OPERATIONAL_STAFF', 'REPORTING_ANALYSIS', 'SECURITY_STAFF');")
    # def downgrade():
    #   op.execute("DROP TYPE userroles;")
    role = mapped_column(
        Enum(UserRoles, name="userroles", create_type=True),
        nullable=True,
    )
