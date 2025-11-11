from fastapi import APIRouter, Depends, Request
from models import AccountsPayable
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette import status
from fastapi.templating import Jinja2Templates


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

templates = Jinja2Templates(directory="./templates")

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

### Pages ###
@router.get("/ap-page")
async def render_ap_page(request: Request, db: db_dependency):
    projects = db.query(AccountsPayable).all()

    return templates.TemplateResponse("accounts-payable.html", {"request": request, "projects": projects})


### Endpoints ###
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(AccountsPayable).all()

@router.post("/project", status_code=status.HTTP_201_CREATED)
async def create_project(db: db_dependency, project_request: ProjectRequest):
    project_model = AccountsPayable(**project_request.model_dump())

    db.add(project_model)
    db.commit()