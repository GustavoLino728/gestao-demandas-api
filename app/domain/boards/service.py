import uuid
from app.core.exceptions import ForbiddenError, NotFoundError
from app.domain.users.models import UserRole
from app.domain.boards.models import Board
from app.domain.boards.repository import BoardRepository
from app.domain.boards.schemas import BoardCreate, BoardUpdate


class BoardService:
    def __init__(self, repo: BoardRepository):
        self.repo = repo

    async def create_board(self, data: BoardCreate, owner_id: uuid.UUID) -> Board:
        board = Board(**data.model_dump(), owner_id=owner_id)
        return await self.repo.create(board)

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
        await self.repo.session.flush()