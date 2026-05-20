import uuid
from app.domain.lists.models import List
from app.domain.lists.repository import ListRepository
from app.domain.lists.schemas import ListCreate, ListUpdate
from app.core.exceptions import NotFoundError

DEFAULT_LISTS = [
    ("Backlog", 0),
    ("Em Andamento", 1),
    ("Concluído", 2),
]


class ListService:
    def __init__(self, repo: ListRepository):
        self.repo = repo

    async def create_defaults_for_board(self, board_id: uuid.UUID) -> list[List]:
        lists = [
            List(name=name, position=pos, board_id=board_id)
            for name, pos in DEFAULT_LISTS
        ]
        return await self.repo.create_many(lists)

    async def create_list(self, board_id: uuid.UUID, data: ListCreate) -> List:
        lst = List(board_id=board_id, **data.model_dump())
        return await self.repo.create(lst)

    async def get_list(self, list_id: uuid.UUID) -> List:
        lst = await self.repo.get_by_id(list_id)
        if not lst:
            raise NotFoundError("Lista não encontrada.")
        return lst

    async def list_by_board(self, board_id: uuid.UUID) -> list[List]:
        return await self.repo.list_by_board(board_id)

    async def update_list(self, list_id: uuid.UUID, data: ListUpdate) -> List:
        lst = await self.repo.get_by_id(list_id)
        if not lst:
            raise NotFoundError("Lista não encontrada.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(lst, field, value)
        await self.repo.db.flush()
        return lst

    async def delete_list(self, list_id: uuid.UUID) -> None:
        lst = await self.repo.get_by_id(list_id)
        if not lst:
            raise NotFoundError("Lista não encontrada.")
        await self.repo.delete(lst)