from fastapi import APIRouter, Depends, Request, HTTPException, Form, Response
from models import AccountsPayable
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette import status
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse


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
    po_amount: float
    invoice_amount: float
    balance: float
    fully_paid: bool

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
                         fully_paid: bool = Form(...),
                         po_amount: float = Form(0.0),
                         invoice_amount: float = Form(0.0)
                         ):
    project_model = db.query(AccountsPayable).filter(AccountsPayable.id == project_id).first()
    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')
    project_model.po_amount = po_amount
    project_model.invoice_amount = invoice_amount
    try:
        balance = po_amount - invoice_amount
        project_model.balance = balance
        if balance == 0:
            project_model.fully_paid = True
        else:
            project_model.fully_paid = False

    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail='Invalid amount')

    db.add(project_model)
    db.commit()

    response.headers["HX-Redirect"] = "/ap/projects"