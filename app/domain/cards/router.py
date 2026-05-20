import uuid
from fastapi import APIRouter, Depends, status
from app.dependencies import DBSession, CurrentUserID, GestorOrAbove, CurrentUserContext
from app.domain.cards.repository import CardRepository
from app.domain.cards.service import CardService
from app.domain.cards.schemas import (
    CardCreate, CardUpdate, CardMove,
    CardResponse, CardDetailResponse,
)

router = APIRouter(prefix="/cards", tags=["Cards"])


def get_card_service(db: DBSession) -> CardService:
    return CardService(CardRepository(db))


@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    data: CardCreate,
    current_user_id: CurrentUserID,
    service: CardService = Depends(get_card_service),
):
    return await service.create_card(data, current_user_id)


@router.get("/list/{list_id}", response_model=list[CardResponse])
async def list_cards_by_list(
    list_id: uuid.UUID,
    current_user_id: CurrentUserID,
    service: CardService = Depends(get_card_service),
):
    return await service.list_by_list(list_id)


@router.get("/me", response_model=list[CardResponse])
async def list_my_cards(
    current_user_id: CurrentUserID,
    service: CardService = Depends(get_card_service),
):
    """Retorna todos os cards atribuídos ao usuário autenticado."""
    return await service.list_by_assignee(current_user_id)


@router.get("/{card_id}", response_model=CardDetailResponse)
async def get_card(
    card_id: uuid.UUID,
    current_user_id: CurrentUserID,
    service: CardService = Depends(get_card_service),
):
    return await service.get_card(card_id)


@router.patch("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: uuid.UUID,
    data: CardUpdate,
    ctx: CurrentUserContext,
    service: CardService = Depends(get_card_service),
):
    user_id, role = ctx
    return await service.update_card(card_id, data, user_id, role)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: uuid.UUID,
    ctx: CurrentUserContext,
    service: CardService = Depends(get_card_service),
):
    user_id, role = ctx
    await service.delete_card(card_id, role)


@router.patch("/{card_id}/move", response_model=CardResponse)
async def move_card(
    card_id: uuid.UUID,
    data: CardMove,
    current_user_id: CurrentUserID,
    service: CardService = Depends(get_card_service),
):
    return await service.move_card(card_id, data, current_user_id)