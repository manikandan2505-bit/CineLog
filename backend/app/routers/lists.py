
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session,joinedload

from app.database import get_db
from app.models import User, List,Movie, TVShow, ListItem
from app.security import get_current_user

router = APIRouter(prefix="/lists", tags=["Lists"])


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    is_public: bool = True


class ListResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: str | None
    is_public: bool

    class Config:
        from_attributes = True


class ListItemCreate(BaseModel):
    movie_id: int | None = None
    tv_show_id: int | None = None
    position: int | None = Field(default=None, ge=1)


class ListUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    is_public: bool | None = None


@router.post("/", response_model=ListResponse, status_code=201)
def create_list(
    list_data: ListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = list_data.name.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="List name cannot be empty.",
        )

    new_list = List(
        user_id=current_user.id,
        name=name,
        description=list_data.description,
        is_public=list_data.is_public,
    )

    db.add(new_list)
    db.commit()
    db.refresh(new_list)

    return new_list


@router.get("/mine", response_model=list[ListResponse])
def get_my_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(List)
        .filter(List.user_id == current_user.id)
        .order_by(List.created_at.desc(), List.id.desc())
        .all()
    )


@router.post("/{list_id}/items", status_code=201)
def add_list_item(
    list_id: int,
    item_data: ListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (item_data.movie_id is None) == (item_data.tv_show_id is None):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of movie_id or tv_show_id.",
        )

    user_list = (
        db.query(List)
        .filter(
            List.id == list_id,
            List.user_id == current_user.id,
        )
        .first()
    )

    if not user_list:
        raise HTTPException(
            status_code=404,
            detail="List not found.",
        )

    if item_data.movie_id is not None:
        movie = db.query(Movie).filter(
            Movie.id == item_data.movie_id
        ).first()

        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found.")

    if item_data.tv_show_id is not None:
        show = db.query(TVShow).filter(
            TVShow.id == item_data.tv_show_id
        ).first()

        if not show:
            raise HTTPException(
                status_code=404,
                detail="TV show not found.",
            )


    # Prevent duplicate movies or TV shows in the same list
    duplicate_query = db.query(ListItem).filter(
        ListItem.list_id == list_id
    )

    if item_data.movie_id is not None:
        duplicate_query = duplicate_query.filter(
            ListItem.movie_id == item_data.movie_id
        )
    else:
        duplicate_query = duplicate_query.filter(
            ListItem.tv_show_id == item_data.tv_show_id
        )

    if duplicate_query.first():
        raise HTTPException(
            status_code=409,
            detail="This movie or TV show is already in the list.",
        )

    new_item = ListItem(
        list_id=list_id,
        movie_id=item_data.movie_id,
        tv_show_id=item_data.tv_show_id,
        position=item_data.position,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {
        "id": new_item.id,
        "list_id": new_item.list_id,
        "movie_id": new_item.movie_id,
        "tv_show_id": new_item.tv_show_id,
        "position": new_item.position,
        "added_at": new_item.added_at,
    }


@router.get("/{list_id}")
def get_list_details(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_list = (
        db.query(List)
        .options(
            joinedload(List.items).joinedload(ListItem.movie),
            joinedload(List.items).joinedload(ListItem.tv_show),
        )
        .filter(List.id == list_id)
        .first()
    )

    if not user_list:
        raise HTTPException(
            status_code=404,
            detail="List not found.",
        )

    if not user_list.is_public and user_list.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="This list is private.",
        )

    items = sorted(
        user_list.items,
        key=lambda item: (
            item.position if item.position is not None else 2**31,
            item.id,
        ),
    )

    return {
        "id": user_list.id,
        "user_id": user_list.user_id,
        "name": user_list.name,
        "description": user_list.description,
        "is_public": user_list.is_public,
        "created_at": user_list.created_at,
        "updated_at": user_list.updated_at,
        "items": [
            {
                "id": item.id,
                "position": item.position,
                "added_at": item.added_at,
                "movie": {
                    "id": item.movie.id,
                    "title": item.movie.title,
                } if item.movie else None,
                "show": {
                    "id": item.tv_show.id,
                    "title": item.tv_show.name,
                } if item.tv_show else None,
            }
            for item in items
        ],
    }


@router.delete("/{list_id}/items/{item_id}")
def remove_list_item(
    list_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_list = (
        db.query(List)
        .filter(
            List.id == list_id,
            List.user_id == current_user.id,
        )
        .first()
    )

    if not user_list:
        raise HTTPException(
            status_code=404,
            detail="List not found.",
        )

    item = (
        db.query(ListItem)
        .filter(
            ListItem.id == item_id,
            ListItem.list_id == list_id,
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="List item not found.",
        )

    db.delete(item)
    db.commit()

    return {
        "message": "Item removed from list successfully.",
        "list_id": list_id,
        "item_id": item_id,
    }


@router.patch("/{list_id}")
def update_list(
    list_id: int,
    list_data: ListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_list = (
        db.query(List)
        .filter(
            List.id == list_id,
            List.user_id == current_user.id,
        )
        .first()
    )

    if not user_list:
        raise HTTPException(
            status_code=404,
            detail="List not found.",
        )

    updates = list_data.model_dump(exclude_unset=True)

    if "name" in updates:
        if updates["name"] is None or not updates["name"].strip():
            raise HTTPException(
                status_code=422,
                detail="List name cannot be empty.",
            )
        updates["name"] = updates["name"].strip()

    for field, value in updates.items():
        setattr(user_list, field, value)

    db.commit()
    db.refresh(user_list)

    return {
        "id": user_list.id,
        "user_id": user_list.user_id,
        "name": user_list.name,
        "description": user_list.description,
        "is_public": user_list.is_public,
        "created_at": user_list.created_at,
        "updated_at": user_list.updated_at,
    }


@router.delete("/{list_id}")
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_list = (
        db.query(List)
        .filter(
            List.id == list_id,
            List.user_id == current_user.id,
        )
        .first()
    )

    if not user_list:
        raise HTTPException(
            status_code=404,
            detail="List not found.",
        )

    db.delete(user_list)
    db.commit()

    return {
        "message": "List deleted successfully.",
        "list_id": list_id,
    }
