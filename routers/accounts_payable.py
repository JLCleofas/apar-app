from decimal import Decimal
from locale import currency

from fastapi import APIRouter, Depends, Request, HTTPException, Form, Response
from models import APProject, Invoice, Transaction, POToVendor
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


def redirect_to_projects_page():
    redirect_response = RedirectResponse(url="/ap/projects", status_code=status.HTTP_302_FOUND)

    return redirect_response


### Pages ###
@router.get("/projects")
async def render_ap_page(request: Request, db: db_dependency):
    projects = db.query(APProject).filter(APProject.is_deleted == False).all()

    return templates.TemplateResponse("accounts-payable.html", {"request": request, "projects": projects})


@router.get("/details/{project_id}")
async def render_project_details(request: Request, db: db_dependency, project_id: int):
    project_model = db.query(APProject).filter(APProject.id == project_id).filter(APProject.is_deleted == False).first()

    if project_model is None:
        return templates.TemplateResponse("not-found.html", {"request": request})

    vendor_po_list = db.query(POToVendor).filter(POToVendor.project_id == project_id).filter(POToVendor.is_deleted == False).all()
    return templates.TemplateResponse("ap-details.html", {"request": request, "project": project_model, "vendor_po_list": vendor_po_list})


@router.get("/add-project-page")
async def render_add_project_page(request: Request):
    return templates.TemplateResponse("add-project.html", {"request": request})


@router.get("/add-vendor-po-page/{project_id}")
async def render_add_vendor_po_page(request: Request, db: db_dependency, project_id: int):
    project_model = db.query(APProject).filter(APProject.id == project_id).first()

    if project_model is None:
        return templates.TemplateResponse("not-found.html", {"request": request})

    return templates.TemplateResponse("ap-add-vendor-po.html", {"request": request, "project": project_model})


@router.get("/add-transaction-page/{project_id}")
async def render_add_transaction_page(request: Request, db: db_dependency, project_id: int):
    invoice_list = db.query(Invoice).filter(Invoice.project_id == project_id).filter(Invoice.is_deleted == False).all()
    project_model = db.query(APProject).filter(APProject.id == project_id).first()
    if project_model is None:
        return templates.TemplateResponse("not-found.html", {"request": request})
    return templates.TemplateResponse("ap-add-transaction.html",
                                      {"request": request, "project": project_model, "invoice_list": invoice_list})


@router.get("/transaction-history-page/{project_id}")
async def render_transaction_history_page(request: Request, db: db_dependency, project_id: int):
    project_model = db.query(APProject).filter(APProject.id == project_id).first()

    if project_model is None:
        return templates.TemplateResponse("not-found.html", {"request": request})

    transaction_logs = db.query(Transaction).filter(Transaction.project_id == project_id).all()
    return templates.TemplateResponse("ap-transaction-history.html",
                                      {"request": request, "project": project_model, "transactions": transaction_logs})


@router.get("/record-invoice-page/{project_id}")
async def render_record_invoice_page(request: Request, db: db_dependency, project_id: int):
    vendor_po_list = db.query(POToVendor).filter(POToVendor.project_id == project_id).all()
    project_model = db.query(APProject).filter(APProject.id == project_id).first()

    if project_model is None:
        return templates.TemplateResponse("not-found.html", {"request": request})

    return templates.TemplateResponse("ap-record-invoice.html",
                                      {"request": request, "project": project_model, "vendor_po_list": vendor_po_list})

@router.get("/vendor-po-details-page/{vendor_po_id}")
async def render_vendor_po_page(request: Request, db: db_dependency, vendor_po_id: int):
    vendor_po_model = db.query(POToVendor).filter(POToVendor.is_deleted == False).filter(POToVendor.id == vendor_po_id).first()

    if vendor_po_model is None:
        return templates.TemplateResponse("not-found.html", {"request": request})

    invoice_list = db.query(Invoice).filter(Invoice.is_deleted == False).filter(Invoice.vendor_po_id == vendor_po_id).all()

    return templates.TemplateResponse("ap-vendor-po-details.html", {"request": request, "po_to_vendor": vendor_po_model, "invoices": invoice_list})


### Endpoints ###

## TODO: Add search functionality
## TODO: Add report generation
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(APProject).filter(APProject.is_deleted == False).all()

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
    existing_project = db.query(APProject).filter(APProject.quotation == quotation).filter(APProject.is_deleted == False).first()
    if existing_project:
        raise HTTPException(status_code=409, detail="Project already exists")
    project_data = {
        "client": client,
        "quotation": quotation,
        "acceptance": acceptance,
        "currency": currency,
        "total_po_amount": total_po_amount,
        "total_paid": 0,
        "balance": total_po_amount,
    }

    if total_po_amount <= 0:
        raise HTTPException(status_code=409, detail="Total PO amount must be greater than 0")

    project_model = APProject(**project_data)
    db.add(project_model)
    db.commit()

    response.headers["HX-Redirect"] = "/ap/projects"
    return None


# TODO: Add error handling for invoices that exceed PO amount
# TODO: Add error handling for negative invoice amounts
# TODO: Add error handling for zero invoice amounts
# TODO: Add error handling for isDeleted column

