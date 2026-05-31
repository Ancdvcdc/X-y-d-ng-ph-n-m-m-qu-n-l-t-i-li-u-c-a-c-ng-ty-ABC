from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
from uuid import uuid4
from typing import Optional
import shutil

from . import models, database, crud

models.Base.metadata.create_all(bind=database.engine)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploaded_files"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    db = database.SessionLocal()
    try:
        if not db.query(models.User).first():
            users = [
                models.User(username="admin", password="admin", role="Admin"),
                models.User(username="giamdoc", password="123", role="Giám đốc"),
                models.User(username="truongphong", password="123", role="Trưởng phòng"),
                models.User(username="nhanvien", password="123", role="Nhân viên"),
            ]
            db.add_all(users)
            db.commit()
    finally:
        db.close()

class LoginRequest(BaseModel):
    username: str
    password: str

class UpdateRequest(BaseModel):
    username: str
    title: Optional[str] = None
    password: Optional[str] = None

@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user(db, request.username)
    if not user or user.password != request.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai tài khoản hoặc mật khẩu")
    return {"username": user.username, "role": user.role}

@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = crud.get_documents(db)
    return [{"id": d.id, "title": d.title, "uploader": d.uploader.username, "date": d.upload_date} for d in docs]

@app.get("/")
def root():
    return {"detail": "Document Manager API is running"}

@app.post("/upload")
async def upload_document(
    title: str = Form(...),
    uploader: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = crud.get_user(db, uploader)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

    file_extension = Path(file.filename).suffix
    saved_name = f"{uuid4().hex}{file_extension}"
    saved_path = UPLOAD_DIR / saved_name
    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = crud.create_document(db, title=title, uploader_id=user.id, password=password, file_path=str(saved_path))
    crud.create_history(db, document.id, "Upload", user.id)
    return {
        "id": document.id,
        "title": document.title,
        "uploader": user.username,
        "date": document.upload_date,
        "file_path": document.file_path,
    }

@app.get("/download/{document_id}")
def download_document(document_id: int, password: str, username: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tài liệu không tồn tại")
    if document.password != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mật khẩu không đúng")
    if not Path(document.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tệp tin không tồn tại")

    crud.create_history(db, document_id, "Download", user.id)
    return FileResponse(path=document.file_path, filename=Path(document.file_path).name, media_type="application/octet-stream")

@app.put("/update/{document_id}")
def update_document(document_id: int, request: UpdateRequest, db: Session = Depends(get_db)):
    user = crud.get_user(db, request.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tài liệu không tồn tại")
    if user.role != "Admin" and document.uploader_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền sửa tài liệu")

    updated = crud.update_document(db, document, title=request.title, password=request.password)
    crud.create_history(db, document_id, "Update", user.id)
    return {"id": updated.id, "title": updated.title, "uploader": user.username, "date": updated.upload_date}

@app.delete("/delete/{document_id}")
def delete_document(document_id: int, username: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tài liệu không tồn tại")
    if user.role != "Admin" and document.uploader_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền xóa tài liệu")

    if document.file_path and Path(document.file_path).exists():
        Path(document.file_path).unlink()
    crud.delete_document(db, document)
    crud.create_history(db, document_id, "Delete", user.id)
    return {"detail": "Xóa tài liệu thành công"}

@app.get("/history/{document_id}")
def get_history(document_id: int, db: Session = Depends(get_db)):
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tài liệu không tồn tại")

    history_entries = crud.get_history(db, document_id)
    result = []
    for entry in history_entries:
        user = db.query(models.User).filter(models.User.id == entry.user_id).first()
        result.append(
            {
                "action": entry.action,
                "user": user.username if user else "Unknown",
                "timestamp": entry.timestamp,
            }
        )
    return result
