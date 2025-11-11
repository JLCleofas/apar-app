from fastapi import APIRouter, Depends
from models import AccountsPayable
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette import status


router = APIRouter(
    prefix='/ap',
    tags=['ap']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class ProjectRequest(BaseModel):
    project_name: str
    quotation: str
    acceptance: str
    vendor_po: str
    supplier: str
    document_type: str
    invoice_number: str
    date_paid: str
    dv_reference: str
    currency: str
    po_amount: str
    invoice_amount: str
    balance: str
    fully_paid: bool

### Endpoints ###
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(AccountsPayable).all()

@router.post("/project", status_code=status.HTTP_201_CREATED)
async def create_project(db: db_dependency, project_request: ProjectRequest):
    project_model = AccountsPayable(**project_request.model_dump())

    db.add(project_model)
    db.commit()