from typing import Awaitable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from .models.ticket import Ticket
from .schemas import TicketCreate, TicketUpdate, ParamsTicket
from app.models import Record, Bill
import re


class CRUDTicket(CRUDBase[Ticket, TicketCreate, TicketUpdate]):
    async def get_multi_by_filter(
        self, db: Session | AsyncSession, *, params: ParamsTicket
    ) -> list[Ticket] | Awaitable[list[Ticket]]:

        query = (
            select(Ticket, Record, Bill)
            .outerjoin(Record, Ticket.record_id == Record.id)
            .outerjoin(Bill, Ticket.bill_id == Bill.id)
        )

        filters = [Ticket.is_deleted == False]

        if params.input_plate is not None and bool(
            re.fullmatch(r"[0-9?]{8}", params.input_plate)
        ):
            filters.append(Record.plate.like(params.input_plate))

        if params.ticket_status is not None:
            filters.append(Ticket.status == params.ticket_status)

        if params.ticket_type is not None:
            filters.append(Ticket.type == params.ticket_type)

        total_count = await self.count_by_filter(db, filters=filters)

        order_by = Ticket.id.asc() if params.asc else Ticket.id.desc()

        if params.size is None:
            resualt = (
                await db.execute(query.filter(*filters).order_by(order_by))
            ).fetchall()
            return resualt, total_count
        resualt = (
            await db.execute(
                query.filter(*filters)
                .offset(params.skip)
                .limit(params.size)
                .order_by(order_by)
            )
        ).fetchall()
        return resualt, total_count


ticket_repo = CRUDTicket(Ticket)
