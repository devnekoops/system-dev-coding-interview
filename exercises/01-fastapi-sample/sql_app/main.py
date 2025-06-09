from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Header
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_session = Depends(get_db)


## 共通で使う認証用のDependsを定義

def verify_token(x_api_token: str = Header(None), db: Session = db_session) -> models.User:
    if x_api_token is None:
        raise HTTPException(status_code=401, detail="API token is required")
    user = crud.get_user_by_api_token(db, api_token=x_api_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return user

request_user = Depends(verify_token)


@app.get("/health-check")
def health_check(db: Session = db_session, _request_user = request_user):
    return {"status": "ok"}


@app.post("/users/", response_model=schemas.UserWithToken)
def create_user(user: schemas.UserCreate, db: Session = db_session):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = db_session, _request_user = request_user):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = db_session, _request_user = request_user):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = db_session, _request_user = request_user):
    # ユーザが有効化どうか確認
    delete_user = crud.get_user(db, user_id)
    if delete_user is None:
        raise HTTPException(status_code=404, detail=f"user_id={user_id} not found")

    if not delete_user.is_active:
        raise HTTPException(status_code=409, detail=f"user_id={user_id} is already deactivated")
    
    # Itemを移すユーザがいるか確認
    transfer_user = crud.get_minimum_id_user(db, user_id=user_id)
    if transfer_user is None:
        raise HTTPException(status_code=403, detail="No eligible user found to transfer item ownership")
    
    item_count = crud.delete_user_with_transfer(db, user_id, transfer_user.id)
    return {"status": f"{item_count} items were transferred to user_id={transfer_user.id}"}


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = db_session, _request_user = request_user
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = db_session, _request_user = request_user):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@app.get("/me/items/", response_model=List[schemas.Item])
def read_my_items(skip: int = 0, limit: int = 100, db: Session = db_session, request_user = request_user):
    request_user_id = request_user.id
    users = crud.get_items_by_user_id(db, request_user_id, skip=skip, limit=limit)
    return users