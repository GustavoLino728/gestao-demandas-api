import uuid
from fastapi import APIRouter, Depends, status
from app.dependencies import DBSession, CurrentUserContext
from app.domain.lists.repository import ListRepository
from app.domain.lists.service import ListService
from app.domain.lists.schemas import ListCreate, ListUpdate, ListResponse

router = APIRouter(prefix="/boards/{board_id}/lists", tags=["Lists"])


def get_list_service(db: DBSession) -> ListService:
    return ListService(ListRepository(db))


@router.post("/", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    board_id: uuid.UUID,
    data: ListCreate,
    ctx: CurrentUserContext,
    service: ListService = Depends(get_list_service),
):
    return await service.create_list(board_id, data)


@router.get("/", response_model=list[ListResponse])
async def list_lists(
    board_id: uuid.UUID,
    ctx: CurrentUserContext,
    service: ListService = Depends(get_list_service),
):
    return await service.list_by_board(board_id)


@router.patch("/{list_id}", response_model=ListResponse)
async def update_list(
    board_id: uuid.UUID,
    list_id: uuid.UUID,
    data: ListUpdate,
    ctx: CurrentUserContext,
    service: ListService = Depends(get_list_service),
):
    return await service.update_list(list_id, data)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    board_id: uuid.UUID,
    list_id: uuid.UUID,
    ctx: CurrentUserContext,
    service: ListService = Depends(get_list_service),
):
    await service.delete_list(list_id)