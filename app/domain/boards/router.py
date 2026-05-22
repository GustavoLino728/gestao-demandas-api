from typing import Literal
import uuid
from fastapi import APIRouter, Depends, Query, status

from app.dependencies import DBSession, CurrentUserContext
from app.domain.boards.member_repository import BoardMemberRepository
from app.domain.boards.member_service import BoardMemberService
from app.domain.boards.repository import BoardRepository
from app.domain.boards.service import BoardService
from app.domain.boards.schemas import (
    BoardCreate,
    BoardUpdate,
    BoardResponse,
    BoardMemberCreate,
    BoardMemberUpdate,
    BoardMemberResponse,
)

router = APIRouter(prefix="/boards", tags=["Boards"])


def get_board_service(db: DBSession) -> BoardService:
    return BoardService(BoardRepository(db))


def get_board_member_service(db: DBSession) -> BoardMemberService:
    return BoardMemberService(
        board_repository=BoardRepository(db),
        member_repository=BoardMemberRepository(db),
    )


@router.post("/", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    data: BoardCreate,
    ctx: CurrentUserContext,
    service: BoardService = Depends(get_board_service),
):
    user_id, _ = ctx
    return await service.create_board(data, user_id)


@router.get("/", response_model=list[BoardResponse])
async def list_boards(
    ctx: CurrentUserContext,
    scope: Literal["mine", "all"] = Query("mine"),
    service: BoardService = Depends(get_board_service),
):
    user_id, role = ctx
    return await service.list_boards(user_id=user_id, role=role, scope=scope)


@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: uuid.UUID,
    ctx: CurrentUserContext,
    service: BoardService = Depends(get_board_service),
):
    user_id, role = ctx
    return await service.get_board(board_id, user_id, role)


@router.patch("/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: uuid.UUID,
    data: BoardUpdate,
    ctx: CurrentUserContext,
    service: BoardService = Depends(get_board_service),
):
    user_id, role = ctx
    return await service.update_board(board_id, data, user_id, role)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: uuid.UUID,
    ctx: CurrentUserContext,
    service: BoardService = Depends(get_board_service),
):
    user_id, role = ctx
    await service.delete_board(board_id, user_id, role)


@router.post(
    "/{board_id}/members",
    response_model=BoardMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_board_member(
    board_id: uuid.UUID,
    data: BoardMemberCreate,
    ctx: CurrentUserContext,
    service: BoardMemberService = Depends(get_board_member_service),
):
    user_id, _ = ctx
    return await service.add_member(board_id, data, user_id)


@router.get(
    "/{board_id}/members",
    response_model=list[BoardMemberResponse],
)
async def list_board_members(
    board_id: uuid.UUID,
    ctx: CurrentUserContext,
    service: BoardMemberService = Depends(get_board_member_service),
):
    user_id, _ = ctx
    return await service.list_members(board_id, user_id)


@router.patch(
    "/{board_id}/members/{member_id}",
    response_model=BoardMemberResponse,
)
async def update_board_member(
    board_id: uuid.UUID,
    member_id: uuid.UUID,
    data: BoardMemberUpdate,
    ctx: CurrentUserContext,
    service: BoardMemberService = Depends(get_board_member_service),
):
    user_id, _ = ctx
    return await service.update_member(board_id, member_id, data, user_id)


@router.delete(
    "/{board_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_board_member(
    board_id: uuid.UUID,
    member_id: uuid.UUID,
    ctx: CurrentUserContext,
    service: BoardMemberService = Depends(get_board_member_service),
):
    user_id, _ = ctx
    await service.remove_member(board_id, member_id, user_id)