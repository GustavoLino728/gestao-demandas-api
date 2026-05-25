import uuid

from app.core.exceptions import ForbiddenError, NotFoundError
from app.domain.users.models import UserRole
from app.domain.boards.models import Board
from app.domain.boards.repository import BoardRepository
from app.domain.boards.schemas import BoardCreate, BoardUpdate
from app.domain.lists.models import List
from app.domain.lists.repository import ListRepository


DEFAULT_LISTS = [
    ("Backlog", 0),
    ("Em andamento", 1),
    ("Finalizado", 2),
]


class BoardService:
    def __init__(self, repo: BoardRepository, list_repo: ListRepository):
        self.repo = repo
        self.list_repo = list_repo

    async def create_board(self, data: BoardCreate, owner_id: uuid.UUID) -> Board:
        board = Board(**data.model_dump(), owner_id=owner_id)
        board = await self.repo.create(board)

        default_lists = [
            List(name=name, position=position, board_id=board.id)
            for name, position in DEFAULT_LISTS
        ]
        await self.list_repo.create_many(default_lists)

        return board

    async def list_boards(
        self,
        user_id: uuid.UUID,
        role: UserRole,
        scope: str = "mine",
    ) -> list[Board]:
        if scope == "all":
            if role not in (UserRole.GESTOR, UserRole.ADMIN):
                raise ForbiddenError("Apenas gestores e admins podem listar todos os boards.")
            return await self.repo.list_all()

        return await self.repo.list_visible_for_user(user_id)

    async def get_board(
        self,
        board_id: uuid.UUID,
        user_id: uuid.UUID,
        role: UserRole,
    ) -> Board:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise NotFoundError("Board não encontrado.")

        if role in (UserRole.GESTOR, UserRole.ADMIN):
            return board

        has_access = await self.repo.user_has_access(board_id, user_id)
        if not has_access:
            raise ForbiddenError("Você não tem acesso a este board.")

        return board

    async def update_board(
        self,
        board_id: uuid.UUID,
        data: BoardUpdate,
        user_id: uuid.UUID,
        role: UserRole,
    ) -> Board:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise NotFoundError("Board não encontrado.")

        if board.owner_id != user_id and role not in (UserRole.GESTOR, UserRole.ADMIN):
            raise ForbiddenError("Apenas o dono do board, gestores ou admins podem editar.")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(board, field, value)

        await self.repo.session.flush()
        await self.repo.session.refresh(board)
        return board

    async def delete_board(
        self,
        board_id: uuid.UUID,
        user_id: uuid.UUID,
        role: UserRole,
    ) -> None:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise NotFoundError("Board não encontrado.")

        if board.owner_id != user_id and role not in (UserRole.GESTOR, UserRole.ADMIN):
            raise ForbiddenError("Apenas o dono do board, gestores ou admins podem deletar.")

        await self.repo.delete(board)