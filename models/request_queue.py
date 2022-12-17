from typing import Optional, List, Dict

from pydantic import BaseModel

from models import user, guild
from models.request import Request, RequestStatus
from util import Interaction


class QueuedRequest(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    request: "Request"
    inter: Interaction
    requestor: "user.User"
    original_author: Optional["user.User"]
    guild: "guild.Guild"


class RequestQueue:
    queue: List[str] = None
    id_lkp: Dict[str, QueuedRequest]
    populated: bool = False

    @classmethod
    async def populate(cls):
        cls.populated = True
        cls.queue = []
        cls.id_lkp = {}

    @classmethod
    async def add(
        cls,
        req: "Request",
        inter: Interaction,
        guild: "guild.Guild",
        requestor: "user.User",
        original_author: "user.User" = None,
    ):
        if not cls.populated:
            await cls.populate()
        req.status = RequestStatus.queued
        await req.save_changes()
        cls.queue.append(req.request_id)
        cls.id_lkp[req.request_id] = QueuedRequest(
            request=req,
            inter=inter,
            guild=guild,
            requestor=requestor,
            original_author=original_author,
        )

    @classmethod
    async def dequeue(cls) -> QueuedRequest | None:
        if not cls.populated:
            await cls.populate()
        if len(cls.queue) > 0:
            qr = cls.id_lkp.pop(cls.queue.pop(0))
            return qr

    @classmethod
    async def requeue(cls, qr: QueuedRequest):
        new = [qr.request.request_id]
        new.extend(cls.queue)
        cls.queue = new
        cls.id_lkp[qr.request.request_id] = qr

    @classmethod
    async def get_length(cls):
        if not cls.populated:
            await cls.populate()
        return len(cls.queue)

    @classmethod
    async def get_pos(cls, req_id: str):
        if not cls.populated:
            await cls.populate()
        if req_id not in cls.queue:
            return -1
        return cls.queue.index(req_id) + 1

    @classmethod
    async def resolve_queue_pos(cls, req_id: str):
        ret = str(await cls.get_pos(req_id=req_id))
        match ret:
            case "1":
                ret += "st"
            case "2":
                ret += "nd"
            case "3":
                ret += "rd"
            case "-1":
                ret = "Queue Error"
            case _:
                ret += "th"
        return ret
