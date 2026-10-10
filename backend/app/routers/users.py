from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User,DiaryEntry, TVShow,MovieRating,ShowRating,MovieReview,ShowReview,Favorite,WatchlistItem,UserFollow
from app.schemas import (
    UserCreate,
    UserResponse,
    UserProfileStatsResponse,
    UserProfileUpdate,
    PasswordChange,
    AccountDeleteRequest,
    PublicUserProfileResponse,
    UserLogin
)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_optional_current_user,
    get_current_user
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db)
):
    users = db.query(User).all()

    return users


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_username = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    existing_email = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        display_name=user_data.display_name,
        bio=user_data.bio,
        avatar_url=user_data.avatar_url
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = verify_password(
        form_data.password,
        user.password_hash
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get("/{username}", response_model=PublicUserProfileResponse)
def get_public_user_profile(
    username: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user)
):
    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    is_following = None

    if current_user is not None:
        is_following = (
                db.query(UserFollow)
                .filter(
                    UserFollow.follower_id == current_user.id,
                    UserFollow.following_id == user.id
                )
                .first()
                is not None
        )

    # Count distinct movies watched
    movie_ids = db.query(DiaryEntry.movie_id).filter(
        DiaryEntry.user_id == user.id,
        DiaryEntry.movie_id.isnot(None)
    ).distinct().all()

    total_movies_watched = len(movie_ids)

    # Count distinct episodes watched
    episode_ids = db.query(DiaryEntry.episode_id).filter(
        DiaryEntry.user_id == user.id,
        DiaryEntry.episode_id.isnot(None)
    ).distinct().all()

    total_episodes_watched = len(episode_ids)

    # Count ratings
    total_movie_ratings = db.query(MovieRating).filter(
        MovieRating.user_id == user.id
    ).count()

    total_show_ratings = db.query(ShowRating).filter(
        ShowRating.user_id == user.id
    ).count()

    # Count reviews
    total_movie_reviews = db.query(MovieReview).filter(
        MovieReview.user_id == user.id
    ).count()

    total_show_reviews = db.query(ShowReview).filter(
        ShowReview.user_id == user.id
    ).count()

    total_reviews = total_movie_reviews + total_show_reviews

    # Count favorites
    total_favorites = db.query(Favorite).filter(
        Favorite.user_id == user.id
    ).count()

    total_followers = (
        db.query(UserFollow)
        .filter(UserFollow.following_id == user.id)
        .count()
    )

    total_following = (
        db.query(UserFollow)
        .filter(UserFollow.follower_id == user.id)
        .count()
    )


    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "total_movies_watched": total_movies_watched,
        "total_episodes_watched": total_episodes_watched,
        "total_movie_ratings": total_movie_ratings,
        "total_show_ratings": total_show_ratings,
        "total_reviews": total_reviews,
        "total_favorites": total_favorites,
        "total_followers": total_followers,
        "total_following": total_following,
        "is_following": is_following,
    }


@router.get("/me/stats", response_model=UserProfileStatsResponse)
def get_current_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id

    # Get this user's diary entries
    diary_entries = db.query(DiaryEntry).filter(
        DiaryEntry.user_id == user_id
    ).all()

    # Count distinct movies watched
    total_movies_watched = len({
        entry.movie_id
        for entry in diary_entries
        if entry.movie_id is not None
    })

    # Count movie rewatches
    total_movie_rewatches = sum(
        1 for entry in diary_entries
        if entry.movie_id is not None and entry.rewatch
    )

    # Count distinct episodes watched
    total_episodes_watched = len({
        entry.episode_id
        for entry in diary_entries
        if entry.episode_id is not None
    })

    # Count distinct TV shows tracked through diary activity
    episode_ids = {
        entry.episode_id
        for entry in diary_entries
        if entry.episode_id is not None
    }

    show_ids = set()

    if episode_ids:
        from app.models import Episode

        episodes = db.query(Episode).filter(
            Episode.id.in_(episode_ids)
        ).all()

        show_ids = {
            episode.season.tv_show_id
            for episode in episodes
            if episode.season is not None
        }


    total_movie_ratings = db.query(MovieRating).filter(
        MovieRating.user_id == user_id
    ).count()

    total_show_ratings = db.query(ShowRating).filter(
        ShowRating.user_id == user_id
    ).count()


    total_movie_reviews = db.query(MovieReview).filter(
        MovieReview.user_id == user_id
    ).count()

    total_show_reviews = db.query(ShowReview).filter(
        ShowReview.user_id == user_id
    ).count()

    total_reviews = total_movie_reviews + total_show_reviews


    total_favorites = db.query(Favorite).filter(
        Favorite.user_id == user_id
    ).count()


    total_watchlist_items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user_id
    ).count()

    return {
        "total_movies_watched": total_movies_watched,
        "total_movie_rewatches": total_movie_rewatches,
        "total_episodes_watched": total_episodes_watched,
        "total_shows_tracked": len(show_ids),
        "total_movie_ratings": total_movie_ratings,
        "total_show_ratings": total_show_ratings,
        "total_reviews": total_reviews,
        "total_favorites": total_favorites,
        "total_watchlist_items": total_watchlist_items
    }


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user


@router.put("/me/password")
def change_current_user_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify the current password
    if not verify_password(
        password_data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    # Prevent reusing the current password
    if verify_password(
        password_data.new_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password"
        )

    # Hash and save the new password
    current_user.password_hash = hash_password(
        password_data.new_password
    )

    db.commit()

    return {"message": "Password changed successfully"}


@router.delete("/me")
def delete_current_user_account(
    password_data: AccountDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(
        password_data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    db.delete(current_user)
    db.commit()

    return {"message": "Account deleted successfully"}

