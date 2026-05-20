import uuid
from fastapi import APIRouter, Depends, status
from app.dependencies import DBSession, CurrentUserContext
from app.domain.boards.repository import BoardRepository
from app.domain.boards.service import BoardService
from app.domain.boards.schemas import BoardCreate, BoardUpdate, BoardResponse, BoardResponse

router = APIRouter(prefix="/boards", tags=["Boards"])

def get_board_service(db: DBSession) -> BoardService:
    return BoardService(BoardRepository(db))

@router.post("/", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    data: BoardCreate,
    ctx: CurrentUserContext,
    service: BoardService = Depends(get_board_service),
):
    user_id, _ = ctx
    return await service.create_board(data, user_id)

@router.get("/me", response_model=list[BoardResponse])
async def list_my_boards(
    ctx: CurrentUserContext,
    service: BoardService = Depends(get_board_service),
):
    user_id, _ = ctx
    return await service.list_my_boards(user_id)

@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: uuid.UUID,
    ctx: CurrentUserContext,
    service: BoardService = Depends(get_board_service),
):
    return await service.get_board(board_id)

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