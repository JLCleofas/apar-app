from decimal import Decimal
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Response
from models import APProject, Invoice, TransactionLog
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
    currency: str = Field(min_length=3, max_length=3)
    total_po_amount: float = Field(default=0.0)
    total_paid: Optional[float] = Field(default=0.0)
    balance: Optional[float] = Field(default=0.0)
    fully_paid: bool = Field(default=False)

class InvoiceRequest(BaseModel):
    vendor: str = Field(min_length=1, max_length=50)
    vendor_po: str = Field(min_length=14, max_length=14)
    invoice_type: Optional[str] = Field(max_length=20, default=None)
    invoice_number: Optional[str] = Field(max_length=30, default=None)

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
    projects = db.query(APProject).all()

    return templates.TemplateResponse("accounts-payable.html", {"request": request, "projects": projects})

@router.get("/details/{project_id}")
async def render_project_details(request: Request, db: db_dependency, project_id: int):
    project_model = db.query(APProject).filter(APProject.id == project_id).first()
    return templates.TemplateResponse("ap-details.html", {"request": request, "project": project_model})

@router.get("/add-project-page")
async def render_add_project_page(request: Request):
    return templates.TemplateResponse("add-project.html", {"request": request})

@router.get("/add-transaction/{project_id}")
async def render_add_transaction_page(request: Request, db: db_dependency, project_id: int):
    project_model = db.query(APProject).filter(APProject.id == project_id).first()
    return templates.TemplateResponse("ap-add-transaction.html", {"request": request, "project":project_model})

@router.get("/transaction-history/{project_id}")
async def render_transaction_history_page(request: Request, db: db_dependency, project_id: int):
    project_model = db.query(APProject).filter(APProject.id == project_id).first()
    transaction_logs = db.query(TransactionLog).filter(TransactionLog.project_id == project_id).all()
    return templates.TemplateResponse("ap-transaction-history.html", {"request": request, "project":project_model, "transactions":transaction_logs})

@router.get("/record-invoice/{project_id}")
async def render_record_invoice_page(request: Request, db: db_dependency, project_id: int):
    project_model = db.query(APProject).filter(APProject.id == project_id).first()
    return templates.TemplateResponse("ap-record-invoice.html", {"request": request, "project":project_model})
### Endpoints ###

## TODO: Add delete project endpoint
## TODO: Add search functionality
## TODO: Add report generation
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(APProject).all()

@router.post("/project", status_code=status.HTTP_201_CREATED)
async def create_project(db: db_dependency, project_request: ProjectRequest):
    project_data = project_request.model_dump()

    try:
        po_amount = project_data['po_amount']
        invoice_amount = project_data['invoice_amount']
        project_data['balance'] = po_amount - invoice_amount
    except (ValueError, TypeError):
        project_data['balance'] = 0

    project_model = APProject(**project_data)
    db.add(project_model)
    db.commit()


@router.post("/add-project", status_code=status.HTTP_201_CREATED)
async def add_project(
        response: Response,
        db: db_dependency,
        client: str = Form(...),
        quotation: str = Form(...),
        acceptance: str = Form(...),
        currency: str = Form(...),
        total_po_amount: Decimal = Form(...)
):
    project_data = {
        "client": client,
        "quotation": quotation,
        "acceptance": acceptance,
        "currency": currency,
        "total_po_amount": total_po_amount,
        "total_paid": 0,
        "balance": total_po_amount,
    }

    project_model = APProject(**project_data)
    db.add(project_model)
    db.commit()

    response.headers["HX-Redirect"] = "/ap/projects"


@router.post("/project/{project_id}", status_code=status.HTTP_201_CREATED)
async def add_transaction(response: Response,
                         db: db_dependency,
                         project_id: int,
                         document_type: Optional[str] = Form(None),
                         transaction_amount: Decimal = Form(Decimal("0")),
                         dv_reference: Optional[str] = Form(None),
                         date_paid: date = Form(...),
                         ):
    project_model = db.query(APProject).filter(APProject.id == project_id).first()
    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')

    transaction_data = {
        "document_type": document_type,
        "transaction_amount": transaction_amount,
        "dv_reference": dv_reference,
        "date_paid": date_paid,
        "project_id": project_id,
    }
    try:
        project_model.invoice_amount += transaction_amount
        ## TODO: Add condition to subtract only if DV-Reference is not None.
        ## TODO: Add error handling when balance is lower than invoice amount.
        ## TODO: Add error handling to prevent negative balance.
        project_model.balance = project_model.po_amount - project_model.invoice_amount

        if project_model.balance == 0:
            project_model.fully_paid = True
        else:
            project_model.fully_paid = False

    except (ValueError, TypeError, ArithmeticError):
        raise HTTPException(status_code=400, detail='Invalid amount')


    transaction_model = TransactionLog(**transaction_data)
    db.add(transaction_model)
    db.add(project_model)
    db.commit()

    response.headers["HX-Redirect"] = f"/ap/details/{project_model.id}"