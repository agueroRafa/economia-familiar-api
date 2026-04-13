import os
import shutil
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import models, schemas
from .auth import create_access_token, hash_password, verify_password
from .database import Base, DATABASE_URL, engine
from .dependencies import get_current_user, get_db

Base.metadata.create_all(bind=engine)


def _ensure_sqlite_attachments_event_column():
    # Migration liviana para bases SQLite ya existentes.
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.connect() as connection:
        rows = connection.exec_driver_sql("PRAGMA table_info(attachments)").fetchall()
        columns = {row[1] for row in rows}
        if "event_id" not in columns:
            connection.exec_driver_sql("ALTER TABLE attachments ADD COLUMN event_id INTEGER")
            connection.commit()


_ensure_sqlite_attachments_event_column()


def _load_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

app = FastAPI(
    title="Economia Familiar by AguerattiSoft",
    description="API para gestionar gastos, deudas, ingresos y eventos familiares.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_load_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


def _validate_user_if_present(db: Session, user_id: int | None):
    if user_id is None:
        return
    exists = db.query(models.User).filter(models.User.id == user_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no existe")


@app.get("/")
def root():
    return {"app": "Economia Familiar by AguerattiSoft", "status": "ok"}


@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ese email ya esta registrado")

    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    token = create_access_token(subject=user.email)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/expenses", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(
    payload: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _validate_user_if_present(db, payload.assigned_to_user_id)
    _validate_user_if_present(db, payload.paid_by_user_id)
    item = models.Expense(created_by_user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/expenses", response_model=List[schemas.ExpenseOut])
def list_expenses(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    return db.query(models.Expense).order_by(models.Expense.created_at.desc()).all()


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    item = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    db.delete(item)
    db.commit()
    return None


@app.post("/debts", response_model=schemas.DebtOut, status_code=201)
def create_debt(
    payload: schemas.DebtCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _validate_user_if_present(db, payload.assigned_to_user_id)
    _validate_user_if_present(db, payload.paid_by_user_id)
    item = models.Debt(created_by_user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/debts", response_model=List[schemas.DebtOut])
def list_debts(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Debt).order_by(models.Debt.created_at.desc()).all()


@app.delete("/debts/{debt_id}", status_code=204)
def delete_debt(debt_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    item = db.query(models.Debt).filter(models.Debt.id == debt_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")
    db.delete(item)
    db.commit()
    return None


@app.post("/incomes", response_model=schemas.IncomeOut, status_code=201)
def create_income(
    payload: schemas.IncomeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _validate_user_if_present(db, payload.assigned_to_user_id)
    item = models.Income(created_by_user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/incomes", response_model=List[schemas.IncomeOut])
def list_incomes(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Income).order_by(models.Income.created_at.desc()).all()


@app.delete("/incomes/{income_id}", status_code=204)
def delete_income(income_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    item = db.query(models.Income).filter(models.Income.id == income_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    db.delete(item)
    db.commit()
    return None


@app.post("/events", response_model=schemas.EventOut, status_code=201)
def create_event(
    payload: schemas.EventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _validate_user_if_present(db, payload.assigned_to_user_id)
    item = models.Event(created_by_user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/events", response_model=List[schemas.EventOut])
def list_events(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Event).order_by(models.Event.created_at.desc()).all()


@app.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    item = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    db.delete(item)
    db.commit()
    return None


def _save_upload(file: UploadFile) -> tuple[str, str]:
    extension = os.path.splitext(file.filename or "")[1]
    safe_name = f"{uuid4().hex}{extension}"
    full_path = UPLOADS_DIR / safe_name
    with full_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return safe_name, str(full_path)


@app.post("/expenses/{expense_id}/attachments", response_model=schemas.AttachmentOut, status_code=201)
def upload_expense_attachment(
    expense_id: int,
    kind: str = "ticket",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    parent = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    _, saved_path = _save_upload(file)
    attachment = models.Attachment(
        kind=kind,
        original_filename=file.filename or "archivo",
        saved_path=saved_path,
        mime_type=file.content_type,
        uploaded_by_user_id=current_user.id,
        expense_id=expense_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@app.post("/debts/{debt_id}/attachments", response_model=schemas.AttachmentOut, status_code=201)
def upload_debt_attachment(
    debt_id: int,
    kind: str = "ticket",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    parent = db.query(models.Debt).filter(models.Debt.id == debt_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")
    _, saved_path = _save_upload(file)
    attachment = models.Attachment(
        kind=kind,
        original_filename=file.filename or "archivo",
        saved_path=saved_path,
        mime_type=file.content_type,
        uploaded_by_user_id=current_user.id,
        debt_id=debt_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@app.post("/incomes/{income_id}/attachments", response_model=schemas.AttachmentOut, status_code=201)
def upload_income_attachment(
    income_id: int,
    kind: str = "comprobante",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    parent = db.query(models.Income).filter(models.Income.id == income_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    _, saved_path = _save_upload(file)
    attachment = models.Attachment(
        kind=kind,
        original_filename=file.filename or "archivo",
        saved_path=saved_path,
        mime_type=file.content_type,
        uploaded_by_user_id=current_user.id,
        income_id=income_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@app.post("/events/{event_id}/attachments", response_model=schemas.AttachmentOut, status_code=201)
def upload_event_attachment(
    event_id: int,
    kind: str = "documento",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    parent = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    _, saved_path = _save_upload(file)
    attachment = models.Attachment(
        kind=kind,
        original_filename=file.filename or "archivo",
        saved_path=saved_path,
        mime_type=file.content_type,
        uploaded_by_user_id=current_user.id,
        event_id=event_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@app.get("/attachments", response_model=List[schemas.AttachmentOut])
def list_attachments(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Attachment).order_by(models.Attachment.uploaded_at.desc()).all()


@app.get("/dashboard", response_model=schemas.DashboardOut)
def get_dashboard(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    expenses = db.query(models.Expense).all()
    debts = db.query(models.Debt).all()
    incomes = db.query(models.Income).all()

    total_expenses = sum(item.amount for item in expenses)
    total_debts = sum(item.amount for item in debts)
    total_incomes = sum(item.amount for item in incomes)

    return {
        "total_expenses": total_expenses,
        "total_debts": total_debts,
        "total_incomes": total_incomes,
        "balance": total_incomes - (total_expenses + total_debts),
    }
