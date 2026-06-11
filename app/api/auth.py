from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.domain.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.api.schemas import UserSignup, UserLogin, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(user: UserSignup, db: Session = Depends(get_db)):

    existing = db.query(User).filter_by(email=user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email})

    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):

    existing = db.query(User).filter_by(email=user.email).first()

    if not existing or not verify_password(user.password, existing.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": existing.email})

    return TokenResponse(access_token=token)
