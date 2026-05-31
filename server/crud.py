from typing import Optional

from sqlalchemy.orm import Session
from . import models

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session):
    return db.query(models.User).all()

def get_documents(db: Session):
    return db.query(models.Document).all()

def get_document(db: Session, document_id: int):
    return db.query(models.Document).filter(models.Document.id == document_id).first()

def create_document(db: Session, title: str, uploader_id: int, password: str, file_path: str):
    doc = models.Document(title=title, uploader_id=uploader_id, password=password, file_path=file_path)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def create_user(db: Session, username: str, password: str, role: str):
    user = models.User(username=username, password=password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user: models.User, username: Optional[str] = None, password: Optional[str] = None, role: Optional[str] = None):
    if username is not None:
        user.username = username
    if password is not None:
        user.password = password
    if role is not None:
        user.role = role
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user: models.User):
    db.delete(user)
    db.commit()

def update_document(db: Session, document: models.Document, title: Optional[str] = None, password: Optional[str] = None):
    if title is not None:
        document.title = title
    if password is not None:
        document.password = password
    db.commit()
    db.refresh(document)
    return document

def delete_document(db: Session, document: models.Document):
    db.delete(document)
    db.commit()

def create_history(db: Session, document_id: int, action: str, user_id: int):
    history = models.History(document_id=document_id, action=action, user_id=user_id)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def get_history(db: Session, document_id: int):
    return (
        db.query(models.History)
        .filter(models.History.document_id == document_id)
        .order_by(models.History.timestamp.desc())
        .all()
    )
