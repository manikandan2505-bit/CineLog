
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserFollow
from app.security import get_current_user

router = APIRouter(prefix="/users", tags=["Follows"])


@router.post("/follow/{username}", status_code=status.HTTP_201_CREATED)
def follow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find the user to follow
    target_user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent following yourself
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself"
        )

    # Prevent duplicate follows
    existing_follow = (
        db.query(UserFollow)
        .filter(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == target_user.id
        )
        .first()
    )

    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already following this user"
        )

    new_follow = UserFollow(
        follower_id=current_user.id,
        following_id=target_user.id
    )

    db.add(new_follow)
    db.commit()
    db.refresh(new_follow)

    return {
        "message": f"You are now following {target_user.username}",
        "follow_id": new_follow.id,
        "follower_id": current_user.id,
        "following_id": target_user.id,
        "created_at": new_follow.created_at
    }


@router.delete("/unfollow/{username}")
def unfollow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find the user to unfollow
    target_user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot unfollow yourself"
        )

    existing_follow = (
        db.query(UserFollow)
        .filter(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == target_user.id
        )
        .first()
    )

    if not existing_follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not following this user"
        )

    db.delete(existing_follow)
    db.commit()

    return {
        "message": f"You have unfollowed {target_user.username}"
    }


@router.get("/{username}/followers")
def get_followers(
    username: str,
    db: Session = Depends(get_db)
):
    # Find the profile owner
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Find users who follow this profile
    follows = (
        db.query(UserFollow)
        .filter(UserFollow.following_id == user.id)
        .order_by(UserFollow.created_at.desc())
        .all()
    )

    return {
        "username": user.username,
        "total_followers": len(follows),
        "followers": [
            {
                "id": follow.follower.id,
                "username": follow.follower.username,
                "display_name": follow.follower.display_name,
                "avatar_url": follow.follower.avatar_url,
                "followed_at": follow.created_at
            }
            for follow in follows
        ]
    }


@router.get("/{username}/following")
def get_following(
    username: str,
    db: Session = Depends(get_db)
):
    # Find the profile owner
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Find profiles this user follows
    follows = (
        db.query(UserFollow)
        .filter(UserFollow.follower_id == user.id)
        .order_by(UserFollow.created_at.desc())
        .all()
    )

    return {
        "username": user.username,
        "total_following": len(follows),
        "following": [
            {
                "id": follow.following.id,
                "username": follow.following.username,
                "display_name": follow.following.display_name,
                "avatar_url": follow.following.avatar_url,
                "followed_at": follow.created_at
            }
            for follow in follows
        ]
    }
