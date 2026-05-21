import uuid

from app.core.exceptions import ForbiddenError, NotFoundError, ConflictError
from app.domain.boards.models import BoardMember, BoardRole
from app.domain.boards.repository import BoardRepository
from app.domain.boards.member_repository import BoardMemberRepository
from app.domain.boards.schemas import BoardMemberCreate, BoardMemberUpdate


class BoardMemberService:
    def __init__(
        self,
        board_repository: BoardRepository,
        member_repository: BoardMemberRepository,
    ):
        self.board_repo = board_repository
        self.member_repo = member_repository

    async def _get_board_or_raise(self, board_id: uuid.UUID):
        board = await self.board_repo.get_by_id(board_id)
        if not board:
            raise NotFoundError("Board não encontrado.")
        return board

    async def _check_manage_permission(
        self,
        board_id: uuid.UUID,
        acting_user_id: uuid.UUID,
    ):
        board = await self._get_board_or_raise(board_id)

        if board.owner_id == acting_user_id:
            return board

        acting_member = await self.member_repo.get_by_board_and_user(
            board_id, acting_user_id
        )
        if not acting_member or acting_member.role != BoardRole.ADMIN:
            raise ForbiddenError(
                "Apenas o dono do board ou membros admin podem gerenciar participantes."
            )

        return board

    async def add_member(
        self,
        board_id: uuid.UUID,
        data: BoardMemberCreate,
        acting_user_id: uuid.UUID,
    ) -> BoardMember:
        board = await self._check_manage_permission(board_id, acting_user_id)

        if data.user_id == board.owner_id:
            raise ConflictError("O dono do board já participa do board.")

        existing = await self.member_repo.get_by_board_and_user(board_id, data.user_id)
        if existing:
            raise ConflictError("Usuário já é membro deste board.")

        member = BoardMember(
            board_id=board_id,
            user_id=data.user_id,
            role=data.role,
        )
        return await self.member_repo.create(member)

    async def list_members(
        self,
        board_id: uuid.UUID,
        acting_user_id: uuid.UUID,
    ) -> list[BoardMember]:
        board = await self._get_board_or_raise(board_id)

        if board.owner_id != acting_user_id:
            membership = await self.member_repo.get_by_board_and_user(
                board_id, acting_user_id
            )
            if not membership:
                raise ForbiddenError("Você não tem acesso a este board.")

        return await self.member_repo.list_by_board(board_id)

    async def update_member(
        self,
        board_id: uuid.UUID,
        member_id: uuid.UUID,
        data: BoardMemberUpdate,
        acting_user_id: uuid.UUID,
    ) -> BoardMember:
        board = await self._check_manage_permission(board_id, acting_user_id)

        member = await self.member_repo.get_by_id(member_id)
        if not member or member.board_id != board_id:
            raise NotFoundError("Membro não encontrado neste board.")

        if member.user_id == board.owner_id:
            raise ForbiddenError("Não é possível alterar o papel do dono do board.")

        member.role = data.role
        await self.member_repo.session.flush()
        await self.member_repo.session.refresh(member)
        return member

    async def remove_member(
        self,
        board_id: uuid.UUID,
        member_id: uuid.UUID,
        acting_user_id: uuid.UUID,
    ) -> None:
        board = await self._check_manage_permission(board_id, acting_user_id)

        member = await self.member_repo.get_by_id(member_id)
        if not member or member.board_id != board_id:
            raise NotFoundError("Membro não encontrado neste board.")

        if member.user_id == board.owner_id:
            raise ForbiddenError("Não é possível remover o dono do board.")

        await self.member_repo.delete(member)
        await self.member_repo.session.flush()