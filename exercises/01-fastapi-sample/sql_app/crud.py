from sqlalchemy.orm import Session
import secrets

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_api_token(db: Session, api_token: str):
    return db.query(models.User).filter(models.User.api_token == api_token).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_minimum_id_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id < user_id, models.User.is_active == True).order_by(models.User.id).first()

def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    api_token = secrets.token_hex(32)
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password, api_token=api_token)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def get_items_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Item).filter(models.Item.owner_id == user_id).offset(skip).limit(limit).all()

def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_user_with_transfer(db: Session, source_user_id: int, target_user_id: int):
    db.query(models.User).filter(models.User.id == source_user_id).update({models.User.is_active: False}, synchronize_session="fetch")
    items = db.query(models.Item).filter(models.Item.owner_id == source_user_id).update({models.Item.owner_id: target_user_id}, synchronize_session="fetch")
    db.commit()
    return items