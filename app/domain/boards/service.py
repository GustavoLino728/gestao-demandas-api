import uuid
from app.domain.boards.models import Board
from app.domain.boards.repository import BoardRepository
from app.domain.boards.schemas import BoardCreate, BoardUpdate
from app.core.exceptions import NotFoundError, ForbiddenError
from app.domain.users.models import UserRole
from app.domain.lists.service import ListService
from app.domain.lists.repository import ListRepository


class BoardService:
    def __init__(self, repo: BoardRepository):
        self.repo = repo

    async def create_board(self, data: BoardCreate, owner_id: uuid.UUID) -> Board:
        board = Board(**data.model_dump(), owner_id=owner_id)
        await self.repo.create(board)
        list_service = ListService(ListRepository(self.repo.db))
        await list_service.create_defaults_for_board(board.id)
        return board

    async def get_board(self, board_id: uuid.UUID) -> Board:
        board = await self.repo.get_by_id_with_lists(board_id)
        if not board:
            raise NotFoundError("Board não encontrado.")
        return board

    async def list_my_boards(self, owner_id: uuid.UUID) -> list[Board]:
        return await self.repo.list_by_owner(owner_id)

    async def update_board(self, board_id: uuid.UUID, data: BoardUpdate, user_id: uuid.UUID, role: UserRole) -> Board:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise NotFoundError("Board não encontrado.")
        if board.owner_id != user_id and role != UserRole.ADMIN:
            raise ForbiddenError("Apenas o dono pode editar este board.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(board, field, value)
        await self.repo.db.flush()
        return board

    async def delete_board(self, board_id: uuid.UUID, user_id: uuid.UUID, role: UserRole) -> None:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise NotFoundError("Board não encontrado.")
        if board.owner_id != user_id and role != UserRole.ADMIN:
            raise ForbiddenError("Apenas o dono pode excluir este board.")
        await self.repo.delete(board)