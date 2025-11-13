from decimal import Decimal
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Response
from models import AccountsPayable
from database import SessionLocal
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from starlette import status
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from datetime import date


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
    project_name: str = Field(min_length=1, max_length=100)
    quotation: str = Field(min_length=14, max_length=20)
    acceptance: str = Field(min_length=14, max_length=14)
    vendor_po: str = Field(min_length=14, max_length=14)
    supplier: str = Field(min_length=1, max_length=50)
    document_type: Optional[str] = Field(max_length=20, default=None)
    invoice_number: Optional[str] = Field(max_length=30, default=None)
    date_paid: Optional[date] = Field(default=None)
    dv_reference: Optional[str] = Field(max_length=11, default=None)
    currency: str = Field(min_length=3, max_length=3)
    po_amount: float = Field(default=0.0)
    invoice_amount: Optional[float] = Field(default=0.0)
    balance: Optional[float] = Field(default=0.0)
    fully_paid: bool = Field(default=False)

class TransactionRequest(BaseModel):
    document_type: str = Field(max_length=20, default=None)
    invoice_amount: float = Field(default=0.0)
    date_paid: date = Field(default=None)
    dv_reference: Optional[str] = Field(max_length=11, default=None)



def redirect_to_projects_page():
    redirect_response = RedirectResponse(url="/ap/projects", status_code=status.HTTP_302_FOUND)

    return redirect_response

### Pages ###
@router.get("/projects")
async def render_ap_page(request: Request, db: db_dependency):
    projects = db.query(AccountsPayable).all()

    return templates.TemplateResponse("accounts-payable.html", {"request": request, "projects": projects})

@router.get("/details/{project_id}")
async def render_project_details(request: Request, db: db_dependency, project_id: int):
    project_model = db.query(AccountsPayable).filter(AccountsPayable.id == project_id).first()
    return templates.TemplateResponse("ap-details.html", {"request": request, "project": project_model})

### Endpoints ###
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(AccountsPayable).all()

@router.post("/project", status_code=status.HTTP_201_CREATED)
async def create_project(db: db_dependency, project_request: ProjectRequest):
    project_data = project_request.model_dump()

    try:
        po_amount = project_data['po_amount']
        invoice_amount = project_data['invoice_amount']
        project_data['balance'] = po_amount - invoice_amount
    except (ValueError, TypeError):
        project_data['balance'] = 0

    project_model = AccountsPayable(**project_data)
    db.add(project_model)
    db.commit()

@router.put("/project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_project(response: Response,
                         db: db_dependency,
                         project_id: int,
                         document_type: Optional[str] = Form(None),
                         invoice_amount: Decimal = Form(Decimal("0")),
                         dv_reference: Optional[str] = Form(None),
                         date_paid: date = Form(...),
                         ):
    project_model = db.query(AccountsPayable).filter(AccountsPayable.id == project_id).first()
    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')
    project_model.document_type = document_type
    project_model.invoice_amount = invoice_amount
    project_model.dv_reference = dv_reference
    project_model.date_paid = date_paid
    try:
        po_amount = project_model.po_amount
        balance = po_amount - invoice_amount
        project_model.balance = balance
        if balance == 0:
            project_model.fully_paid = True
        else:
            project_model.fully_paid = False

    except (ValueError, TypeError, ArithmeticError):
        raise HTTPException(status_code=400, detail='Invalid amount')

    db.add(project_model)
    db.commit()

    response.headers["HX-Redirect"] = "/ap/projects"