@router.post("/add-vendor-po/{project_id}", status_code=status.HTTP_201_CREATED)
async def add_vendor_po(response: Response,
                        db: db_dependency,
                        project_id: int,
                        vendor_po: str = Form(...),
                        vendor: str = Form(...),
                        po_amount: Decimal = Form(...),
                        ):
    currency = db.query(APProject).filter(APProject.id == project_id).first().currency
    vendor_po_data = {
        "project_id": project_id,
        "vendor_po": vendor_po,
        "vendor": vendor,
        "po_amount": po_amount,
        "currency": currency,
        "balance": po_amount
    }

    existing_vendor_po = db.query(POToVendor).filter(POToVendor.vendor_po == vendor_po).filter(POToVendor.is_deleted == False).first()

    total_project_balance = db.query(APProject).filter(APProject.id == project_id).filter(APProject.is_deleted == False).first().balance

    if existing_vendor_po:
        raise HTTPException(status_code=409, detail="Vendor already exists")

    if po_amount <= 0:
        raise HTTPException(status_code=422, detail="PO amount must be greater than 0")

    if po_amount > total_project_balance:
        raise HTTPException(status_code=422, detail="PO amount is more than the balance")

    vendor_po_model = POToVendor(**vendor_po_data)
    db.add(vendor_po_model)
    db.commit()

    response.headers["HX-Redirect"] = f"/ap/details/{project_id}"
    return None


@router.post("/record-invoice/{project_id}", status_code=status.HTTP_201_CREATED)
async def add_invoice(db: db_dependency,
                      project_id: int,
                      vendor_po_id: str = Form(...),
                      invoice_type: str = Form(...),
                      invoice_number: str = Form(...),
                      invoice_amount: Decimal = Form(Decimal("0"))
                      ):
    currency = db.query(APProject).filter(APProject.id == project_id).first().currency
    invoice_data = {
        "project_id": project_id,
        "vendor_po_id": vendor_po_id,
        "invoice_type": invoice_type,
        "invoice_number": invoice_number,
        "invoice_amount": invoice_amount,
        "currency": currency
    }

    existing_invoice = db.query(Invoice).filter(Invoice.project_id == project_id).filter(Invoice.invoice_number == invoice_number).first()
    if existing_invoice:
        raise HTTPException(status_code=409, detail="Invoice already exists")

    invoice_model = Invoice(**invoice_data)
    db.add(invoice_model)
    db.commit()


# TODO: Add error handling for negative transaction amounts
# TODO: Add error handling for zero transaction amounts
# TODO: Add error handling for DV-Reference not being unique
# TODO: Add error handling for DV-Reference not being 11 characters long
# TODO: Add error handling for transaction amount higher than po_amount
@router.post("/add-transaction/{project_id}", status_code=status.HTTP_201_CREATED)
async def add_transaction(response: Response,
                          db: db_dependency,
                          project_id: int,
                          invoice_id: int = Form(...),
                          transaction_amount: Decimal = Form(Decimal("0")),
                          dv_reference: str = Form(...),
                          date_paid: date = Form(date.today())
                          ):
    project_model = db.query(APProject).filter(APProject.id == project_id).first()
    vendor_po_model = db.query(POToVendor).filter(POToVendor.project_id == project_id).first()
    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')


    vendor_po_id = db.query(POToVendor).filter(POToVendor.project_id == project_id).first().id

    transaction_data = {
        "transaction_amount": transaction_amount,
        "dv_reference": dv_reference,
        "date_paid": date_paid,
        "project_id": project_id,
        "vendor_po_id": vendor_po_id,
        "invoice_id": invoice_id,
    }
    try:
        # vendor_po_model.balance = vendor_po_model.po_amount - transaction_amount
    ## TODO: Add condition to subtract only if DV-Reference is not None.
    ## TODO: Add error handling when balance is lower than invoice amount.
    ## TODO: Add error handling to prevent negative balance.
    # TODO: If transaction amount == invoice amount, soft delete the invoice
        project_model.balance -= transaction_amount
        vendor_po_model.balance -= transaction_amount
        project_model.total_paid += transaction_amount
        project_model.balance = project_model.total_po_amount - project_model.total_paid

        if vendor_po_model.balance == 0:
            vendor_po_model.is_paid = True
        else:
            vendor_po_model.is_paid = False

        if project_model.balance == 0:
            project_model.fully_paid = True
        else:
            project_model.fully_paid = False

    except (ValueError, TypeError, ArithmeticError):
        raise HTTPException(status_code=400, detail='Invalid amount')

    transaction_model = Transaction(**transaction_data)
    db.add(transaction_model)
    db.add(project_model)
    db.commit()

    response.headers["HX-Redirect"] = f"/ap/details/{project_model.id}"


@router.put("/delete-project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(db: db_dependency, project_id: int):

    project_model = db.query(APProject).filter(APProject.id == project_id).filter(APProject.is_deleted == False).first()

    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')

    project_model.is_deleted = True

    db.add(project_model)
    db.commit()