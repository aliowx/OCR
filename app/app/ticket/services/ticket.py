from sqlalchemy.ext.asyncio import AsyncSession
from app.ticket.schemas.ticket import ParamsTicket
from datetime import timedelta
from typing import List, Optional
from fastapi import Query
from app.ticket.repo import ticket_repo


async def get_record_bill(db: AsyncSession, *, params: ParamsTicket):

    tickets, total_count = await ticket_repo.get_multi_by_filter(
        db, params=params
    )
    ## ---> tickets
    #                   --> ticket[0] ==> ticket
    #                   --> ticket[1] ==> record
    #                   --> ticket[2] ==> bill
    resualt_tickets = []
    for ticket in tickets:
        ticket[0].record = ticket[1]
        ticket[0].bill = ticket[2]
        resualt_tickets.append(ticket[0])
    return resualt_tickets, total_count
